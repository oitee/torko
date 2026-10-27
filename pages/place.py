"""The data of the place page: one place tag, its speeches, its seat holders, the members and subjects tied to it.

Counts: a speech counts once for a place when a kept tag of the speech is that place.
The seat holder of a place is a member whose seat (speakers.constituency) has the same name as the place,
in a Lok Sabha term. A state has no seat holder.
"""
import re

from sqlalchemy import text

from pages.common import slug as to_slug
from pages.common import (PARTY_AT_DATE, SPEECH_TAGS_CTE, cached, corpus_party_totals, resolve_tag, speech_rows,
                          speech_tags_cte, tag_speeches)

# Subjects most associated with a place. lift = the share of the place's tagged speeches that carry the tag,
# divided by the share of all tagged speeches that carry it.
GENERAL_SHARE = 0.03   # a tag in more than this share of all tagged speeches is very general
MIN_PLACE = 5          # speeches of the place that carry the tag
MIN_ALL = 20           # speeches in all that carry the tag
TOP = 8
MIN_MEMBER_SPEECHES = 3
PARTY_WORDS = re.compile(r"\b(party|congress|kazhagam|morcha|sena|dal|league)\b", re.I)

COUNTS_NOTE = (
    "total, sessions[].n, members[].n, related[].n and associated[].n count speeches that carry a kept tag of the place, "
    "each speech once. associated[].all counts all speeches that carry the associated tag. "
    "parties[].per100 is the party's speeches on the place per 100 of all speeches of that party that have any kept item "
    "(party_total). n_members counts distinct members with at least one such speech."
)

# The tags of the speeches in :ids only. It is fast for one tag.
LOCAL_TAGS_CTE = speech_tags_cte("si.speech_id = ANY(:ids)")


def speech_ids_for_tag(conn, tag_id):
    """The ids of the speeches that carry the tag (a kept item that links to it, or to a tag merged into it), sorted."""
    return [sid for sid, _ in tag_speeches(conn, tag_id)]


def corpus_tag_counts(conn):
    """(speeches per live tag, number of tagged speeches). A tagged speech has at least one kept tag."""
    def load():
        per = dict(conn.execute(text(f"WITH {SPEECH_TAGS_CTE} SELECT tag_id, count(*) FROM speech_tags GROUP BY 1")).all())
        total = conn.execute(text(f"WITH {SPEECH_TAGS_CTE} SELECT count(DISTINCT speech_id) FROM speech_tags")).scalar()
        return per, total
    return cached("tag_counts", load)


def same_seat(seat, name):
    """True when the seat name, without a bracket suffix such as '(SC)', equals the place name (case ignored)."""
    return bool(seat) and re.sub(r"\s*\(.*\)$", "", seat).strip().lower() == name.lower()


def associated(conn, ids, tag_id, place_total):
    """The tags with the highest lift for the place, most lift first, then most speeches.

    Hidden: place, role, person and group tags, party tags, Parliament and Procedure tags, and general tags.
    """
    per, gtotal = corpus_tag_counts(conn)
    rows = conn.execute(text(f"""
        WITH {LOCAL_TAGS_CTE}
        SELECT t.id, t.tag, t.type, t.domain, count(*) AS n FROM speech_tags o JOIN tags t ON t.id = o.tag_id
        WHERE o.tag_id <> :id GROUP BY t.id HAVING count(*) >= :minp"""), {"ids": ids, "id": tag_id, "minp": MIN_PLACE}).mappings().all()
    parties = {r[0].lower() for r in conn.execute(text("SELECT name FROM parties"))}
    out = []
    for r in rows:
        gn = per.get(r["id"], 0)
        if r["type"] in ("place", "role", "person", "group") or r["domain"] == "Parliament and Procedure":
            continue
        if r["tag"].lower() in parties or (r["type"] == "institution" and PARTY_WORDS.search(r["tag"])):
            continue
        if gn / gtotal > GENERAL_SHARE or gn < MIN_ALL:
            continue
        out.append({"name": r["tag"], "slug": to_slug(r["tag"]), "type": r["type"], "n": r["n"], "all": gn,
                    "lift": round((r["n"] / place_total) / (gn / gtotal), 1)})
    out.sort(key=lambda x: (-x["lift"], -x["n"], x["name"]))
    return out[:TOP]


def place_page(conn, slug, args):
    t = resolve_tag(conn, slug, "place")
    if t is None:
        return None
    name = t["tag"]
    ids = speech_ids_for_tag(conn, t["id"])
    p = {"ids": ids, "id": t["id"]}
    total = len(ids)
    
    by_session = {(r["term"], r["session"]): r["n"] for r in conn.execute(text("""
        SELECT d.loksabha AS term, d.session, count(*) AS n FROM speeches s JOIN debates d ON d.id = s.debate_id
        WHERE s.id = ANY(:ids) GROUP BY 1, 2"""), p).mappings()}
    sessions = conn.execute(text("""
        SELECT loksabha AS term, session, min(debate_date) AS first FROM debates GROUP BY 1, 2 ORDER BY 1, 2""")).mappings().all()
    span = conn.execute(text("""
        SELECT min(d.debate_date), max(d.debate_date), count(DISTINCT s.debate_id)
        FROM speeches s JOIN debates d ON d.id = s.debate_id WHERE s.id = ANY(:ids)"""), p).one()

    holders = []
    if t["subtype"] != "state":
        holders = conn.execute(text("""
            SELECT sp.lok_sabha_term AS term, pe.id AS mid, pe.name, pa.code AS party, sp.constituency AS seat,
                   st.name AS state, min(sp.effective_from) AS since
            FROM speakers sp JOIN persons pe ON pe.id = sp.person_id LEFT JOIN parties pa ON pa.id = sp.party_id
            LEFT JOIN states st ON st.id = sp.state_id
            WHERE lower(regexp_replace(sp.constituency, '\\s*\\(.*\\)$', '')) = lower(:n)
            GROUP BY 1, 2, 3, 4, 5, 6 ORDER BY 1, since, 2"""), {"n": name}).mappings().all()

    # The record gives the same start date to two holders of one term (a bypoll),
    # so the page also gives the first and last day each holder spoke in the term.
    spoke = {(r["mid"], r["term"]): (str(r["first"]), str(r["last"])) for r in conn.execute(text("""
        SELECT s.person_id AS mid, d.loksabha AS term, min(d.debate_date) AS first, max(d.debate_date) AS last
        FROM speeches s JOIN debates d ON d.id = s.debate_id
        WHERE s.person_id = ANY(:ids) GROUP BY 1, 2"""), {"ids": [h["mid"] for h in holders] or [0]}).mappings()}

    members = conn.execute(text(f"""
        SELECT pe.id AS mid, pe.name, count(*) AS n, max(d.debate_date) AS last,
               (array_agg(pa.party ORDER BY d.debate_date DESC))[1] AS party,
               (array_agg(pa.seat ORDER BY d.debate_date DESC))[1] AS seat,
               (array_agg(pa.state ORDER BY d.debate_date DESC))[1] AS state
        FROM speeches s JOIN debates d ON d.id = s.debate_id
        JOIN persons pe ON pe.id = s.person_id {PARTY_AT_DATE}
        WHERE s.id = ANY(:ids)
        GROUP BY pe.id HAVING count(*) >= :minm ORDER BY n DESC, last DESC, pe.name LIMIT 12"""),
        {**p, "minm": MIN_MEMBER_SPEECHES}).mappings().all()
    totals = corpus_party_totals(conn)
    tagged_party = conn.execute(text(f"""
        SELECT pa.party, count(*) AS n FROM speeches s JOIN debates d ON d.id = s.debate_id
        {PARTY_AT_DATE} WHERE s.id = ANY(:ids) AND pa.party IS NOT NULL GROUP BY 1 ORDER BY 2 DESC, 1 LIMIT 10"""), p).all()
    n_members = conn.execute(text("SELECT count(DISTINCT person_id) FROM speeches WHERE id = ANY(:ids)"), p).scalar()
    related = conn.execute(text(f"""
        WITH {LOCAL_TAGS_CTE}
        SELECT t.tag, t.type, count(*) AS n FROM speech_tags o
        JOIN tags t ON t.id = o.tag_id WHERE o.tag_id <> :id AND t.type NOT IN ('place', 'role')
        GROUP BY t.id ORDER BY n DESC, t.tag LIMIT 14"""), p).mappings().all()
    recent_ids = [r[0] for r in conn.execute(text("""
        SELECT s.id FROM speeches s JOIN debates d ON d.id = s.debate_id
        WHERE s.id = ANY(:ids) AND s.person_id IS NOT NULL ORDER BY d.debate_date DESC, s.word_count DESC, s.id LIMIT 8"""), p).all()]

    return {
        "name": name, "slug": to_slug(name), "subtype": t["subtype"], "domain": t["domain"],
        "description": t["description"], "aliases": t["aliases"],
        "total": total, "first": str(span[0]) if span[0] else None, "last": str(span[1]) if span[1] else None,
        "debates": span[2], "n_members": n_members,
        "counts_note": COUNTS_NOTE,
        "order_notes": {
            "sessions": "by Lok Sabha term, then session",
            "holders": "by term, then start date of the seat record",
            "associated": f"by lift, highest first, then by speeches; only tags with at least {MIN_PLACE} speeches of the place and {MIN_ALL} in all, in at most {GENERAL_SHARE:.0%} of tagged speeches",
            "parties": "by speeches of the place, most first; at most 10",
            "members": f"by speeches of the place, most first; only members with at least {MIN_MEMBER_SPEECHES}; at most 12",
            "related": "by speeches shared with the place, most first; place and role tags are left out; at most 14",
            "recent": "by debate date, latest first, then by word count; at most 8",
        },
        "sessions": [{"term": r["term"], "session": r["session"], "n": by_session.get((r["term"], r["session"]), 0),
                      "year": r["first"].year if r["first"] else None} for r in sessions],
        "holders": [{"term": r["term"], "id": r["mid"], "name": r["name"], "party": r["party"],
                     "seat": r["seat"], "state": r["state"], "since": str(r["since"]),
                     "first_spoke": spoke.get((r["mid"], r["term"]), (None, None))[0],
                     "last_spoke": spoke.get((r["mid"], r["term"]), (None, None))[1]} for r in holders],
        "associated": associated(conn, ids, t["id"], total) if total else [],
        "parties": [{"party": party, "n": n, "per100": round(100 * n / totals[party], 2), "party_total": totals[party]}
                    for party, n in tagged_party if totals.get(party)],
        "members": [{"id": r["mid"], "name": r["name"], "n": r["n"], "party": r["party"], "seat": r["seat"],
                     "state": r["state"], "last": str(r["last"]), "own_seat": same_seat(r["seat"], name)} for r in members],
        "related": [{"name": r["tag"], "slug": to_slug(r["tag"]), "type": r["type"], "n": r["n"]} for r in related],
        "recent": speech_rows(conn, recent_ids),
    }


ROUTES = [("/place/<slug>", place_page)]
