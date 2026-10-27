"""The member page: the data of one member of parliament, as JSON.

Route: /member/<member_id>. The key is persons.id. An unknown key gives None.
The page shows terms, typical subjects, places, specific subjects, one mark per speech, and house turns.
Every query is read-only.
"""
import re
from collections import Counter

from sqlalchemy import text

from pages.common import SPEECH_TAGS_CTE, cached, slug, speech_rows, speech_tags_cte

# A tag that more than this share of all tagged speeches carry is "very general".
GENERAL_SHARE = 0.03
# A tag needs at least this many speeches of the member, and this many speeches in all.
MIN_MEMBER = 3
MIN_ALL = 20
SHORT_TURN = 25  # words


def split_name(raw):
    """Split 'Ravindra Shukla Alias Ravi Kishan' into ('Ravindra Shukla', 'Ravi Kishan')."""
    m = re.split(r"\s+\(?alias\)?\s+", raw, maxsplit=1, flags=re.I)
    return (m[0].strip(), m[1].strip()) if len(m) == 2 else (raw.strip(), None)


def global_tags(conn):
    """Return the speech count of each tag over the whole corpus, and the number of tagged speeches.

    The result changes only when the tags are loaded again, so the function keeps it for one hour.
    """
    def load():
        rows = conn.execute(text(f"""
            WITH {SPEECH_TAGS_CTE}
            SELECT t.id, t.tag, t.type, count(*) AS n FROM speech_tags st JOIN tags t ON t.id = st.tag_id GROUP BY t.id"""
        )).mappings().all()
        total = conn.execute(text(f"WITH {SPEECH_TAGS_CTE} SELECT count(DISTINCT speech_id) FROM speech_tags")).scalar()
        return {r["id"]: dict(r) for r in rows}, total
    return cached("global_tags", load)


def member_tag_rows(conn, person_id, terms=None):
    """Return (speech_id, term, tag_id) rows for the tagged speeches of one member, optionally in some terms."""
    cte = speech_tags_cte("si.speech_id IN (SELECT id FROM speeches WHERE person_id = :p)")
    return conn.execute(text(f"""
        WITH {cte}
        SELECT st.speech_id, d.loksabha AS term, st.tag_id
        FROM speech_tags st JOIN speeches s ON s.id = st.speech_id JOIN debates d ON d.id = s.debate_id
        WHERE (CAST(:terms AS int[]) IS NULL OR d.loksabha = ANY(CAST(:terms AS int[])))"""),
        {"p": person_id, "terms": list(terms) if terms else None}).all()


def lift(member_n, member_total, all_n, all_total):
    """Share of the member's tagged speeches with the tag, divided by the same share over all tagged speeches."""
    return round((member_n / member_total) / (all_n / all_total), 1)


def pick_typical(mrows, gtags, gtotal, mtotal):
    """Split the member's tag counts into typical subjects and places. Return both lists, sorted by a stated rule.

    Typical subjects sort by lift (high first), then by the member's count. Places sort by the member's count.
    """
    typical, places = [], []
    for tag_id, n in mrows:
        g = gtags[tag_id]
        base = {"name": g["tag"], "slug": slug(g["tag"]), "type": g["type"], "n": n, "all": g["n"]}
        if g["type"] == "place":
            places.append(base)
            continue
        if g["type"] in ("role", "person"):
            continue
        if g["n"] / gtotal > GENERAL_SHARE or g["n"] < MIN_ALL or n < MIN_MEMBER:
            continue
        base["lift"] = lift(n, mtotal, g["n"], gtotal)
        typical.append(base)
    typical.sort(key=lambda x: (-x["lift"], -x["n"]))
    places.sort(key=lambda x: (-x["n"], x["name"]))
    return typical, places


def party_path(term_list):
    path = []
    for t in term_list:
        for party in t["parties"]:
            if not path or path[-1] != party:
                path.append(party)
    return path


def member_page(conn, member_id, args=None):
    try:
        pid = int(member_id)
    except (TypeError, ValueError):
        return None
    pe = conn.execute(text("SELECT id, name FROM persons WHERE id = :p"), {"p": pid}).mappings().first()
    if pe is None:
        return None
    gtags, gtotal = global_tags(conn)
    pid = pe["id"]
    name, known_as = split_name(pe["name"])
    p = {"p": pid}

    seats = conn.execute(text("""
        SELECT sp.lok_sabha_term AS term, sp.constituency, st.name AS state, pa.code AS party, sp.effective_from
        FROM speakers sp LEFT JOIN parties pa ON pa.id = sp.party_id LEFT JOIN states st ON st.id = sp.state_id
        WHERE sp.person_id = :p ORDER BY 1, 4"""), p).mappings().all()
    counts = {r["term"]: r for r in conn.execute(text("""
        SELECT d.loksabha AS term, count(*) AS n, sum(s.word_count) AS words,
               min(d.debate_date) AS first, max(d.debate_date) AS last
        FROM speeches s JOIN debates d ON d.id = s.debate_id WHERE s.person_id = :p GROUP BY 1"""), p).mappings().all()}
    terms = {}
    for r in seats:
        t = terms.setdefault(r["term"], {"term": r["term"], "seat": None, "state": None, "parties": []})
        if r["constituency"]:
            t["seat"], t["state"] = r["constituency"], r["state"]
        if r["party"] and r["party"] not in t["parties"]:
            t["parties"].append(r["party"])
    for tnum in counts:
        terms.setdefault(tnum, {"term": tnum, "seat": None, "state": None, "parties": []})
    for tnum, t in terms.items():
        r = counts.get(tnum)
        t["speeches"] = r["n"] if r else 0
        t["words"] = int(r["words"] or 0) if r else 0
        t["first"] = r["first"].isoformat() if r and r["first"] else None
        t["last"] = r["last"].isoformat() if r and r["last"] else None
    term_list = [terms[k] for k in sorted(terms)]

    # The tags of the member's speeches only. The shared CTE gets one more condition, so the scan stays small.
    mine_cte = speech_tags_cte("si.speech_id IN (SELECT id FROM speeches WHERE person_id = :p)")
    pairs = conn.execute(text(f"WITH {mine_cte} SELECT speech_id, tag_id FROM speech_tags"), p).all()
    mtotal = len({sp for sp, _ in pairs})
    per_tag = Counter(tag_id for _, tag_id in pairs)
    typical, places = pick_typical(list(per_tag.items()), gtags, gtotal, mtotal) if mtotal else ([], [])

    # Specific subjects: subjects of the entity names of the member's kept items.
    # The order is n * n / all, which rewards a high count and a high share of the subject's speeches.
    # The stored subjects.n_speeches is not used, because it does not match the kept items.
    mine = conn.execute(text("""
        SELECT su.id, su.label, t.tag AS parent, count(DISTINCT si.speech_id) AS n
        FROM speech_items si JOIN speeches s ON s.id = si.speech_id
        JOIN subject_names sn ON sn.entity_name_id = si.entity_name_id
        JOIN subjects su ON su.id = sn.subject_id LEFT JOIN tags t ON t.id = su.parent_tag_id
        WHERE si.kept AND s.person_id = :p AND lower(su.label) <> lower(COALESCE(t.tag, ''))
        GROUP BY su.id, t.id HAVING count(DISTINCT si.speech_id) >= 2"""), p).mappings().all()
    allc = {r["id"]: r["n"] for r in conn.execute(text("""
        SELECT sn.subject_id AS id, count(DISTINCT si.speech_id) AS n
        FROM speech_items si JOIN subject_names sn ON sn.entity_name_id = si.entity_name_id
        WHERE si.kept AND sn.subject_id = ANY(:ids) GROUP BY 1"""), {"ids": [r["id"] for r in mine]}).mappings()}
    subjects = sorted(({**r, "all_n": allc.get(r["id"], r["n"])} for r in mine),
                      key=lambda r: (-(r["n"] ** 2 / max(r["all_n"], 1)), -r["n"], r["label"]))[:14]

    marks = conn.execute(text("""
        SELECT d.debate_date, s.word_count, d.loksabha FROM speeches s JOIN debates d ON d.id = s.debate_id
        WHERE s.person_id = :p AND d.debate_date IS NOT NULL ORDER BY d.debate_date, s.id"""), p).all()

    # A short turn has SHORT_TURN words or fewer. A short turn of the member inside the span of another
    # member's speech is an interruption BY the member. A short turn of anybody else inside the member's
    # speech is an interruption OF the member.
    by = conn.execute(text("""
        SELECT count(*) AS turns, count(DISTINCT o.id) AS speeches
        FROM turns t JOIN speeches o ON o.debate_id = t.debate_id AND t.seq BETWEEN o.seq_start AND o.seq_end
             AND o.person_id <> t.person_id
        WHERE t.person_id = :p AND t.speech_id IS NULL AND t.word_count <= :w"""), {**p, "w": SHORT_TURN}).mappings().one()
    of = conn.execute(text("""
        SELECT count(*) AS turns, count(DISTINCT o.id) AS speeches,
               count(*) FILTER (WHERE t.role_kind = 'presiding') AS chair,
               count(*) FILTER (WHERE t.person_id IS NOT NULL AND t.role_kind IS NULL) AS members,
               count(*) FILTER (WHERE t.person_id IS NULL AND COALESCE(t.role_kind, '') <> 'presiding') AS other
        FROM speeches o JOIN turns t ON t.debate_id = o.debate_id AND t.seq BETWEEN o.seq_start AND o.seq_end
             AND t.speech_id IS NULL
        WHERE o.person_id = :p AND t.word_count <= :w"""), {**p, "w": SHORT_TURN}).mappings().one()

    recent_ids = [r[0] for r in conn.execute(text("""
        SELECT s.id FROM speeches s JOIN debates d ON d.id = s.debate_id
        WHERE s.person_id = :p AND s.word_count >= 99 ORDER BY d.debate_date DESC, s.word_count DESC, s.id LIMIT 6"""), p)]
    long_ids = [r[0] for r in conn.execute(text("""
        SELECT s.id FROM speeches s WHERE s.person_id = :p ORDER BY s.word_count DESC, s.id LIMIT 4"""), p)]

    return {
        "id": pid, "name": name, "known_as": known_as, "raw_name": pe["name"],
        "party_path": party_path(term_list), "seat": term_list[-1]["seat"] if term_list else None,
        "state": term_list[-1]["state"] if term_list else None,
        "terms": term_list, "speeches": sum(t["speeches"] for t in term_list), "tagged_speeches": mtotal,
        "typical": typical[:14], "typical_total_candidates": len(typical),
        "rule": {"general_share": GENERAL_SHARE, "min_member": MIN_MEMBER, "min_all": MIN_ALL,
                 "all_tagged": gtotal},
        "places": places[:10],
        "subjects": [{"id": r["id"], "label": r["label"], "parent": r["parent"], "n": r["n"], "all": r["all_n"]}
                     for r in subjects],
        "marks": [[d.isoformat(), w, t] for d, w, t in marks],
        "house": {"short_words": SHORT_TURN,
                  "by": {"turns": by["turns"], "speeches": by["speeches"]},
                  "of": {"turns": of["turns"], "speeches": of["speeches"], "chair": of["chair"],
                         "members": of["members"], "other": of["other"]}},
        "recent": speech_rows(conn, recent_ids),
        "longest": speech_rows(conn, long_ids),
        "counts_note": (
            "speeches and terms[].speeches count all speeches of the member. "
            "tagged_speeches counts the member's speeches with at least one kept tag. "
            "typical[].n and places[].n count the member's tagged speeches with the tag. "
            "typical[].all counts all tagged speeches of every member with the tag, and rule.all_tagged is the count of all tagged speeches. "
            "typical[].lift is the member's share of tagged speeches with the tag, divided by the same share over rule.all_tagged. "
            "subjects[].n counts the member's speeches with a kept item of the subject, and subjects[].all counts the same over all members. "
            "house counts turns of at most house.short_words words that belong to no speech."),
    }


ROUTES = [("/member/<int:member_id>", member_page)]
