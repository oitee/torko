import argparse
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from alias_build import is_synthetic_code
from db import get_engine
from debate_fetch import _folded_key, is_crowd_label, is_presiding_label
from label_attribution import build_unique_index, resolve_label_to_person


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="report, write nothing")
    args = ap.parse_args()

    engine = get_engine()
    with engine.connect() as conn:
        index = build_unique_index(
            {pid: name for pid, name in conn.execute(text("SELECT id, name FROM persons"))},
            _folded_key,
        )
        rows = conn.execute(
            text(
                """SELECT id, mp_code, speaker_label FROM turns
                   WHERE person_id IS NULL AND role_id IS NULL
                     AND mp_code ~ '^[0-9]+$' AND speaker_label <> ''"""
            )
        ).fetchall()

    # Synthetic minister codes (>= 10000) are reused across different people.
    # Resolve each turn by the name in its own label, never by code.
    by_person: dict[int, list[int]] = defaultdict(list)
    for r in rows:
        if not is_synthetic_code(r.mp_code):
            continue
        pid = resolve_label_to_person(
            r.speaker_label, index, _folded_key, is_presiding_label, is_crowd_label
        )
        if pid is not None:
            by_person[pid].append(r.id)

    total = sum(len(ids) for ids in by_person.values())
    print(f"ministerial turns to attribute: {total} across {len(by_person)} persons")
    if args.dry_run:
        with engine.connect() as conn:
            for pid, ids in sorted(by_person.items(), key=lambda x: -len(x[1]))[:20]:
                name = conn.execute(text("SELECT name FROM persons WHERE id=:i"), {"i": pid}).scalar()
                print(f"  {len(ids):>4}  person {pid} {name!r}")
        print("dry run -- nothing written")
        return

    with engine.begin() as conn:
        for pid, ids in by_person.items():
            conn.execute(
                text(
                    """UPDATE turns SET person_id = :p, name_source = 'minister-name'
                       WHERE id = ANY(:ids) AND person_id IS NULL AND role_id IS NULL"""
                ),
                {"p": pid, "ids": ids},
            )
    print(f"attributed {total} ministerial turns (name_source='minister-name')")


if __name__ == "__main__":
    main()
