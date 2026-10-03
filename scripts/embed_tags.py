"""Embed every tag in the table `tags` with the embedding model, for one task type.

The script skips a tag that has a vector with the same md5 hash. It needs GEMINI_API_KEY in the environment.
Run from the repo root:

    set -a && source .env && set +a
    python3 scripts/embed_tags.py --task-type RETRIEVAL_DOCUMENT
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from db import get_engine
from tag_embed import DIMS, MODEL, TASK_TYPES, build_input_text, embed_texts, input_hash, to_pgvector


def to_embed(tags: list[dict], stored: dict[int, str]) -> list[dict]:
    out = []
    for t in tags:
        body = build_input_text(t["tag"], t["type"], t["domain"], t["description"], t["aliases"])
        h = input_hash(body)
        if stored.get(t["id"]) != h:
            out.append({"id": t["id"], "text": body, "hash": h})
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--task-type", required=True, choices=sorted(TASK_TYPES))
    args = ap.parse_args()

    engine = get_engine()
    with engine.connect() as conn:
        tags = [dict(r._mapping) for r in conn.execute(text(
            "SELECT id, tag, type, domain, description, aliases FROM tags WHERE status <> 'rejected' ORDER BY id"))]
        stored = dict(conn.execute(text(
            "SELECT tag_id, input_hash FROM tag_embeddings WHERE model = :m AND task_type = :t"),
            {"m": MODEL, "t": args.task_type}).all())
    if not tags:
        raise SystemExit("the table tags is empty. Run scripts/load_tags.py first.")

    todo = to_embed(tags, stored)
    print(f"{len(tags)} tags, {len(todo)} need a vector ({MODEL}, {args.task_type})", flush=True)
    if not todo:
        return
    vectors = embed_texts([t["text"] for t in todo], args.task_type)

    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO tag_embeddings (tag_id, model, task_type, dims, input_text, input_hash, embedding)
            VALUES (:id, :m, :t, :dims, :text, :hash, CAST(:vec AS vector))
            ON CONFLICT (tag_id, model, task_type) DO UPDATE SET
                dims = EXCLUDED.dims, input_text = EXCLUDED.input_text, input_hash = EXCLUDED.input_hash,
                embedding = EXCLUDED.embedding, created_at = now()
        """), [{**t, "m": MODEL, "t": args.task_type, "dims": DIMS, "vec": to_pgvector(v)}
               for t, v in zip(todo, vectors)])
        n = conn.execute(text("SELECT count(*) FROM tag_embeddings WHERE model = :m AND task_type = :t"),
                         {"m": MODEL, "t": args.task_type}).scalar()
    print(f"stored. {n} vectors for {MODEL}, {args.task_type}", flush=True)


if __name__ == "__main__":
    main()
