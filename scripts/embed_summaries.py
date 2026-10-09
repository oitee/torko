"""Embed the summary of each speech, so that a search can find the nearest tags.

The script skips a summary that has a vector with the same md5 hash and the summaries of the model 'rule-stub'.
It needs GEMINI_API_KEY in the environment. Run from the repo root:

    set -a && source .env && set +a
    python3 scripts/embed_summaries.py --dry-run
    python3 scripts/embed_summaries.py --term 16 --limit 100
    python3 scripts/embed_summaries.py
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from db import get_engine
from tag_embed import DIMS, MODEL, embed_texts, input_hash, to_pgvector

TASK_TYPE = "RETRIEVAL_QUERY"
TAG_TASK_TYPE = "RETRIEVAL_DOCUMENT"
STUB_MODEL = "rule-stub"
# A rough size of one token in characters. It gives the estimate in --dry-run.
CHARS_PER_TOKEN = 4
WRITE_BATCH = 500


def to_embed(rows: list[dict], stored: dict[int, str]) -> list[dict]:
    out = []
    for r in rows:
        body = (r["summary"] or "").strip()
        if not body:
            continue
        h = input_hash(body)
        if stored.get(r["extraction_id"]) != h:
            out.append({"extraction_id": r["extraction_id"], "speech_id": r["speech_id"], "text": body, "hash": h})
    return out


def estimate_tokens(texts: list[str]) -> int:
    return sum(len(t) for t in texts) // CHARS_PER_TOKEN


def select_summaries(conn, term: int | None = None, extraction_ids: list[int] | None = None) -> list[dict]:
    sql = """
        SELECT e.id AS extraction_id, e.speech_id, e.summary
        FROM speech_extractions e
        JOIN models m ON m.id = e.model_id
        JOIN speeches s ON s.id = e.speech_id
        JOIN debates d ON d.id = s.debate_id
        WHERE m.name <> :stub
          AND (CAST(:term AS int) IS NULL OR d.loksabha = :term)
          AND (CAST(:ids AS bigint[]) IS NULL OR e.id = ANY(CAST(:ids AS bigint[])))
        ORDER BY e.id
    """
    return [dict(r._mapping) for r in conn.execute(
        text(sql), {"stub": STUB_MODEL, "term": term, "ids": extraction_ids})]


def stored_hashes(conn) -> dict[int, str]:
    return dict(conn.execute(text(
        "SELECT extraction_id, input_hash FROM speech_summary_embeddings WHERE model = :m AND task_type = :t"),
        {"m": MODEL, "t": TASK_TYPE}).all())


def store(conn, todo: list[dict], vectors: list[list[float]]) -> None:
    conn.execute(text("""
        INSERT INTO speech_summary_embeddings (extraction_id, speech_id, model, task_type, dims, input_hash, embedding)
        VALUES (:extraction_id, :speech_id, :m, :t, :dims, :hash, CAST(:vec AS vector))
        ON CONFLICT (extraction_id) DO UPDATE SET
            speech_id = EXCLUDED.speech_id, model = EXCLUDED.model, task_type = EXCLUDED.task_type,
            dims = EXCLUDED.dims, input_hash = EXCLUDED.input_hash, embedding = EXCLUDED.embedding,
            created_at = now()
    """), [{"extraction_id": t["extraction_id"], "speech_id": t["speech_id"], "m": MODEL, "t": TASK_TYPE,
            "dims": DIMS, "hash": t["hash"], "vec": to_pgvector(v)} for t, v in zip(todo, vectors)])


def nearest_tags(conn, speech_ids: list[int], n: int = 20) -> dict[int, list[dict]]:
    """Each row has rank (1 is the nearest) and cosine distance (0 is the same direction).
    A speech with no summary vector gets an empty list."""
    sql = """
        SELECT q.speech_id, t.tag_id, t.tag, t.type, t.description, t.distance, t.rank
        FROM speech_summary_embeddings q
        CROSS JOIN LATERAL (
            SELECT g.id AS tag_id, g.tag, g.type, g.description,
                   te.embedding <=> q.embedding AS distance,
                   row_number() OVER (ORDER BY te.embedding <=> q.embedding, g.id) AS rank
            FROM tag_embeddings te
            JOIN tags g ON g.id = te.tag_id
            WHERE te.model = :m AND te.task_type = :tt AND g.status <> 'rejected'
            ORDER BY te.embedding <=> q.embedding, g.id
            LIMIT :n
        ) t
        WHERE q.speech_id = ANY(:ids) AND q.model = :m AND q.task_type = :qt
        ORDER BY q.speech_id, t.rank
    """
    out: dict[int, list[dict]] = {i: [] for i in speech_ids}
    for r in conn.execute(text(sql), {"m": MODEL, "tt": TAG_TASK_TYPE, "qt": TASK_TYPE,
                                      "n": n, "ids": list(speech_ids)}):
        d = dict(r._mapping)
        out[d.pop("speech_id")].append(d)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--term", type=int, help="only speeches of this Lok Sabha term (debates.loksabha)")
    ap.add_argument("--limit", type=int, help="embed at most this many summaries")
    ap.add_argument("--extraction-ids", help="comma-separated extraction ids: embed only these")
    ap.add_argument("--dry-run", action="store_true", help="count and estimate, with no API call")
    args = ap.parse_args()

    ids = [int(x) for x in args.extraction_ids.split(",")] if args.extraction_ids else None
    engine = get_engine()
    with engine.connect() as conn:
        rows = select_summaries(conn, args.term, ids)
        todo = to_embed(rows, stored_hashes(conn))
    if args.limit is not None:
        todo = todo[:args.limit]
    print(f"{len(rows)} summaries (no stubs), {len(todo)} need a vector ({MODEL}, {TASK_TYPE})", flush=True)
    print(f"about {estimate_tokens([t['text'] for t in todo])} input tokens", flush=True)
    if args.dry_run or not todo:
        return

    done = 0
    for start in range(0, len(todo), WRITE_BATCH):
        chunk = todo[start:start + WRITE_BATCH]
        vectors = embed_texts([t["text"] for t in chunk], TASK_TYPE)
        with engine.begin() as conn:
            store(conn, chunk, vectors)
        done += len(chunk)
        print(f"stored {done}/{len(todo)}", flush=True)
    with engine.connect() as conn:
        n = conn.execute(text("SELECT count(*) FROM speech_summary_embeddings")).scalar()
    print(f"done. {n} summary vectors in the table", flush=True)


if __name__ == "__main__":
    main()
