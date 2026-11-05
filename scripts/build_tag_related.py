"""Build the table tag_related: the related tags of each tag, ranked by lift.

Lift tells how much more often two tags share a speech than chance gives.
    expected = (speeches with tag A x speeches with tag B) / all tagged speeches
    lift     = shared / expected
A pair needs at least MIN_SHARED shared speeches. The related tag cannot be of type place or role.
Tags with status merged or rejected do not count. A merged tag counts as its kept tag,
exactly as SPEECH_TAGS_CTE does. Each speech counts once for each tag.
The script keeps the TOP best related tags for each tag. It replaces all rows in one transaction.
It calls no model, and a second run gives the same rows.

    source .venv/bin/activate && set -a && source .env && set +a
    python3 scripts/build_tag_related.py --dry-run
    python3 scripts/build_tag_related.py
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

MIN_SHARED = 8
TOP = 30

PAIRS_SQL = """
WITH {cte},
live AS (
    SELECT st.speech_id, st.tag_id, t.type FROM speech_tags st JOIN tags t ON t.id = st.tag_id
    WHERE t.status NOT IN ('rejected', 'merged')
)
SELECT a.tag_id, b.tag_id, count(*) FROM live a JOIN live b ON a.speech_id = b.speech_id AND a.tag_id <> b.tag_id
WHERE b.type NOT IN ('place', 'role')
GROUP BY 1, 2 HAVING count(*) >= :min_shared
"""

COUNTS_SQL = """
WITH {cte},
live AS (
    SELECT st.speech_id, st.tag_id FROM speech_tags st JOIN tags t ON t.id = st.tag_id
    WHERE t.status NOT IN ('rejected', 'merged')
)
SELECT tag_id, count(*) FROM live GROUP BY 1
"""

TOTAL_SQL = "WITH {cte} SELECT count(DISTINCT speech_id) FROM speech_tags"


def rank_related(pairs, tag_counts, total, names, min_shared=MIN_SHARED, top=TOP):
    """Return the rows (tag_id, related_tag_id, shared, expected, lift) of the table. No database is needed.

    pairs: a list of (tag_id, related_tag_id, shared). tag_counts: tag_id to its number of speeches.
    total: the number of all tagged speeches. names: tag_id to tag name, used to order equal rows.
    A tag keeps its top related tags: the highest lift first, then more shared speeches, then the name.
    """
    by_tag = {}
    for a, b, shared in pairs:
        if shared < min_shared:
            continue
        expected = tag_counts[a] * tag_counts[b] / total
        by_tag.setdefault(a, []).append((a, b, shared, expected, shared / expected))
    out = []
    for a, rows in by_tag.items():
        rows.sort(key=lambda r: (-r[4], -r[2], names[r[1]], r[1]))
        out.extend(rows[:top])
    return sorted(out)


def main() -> None:
    from db import get_engine
    from pages.common import SPEECH_TAGS_CTE
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="count the rows and write nothing")
    args = ap.parse_args()
    engine = get_engine()
    cte = SPEECH_TAGS_CTE.strip()
    with engine.connect() as conn:
        total = conn.execute(text(TOTAL_SQL.format(cte=cte))).scalar()
        print(f"tagged speeches {total}", flush=True)
        counts = dict(conn.execute(text(COUNTS_SQL.format(cte=cte))).all())
        print(f"live tags with a speech {len(counts)}", flush=True)
        pairs = conn.execute(text(PAIRS_SQL.format(cte=cte)), {"min_shared": MIN_SHARED}).all()
        print(f"pairs with {MIN_SHARED} or more shared speeches {len(pairs)}", flush=True)
        names = dict(conn.execute(text("SELECT id, tag FROM tags")).all())
    rows = rank_related(pairs, counts, total, names)
    print(f"rows to keep {len(rows)}, tags with a row {len({r[0] for r in rows})}", flush=True)
    if args.dry_run:
        return
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM tag_related"))
        conn.execute(text("INSERT INTO tag_related (tag_id, related_tag_id, shared, expected, lift) "
                          "VALUES (:a, :b, :s, :e, :l)"),
                     [{"a": a, "b": b, "s": s, "e": e, "l": l} for a, b, s, e, l in rows])
    print("loaded", flush=True)


if __name__ == "__main__":
    main()
