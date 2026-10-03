"""
Load the seed tag list into the table `tags`. This script calls no model.

Input: tags/seed_tags_v1/results/seed_tags_v1.tsv, made by
scripts/build_seed_tags.py. Columns: tag, type, subtype, domain, description,
aliases ('|' between names, '-' for none), debate_count.

Safe to run again. A tag that exists gets the new values from the file and
keeps its id. A seed tag that is no longer in the file is deleted, with its
vectors. Tags from other sources are not touched.

Run from the repo root, with .env loaded and db/init/10-tags.sql applied:

    python3 scripts/load_tags.py
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from db import get_engine

SEED_FILE = Path(__file__).resolve().parent.parent / "tags" / "seed_tags_v1" / "results" / "seed_tags_v1.tsv"
SOURCE = "seed_v1"


def parse_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE))
    out = []
    for r in rows:
        out.append({
            "tag": r["tag"],
            "type": r["type"],
            "subtype": r["subtype"] or None,
            "domain": None if r["domain"] in ("", "-") else r["domain"],
            "description": r["description"],
            "aliases": [] if r["aliases"] in ("", "-") else r["aliases"].split("|"),
            "debate_count": int(r["debate_count"]),
        })
    names = [r["tag"] for r in out]
    if len(set(names)) != len(names):
        raise SystemExit("the file holds the same tag name two times")
    if any(n != n.strip() or not n for n in names):
        raise SystemExit("a tag name is empty or has outer spaces. Run scripts/build_seed_tags.py first.")
    return out


def main() -> None:
    rows = parse_rows(SEED_FILE)
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO tags (tag, type, subtype, domain, description, aliases, debate_count, source, status)
            VALUES (:tag, :type, :subtype, :domain, :description, :aliases, :debate_count, :source, 'reviewed')
            ON CONFLICT (tag) DO UPDATE SET
                type = EXCLUDED.type, subtype = EXCLUDED.subtype, domain = EXCLUDED.domain,
                description = EXCLUDED.description, aliases = EXCLUDED.aliases,
                debate_count = EXCLUDED.debate_count
        """), [{**r, "source": SOURCE} for r in rows])
        gone = conn.execute(text("DELETE FROM tags WHERE source = :s AND NOT (tag = ANY(:names)) RETURNING tag"),
                            {"s": SOURCE, "names": [r["tag"] for r in rows]}).scalars().all()
        total = conn.execute(text("SELECT count(*) FROM tags WHERE source = :s"), {"s": SOURCE}).scalar()
    print(f"{len(rows)} rows in the file, {total} seed tags in the table, {len(gone)} deleted", flush=True)
    for name in gone:
        print(f"  deleted: {name!r}", flush=True)
    if total != len(rows):
        raise SystemExit(f"count mismatch: file {len(rows)}, table {total}")


if __name__ == "__main__":
    main()
