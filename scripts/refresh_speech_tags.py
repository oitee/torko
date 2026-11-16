"""Fill the stored tags of each speech (the view speech_tags_mv) again from speech_items, entity_names, and tags.

Run it from the repo root after each change to tags, links, or kept items:

    python3 scripts/refresh_speech_tags.py

scripts/build_tag_related.py calls it first, so the publish step runs it too.
The pages keep reading the old rows while the refresh runs.
"""
import sys
import time
from pathlib import Path

from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import dashboard_db  # noqa: E402


def refresh(conn):
    """Fill the view again and update its statistics. Return the number of rows."""
    conn.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY speech_tags_mv"))
    conn.execute(text("ANALYZE speech_tags_mv"))
    return conn.execute(text("SELECT count(*) FROM speech_tags_mv")).scalar()


def main():
    start = time.monotonic()
    with dashboard_db.get_engine().begin() as conn:
        n = refresh(conn)
    print(f"speech_tags_mv: {n} rows in {time.monotonic() - start:.1f} s")


if __name__ == "__main__":
    main()
