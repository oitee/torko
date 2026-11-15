"""Embed every argument point whose quote is in its speech, for the order of the points before the grouping.

The vector is of the point text only. A point that has a vector with the same md5 hash is skipped.
It needs GEMINI_API_KEY in the environment. Run from the repo root:

    set -a && source .env && set +a
    python3 scripts/embed_arguments.py --dry-run   # count only
    python3 scripts/embed_arguments.py
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from db import get_engine
from tag_embed import MODEL, embed_texts, to_pgvector

TASK_TYPE = "SEMANTIC_SIMILARITY"
CHUNK = 2000


def md5(body: str) -> str:
    return hashlib.md5(body.encode("utf-8")).hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    eng = get_engine()
    with eng.connect() as conn:
        rows = conn.execute(text("""
            SELECT a.id, a.point, v.input_md5 FROM speech_arguments a
            LEFT JOIN argument_vectors v ON v.argument_id = a.id
            WHERE a.quote_found ORDER BY a.id""")).all()
    todo = [(i, p) for i, p, h in rows if h != md5(p)]
    print(f"{len(rows)} points, {len(todo)} need a vector")
    if args.dry_run or not todo:
        return
    for start in range(0, len(todo), CHUNK):
        part = todo[start:start + CHUNK]
        vectors = embed_texts([p for _, p in part], TASK_TYPE)
        with eng.begin() as conn:
            for (i, p), v in zip(part, vectors):
                conn.execute(text("""
                    INSERT INTO argument_vectors (argument_id, model, input_md5, vector)
                    VALUES (:i, :m, :h, CAST(:v AS vector))
                    ON CONFLICT (argument_id) DO UPDATE SET model = :m, input_md5 = :h, vector = CAST(:v AS vector)"""),
                    {"i": i, "m": MODEL, "h": md5(p), "v": to_pgvector(v)})
        print(f"stored {start + len(part)}/{len(todo)}", flush=True)


if __name__ == "__main__":
    main()
