from __future__ import annotations

import csv
import sys
from pathlib import Path

from sqlalchemy import text

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from db import get_engine  # noqa: E402

TSV = ROOT / "data" / "turn_reassignments.tsv"


def read_rows() -> list[dict]:
    with open(TSV, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def apply(rows: list[dict]) -> None:
    with get_engine().begin() as conn:
        for r in rows:
            term, src, dst = int(r["term"]), int(r["from_mpsno"]), int(r["to_mpsno"])
            src_id = conn.execute(text("SELECT id FROM persons WHERE sansad_id = :c"), {"c": src}).scalar()
            if src_id is None:
                raise SystemExit(f"no person with code {src}")
            # Members whose last term is before the 13th have no persons row yet.
            dst_id = conn.execute(
                text(
                    """
                    INSERT INTO persons (name, sansad_id) VALUES (:name, :code)
                    ON CONFLICT (sansad_id) DO UPDATE SET name = persons.name
                    RETURNING id
                    """
                ),
                {"name": r["to_name"], "code": dst},
            ).scalar_one()
            turns = conn.execute(
                text(
                    """
                    UPDATE turns t SET person_id = :dst, name_source = 'manual-reassign'
                    FROM debates d
                    WHERE d.id = t.debate_id AND d.loksabha = :term AND t.person_id = :src
                    """
                ),
                {"dst": dst_id, "src": src_id, "term": term},
            ).rowcount
            speeches = conn.execute(
                text(
                    """
                    UPDATE speeches s SET person_id = :dst
                    FROM debates d
                    WHERE d.id = s.debate_id AND d.loksabha = :term AND s.person_id = :src
                    """
                ),
                {"dst": dst_id, "src": src_id, "term": term},
            ).rowcount
            print(f"term {term}: {src} -> {dst}: {turns} turns, {speeches} speeches", flush=True)


def main() -> None:
    apply(read_rows())


if __name__ == "__main__":
    sys.exit(main())
