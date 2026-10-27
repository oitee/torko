"""The member page: the data of one member of parliament, as JSON.

Route: /member/<member_id>. The key is persons.id. An unknown key gives None.
The page shows terms, typical subjects, places, specific subjects, one mark per speech, and house turns.
Every query is read-only.
"""
import datetime
import re
from collections import Counter

from sqlalchemy import text

from pages.common import SPEECH_TAGS_CTE, cached, slug, speech_rows, speech_tags_cte
from pages.sessions import session_labels

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


def tags_by_term(conn):
    """Return ({(term, tag_id): speeches with the tag}, {term: tagged speeches}), over all members. Cached."""
    def load():
        rows = conn.execute(text(f"""
            WITH {SPEECH_TAGS_CTE}
            SELECT d.loksabha, st.tag_id, count(*) FROM speech_tags st JOIN speeches s ON s.id = st.speech_id
            JOIN debates d ON d.id = s.debate_id GROUP BY 1, 2""")).all()
        totals = dict(conn.execute(text(f"""
            WITH {SPEECH_TAGS_CTE}
            SELECT d.loksabha, count(DISTINCT st.speech_id) FROM speech_tags st JOIN speeches s ON s.id = st.speech_id
            JOIN debates d ON d.id = s.debate_id GROUP BY 1""")).all())
        return {(t, i): n for t, i, n in rows}, totals
    return cached("tags_by_term", load)


def shares(member_n, member_total, house_n, house_total):
    """Return (member share, house share, ratio). The ratio is None when the house share is 0."""
    ms = member_n / member_total if member_total else 0
    hs = house_n / house_total if house_total else 0
    return round(ms, 4), round(hs, 4), (round(ms / hs, 1) if hs else None)


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
        base = {"tag_id": tag_id, "name": g["tag"], "slug": slug(g["tag"]), "type": g["type"], "n": n, "all": g["n"]}
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


def party_path(rows, term_end=None, latest_term=None):
    """Return the parties of a member in date order: [{code, from, to}] with years.

    rows are (term, party code, effective_from date) in date order. Two rows of one party in a row make one item.
    "from" is the year of the first row. "to" is the year of the next party's first row.
    For the last party, "to" is the year in which its last term ended. It is None while that term is the latest term.
    term_end is {term: last date of the term}.
    """
    term_end = term_end or {}
    runs = []
    for term, code, start in rows:
        if not code:
            continue
        if runs and runs[-1]["code"] == code:
            runs[-1]["term"] = term
            continue
        runs.append({"code": code, "from": start.year if start else None, "term": term})
    path = []
    for i, r in enumerate(runs):
        if i + 1 < len(runs):
            to = runs[i + 1]["from"]
        elif r["term"] == latest_term or r["term"] not in term_end:
            to = None
        else:
            to = term_end[r["term"]].year
        path.append({"code": r["code"], "from": r["from"], "to": to})
    return path


def median_with_zeros(counts, n_members):
    """Median of n_members numbers. counts holds the non-zero ones. The members not in counts have 0."""
    values = sorted(list(counts) + [0] * max(n_members - len(counts), 0))
    if not values:
        return 0
    mid = len(values) // 2
    m = values[mid] if len(values) % 2 else (values[mid - 1] + values[mid]) / 2
    return int(m) if m == int(m) else m


def house_medians(conn):
    """Return {(term, session): median speeches of a member}, over all members of the term. Cached.

    All members of the term are all persons with a row in speakers for the term. A member with no speech in the
    session counts as 0. A member who joined or left during the term counts in every session.
    """
    def load():
        members = dict(conn.execute(text(
            "SELECT lok_sabha_term, count(DISTINCT person_id) FROM speakers GROUP BY 1")).all())
        per = {}
        for term, session, n in conn.execute(text("""
                SELECT d.loksabha, d.session, count(*) FROM speeches s JOIN debates d ON d.id = s.debate_id
                WHERE s.person_id IS NOT NULL AND d.session IS NOT NULL
                  AND EXISTS (SELECT 1 FROM speakers sp WHERE sp.person_id = s.person_id AND sp.lok_sabha_term = d.loksabha)
                GROUP BY d.loksabha, d.session, s.person_id""")).all():
            per.setdefault((term, session), []).append(n)
        return {k: median_with_zeros(v, members.get(k[0], 0)) for k, v in per.items()}, members
    return cached("house_medians", load)


def member_sessions(conn, pid, term_numbers):
    """Return one row for each session of each term of the member: term, session, label, n, house_median."""
    medians, _ = house_medians(conn)
    labels = session_labels(conn)
    mine = {(t, s): n for t, s, n in conn.execute(text("""
        SELECT d.loksabha, d.session, count(*) FROM speeches s JOIN debates d ON d.id = s.debate_id
        WHERE s.person_id = :p AND d.session IS NOT NULL GROUP BY 1, 2"""), {"p": pid}).all()}
    keys = {k for k in set(medians) | set(mine) | set(labels) if k[0] in term_numbers}
    return [{"term": t, "session": s, "label": (labels.get((t, s)) or {}).get("label"),
             "n": mine.get((t, s), 0), "house_median": medians.get((t, s), 0)} for t, s in sorted(keys)]


def pick_seat_tag(seat, state, candidates):
    """Return the id of the place tag of a seat, or None when it is not certain.

    candidates are place tags: dicts with id, tag and description. A tag matches by name AND state:
    "Seat (State)" with the state of the seat, or a tag named like the seat whose description says "in <State>",
    or a tag whose description says "listed as <Seat>" and "in <State>". With no state, only a plain tag
    that is the only candidate matches. Two matches give None.
    """
    base = re.sub(r"\s*\(.*\)$", "", seat or "").strip().lower()
    if not base:
        return None
    found = set()
    for c in candidates:
        name, desc = c["tag"].lower(), (c["description"] or "")
        in_state = bool(state) and re.search(rf"\bin {re.escape(state)}\b", desc, re.I) is not None
        if state and name == f"{base} ({state.lower()})":
            found.add(c["id"])
        elif name == base and (in_state or (not state and len(candidates) == 1)):
            found.add(c["id"])
        elif state and in_state and re.search(rf"listed as {re.escape(base)}\b", desc, re.I):
            found.add(c["id"])
    return found.pop() if len(found) == 1 else None


def seat_tags(conn, seats):
    """Return {(seat, state): place tag row or None} for the seats, using pick_seat_tag."""
    out = {}
    for seat, state in seats:
        base = re.sub(r"\s*\(.*\)$", "", seat or "").strip()
        if not base:
            continue
        cands = conn.execute(text("""
            SELECT id, tag, description FROM tags WHERE type = 'place'
              AND (lower(tag) = lower(:b) OR lower(tag) LIKE lower(:b) || ' (%%' OR description ILIKE '%%listed as ' || :b || '%%')"""),
            {"b": base}).mappings().all()
        out[(seat, state)] = pick_seat_tag(seat, state, [dict(c) for c in cands])
    return out


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
    path_rows = conn.execute(text("""
        SELECT sp.lok_sabha_term, pa.code, sp.effective_from FROM speakers sp LEFT JOIN parties pa ON pa.id = sp.party_id
        WHERE sp.person_id = :p ORDER BY sp.effective_from NULLS FIRST, sp.lok_sabha_term"""), p).all()
    ends = {t: max(v["last"] for k, v in session_labels(conn).items() if k[0] == t)
            for t in {r[0] for r in path_rows}}
    ends = {t: datetime.date.fromisoformat(d) for t, d in ends.items()}
    latest_term = conn.execute(text("SELECT max(loksabha) FROM debates")).scalar()
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
    sessions = member_sessions(conn, pid, set(terms))
    seat_ids = seat_tags(conn, {(t["seat"], t["state"]) for t in term_list if t["seat"]})
    own_ids = {v for v in seat_ids.values() if v}
    last = term_list[-1] if term_list else None
    seat_id = seat_ids.get((last["seat"], last["state"])) if last and last["seat"] else None

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
        SELECT su.id, su.label, su.parent_tag_id, t.tag AS parent, count(DISTINCT si.speech_id) AS n
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

    # M2: the shares over the terms of the member, and the specific subjects under each listed tag.
    by_term, term_totals = tags_by_term(conn)
    house_total = sum(term_totals.get(t, 0) for t in terms)
    listed = typical[:14]
    for row in listed:
        house_n = sum(by_term.get((t, row["tag_id"]), 0) for t in terms)
        row["member_share"], row["house_share"], row["lift_terms"] = shares(row["n"], mtotal, house_n, house_total)
        row["subjects"] = [{"id": r["id"], "label": r["label"], "n": r["n"], "all": allc.get(r["id"], r["n"])}
                           for r in sorted(mine, key=lambda r: (-r["n"], r["label"])) if r["parent_tag_id"] == row["tag_id"]]
    listed_ids = [r["tag_id"] for r in listed]
    with_listed = {sp for sp, tg in pairs if tg in set(listed_ids)}
    other_n = mtotal - len(with_listed)
    # The filter keeps only the speeches of the member's terms in the CTE, so the scan stays small.
    in_terms = speech_tags_cte("si.speech_id IN (SELECT s2.id FROM speeches s2 JOIN debates d2 ON d2.id = s2.debate_id "
                               "WHERE d2.loksabha = ANY(CAST(:terms AS int[])))")
    house_listed = conn.execute(text(f"""
        WITH {in_terms}
        SELECT count(DISTINCT st.speech_id) FROM speech_tags st WHERE st.tag_id = ANY(:ids)"""),
        {"ids": listed_ids, "terms": list(terms)}).scalar() if listed_ids else 0
    other = dict(zip(("member_share", "house_share", "lift_terms"),
                     shares(other_n, mtotal, house_total - house_listed, house_total)))
    other.update({"n": other_n, "all": house_total - house_listed})
    subtype_of = dict(conn.execute(text("SELECT id, subtype FROM tags WHERE id = ANY(:i)"),
                                    {"i": [x["tag_id"] for x in places[:10]]}).all()) if places else {}

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
        "party_path": party_path([(a, b, c) for a, b, c in path_rows], ends, latest_term),
        "seat": term_list[-1]["seat"] if term_list else None,
        "seat_slug": slug(conn.execute(text("SELECT tag FROM tags WHERE id = :i"), {"i": seat_id}).scalar()) if seat_id else None,
        "state": term_list[-1]["state"] if term_list else None,
        "terms": term_list, "sessions": sessions, "speeches": sum(t["speeches"] for t in term_list), "tagged_speeches": mtotal,
        "typical": listed, "other": other, "typical_total_candidates": len(typical),
        "rule": {"general_share": GENERAL_SHARE, "min_member": MIN_MEMBER, "min_all": MIN_ALL,
                 "all_tagged": gtotal},
        "places": [{**x, "subtype": subtype_of.get(x["tag_id"]), "own_seat": x["tag_id"] in own_ids}
                   for x in places[:10]],
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
            "sessions[].n counts the member's speeches in the session. sessions[].house_median is the median over all members of the term; a member who joined or left during the term counts in every session. A member with no speech in the session counts as 0. "
            "typical[].member_share is typical[].n divided by tagged_speeches. typical[].house_share is the count of tagged speeches with the tag in the terms of the member, divided by the count of all tagged speeches in those terms (all members). "
            "typical[].lift_terms is member_share divided by house_share. other counts the member's tagged speeches with none of the listed typical tags, and other.all counts the same over all members in the terms of the member. "
            "places[].own_seat is true when the place is a seat of the member. "
            "subjects[].n counts the member's speeches with a kept item of the subject, and subjects[].all counts the same over all members. "
            "house counts turns of at most house.short_words words that belong to no speech."),
    }


ROUTES = [("/member/<int:member_id>", member_page)]
