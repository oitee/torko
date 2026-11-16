"""Apply the bill checks again to every stored answer in bill_extractions. It calls no model.

Use it after a change to the checks in bill_extract.py. The model, the prompt version, and the tokens of
each row stay the same. A debate whose input text changed is skipped.
Without --commit the script rolls back, so a dry run also tests the inserts.

    set -a && source .env && set +a
    python3 scripts/recheck_bills.py            # dry run
    python3 scripts/recheck_bills.py --commit
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import bill_extract as be
from db import get_engine


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--commit", action="store_true", help="keep the changes")
    args = ap.parse_args()
    with get_engine().connect() as conn:
        tx = conn.begin()
        counts = be.recheck_stored(conn)
        tx.commit() if args.commit else tx.rollback()
    print(", ".join(f"{name.replace('_', ' ')}: {v}" for name, v in counts.items()))
    print("Committed." if args.commit else "Dry run: rolled back. Use --commit to keep the changes.")


if __name__ == "__main__":
    main()
