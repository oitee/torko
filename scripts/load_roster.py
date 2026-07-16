"""
Load the full Lok Sabha member roster from the sansad.in API into our DB.

    persons  -- one row per real human (our own id; mpCode kept as sansad_id)
    speakers -- one row per (person, Lok Sabha term)

Design decisions (see internal_docs/006_SCHEMA.md and 001_SANSAD_API_FINDINGS.md):

* Source is a single call: GET /api_ls/member?size=5427 -> everyone, one row
  per person, with `lastLoksabha`, `partySname`, `constName`.
* We attach each speaker to that person's OWN last term (`lastLoksabha`). The
  member snapshot's party/constituency is the *latest-term* value, so pinning it
  to the person's last LS makes the snapshot correct rather than fictional.
  Per-term affiliation for earlier terms is a future feature.
* The member directory spans ALL Lok Sabhas (1st-18th). Our debate corpus starts
  at LS13, and a person who never served in LS13-18 can never appear in it, so we
  skip anyone whose last term is < 13 (their `lastLoksabha` has no lok_sabhas row
  anyway). Skipped count is reported.
* Idempotent: safe to re-run. persons upsert on sansad_id; speakers on
  (lok_sabha_term, person_id).

Run from the repo root (with the DB up and db/init/*.sql applied):

    python -m scripts.load_roster
"""
from __future__ import annotations

import sys

import requests
from sqlalchemy import text

from db import get_engine

MEMBER_API = "https://sansad.in/api_ls/member"
COVERED_TERMS = {13, 14, 15, 16, 17, 18}


def fetch_all_members() -> list[dict]:
    """Fetch the entire member directory in one call."""
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

            # Upsert the person; RETURNING gives us the id whether we inserted or
            # collided (DO UPDATE is a no-op touch just to force a row back).
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
                        (person_id, lok_sabha_term, name, party, constituency)
                    VALUES
                        (:person_id, :lok_sabha_term, :name, :party, :constituency)
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
