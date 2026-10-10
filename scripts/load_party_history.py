"""
Load the party and the constituency of each member for each term into `speakers`.

Input: data/party_history/results/speaker_terms.tsv (made by scripts/build_party_history.py).

For each (member, term) row in the file, except the member's last term:
  - a Wikipedia match gives a row with source 'wikipedia', the party code, and the constituency.
  - no match gives a row with source 'sansad-term-list' and no party: the member sat in the
    term, but the party is not known.
The member's last-term row comes from scripts/load_roster.py (source 'sansad-last-term').
This script never changes that row.

Safe to run again: it replaces the rows that it owns, and only those.

Run from the repo root, with the database up and db/init/16-speaker-terms.sql applied:

    python3 -m scripts.load_party_history
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

from sqlalchemy import text

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from db import get_engine  # noqa: E402

TSV = ROOT / "data" / "party_history" / "results" / "speaker_terms.tsv"
OWNED = ("wikipedia", "sansad-term-list")


def read_rows() -> list[dict]:
    with open(TSV, encoding="utf-8", newline="") as f:
        return [r for r in csv.DictReader(f, delimiter="\t") if r["term"] != r["last_term"]]


def load(rows: list[dict]) -> None:
    engine = get_engine()
    with engine.begin() as conn:
        persons = dict(conn.execute(text("SELECT sansad_id, id FROM persons WHERE sansad_id IS NOT NULL")).all())
        names = dict(conn.execute(text("SELECT id, name FROM persons")).all())
        missing = sorted({int(r["mpsno"]) for r in rows} - set(persons))
        if missing:
            print(f"members with no row in persons, skipped: {len(missing)} {missing[:20]}", flush=True)
        removed = conn.execute(text("DELETE FROM speakers WHERE source = ANY(:owned)"),
                               {"owned": list(OWNED)}).rowcount
        params = []
        for r in rows:
            pid = persons.get(int(r["mpsno"]))
            if pid is None:
                continue
            matched = r["method"] != "none"
            params.append({
                "person_id": pid,
                "term": int(r["term"]),
                "name": names[pid],
                "party": (r["party"] or None) if matched else None,
                "constituency": (r["constituency"] or None) if matched else None,
                "source": "wikipedia" if matched else "sansad-term-list",
                "method": r["method"] if matched else None,
            })
        result = conn.execute(
            text(
                """
                INSERT INTO speakers (person_id, lok_sabha_term, name, party, constituency, source, match_method)
                VALUES (:person_id, :term, :name, :party, :constituency, :source, :method)
                ON CONFLICT (lok_sabha_term, person_id) DO NOTHING
                """
            ),
            params,
        )
        print(f"removed old rows: {removed}", flush=True)
        print(f"rows to insert  : {len(params)}", flush=True)
        print(f"inserted        : {result.rowcount}", flush=True)
        if result.rowcount != len(params):
            print("some rows collided with a sansad-last-term row and were not inserted", flush=True)


def main() -> None:
    load(read_rows())


if __name__ == "__main__":
    sys.exit(main())
