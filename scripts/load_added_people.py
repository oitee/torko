#!/usr/bin/env python3
"""Add the people who speak but are on no Lok Sabha member list, and link people to the Rajya Sabha list.

Reads data/people_added.tsv, data/people_added_seats.tsv, and data/rajya_sabha_links.tsv. A new person has
no sansad_id, so the parser roster and the code lookup of scripts/populate_turns.py never see this person.
A repeat run changes nothing. Run it before scripts/load_label_aliases.py.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sqlalchemy import text  # noqa: E402

from db import get_engine  # noqa: E402

DATA = ROOT / "data"


def read(name: str) -> list[dict]:
    with open(DATA / name, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def person_id(conn, row: dict) -> int:
    """A person with a Rajya Sabha number is keyed by it, and any other added person by the exact name."""
    number = int(row["rajya_sabha_id"]) if row["rajya_sabha_id"] else None
    if number:
        found = conn.execute(text("SELECT id FROM persons WHERE rajya_sabha_id = :n"), {"n": number}).scalar()
    else:
        found = conn.execute(text("SELECT id FROM persons WHERE name = :n AND sansad_id IS NULL AND rajya_sabha_id IS NULL"),
                             {"n": row["name"]}).scalar()
    if found:
        conn.execute(text("UPDATE persons SET name = :name WHERE id = :id"), {"name": row["name"], "id": found})
        return found
    return conn.execute(text("INSERT INTO persons (name, rajya_sabha_id) VALUES (:name, :n) RETURNING id"),
                        {"name": row["name"], "n": number}).scalar()


def main() -> None:
    with get_engine().begin() as conn:
        for link in read("rajya_sabha_links.tsv"):
            conn.execute(text("UPDATE persons SET rajya_sabha_id = :n WHERE id = :id"),
                         {"n": int(link["rajya_sabha_id"]), "id": int(link["person_id"])})
        ids = {row["name"]: person_id(conn, row) for row in read("people_added.tsv")}
        for seat in read("people_added_seats.tsv"):
            conn.execute(text("""
                INSERT INTO speakers (person_id, lok_sabha_term, name, constituency, state_id, source, match_method,
                                      party_id, effective_from)
                SELECT :pid, ls.number, :name, :seat, st.id, 'added-person', NULL, pa.id, ls.start_date
                FROM lok_sabhas ls
                LEFT JOIN states st ON st.name = :state LEFT JOIN parties pa ON pa.code = :party
                WHERE ls.number = :term
                ON CONFLICT (lok_sabha_term, person_id, effective_from) DO NOTHING"""),
                {"pid": ids[seat["name"]], "name": seat["name"], "seat": seat["seat"], "state": seat["state"],
                 "party": seat["party"], "term": int(seat["term"])})
        # Run this part again after the turns are linked: each person with turns in a term needs a row.
        rows = conn.execute(text("""
            INSERT INTO speakers (person_id, lok_sabha_term, name, source, effective_from)
            SELECT DISTINCT t.person_id, d.loksabha, coalesce(latest.name, p.name), 'not-a-member', ls.start_date
            FROM turns t JOIN debates d ON d.id = t.debate_id JOIN persons p ON p.id = t.person_id
            JOIN lok_sabhas ls ON ls.number = d.loksabha
            LEFT JOIN LATERAL (SELECT name FROM speakers WHERE person_id = p.id ORDER BY lok_sabha_term DESC LIMIT 1) latest ON true
            WHERE NOT EXISTS (SELECT 1 FROM speakers s WHERE s.person_id = t.person_id AND s.lok_sabha_term = d.loksabha)
            ON CONFLICT (lok_sabha_term, person_id, effective_from) DO NOTHING""")).rowcount
    print(f"{len(ids)} added people. {rows} new term rows.", flush=True)


if __name__ == "__main__":
    main()
