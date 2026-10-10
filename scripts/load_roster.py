from __future__ import annotations

import sys

import requests
from sqlalchemy import text

from db import get_engine

MEMBER_API = "https://sansad.in/api_ls/member"
# The member directory spans terms 1 to 18. The corpus starts at term 13, so members whose last term is earlier are skipped.
COVERED_TERMS = {13, 14, 15, 16, 17, 18}


def fetch_all_members() -> list[dict]:
    resp = requests.get(MEMBER_API, params={"size": 5427, "page": 1}, timeout=60)
    resp.raise_for_status()
    return resp.json().get("membersDtoList", [])


def load(members: list[dict]) -> None:
    engine = get_engine()

    inserted_persons = 0
    inserted_speakers = 0
    skipped = 0

    with engine.begin() as conn:
        for m in members:
            last_ls = m.get("lastLoksabha")
            if last_ls not in COVERED_TERMS:
                skipped += 1
                continue

            name = (m.get("mpFirstLastName") or "").strip()
            sansad_id = m.get("mpsno")
            if not name or sansad_id is None:
                skipped += 1
                continue

            # DO UPDATE forces RETURNING to give the id on a conflict. xmax = 0 marks a new row.
            person_id = conn.execute(
                text(
                    """
                    INSERT INTO persons (name, sansad_id)
                    VALUES (:name, :sansad_id)
                    ON CONFLICT (sansad_id)
                    DO UPDATE SET name = EXCLUDED.name
                    RETURNING id, (xmax = 0) AS was_inserted
                    """
                ),
                {"name": name, "sansad_id": sansad_id},
            ).one()
            if person_id.was_inserted:
                inserted_persons += 1

            result = conn.execute(
                text(
                    """
                    INSERT INTO speakers
                        (person_id, lok_sabha_term, name, party, constituency, source)
                    VALUES
                        (:person_id, :lok_sabha_term, :name, :party, :constituency, 'sansad-last-term')
                    ON CONFLICT (lok_sabha_term, person_id) DO NOTHING
                    """
                ),
                {
                    "person_id": person_id.id,
                    "lok_sabha_term": last_ls,
                    "name": name,
                    "party": (m.get("partySname") or "").strip() or None,
                    "constituency": (m.get("constName") or "").strip() or None,
                },
            )
            inserted_speakers += result.rowcount

    print(f"members fetched : {len(members)}")
    print(f"persons  added  : {inserted_persons}")
    print(f"speakers added  : {inserted_speakers}")
    print(f"skipped (pre-13 / incomplete): {skipped}")


def main() -> None:
    members = fetch_all_members()
    if not members:
        print("No members returned from the API; aborting.", file=sys.stderr)
        sys.exit(1)
    load(members)


if __name__ == "__main__":
    main()
