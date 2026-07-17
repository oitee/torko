"""
Populate the `turns` table from every debate already in `debates.raw_html`.

Read-only against `debates` -- writes only to `turns`. Idempotent: turns are
upserted on (debate_id, seq), so a crashed run is resumed by just re-running
the whole script.

Turns only, not stitched speeches -- speechification is a later todo.

Run: source .venv/bin/activate && python3 scripts/populate_turns.py [--limit N]
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from db import get_engine
from debate_fetch import split_by_speaker
from debate_fetch_legacy import looks_legacy, split_by_speaker_legacy
from db_roster import load_db_roster


def person_id_lookup(engine) -> dict[str, int]:
    """mpCode (string) -> persons.id."""
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT sansad_id, id FROM persons WHERE sansad_id IS NOT NULL")
        ).fetchall()
    return {str(r.sansad_id): r.id for r in rows}


def role_id_lookup(engine) -> dict[str, tuple[int, str]]:
    """roleCode -> (speaker_roles.id, kind)."""
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT id, code, kind FROM speaker_roles")).fetchall()
    return {r.code: (r.id, r.kind) for r in rows}


def parse_debate(raw_html: str, mp_list_raw: list[dict], db_roster: list[dict]) -> list[dict]:
    """Mirrors scripts/build_dashboard_fixtures.py's routing exactly: both
    readers already run annotate_speakers/reuse_anchors internally, so segments
    come back fully resolved -- do not re-run either pass over them."""
    if looks_legacy(raw_html):
        return split_by_speaker_legacy(raw_html, mp_list_raw, db_roster)
    return split_by_speaker(raw_html, mp_list_raw, db_roster)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None, help="cap debates processed, for a dry run")
    args = ap.parse_args()

    engine = get_engine()
    roster_cache: dict[int, list] = {}
    persons = person_id_lookup(engine)
    roles = role_id_lookup(engine)

    with engine.connect() as conn:
        query = "SELECT id, loksabha, raw_html, mp_list_raw FROM debates ORDER BY id"
        if args.limit:
            query += f" LIMIT {int(args.limit)}"
        debate_rows = conn.execute(text(query)).fetchall()

    print(f"{len(debate_rows)} debates to process")

    total_turns = 0
    for n, row in enumerate(debate_rows, 1):
        if row.loksabha not in roster_cache:
            roster_cache[row.loksabha] = load_db_roster(row.loksabha)
        db_roster = roster_cache[row.loksabha]

        segments = parse_debate(row.raw_html, row.mp_list_raw, db_roster)

        values = []
        for seq, seg in enumerate(segments):
            role_id, role_kind = (None, None)
            if seg.get("roleCode") in roles:
                role_id, role_kind = roles[seg["roleCode"]]

            mp_code = seg.get("mpCode")
            values.append({
                "debate_id": row.id,
                "seq": seq,
                "speaker_label": seg.get("speakerLabel"),
                "mp_code": mp_code,
                "person_id": persons.get(mp_code) if mp_code else None,
                "role_id": role_id,
                "role_kind": role_kind,
                "name_source": seg.get("nameSource"),
                "text": seg["text"],
                "word_count": len(seg["text"].split()),
                "char_count": len(seg["text"]),
            })

        if values:
            with engine.begin() as conn:
                conn.execute(
                    text("DELETE FROM turns WHERE debate_id = :debate_id"),
                    {"debate_id": row.id},
                )
                conn.execute(
                    text(
                        """
                        INSERT INTO turns
                            (debate_id, seq, speaker_label, mp_code, person_id,
                             role_id, role_kind, name_source, text, word_count, char_count)
                        VALUES
                            (:debate_id, :seq, :speaker_label, :mp_code, :person_id,
                             :role_id, :role_kind, :name_source, :text, :word_count, :char_count)
                        """
                    ),
                    values,
                )
            total_turns += len(values)

        if n % 500 == 0:
            print(f"  {n}/{len(debate_rows)} debates, {total_turns} turns so far")

    print(f"done: {len(debate_rows)} debates, {total_turns} turns")


if __name__ == "__main__":
    main()
