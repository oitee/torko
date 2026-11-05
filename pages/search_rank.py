"""Best-match search: join a list of word matches and a list of the nearest summaries.

Word search finds the words themselves. Search by meaning compares the vector of the search text with the vector of the
one-sentence summary of each speech, so it finds a speech that uses other words or another language. Each list gives
points by rank (reciprocal rank fusion): a speech gets 1 / (K + rank) from each list that holds it.
"""
import re

from sqlalchemy import text

from tag_embed import MODEL, embed_query, to_pgvector

K = 60
WORD_LIST = 500
VECTOR_LIST = 200
MAX_DISTANCE = 0.42  # On the test set, real questions stay below this cosine distance, and nonsense stays above it.
MAX_QUERY_CHARS = 300
# A match in the title, name or summary counts more than a match in a long text.
WORD_RANK_SQL = """(ts_rank(ss.head, {q}) * 2 + ts_rank(ss.words, {q}, 2))"""


def phrase_of(q):
    """The words between quote marks when the whole search text is in quote marks, else None."""
    m = re.fullmatch(r'\s*["“](.+?)["”]\s*', q or "")
    return m.group(1).strip() if m else None


def normal_query(q):
    return re.sub(r"\s+", " ", (q or "").strip().lower())[:MAX_QUERY_CHARS]


def fuse(lists, k=K):
    """Return the speech ids in order of the sum of 1 / (k + rank) over the lists. A tie goes to the lower id."""
    points = {}
    for ids in lists:
        for rank, sid in enumerate(ids, 1):
            points[sid] = points.get(sid, 0) + 1 / (k + rank)
    return sorted(points, key=lambda sid: (-points[sid], sid))


def query_vector(store, q):
    """Return the vector of the search text as text for pgvector, or None when the model call fails.

    store is an engine. A vector that was read before comes from the table query_vectors, with no model call.
    """
    key = normal_query(q)
    with store.connect() as conn:
        got = conn.execute(text("SELECT embedding::text FROM query_vectors WHERE query = :q AND model = :m"),
                           {"q": key, "m": MODEL}).scalar()
    if got:
        return got
    try:
        vector = to_pgvector(embed_query(key))
    except Exception as err:  # Word results are still correct when the model call fails.
        print(f"query vector failed: {err}", flush=True)
        return None
    with store.begin() as conn:
        conn.execute(text("""INSERT INTO query_vectors (query, model, embedding) VALUES (:q, :m, CAST(:v AS vector))
            ON CONFLICT (query) DO NOTHING"""), {"q": key, "m": MODEL, "v": vector})
    return vector


def stored_near(store, q):
    """The stored nearest speeches of the search text with no filter, or None."""
    with store.connect() as conn:
        return conn.execute(text("SELECT near_ids FROM query_vectors WHERE query = :q AND model = :m"),
                            {"q": normal_query(q), "m": MODEL}).scalar()


def save_near(store, q, ids):
    with store.begin() as conn:
        conn.execute(text("UPDATE query_vectors SET near_ids = :ids WHERE query = :q AND model = :m"),
                     {"ids": ids, "q": normal_query(q), "m": MODEL})


def nearest_speeches(conn, vector, from_sql, where_sql, params, limit=VECTOR_LIST, max_distance=MAX_DISTANCE):
    """The nearest summaries under the filters, nearest first, within the distance limit."""
    rows = conn.execute(text(f"""
        SELECT s.id, v.embedding <=> CAST(:qv AS vector) AS distance
        {from_sql} JOIN speech_summary_embeddings v ON v.speech_id = s.id
        LEFT JOIN speech_search ss ON ss.speech_id = s.id
        WHERE {where_sql} AND ss.repeat_of IS NULL
        ORDER BY v.embedding <=> CAST(:qv AS vector) LIMIT :lim"""), {**params, "qv": vector, "lim": limit}).all()
    return [r[0] for r in rows if r[1] <= max_distance]


def word_speeches(conn, q, from_sql, where_sql, params, limit=WORD_LIST):
    """The speeches with every word of q under the filters, best word match first."""
    tsq = "plainto_tsquery('simple', :wq)"
    return [r[0] for r in conn.execute(text(f"""
        SELECT s.id {from_sql} JOIN speech_search ss ON ss.speech_id = s.id
        WHERE {where_sql} AND ss.words @@ {tsq} AND ss.repeat_of IS NULL
        ORDER BY {WORD_RANK_SQL.format(q=tsq)} DESC, s.id LIMIT :lim"""), {**params, "wq": q, "lim": limit})]
