"""Shared read-only parts of the page queries: the read-only engine, slugs, the tags of a speech, and speech rows.

The page modules in this package use them, and so do the export scripts of the design prototype.
Every connection of engine() is read-only, so no page query can change the database.
"""
import re
import time

from sqlalchemy import create_engine, event, text

from db import database_url


def engine():
    eng = create_engine(database_url(), future=True)

    @event.listens_for(eng, "connect")
    def _read_only(dbapi_conn, _record):
        cur = dbapi_conn.cursor()
        cur.execute("SET default_transaction_read_only = on")
        cur.close()

    return eng


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


# A tag of a speech: a kept item whose name links to a tag, or a kept summary tag.
# Merged tags resolve to their kept tag. Each (speech, tag) counts once.
SPEECH_TAGS_CTE = """
speech_tags AS (
    SELECT DISTINCT ON (si.speech_id, COALESCE(km.id, kt.id))
           si.speech_id, COALESCE(km.id, kt.id) AS tag_id, si.source
    FROM speech_items si
    LEFT JOIN entity_names en ON en.id = si.entity_name_id AND en.link_status = 'linked'
    LEFT JOIN tags kt ON kt.id = COALESCE(si.tag_id, en.tag_id)
    LEFT JOIN tags km ON km.id = kt.merged_into
    WHERE si.kept AND kt.id IS NOT NULL
    ORDER BY si.speech_id, COALESCE(km.id, kt.id),
             CASE si.source WHEN 'llm' THEN 0 WHEN 'dictionary' THEN 1 ELSE 2 END
)
"""

def speech_tags_cte(filter_sql=None):
    """Return SPEECH_TAGS_CTE, with one more condition on the speech_items row when filter_sql is given.

    The condition keeps the scan small when a page needs the tags of a few speeches only.
    Use the table alias si in the condition. Bind the parameters of the condition in the query.
    """
    if not filter_sql:
        return SPEECH_TAGS_CTE
    out = SPEECH_TAGS_CTE.replace("WHERE si.kept AND kt.id IS NOT NULL",
                                  f"WHERE si.kept AND kt.id IS NOT NULL AND {filter_sql}")
    assert out != SPEECH_TAGS_CTE
    return out


CACHE_SECONDS = 3600
_cache = {}


def cached(key, fn):
    """Keep the result of fn() for CACHE_SECONDS in this process.

    Use it for numbers over the whole corpus. They are the same for every request and change only when new data loads.
    """
    now = time.monotonic()
    hit = _cache.get(key)
    if hit and now - hit[0] < CACHE_SECONDS:
        return hit[1]
    value = fn()
    _cache[key] = (now, value)
    return value


def corpus_party_totals(conn):
    """Return a dict: party code to the number of speeches of that party that have any kept item.

    The party is the party of the member at the date of the debate. A speech with no known party is left out.
    """
    def load():
        return dict(conn.execute(text(f"""
            SELECT pa.party, count(*) FROM (SELECT DISTINCT speech_id FROM speech_items WHERE kept) k
            JOIN speeches s ON s.id = k.speech_id JOIN debates d ON d.id = s.debate_id {PARTY_AT_DATE}
            WHERE pa.party IS NOT NULL GROUP BY 1""")).all())
    return cached("party_totals", load)


def resolve_slug(rows, wanted, accept=None):
    """Return the id of the live tag for a slug, or None.

    rows is a list of (id, tag, status, merged_into). A live tag wins over a merged tag
    with the same slug. A merged tag leads to its kept tag, through the chain of merged_into.
    When accept is given, it is a function of a tag id. Only a kept tag for which it returns True can win.
    """
    by_id = {r[0]: r for r in rows}
    ok = accept or (lambda _tid: True)
    live = sorted(r[0] for r in rows if r[2] not in ("rejected", "merged") and slug(r[1]) == wanted)
    for tid in live:
        if ok(tid):
            return tid
    merged = sorted(r[0] for r in rows if r[2] == "merged" and slug(r[1]) == wanted)
    for tid in merged:
        seen = set()
        while tid in by_id and by_id[tid][3] is not None and tid not in seen:
            seen.add(tid)
            tid = by_id[tid][3]
        row = by_id.get(tid)
        if row and row[2] not in ("rejected", "merged") and ok(tid):
            return tid
    return None


def resolve_tag(conn, key, tag_type=None):
    """Return the live tag row (a dict) for a slug, or None.

    A live tag wins. A merged tag whose slug matches resolves to its kept tag. When tag_type is given, the kept tag must have it.
    """
    rows = conn.execute(text("SELECT id, tag, status, merged_into, type FROM tags")).all()
    types = {r[0]: r[4] for r in rows}
    tid = resolve_slug([r[:4] for r in rows], key,
                       (lambda i: types[i] == tag_type) if tag_type is not None else None)
    if tid is None:
        return None
    row = conn.execute(text("SELECT * FROM tags WHERE id = :i"), {"i": tid}).mappings().first()
    return dict(row) if row else None


# The party and seat of a member at the date of a debate, as pa.party and pa.seat.
# The lateral part runs once for each row, so it finds only the speakers period in force.
# The join to parties runs once after it, not once for each row.
PARTY_AT_DATE = """
LEFT JOIN LATERAL (
    SELECT sp.party_id, sp.constituency AS seat
    FROM speakers sp
    WHERE sp.person_id = s.person_id AND sp.lok_sabha_term = d.loksabha
      AND sp.effective_from <= COALESCE(d.debate_date, sp.effective_from)
    ORDER BY sp.effective_from DESC LIMIT 1
) pa_row ON true
LEFT JOIN parties pa_party ON pa_party.id = pa_row.party_id
CROSS JOIN LATERAL (SELECT pa_party.code AS party, pa_row.seat AS seat) pa
"""


def speech_rows(conn, speech_ids, with_tags=True):
    """Return list rows for the speeches, in the order given."""
    if not speech_ids:
        return []
    rows = conn.execute(text(f"""
        SELECT s.id, s.person_id, pe.name AS member, pa.party, pa.seat,
               d.debate_date, d.loksabha, d.session, s.word_count, d.title, d.debate_type,
               d.source_url, se.summary
        FROM speeches s
        JOIN debates d ON d.id = s.debate_id
        LEFT JOIN persons pe ON pe.id = s.person_id
        LEFT JOIN speech_extractions se ON se.speech_id = s.id
        {PARTY_AT_DATE}
        WHERE s.id = ANY(:ids)"""), {"ids": list(speech_ids)}).mappings().all()
    by_id = {r["id"]: r for r in rows}
    tags = speech_tag_map(conn, speech_ids) if with_tags else {}
    out = []
    for sid in speech_ids:
        r = by_id.get(sid)
        if not r:
            continue
        out.append({
            "id": r["id"], "member_id": r["person_id"], "member": r["member"],
            "party": r["party"], "seat": r["seat"],
            "date": r["debate_date"].isoformat() if r["debate_date"] else None,
            "term": r["loksabha"], "session": r["session"], "words": r["word_count"],
            "debate": tidy_title(r["title"]), "debate_type": tidy_type(r["debate_type"]),
            "source_url": r["source_url"], "summary": r["summary"],
            "tags": tags.get(sid, []),
        })
    return out


def speech_tag_map(conn, speech_ids):
    rows = conn.execute(text(f"""
        WITH {SPEECH_TAGS_CTE}
        SELECT st.speech_id, t.tag, t.type, st.source
        FROM speech_tags st JOIN tags t ON t.id = st.tag_id
        WHERE st.speech_id = ANY(:ids)
        ORDER BY st.speech_id, CASE st.source WHEN 'llm' THEN 0 WHEN 'dictionary' THEN 1 ELSE 2 END, t.tag"""),
        {"ids": list(speech_ids)}).mappings().all()
    out = {}
    for r in rows:
        out.setdefault(r["speech_id"], []).append(
            {"name": r["tag"], "slug": slug(r["tag"]), "type": r["type"], "source": r["source"]})
    return out


def tidy_title(t):
    if not t:
        return t
    t = re.sub(r"\s+", " ", t).strip()
    return t[:1] + t[1:].lower() if t.isupper() else t


def tidy_type(t):
    if not t:
        return t
    t = re.sub(r"\s+", " ", t).strip()
    return t.capitalize() if t.isupper() else t


# The speeches of one tag, with the best source of the tag in each speech. A kept item carries the tag when its
# own tag_id is the tag, or when it has no tag_id and its linked entity name has the tag. A tag merged into the
# tag counts as the tag. The two roads are two queries joined by UNION ALL, so each road can use its index.
TAG_SPEECHES_SQL = """
WITH ids AS (SELECT id FROM tags WHERE id = :id OR merged_into = :id),
items AS (
    SELECT si.speech_id, si.source FROM speech_items si
    WHERE si.kept AND si.tag_id IN (SELECT id FROM ids)
    UNION ALL
    SELECT si.speech_id, si.source FROM speech_items si
    JOIN entity_names en ON en.id = si.entity_name_id
    WHERE si.kept AND si.tag_id IS NULL AND en.link_status = 'linked' AND en.tag_id IN (SELECT id FROM ids)
)
SELECT DISTINCT ON (speech_id) speech_id, source FROM items
ORDER BY speech_id, CASE source WHEN 'llm' THEN 0 WHEN 'dictionary' THEN 1 ELSE 2 END
"""


def tag_speeches(conn, tag_id):
    """(speech_id, best source) for each speech of the tag, sorted by speech_id."""
    return [(r[0], r[1]) for r in conn.execute(text(TAG_SPEECHES_SQL), {"id": tag_id})]
