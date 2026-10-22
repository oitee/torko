"""List the subjects with no tag that are large enough for a tag of their own (candidates for stages 6 and 7).

A subject comes from scripts/subject_join.py (results/subjects_v1.tsv). A candidate has no parent tag,
at least --min-speeches distinct speeches, and at least --min-debates distinct debates. The parent tag comes from the
table subjects (chosen by scripts/subject_parents.py), not from the vote parent in the file.
For each candidate, the script finds the 5 nearest tags of the tag list: the cosine distance between the centre
of the subject (the mean of its name vectors) and the tag vector. A near tag can mean that stage 5 missed a link.
It reads the database only. It calls no model and writes nothing to the database.

    source .venv/bin/activate && set -a && source .env && set +a
    python3 scripts/new_tag_candidates.py
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from scripts.subject_groups import load_vectors
from tag_embed import ARMS

RESULTS = Path(__file__).resolve().parent.parent / "tags" / "subject_groups" / "results"
TAG_TASK = ARMS["B"][0]
N_TAGS = 5
SHOW_NAMES = 10


def subject_key(row: dict) -> str:
    return " ".join(str(n) for n in sorted(int(m) for m in row["name_ids"].split()))


def with_db_parents(rows: list[dict], parents: dict[str, str | None]) -> tuple[list[dict], int]:
    """parents: subject key -> parent tag name, or None. Returns the rows with parent_tag from the database, and the
    count of rows whose subject is not in the database. Such a row keeps no parent, so it stays a candidate."""
    out, missing = [], 0
    for r in rows:
        key = subject_key(r)
        missing += key not in parents
        out.append({**r, "parent_tag": parents.get(key) or ""})
    return out, missing


def is_candidate(row: dict, min_speeches: int, min_debates: int) -> bool:
    return not row["parent_tag"] and int(row["n_speeches"]) >= min_speeches and int(row["n_debates"]) >= min_debates


def main() -> None:
    import numpy as np
    from db import get_engine
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--min-speeches", type=int, default=10)
    ap.add_argument("--min-debates", type=int, default=3)
    args = ap.parse_args()
    rows = list(csv.DictReader((RESULTS / "subjects_v1.tsv").open(), delimiter="\t"))
    with get_engine().connect() as conn:
        parents = dict(conn.execute(text(
            "SELECT s.subject_key, t.tag FROM subjects s LEFT JOIN tags t ON t.id = s.parent_tag_id")).all())
        rows, missing = with_db_parents(rows, parents)
        if missing:
            print(f"warning: {missing} subjects of the file are not in the table subjects. Run scripts/load_subjects.py.")
        rows = [r for r in rows if is_candidate(r, args.min_speeches, args.min_debates)]
        name_ids = sorted({int(m) for r in rows for m in r["name_ids"].split()})
        mat = load_vectors(conn, name_ids)
        tags = conn.execute(text("""SELECT t.tag, t.type, e.embedding::text FROM tags t
            JOIN tag_embeddings e ON e.tag_id = t.id AND e.task_type = :t WHERE t.status NOT IN ('rejected', 'merged')"""),
                            {"t": TAG_TASK}).fetchall()
    pos = {m: i for i, m in enumerate(name_ids)}
    tag_mat = np.array([np.array(v[1:-1].split(","), dtype=np.float32) for _, _, v in tags])
    tag_mat /= np.linalg.norm(tag_mat, axis=1, keepdims=True)
    out = []
    for r in rows:
        c = mat[[pos[int(m)] for m in r["name_ids"].split()]].mean(0)
        c /= np.linalg.norm(c)
        dist = 1.0 - tag_mat @ c
        near = np.argsort(dist)[:N_TAGS]
        names = r["names"].split(" | ")
        out.append({"subject_id": r["subject_id"], "label_auto": r["label_auto"], "n_names": r["n_names"],
                    "n_speeches": r["n_speeches"], "n_debates": r["n_debates"],
                    "names": " | ".join(names[:SHOW_NAMES]) + (f" | (+{len(names) - SHOW_NAMES} more)" if len(names) > SHOW_NAMES else ""),
                    "nearest_tags": " | ".join(f"{tags[i][0]} ({tags[i][1]}, {dist[i]:.2f})" for i in near)})
    cols = ["subject_id", "label_auto", "n_names", "n_speeches", "n_debates", "names", "nearest_tags"]
    with (RESULTS / "new_tag_candidates_v1.tsv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, delimiter="\t")
        w.writeheader()
        w.writerows(out)
    print(f"candidates {len(out)} (no tag, >= {args.min_speeches} speeches, >= {args.min_debates} debates)")


if __name__ == "__main__":
    main()
