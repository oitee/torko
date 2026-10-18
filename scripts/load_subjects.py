"""Load the final subjects into the tables subjects and subject_names.

It reads tags/subject_groups/results/subjects_final_v1.tsv (written by scripts/subject_join.py final)
and the name IDs of each subject from tags/subject_groups/results/subjects_v1.tsv.
It replaces every row of both tables in one transaction, so a run after a rebuild leaves no old subject.
It calls no model.

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


def subject_rows(final_rows: list, name_ids: dict, tag_ids: dict) -> tuple[list, list]:
    """final_rows: rows of subjects_final_v1.tsv. name_ids: subject_id -> list of entity name IDs.
    tag_ids: tag name -> tag ID. Return (subjects, problems). A parent tag that is not in tag_ids is a problem."""
    out, problems = [], []
    for r in final_rows:
        ids = sorted(int(m) for m in name_ids[r["subject_id"]])
        parent = r["parent_tag"] or None
        if parent and parent not in tag_ids:
            problems.append(f"{r['subject_id']}: unknown parent tag {parent!r}")
            parent = None
        out.append({"key": " ".join(map(str, ids)), "label": r["label"], "source": r["label_source"],
                    "parent": tag_ids.get(parent) if parent else None, "n_names": int(r["n_names"]),
                    "n_speeches": int(r["n_speeches"]), "n_debates": int(r["n_debates"]), "names": ids})
    return out, problems


def main() -> None:
    from db import get_engine
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    final_rows = list(csv.DictReader((RESULTS / "subjects_final_v1.tsv").open(), delimiter="\t"))
    name_ids = {r["subject_id"]: r["name_ids"].split() for r in csv.DictReader((RESULTS / "subjects_v1.tsv").open(), delimiter="\t")}
    engine = get_engine()
    with engine.connect() as conn:
        tag_ids = dict(conn.execute(text("SELECT tag, id FROM tags")).fetchall())
    rows, problems = subject_rows(final_rows, name_ids, tag_ids)
    for p in problems[:10]:
        print("problem:", p)
    print(f"subjects {len(rows)}, names {sum(len(r['names']) for r in rows)}, with a parent tag {sum(r['parent'] is not None for r in rows)}, problems {len(problems)}")
    if args.dry_run:
        return
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM subject_names"))
        conn.execute(text("DELETE FROM subjects"))
        for r in rows:
            sid = conn.execute(text("""INSERT INTO subjects (subject_key, label, label_source, parent_tag_id, n_names, n_speeches, n_debates)
                VALUES (:key, :label, :source, :parent, :n_names, :n_speeches, :n_debates) RETURNING id"""), r).scalar()
            conn.execute(text("INSERT INTO subject_names (entity_name_id, subject_id) VALUES (:n, :s)"),
                         [{"n": n, "s": sid} for n in r["names"]])
    print("loaded")


if __name__ == "__main__":
    main()
