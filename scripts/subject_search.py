"""Search tags and subjects from the command line. The rule is in tag_search.py.

    source .venv/bin/activate && set -a && source .env && set +a
    python3 scripts/subject_search.py "arrears" "farmers arrears"
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tag_search import load_index, search


def main() -> None:
    from db import get_engine
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("query", nargs="+")
    args = ap.parse_args()
    with get_engine().connect() as conn:
        tags, subjects = load_index(conn)
    for q in args.query:
        print(f"\n=== {q}")
        for r in search(q, tags, subjects):
            if r["kind"] == "tag":
                print(f"TAG {r['name']} ({r['n_speeches']} speeches with its subjects)")
                for s in r["subjects"][:8]:
                    print(f"    subject: {s['label']} ({s['n_speeches']})")
            else:
                print(f"SUBJECT {r['name']} ({r['n_speeches']}) under tag: {r['parent_tag'] or '-'}")


if __name__ == "__main__":
    main()
