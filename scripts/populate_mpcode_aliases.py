"""Build the mpcode_aliases table from the corpus, then backfill turns.

Reads turns + persons, decides which orphan mpCodes alias to a single person
(alias_build.build_aliases -- pure, tested offline), writes mpcode_aliases, and
sets person_id / name_source='mpcode-alias' on the turns that safely resolve.

Never-guess, restated as code:
  * only codes whose printed name labels unanimously fold to ONE roster person
    get a row (conflicts dropped by build_aliases);
  * the synthetic minister block (>=10000) is excluded (build_aliases);
  * backfill touches only turns with NO person and NO role, and skips any turn
    whose stored label is itself presiding/crowd (belt-and-suspenders: such a
    turn must stay a role/unresolved, never inherit the code's person).

Idempotent: DELETEs and rebuilds mpcode_aliases each run; the backfill is a
plain UPDATE guarded by person_id IS NULL so re-running never overwrites a
directly-resolved turn.

Run: source .venv/bin/activate && python3 scripts/populate_mpcode_aliases.py [--dry-run]
"""
import argparse
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from alias_build import build_aliases
from db import get_engine
from debate_fetch import _folded_key, is_crowd_label, is_presiding_label


def unique_person_by_key(conn) -> dict[str, int]:
    """Folded roster-name key -> person id, colliding keys dropped (never-guess)."""
    key2pids: dict[str, set] = defaultdict(set)
    for pid, name in conn.execute(text("SELECT id, name FROM persons")):
        k = _folded_key(name)
        if k:
            key2pids[k].add(pid)
    return {k: next(iter(v)) for k, v in key2pids.items() if len(v) == 1}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="report, write nothing")
    args = ap.parse_args()

    engine = get_engine()
    with engine.connect() as conn:
        upk = unique_person_by_key(conn)
        label_rows = conn.execute(
            text(
                """
                SELECT mp_code, speaker_label, count(*) AS n
                FROM turns
                WHERE person_id IS NULL AND role_id IS NULL
                  AND mp_code IS NOT NULL AND speaker_label <> ''
                GROUP BY mp_code, speaker_label
                """
            )
        ).fetchall()

    aliases, dropped = build_aliases(
        ((r.mp_code, r.speaker_label, r.n) for r in label_rows),
        upk,
        _folded_key,
        is_presiding_label,
        is_crowd_label,
    )
    print(f"aliasable codes: {len(aliases)}   dropped (conflict): {len(dropped)}")
    for code, info in dropped.items():
        print(f"  DROP {code}: {info['persons']}")

    if args.dry_run:
        print("dry run -- nothing written")
        for code, info in sorted(aliases.items(), key=lambda x: -x[1]["evidence_turns"]):
            print(f"  {code:>7} -> person {info['person_id']} ({info['evidence_turns']} name-turns)")
        return

    backfilled = 0
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM mpcode_aliases"))
        for code, info in aliases.items():
            conn.execute(
                text(
                    """INSERT INTO mpcode_aliases (mp_code, person_id, evidence_turns)
                       VALUES (:c, :p, :e)"""
                ),
                {"c": code, "p": info["person_id"], "e": info["evidence_turns"]},
            )
            # Backfill: only unresolved, non-role turns of this code, and skip any
            # turn whose own label is presiding/crowd (checked in Python -- SQL
            # cannot call is_presiding_label).
            cand = conn.execute(
                text(
                    """SELECT id, speaker_label FROM turns
                       WHERE mp_code = :c AND person_id IS NULL AND role_id IS NULL"""
                ),
                {"c": code},
            ).fetchall()
            ids = [
                r.id
                for r in cand
                if not is_presiding_label(r.speaker_label or "")
                and not is_crowd_label(r.speaker_label or "")
            ]
            if ids:
                conn.execute(
                    text(
                        """UPDATE turns SET person_id = :p, name_source = 'mpcode-alias'
                           WHERE id = ANY(:ids)"""
                    ),
                    {"p": info["person_id"], "ids": ids},
                )
                backfilled += len(ids)

    print(f"wrote {len(aliases)} alias rows; backfilled {backfilled} turns")


if __name__ == "__main__":
    main()
