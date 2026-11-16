"""Build the prebuilt API answers again: /api/home, /api/home/featured, /api/method.

Each answer goes to data/built/<name>.json. The routes send these files with no database call.
Run it from the repo root after each data update, or after a change to the featured sample:

    python3 scripts/build_snapshots.py                      # all answers
    python3 scripts/build_snapshots.py --only home method   # some answers
    python3 scripts/build_snapshots.py --featured other.json

--featured builds the featured parts from another sample file. The default is data/home/featured.json.
scripts/build_tag_related.py runs this script at its end, so the publish step runs it too.
After this script, clear the nginx cache of these addresses, or nginx keeps the old answers.
"""
import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import dashboard_db  # noqa: E402
from pages import home_featured, prebuilt  # noqa: E402


def build_all(conn, names=None, featured=None, built_dir=None):
    """Build each named answer, or all answers. Return name -> number of bytes."""
    if featured:
        home_featured.FEATURED_FILE = featured
    out = {}
    for name in names or prebuilt.builders():
        out[name] = len(prebuilt.build(conn, name, built_dir))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--only", nargs="+", choices=sorted(prebuilt.builders()), help="build only these answers")
    ap.add_argument("--featured", help="the featured sample file, in place of data/home/featured.json")
    args = ap.parse_args(argv)
    start = time.monotonic()
    with dashboard_db.get_engine().connect() as conn:
        sizes = build_all(conn, args.only, args.featured)
    for name, n in sizes.items():
        print(f"{prebuilt.path_of(name)}: {n} bytes")
    print(f"built {len(sizes)} answers in {time.monotonic() - start:.1f} s")


if __name__ == "__main__":
    main()
