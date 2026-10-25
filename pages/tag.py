"""The data of the tag page, and the list of all live tags.

A live tag has a status other than 'rejected' and 'merged'. A merged tag points to its kept tag
through tags.merged_into. The slug of a merged tag therefore opens the page of its kept tag.
"""
from sqlalchemy import text

from pages.common import (PARTY_AT_DATE, SPEECH_TAGS_CTE, corpus_party_totals, resolve_slug, resolve_tag, slug, tag_speeches,
                          speech_rows, speech_tags_cte)

COUNTS_NOTE = (
    "total and by_source count speeches that carry this tag (each speech once). "
    "sessions.speeches_tagged counts those speeches in one session. "
    "parties.speeches_tagged counts tagged speeches of the party, and party_speeches_with_tags counts all speeches "
    "of the party that have at least one kept tag, so per100 is the tagged share of that party's tagged speeches. "
    "members.speeches_tagged counts tagged speeches of the member (members with 3 or more). "
    "related.speeches_shared counts speeches that carry both tags. "
    "subjects.speeches and subjects.debates count the speeches and debates of the subject."
)


def find_tag_id(conn, wanted):
    row = resolve_tag(conn, wanted)
    return row["id"] if row else None


def shape_tag(t, by_source, sessions, parties, members, subjects, related, recent, longest):
    """Put the query results in the output shape of the tag page."""
    return {
        "name": t["tag"], "slug": slug(t["tag"]), "type": t["type"], "domain": t["domain"],
        "description": t["description"], "aliases": t["aliases"],
        "total": sum(by_source.values()), "by_source": by_source, "counts_note": COUNTS_NOTE,
        "sessions": [{"term": r["term"], "session": r["session"], "n": r["n"], "speeches_tagged": r["n"],
                      "year": r["first"].year if r["first"] else None} for r in sessions],
        "parties": [{"party": r["party"], "n": r["n"], "speeches_tagged": r["n"],
                     "per100": round(100 * r["n"] / r["party_total"], 2),
                     "party_total": r["party_total"], "party_speeches_with_tags": r["party_total"]} for r in parties],
        "members": [{"id": r["mid"], "name": r["name"], "n": r["n"], "speeches_tagged": r["n"],
                     "party": r["party"], "seat": r["seat"], "last": str(r["last"])} for r in members],
        "subjects": [{"id": r["id"], "label": r["label"], "n": r["n_speeches"], "speeches": r["n_speeches"],
                      "debates": r["n_debates"]} for r in subjects],
        "related": [{"name": r["tag"], "slug": slug(r["tag"]), "type": r["type"], "n": r["n"],
                     "speeches_shared": r["n"]} for r in related],
        "recent": recent, "longest": longest,
    }


# The shared CTE, limited to the speeches of this tag (passed as :sids).
LIMITED_SPEECH_TAGS = speech_tags_cte("si.speech_id = ANY(:sids)")


def tag_data(c, tag_id):
    t = c.execute(text("SELECT * FROM tags WHERE id = :i"), {"i": tag_id}).mappings().one()
    found = tag_speeches(c, tag_id)
    sids = [r[0] for r in found]
    srcs = [r[1] for r in found]
    p = {"sids": sids, "srcs": srcs, "id": tag_id}
    base = "WITH ts AS (SELECT * FROM unnest(CAST(:sids AS int[]), CAST(:srcs AS text[])) AS u(speech_id, source))"

    by_source = {}
    for src in srcs:
        by_source[src] = by_source.get(src, 0) + 1
    sessions = c.execute(text(base + """
        SELECT d.loksabha AS term, d.session, count(ts.speech_id) AS n, min(d.debate_date) AS first
        FROM debates d LEFT JOIN speeches s ON s.debate_id = d.id LEFT JOIN ts ON ts.speech_id = s.id
        GROUP BY 1, 2 ORDER BY 1, 2"""), p).mappings().all()
    tagged_party = c.execute(text(base + f"""
        SELECT pa.party, count(*) AS n FROM ts JOIN speeches s ON s.id = ts.speech_id JOIN debates d ON d.id = s.debate_id
        {PARTY_AT_DATE} WHERE pa.party IS NOT NULL GROUP BY 1 ORDER BY n DESC, pa.party LIMIT 10"""), p).all()
    totals = corpus_party_totals(c)
    parties = [{"party": party, "n": n, "party_total": totals.get(party, n)} for party, n in tagged_party]
    members = c.execute(text(base + f"""
        SELECT pe.id AS mid, pe.name, count(*) AS n, max(d.debate_date) AS last,
               (array_agg(pa.party ORDER BY d.debate_date DESC))[1] AS party,
               (array_agg(pa.seat ORDER BY d.debate_date DESC))[1] AS seat
        FROM ts JOIN speeches s ON s.id = ts.speech_id JOIN debates d ON d.id = s.debate_id
        JOIN persons pe ON pe.id = s.person_id {PARTY_AT_DATE}
        GROUP BY pe.id HAVING count(*) >= 3 ORDER BY n DESC, pe.name LIMIT 12"""), p).mappings().all()
    subjects = c.execute(text(
        "SELECT id, label, n_speeches, n_debates FROM subjects WHERE parent_tag_id = :id "
        "ORDER BY n_speeches DESC, label LIMIT 40"), p).mappings().all()
    related = c.execute(text(f"""
        WITH {LIMITED_SPEECH_TAGS}
        SELECT t.tag, t.type, count(*) AS n FROM speech_tags o JOIN tags t ON t.id = o.tag_id
        WHERE o.tag_id <> :id AND t.type NOT IN ('place', 'role')
        GROUP BY t.id ORDER BY n DESC, t.tag LIMIT 14"""), p).mappings().all()
    recent_ids = [r[0] for r in c.execute(text(base + """
        SELECT ts.speech_id FROM ts JOIN speeches s ON s.id = ts.speech_id JOIN debates d ON d.id = s.debate_id
        WHERE ts.source = 'llm' AND s.person_id IS NOT NULL ORDER BY d.debate_date DESC, s.word_count DESC LIMIT 8"""), p).all()]
    long_ids = [r[0] for r in c.execute(text(base + """
        SELECT ts.speech_id FROM ts JOIN speeches s ON s.id = ts.speech_id
        WHERE ts.source = 'llm' AND s.person_id IS NOT NULL ORDER BY s.word_count DESC LIMIT 4"""), p).all()]
    return shape_tag(t, by_source, sessions, parties, members, subjects, related,
                     speech_rows(c, recent_ids), speech_rows(c, long_ids))


def tag_page(conn, slug, args):
    """Route function. Returns the tag page data, or None for an unknown slug."""
    tag_id = find_tag_id(conn, slug)
    if tag_id is None:
        return None
    return tag_data(conn, tag_id)


def tags_list(conn, args):
    """All live tags, A to Z by name. speeches_tagged counts the speeches that carry the tag."""
    rows = conn.execute(text(f"""
        WITH {SPEECH_TAGS_CTE},
        n AS (SELECT tag_id, count(*) AS c FROM speech_tags GROUP BY 1)
        SELECT t.tag, t.type, t.domain, COALESCE(n.c, 0) AS c
        FROM tags t LEFT JOIN n ON n.tag_id = t.id
        WHERE t.status NOT IN ('rejected', 'merged')""")).all()
    rows = sorted(rows, key=lambda r: (r[0].lower(), r[0]))
    return {
        "counts_note": "speeches_tagged counts the speeches that carry the tag, each speech once. Order: name A to Z.",
        "tags": [{"name": r[0], "slug": slug(r[0]), "type": r[1], "domain": r[2], "speeches_tagged": r[3]} for r in rows],
    }


ROUTES = [("/tag/<slug>", tag_page), ("/tags", tags_list)]
