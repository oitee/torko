"""
Load the party and the constituency of each member for each term into `speakers`.

Input: data/party_history/results/speaker_terms.tsv (made by scripts/build_party_history.py),
       data/party_history/party_codes.tsv and the sansad.in lists, for the full party names.

For each (member, term) row in the file, except the member's last term:
  - a Wikipedia match gives a row with source 'wikipedia', the party, and the constituency.
  - a row from manual.tsv gives a row with source 'manual'.
  - no match gives a row with source 'sansad-term-list' and no party: the member sat in the
    term, but the party is not known.
The member's last-term row comes from scripts/load_roster.py (source 'sansad-last-term').
This script never changes that row.

Then, for each member who has turns in a term with no row (mostly a minister from the
Rajya Sabha), it adds a row with source 'last-term-fallback'. That row copies the party of the
member's last-term row and has no constituency. TODO: a real party for these speakers.

The script also writes the full name of each party into `parties`.

Safe to run again: it replaces the rows that it owns, and only those.

Run from the repo root, with the database up and db/init/16 and 17 applied:

    python3 -m scripts.load_party_history
"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

from sqlalchemy import text

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from db import get_engine  # noqa: E402

DATA = ROOT / "data" / "party_history"
TSV = DATA / "results" / "speaker_terms.tsv"
OWNED = ("wikipedia", "sansad-term-list", "manual", "last-term-fallback")


def read_rows() -> list[dict]:
    with open(TSV, encoding="utf-8", newline="") as f:
        return [r for r in csv.DictReader(f, delimiter="\t") if r["term"] != r["last_term"]]


def party_names(rows: list[dict]) -> dict[str, str]:
    names: dict[str, str] = {}
    for path in sorted((DATA / "raw").glob("sansad_ls*.json")):
        for m in json.loads(path.read_text(encoding="utf-8")):
            code, name = (m.get("partySname") or "").strip(), (m.get("partyFname") or "").strip()
            if code and name and code != "Not Available":
                names[code] = re.sub(r"\s+", " ", name)
    with open(DATA / "party_codes.tsv", encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            if r["code"].strip():
                names.setdefault(r["code"].strip(), r["wiki_party"].strip())
    for r in rows:
        if r["party"]:
            names.setdefault(r["party"], r["wiki_party"] or r["party"])
    return names


def load(rows: list[dict]) -> None:
    engine = get_engine()
    with engine.begin() as conn:
        for code, name in party_names(rows).items():
            conn.execute(text("INSERT INTO parties (code, name) VALUES (:c, :n) "
                              "ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name"), {"c": code, "n": name})
        party_ids = dict(conn.execute(text("SELECT code, id FROM parties")).all())
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
            method = r["method"]
            matched = method != "none"
            params.append({
                "person_id": pid,
                "term": int(r["term"]),
                "name": names[pid],
                "party_id": party_ids[r["party"]] if matched and r["party"] else None,
                "constituency": (r["constituency"] or None) if matched else None,
                "source": "manual" if method == "manual" else "wikipedia" if matched else "sansad-term-list",
                "method": method if matched else None,
            })
        inserted = conn.execute(
            text(
                """
                INSERT INTO speakers (person_id, lok_sabha_term, name, party_id, constituency, source, match_method)
                VALUES (:person_id, :term, :name, :party_id, :constituency, :source, :method)
                ON CONFLICT (lok_sabha_term, person_id) DO NOTHING
                """
            ),
            params,
        ).rowcount
        fallback = conn.execute(
            text(
                """
                INSERT INTO speakers (person_id, lok_sabha_term, name, party_id, constituency, source)
                SELECT pt.person_id, pt.loksabha, p.name, last.party_id, NULL, 'last-term-fallback'
                FROM (SELECT DISTINCT t.person_id, d.loksabha
                      FROM turns t JOIN debates d ON d.id = t.debate_id
                      WHERE t.person_id IS NOT NULL) pt
                JOIN persons p ON p.id = pt.person_id
                JOIN speakers last ON last.person_id = pt.person_id AND last.source = 'sansad-last-term'
                WHERE NOT EXISTS (SELECT 1 FROM speakers s
                                  WHERE s.person_id = pt.person_id AND s.lok_sabha_term = pt.loksabha)
                """
            )
        ).rowcount
        print(f"removed old rows      : {removed}", flush=True)
        print(f"rows to insert        : {len(params)}", flush=True)
        print(f"inserted              : {inserted}", flush=True)
        print(f"last-term fallbacks   : {fallback}", flush=True)
        if inserted != len(params):
            print("some rows collided with a sansad-last-term row and were not inserted", flush=True)


def main() -> None:
    load(read_rows())


if __name__ == "__main__":
    sys.exit(main())
