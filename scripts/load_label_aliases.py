"""Load data/label_aliases.tsv into the table label_aliases.

Each row says that one speaker label, in one Lok Sabha term, names one member.
The script checks every row, stops on the first bad row, then replaces the whole table in one transaction.

Run before scripts/populate_turns.py:
    python3 scripts/load_label_aliases.py --dry-run
    python3 scripts/load_label_aliases.py
"""
from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text  # noqa: E402

from db import get_engine  # noqa: E402
from debate_fetch import is_crowd_label, is_presiding_label  # noqa: E402
from label_attribution import normalize_label  # noqa: E402

FILE = Path(__file__).resolve().parent.parent / "data" / "label_aliases.tsv"
COLUMNS = ["loksabha", "speaker_label", "person_id", "member_name", "basis", "source"]
BASES = {"name_and_constituency", "name", "constituency", "office"}


def read_rows(path: Path) -> list[dict]:
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE)
        if reader.fieldnames != COLUMNS:
            raise SystemExit(f"{path}: the header must be {COLUMNS}, not {reader.fieldnames}")
        return [dict(r, loksabha=int(r["loksabha"]), person_id=int(r["person_id"])) for r in reader]


def check_rows(rows: list[dict], terms: set[int], names: dict[int, str]) -> None:
    for n, r in enumerate(rows, 2):
        label = r["speaker_label"]
        if label != normalize_label(label) or not label:
            raise SystemExit(f"line {n}: the label is empty or not normalised: {label!r}")
        if is_presiding_label(label) or is_crowd_label(label):
            raise SystemExit(f"line {n}: a chair or crowd label never names a member: {label!r}")
        if r["loksabha"] not in terms:
            raise SystemExit(f"line {n}: unknown term {r['loksabha']}")
        if r["person_id"] not in names:
            raise SystemExit(f"line {n}: unknown person {r['person_id']}")
        if normalize_label(names[r["person_id"]]) != normalize_label(r["member_name"]):
            raise SystemExit(f"line {n}: member_name {r['member_name']!r} is not the roster name "
                             f"{names[r['person_id']]!r} of person {r['person_id']}")
        if r["basis"] not in BASES:
            raise SystemExit(f"line {n}: unknown basis {r['basis']!r}")
        if not r["source"]:
            raise SystemExit(f"line {n}: empty source")
    doubles = [k for k, c in Counter((r["loksabha"], r["speaker_label"]) for r in rows).items() if c > 1]
    if doubles:
        raise SystemExit(f"{len(doubles)} (term, label) pairs occur twice, for example {doubles[0]}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--file", type=Path, default=FILE)
    ap.add_argument("--dry-run", action="store_true", help="check the rows and roll back")
    args = ap.parse_args()

    rows = read_rows(args.file)
    engine = get_engine()
    with engine.connect() as conn:
        terms = {r[0] for r in conn.execute(text("SELECT number FROM lok_sabhas"))}
        names = dict(conn.execute(text("""
            SELECT p.id, coalesce(s.name, p.name) FROM persons p
            LEFT JOIN LATERAL (SELECT name FROM speakers WHERE person_id = p.id
                               ORDER BY lok_sabha_term DESC LIMIT 1) s ON true""")).all())
    check_rows(rows, terms, names)

    with engine.connect() as conn:
        trans = conn.begin()
        before = conn.execute(text("SELECT count(*) FROM label_aliases")).scalar()
        conn.execute(text("DELETE FROM label_aliases"))
        conn.execute(text("""
            INSERT INTO label_aliases (loksabha, speaker_label, person_id, basis, source)
            VALUES (:loksabha, :speaker_label, :person_id, :basis, :source)"""), rows)
        after = conn.execute(text("SELECT count(*) FROM label_aliases")).scalar()
        trans.rollback() if args.dry_run else trans.commit()
    by_term = Counter(r["loksabha"] for r in rows)
    print(f"{len(rows)} rows checked ({', '.join(f'LS {t}: {c}' for t, c in sorted(by_term.items()))}), "
          f"{len({r['person_id'] for r in rows})} persons. Table rows: {before} before, {after} after.")
    print("DRY RUN: rolled back." if args.dry_run else "Stored.")


if __name__ == "__main__":
    main()
