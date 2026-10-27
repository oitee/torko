"""The data of the tag page, and the list of all live tags.

A live tag has a status other than 'rejected' and 'merged'. A merged tag points to its kept tag
through tags.merged_into. The slug of a merged tag therefore opens the page of its kept tag.
"""
import re

from sqlalchemy import text

from pages.common import (PARTY_AT_DATE, SPEECH_TAGS_CTE, corpus_party_totals, party_colours, resolve_slug, resolve_tag, slug, tag_speeches,
                          speech_rows, speech_tags_cte)
from pages.quotes import clean, good, good_hi, score, sentences

COUNTS_NOTE = (
    "total and by_source count speeches that carry this tag (each speech once). "
    "sessions.speeches_tagged counts those speeches in one session. "
    "parties.speeches_tagged counts tagged speeches of the party, and party_speeches_with_tags counts all speeches "
    "of the party that have at least one kept tag, so per100 is the tagged share of that party's tagged speeches. "
    "members.speeches_tagged counts tagged speeches of the member (members with 3 or more). "
    "related.speeches_shared counts speeches that carry both tags. "
    "subjects.speeches and subjects.debates count the speeches and debates of the subject. "
    "subjects.peak is the year with the most speeches of the subject (a tie goes to the earlier year). "
    "n_members counts the distinct members with at least one tagged speech, in all terms. It does not count speakers with no identified member, "
    "because a speech with no member has no tags. n_subjects counts all subjects under this tag, while subjects lists at most 40. "
    "first and last are the dates of the first and the last tagged speech. "
    "With the argument term, parties, members, recent and longest count only the speeches of that term. n_members, first and last, "
    "total, by_source, sessions, subjects and related stay for all terms. "
    "members.first and members.last are the dates of the first and the last tagged speech of the member in the chosen terms, "
    "and members.terms are the terms with such a speech. "
    "recent.quote is one sentence from the own turns of the member in that speech, or null. It is English when the speech has a good "
    "English sentence, else Hindi. quote_lang is en or hi. "
    "recent.subject is the subject of the speech under this tag (the one with more speeches when there are two), or null."
)


def find_tag_id(conn, wanted):
    row = resolve_tag(conn, wanted)
    return row["id"] if row else None


def shape_tag(t, by_source, sessions, parties, members, subjects, related, recent, longest, header=None, peaks=None):
    """Put the query results in the output shape of the tag page.

    header has n_members, n_subjects, first and last. peaks maps a subject id to its peak year.
    """
    header = header or {}
    peaks = peaks or {}
    return {
        "name": t["tag"], "slug": slug(t["tag"]), "type": t["type"], "domain": t["domain"],
        "description": t["description"], "aliases": t["aliases"],
        "total": sum(by_source.values()),
        "n_members": header.get("n_members", 0), "n_subjects": header.get("n_subjects", len(subjects)),
        "first": header["first"].isoformat() if header.get("first") else None,
        "last": header["last"].isoformat() if header.get("last") else None,
        "by_source": by_source, "counts_note": COUNTS_NOTE,
        "sessions": [{"term": r["term"], "session": r["session"], "n": r["n"], "speeches_tagged": r["n"],
                      "year": r["first"].year if r["first"] else None} for r in sessions],
        "parties": [{"party": r["party"], "colour": r.get("colour"), "n": r["n"], "speeches_tagged": r["n"],
                     "per100": round(100 * r["n"] / r["party_total"], 2),
                     "party_total": r["party_total"], "party_speeches_with_tags": r["party_total"]} for r in parties],
        "members": [{"id": r["mid"], "name": r["name"], "n": r["n"], "speeches_tagged": r["n"],
                     "party": r["party"], "seat": r["seat"], "state": r["state"], "last": str(r["last"]),
                     "first": str(r["first"]), "terms": sorted(r["terms"])} for r in members],
        "subjects": [{"id": r["id"], "label": r["label"], "n": r["n_speeches"], "speeches": r["n_speeches"],
                      "debates": r["n_debates"], "peak": peaks.get(r["id"])} for r in subjects],
        "related": [{"name": r["tag"], "slug": slug(r["tag"]), "type": r["type"], "n": r["n"],
                     "speeches_shared": r["n"]} for r in related],
        "recent": recent, "longest": longest,
    }


def peak_year(year_counts):
    """The year with the most speeches. A tie goes to the earlier year. year_counts is {year: n}."""
    if not year_counts:
        return None
    return min(year_counts, key=lambda y: (-year_counts[y], y))


def pick_quote(turn_texts, title):
    """Return (sentence, language) for the best good sentence in the turn texts, or (None, None).

    Same rule as the page "On this day": an English sentence first, and a Hindi sentence only when no English one is good.
    """
    title_words = {w.lower() for w in re.findall(r"[A-Za-z]{5,}", title or "")}
    sents = [sent for t in turn_texts for sent in sentences(clean(t or ""))]
    best = None
    for sent in sents:
        if good(sent):
            key = (score(sent, title_words), -abs(len(sent.split()) - 24))
            if best is None or key > best[0]:
                best = (key, sent)
    if best:
        return best[1], "en"
    for sent in sents:
        if good_hi(sent):
            key = -abs(len(sent.split()) - 18)
            if best is None or key > best[0]:
                best = (key, sent)
    return (best[1], "hi") if best else (None, None)


def add_quotes_and_subjects(c, rows, tag_id):
    """Add quote and subject to each speech row."""
    ids = [r["id"] for r in rows]
    if not ids:
        return rows
    turns = {}
    for sid, txt in c.execute(text("""
        SELECT t.speech_id, t.text FROM turns t JOIN speeches s ON s.id = t.speech_id
        WHERE t.speech_id = ANY(:ids) AND t.person_id = s.person_id AND t.person_id IS NOT NULL ORDER BY t.speech_id, t.seq"""), {"ids": ids}):
        turns.setdefault(sid, []).append(txt)
    subj = {}
    for sid, label in c.execute(text("""
        SELECT si.speech_id, su.label FROM speech_items si
        JOIN subject_names sn ON sn.entity_name_id = si.entity_name_id
        JOIN subjects su ON su.id = sn.subject_id
        WHERE si.kept AND si.speech_id = ANY(:ids) AND su.parent_tag_id IN (SELECT id FROM tags WHERE id = :id OR merged_into = :id)
        ORDER BY si.speech_id, su.n_speeches DESC, su.label"""), {"ids": ids, "id": tag_id}):
        subj.setdefault(sid, label)  # the first row has the most speeches
    for r in rows:
        r["quote"], r["quote_lang"] = pick_quote(turns.get(r["id"], []), r["debate"])
        r["subject"] = subj.get(r["id"])
    return rows


# The shared CTE, limited to the speeches of this tag (passed as :sids).
LIMITED_SPEECH_TAGS = speech_tags_cte("si.speech_id = ANY(:sids)")


def tag_data(c, tag_id, term=None):
    t = c.execute(text("SELECT * FROM tags WHERE id = :i"), {"i": tag_id}).mappings().one()
    found = tag_speeches(c, tag_id)
    sids = [r[0] for r in found]
    srcs = [r[1] for r in found]
    p = {"sids": sids, "srcs": srcs, "id": tag_id, "term": term}
    in_term = "(CAST(:term AS int) IS NULL OR d.loksabha = CAST(:term AS int))"
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
        {PARTY_AT_DATE} WHERE pa.party IS NOT NULL AND {in_term} GROUP BY 1 ORDER BY n DESC, pa.party LIMIT 10"""), p).all()
    totals = corpus_party_totals(c)
    colours = party_colours(c)
    parties = [{"party": party, "colour": colours.get(party), "n": n, "party_total": totals.get(party, n)}
               for party, n in tagged_party]
    members = c.execute(text(base + f"""
        SELECT pe.id AS mid, pe.name, count(*) AS n, max(d.debate_date) AS last, min(d.debate_date) AS first,
               array_agg(DISTINCT d.loksabha) AS terms,
               (array_agg(pa.party ORDER BY d.debate_date DESC))[1] AS party,
               (array_agg(pa.seat ORDER BY d.debate_date DESC))[1] AS seat,
               (array_agg(pa.state ORDER BY d.debate_date DESC))[1] AS state
        FROM ts JOIN speeches s ON s.id = ts.speech_id JOIN debates d ON d.id = s.debate_id
        JOIN persons pe ON pe.id = s.person_id {PARTY_AT_DATE}
        WHERE {in_term}
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
        WHERE ts.source = 'llm' AND s.person_id IS NOT NULL AND """ + in_term + """ ORDER BY d.debate_date DESC, s.word_count DESC LIMIT 8"""), p).all()]
    long_ids = [r[0] for r in c.execute(text(base + """
        SELECT ts.speech_id FROM ts JOIN speeches s ON s.id = ts.speech_id JOIN debates d ON d.id = s.debate_id
        WHERE ts.source = 'llm' AND s.person_id IS NOT NULL AND """ + in_term + """ ORDER BY s.word_count DESC LIMIT 4"""), p).all()]
    head = c.execute(text(base + """
        SELECT count(DISTINCT s.person_id) AS n_members, min(d.debate_date) AS first, max(d.debate_date) AS last
        FROM ts JOIN speeches s ON s.id = ts.speech_id JOIN debates d ON d.id = s.debate_id"""), p).mappings().one()
    header = dict(head)
    header["n_subjects"] = c.execute(text("SELECT count(*) FROM subjects WHERE parent_tag_id = :id"), p).scalar()
    peaks = {}
    if subjects:
        # Speeches of each shown subject by year. A speech counts once for a subject.
        for sub_id, year, n in c.execute(text("""
            SELECT x.subject_id, x.y, count(*) FROM (
                SELECT DISTINCT sn.subject_id, si.speech_id, extract(year FROM d.debate_date)::int AS y
                FROM speech_items si JOIN subject_names sn ON sn.entity_name_id = si.entity_name_id
                JOIN speeches s ON s.id = si.speech_id JOIN debates d ON d.id = s.debate_id
                WHERE si.kept AND sn.subject_id = ANY(:sub) AND d.debate_date IS NOT NULL) x
            GROUP BY 1, 2"""), {"sub": [r["id"] for r in subjects]}):
            peaks.setdefault(sub_id, {})[year] = n
        peaks = {k: peak_year(v) for k, v in peaks.items()}
    recent = add_quotes_and_subjects(c, speech_rows(c, recent_ids), tag_id)
    longest = add_quotes_and_subjects(c, speech_rows(c, long_ids), tag_id)
    return shape_tag(t, by_source, sessions, parties, members, subjects, related, recent, longest, header, peaks)


def tag_page(conn, slug, args):
    """Route function. Returns the tag page data, or None for an unknown slug."""
    tag_id = find_tag_id(conn, slug)
    if tag_id is None:
        return None
    term = args.get("term")
    term = int(term) if str(term or "").isdigit() else None
    return tag_data(conn, tag_id, term)


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
