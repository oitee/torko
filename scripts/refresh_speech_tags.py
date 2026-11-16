"""Fill the stored views of each speech again: the tags (speech_tags_mv) and the party at the debate date (speech_party_mv).

Run it from the repo root after each change to tags, links, kept items, speeches, or speakers:

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


VIEWS = ("speech_tags_mv", "speech_party_mv")


def refresh(conn):
    """Fill each view again and update its statistics. Return the number of rows of speech_tags_mv."""
    for view in VIEWS:
        conn.execute(text(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {view}"))
        conn.execute(text(f"ANALYZE {view}"))
    return conn.execute(text("SELECT count(*) FROM speech_tags_mv")).scalar()


def main():
    start = time.monotonic()
    with dashboard_db.get_engine().begin() as conn:
        n = refresh(conn)
    print(f"views refreshed, speech_tags_mv {n} rows, in {time.monotonic() - start:.1f} s")


if __name__ == "__main__":
    main()
