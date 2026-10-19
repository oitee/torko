"""Load the final subjects into the tables subjects and subject_names.

It reads tags/subject_groups/results/subjects_final_v1.tsv (written by scripts/subject_join.py final)
and the name IDs of each subject from tags/subject_groups/results/subjects_v1.tsv.
It replaces every row of both tables in one transaction, so a run after a rebuild leaves no old subject.
The parent tag of each subject comes from the table subject_parents (scripts/subject_parents.py), by subject key.
A subject that the decision model did not decide yet has no parent. It calls no model.

    source .venv/bin/activate && set -a && source .env && set +a
    python3 scripts/load_subjects.py --dry-run
    python3 scripts/load_subjects.py
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

RESULTS = Path(__file__).resolve().parent.parent / "tags" / "subject_groups" / "results"


def subject_rows(final_rows: list, name_ids: dict) -> list:
    """final_rows: rows of subjects_final_v1.tsv. name_ids: subject_id -> list of entity name IDs."""
    out = []
    for r in final_rows:
        ids = sorted(int(m) for m in name_ids[r["subject_id"]])
        out.append({"key": " ".join(map(str, ids)), "label": r["label"], "source": r["label_source"],
                    "n_names": int(r["n_names"]), "n_speeches": int(r["n_speeches"]),
                    "n_debates": int(r["n_debates"]), "names": ids})
    return out


SYNC_PARENTS = """UPDATE subjects s SET parent_tag_id = p.parent_tag_id
    FROM subject_parents p WHERE p.subject_key = s.subject_key AND s.parent_tag_id IS DISTINCT FROM p.parent_tag_id"""


def main() -> None:
    from db import get_engine
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    final_rows = list(csv.DictReader((RESULTS / "subjects_final_v1.tsv").open(), delimiter="\t"))
    name_ids = {r["subject_id"]: r["name_ids"].split() for r in csv.DictReader((RESULTS / "subjects_v1.tsv").open(), delimiter="\t")}
    engine = get_engine()
    rows = subject_rows(final_rows, name_ids)
    with engine.connect() as conn:
        decided = {k for (k,) in conn.execute(text("SELECT subject_key FROM subject_parents"))}
    print(f"subjects {len(rows)}, names {sum(len(r['names']) for r in rows)}, "
          f"with a parent decision {sum(r['key'] in decided for r in rows)}")
    if args.dry_run:
        return
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM subject_names"))
        conn.execute(text("DELETE FROM subjects"))
        for r in rows:
            sid = conn.execute(text("""INSERT INTO subjects (subject_key, label, label_source, parent_tag_id, n_names, n_speeches, n_debates)
                VALUES (:key, :label, :source, NULL, :n_names, :n_speeches, :n_debates) RETURNING id"""), r).scalar()
            conn.execute(text("INSERT INTO subject_names (entity_name_id, subject_id) VALUES (:n, :s)"),
                         [{"n": n, "s": sid} for n in r["names"]])
        conn.execute(text(SYNC_PARENTS))
    print("loaded")


if __name__ == "__main__":
    main()
