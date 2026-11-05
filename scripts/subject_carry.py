"""Keep the stored subject answers of a group that only gained close names (the sort step after new speeches).

The stored answers of the subject steps are keyed by a set of entity name IDs:
- data/joins_v1.tsv and data/cannot_links_v1.tsv: a pair of units (a unit is a group of names, see subject_join.py).
- data/subject_labels_v1.tsv and data/new_tag_reviews_v1.tsv: a subject (one or more joined units).
- the table subject_parents: a subject key.
When new speeches add one name to a group, the set of names changes, and the stored answers stop matching.
This script finds the new units that only gained close names, and copies their answers to the new keys.

Rule for a unit. A new unit keeps the answers of an old unit only when all of these are true:
1. The new unit holds every name of exactly one old unit.
2. Each added name was in no old unit.
3. Each added name has a cosine distance to the centre of the old unit of MAX_DIST or less.
   The centre is the normalised mean of the vectors of the old names.
4. The added names are MAX_GROWTH (50%) or less of the old names.
Every other new unit is changed, and steps 9 to 12 treat it as new.

Rule for a subject. A new subject key replaces an old one when each unit of the old subject is unchanged or kept by the
unit rule, and the added names are MAX_GROWTH or less of the old names. The new key assumes that the join step adds
no other unit to the subject. If it does, the copied answers match nothing and do no harm.

Copies are added. No stored answer is deleted.

    source .venv/bin/activate && set -a && source .env && set +a
    python3 scripts/subject_carry.py snapshot --out <old.pkl>            # before the new speeches are loaded
    python3 scripts/subject_join.py candidates --cache <new.pkl>         # after stage 5 (step 7)
    python3 scripts/subject_carry.py sort --old <old.pkl> --new <new.pkl>           # report only
    python3 scripts/subject_carry.py sort --old <old.pkl> --new <new.pkl> --apply   # copy the answers
"""
from __future__ import annotations

import argparse
import csv
import pickle
import random
import shutil
import sys
from collections import Counter
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.subject_join import CANNOT, JOINS, LABELS, RESULTS, unit_key

REVIEWS = RESULTS.parent / "data" / "new_tag_reviews_v1.tsv"
MAX_DIST = 0.10
MAX_GROWTH = 0.5
SAME, KEPT, FAR, GREW, CHANGED = "same", "kept", "far", "grew", "changed"


# ---------- pure functions ----------

def growth_ok(n_old: int, n_added: int, max_growth: float = MAX_GROWTH) -> bool:
    return n_added <= max_growth * n_old


def classify_units(old_units: list, new_units: list, dist, max_dist: float = MAX_DIST,
                   max_growth: float = MAX_GROWTH) -> list:
    """old_units, new_units: lists of name ID lists. dist(old index, name ID) -> cosine distance to the old centre.
    Return one dict per new unit: status, old (old unit index or None), added (list of (name ID, distance))."""
    owner = {m: i for i, u in enumerate(old_units) for m in u}
    old_keys = {unit_key(u): i for i, u in enumerate(old_units)}
    out = []
    for u in new_units:
        if unit_key(u) in old_keys:
            out.append({"status": SAME, "old": old_keys[unit_key(u)], "added": []})
            continue
        names = set(u)
        olds = {owner[m] for m in u if m in owner}
        full = [i for i in olds if set(old_units[i]) <= names]
        if len(olds) != 1 or len(full) != 1:
            out.append({"status": CHANGED, "old": None, "added": []})
            continue
        i = full[0]
        added = [(m, dist(i, m)) for m in sorted(names - set(old_units[i]))]
        if not growth_ok(len(old_units[i]), len(added), max_growth):
            status = GREW
        elif any(d > max_dist for _, d in added):
            status = FAR
        else:
            status = KEPT
        out.append({"status": status, "old": i, "added": added})
    return out


def unit_map(old_units: list, new_units: list, results: list) -> dict:
    """Old unit key -> new unit key, for the units with the status same or kept."""
    return {unit_key(old_units[r["old"]]): unit_key(u) for u, r in zip(new_units, results) if r["status"] in (SAME, KEPT)}


def carry_subjects(old_subjects: dict, old_units: list, umap: dict, max_growth: float = MAX_GROWTH) -> tuple[dict, Counter]:
    """old_subjects: old subject key -> list of name IDs. Return (old subject key -> new subject key, counts by reason).
    An old subject is the union of its old units. Each of them must be in umap."""
    by_name = {m: unit_key(u) for u in old_units for m in u}
    out, why = {}, Counter()
    for key, names in old_subjects.items():
        ukeys = {by_name.get(m) for m in names}
        if None in ukeys:
            why["a name is in no old unit"] += 1
            continue
        if any(k not in umap for k in ukeys):
            why["a unit changed"] += 1
            continue
        new_names = sorted({int(m) for k in ukeys for m in umap[k].split()})
        if not growth_ok(len(names), len(new_names) - len(names), max_growth):
            why["grew too much"] += 1
            continue
        new_key = " ".join(map(str, new_names))
        why["same" if new_key == key else "kept"] += 1
        out[key] = new_key
    return out, why


def copy_pair_rows(rows: list, umap: dict) -> list:
    """rows: dicts with name_ids_a and name_ids_b. Return a copy under the new keys of each row whose two units are both
    in umap with a changed key on at least one side, and whose new pair has no row yet."""
    have = {frozenset((r["name_ids_a"], r["name_ids_b"])) for r in rows}
    out = []
    for r in rows:
        a, b = umap.get(r["name_ids_a"]), umap.get(r["name_ids_b"])
        if a is None or b is None or (a == r["name_ids_a"] and b == r["name_ids_b"]):
            continue
        if frozenset((a, b)) in have:
            continue
        have.add(frozenset((a, b)))
        out.append(dict(r, name_ids_a=a, name_ids_b=b))
    return out


def copy_keyed_rows(rows: list, smap: dict, col: str = "name_ids") -> list:
    """rows: dicts keyed by a subject key in col. Return a copy under the new key of each row whose key changed,
    when the new key has no row yet."""
    have = {r[col] for r in rows}
    out = []
    for r in rows:
        new = smap.get(r[col])
        if new is None or new == r[col] or new in have:
            continue
        have.add(new)
        out.append(dict(r, **{col: new}))
    return out


# ---------- files and database ----------

def read_tsv(path: Path) -> tuple[list, list]:
    with path.open() as f:
        reader = csv.DictReader(f, delimiter="\t")
        return list(reader.fieldnames), list(reader)


def append_tsv(path: Path, cols: list, rows: list, backup_tag: str) -> None:
    shutil.copy2(path, path.with_name(f"{path.stem}.before_{backup_tag}{path.suffix}"))
    with path.open("a", newline="") as f:
        csv.DictWriter(f, fieldnames=cols, delimiter="\t").writerows(rows)


def snapshot(args) -> None:
    from sqlalchemy import text
    from db import get_engine
    from scripts.subject_join import build_units
    with get_engine().connect() as conn:
        b = build_units(conn)
        subs = {}
        for key, nid in conn.execute(text("""SELECT s.subject_key, n.entity_name_id FROM subjects s
                JOIN subject_names n ON n.subject_id = s.id""")):
            subs.setdefault(key, []).append(nid)
    pos = {m: i for i, m in enumerate(b["ids"])}
    import numpy as np
    cen = np.stack([b["mat"][[pos[m] for m in u]].mean(0) for u in b["units"]])
    cen /= np.linalg.norm(cen, axis=1, keepdims=True)
    with args.out.open("wb") as f:
        pickle.dump({"units": b["units"], "centres": cen, "subjects": subs, "info": b["info"]}, f)
    keys = {unit_key(u) for u in b["units"]}
    rows = read_tsv(JOINS)[1] + read_tsv(CANNOT)[1]
    hit = sum(r["name_ids_a"] in keys and r["name_ids_b"] in keys for r in rows)
    print(f"old units {len(b['units'])}, old subjects {len(subs)}; stored pair rows that match these units: "
          f"{hit} of {len(rows)}")


def sort(args) -> None:
    import numpy as np
    from sqlalchemy import text
    from db import get_engine
    from scripts.subject_groups import load_vectors
    old = pickle.load(args.old.open("rb"))
    new = pickle.load(args.new.open("rb"))
    old_units, new_units, cen = old["units"], new["units"], old["centres"]
    owner = {m for u in old_units for m in u}
    extra = sorted({m for u in new_units for m in u if m not in owner})
    with get_engine().connect() as conn:
        vec = dict(zip(extra, load_vectors(conn, extra))) if extra else {}

    def dist(i, m):
        return float(1.0 - cen[i] @ vec[m]) if m in vec else 2.0

    results = classify_units(old_units, new_units, dist, args.max_dist, args.max_growth)
    umap = unit_map(old_units, new_units, results)
    smap, why = carry_subjects(old["subjects"], old_units, umap, args.max_growth)
    counts = Counter(r["status"] for r in results)
    print(f"new units {len(new_units)}: " + ", ".join(f"{k} {counts[k]}" for k in (SAME, KEPT, FAR, GREW, CHANGED)))
    print(f"old subjects {len(old['subjects'])}: " + ", ".join(f"{k} {v}" for k, v in why.most_common()))
    info = {**old["info"], **new["info"]}
    tag = args.tag or date.today().isoformat()
    report = RESULTS / f"carry_units_{tag}.tsv"
    with report.open("w", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["status", "old_names", "added_names", "new_key"])
        for u, r in zip(new_units, results):
            if r["status"] in (KEPT, FAR, GREW):
                w.writerow([r["status"], " | ".join(info[m][0] for m in old_units[r["old"]]),
                            " | ".join(f"{info[m][0]} ({d:.3f})" for m, d in r["added"]), unit_key(u)])
    print(f"report: {report}")
    rng = random.Random(5)
    for status in (FAR, GREW, KEPT):
        rows = [(u, r) for u, r in zip(new_units, results) if r["status"] == status]
        print(f"\n--- sample of {status} ({len(rows)})")
        for u, r in rng.sample(rows, min(args.sample, len(rows))):
            print("  old: " + "; ".join(info[m][0] for m in old_units[r["old"]])[:160])
            print("  add: " + "; ".join(f"{info[m][0]} ({d:.3f})" for m, d in r["added"])[:160])
    jcols, jrows = read_tsv(JOINS)
    ccols, crows = read_tsv(CANNOT)
    lcols, lrows = read_tsv(LABELS)
    rcols, rrows = read_tsv(REVIEWS)
    new_j, new_c = copy_pair_rows(jrows, umap), copy_pair_rows(crows, umap)
    new_l, new_r = copy_keyed_rows(lrows, smap), copy_keyed_rows(rrows, smap)
    moved = {k: v for k, v in smap.items() if k != v}
    print(f"\ncopies: joins {len(new_j)}, cannot-links {len(new_c)}, labels {len(new_l)}, tag reviews {len(new_r)}, "
          f"parent rows up to {len(moved)}")
    if not args.apply:
        print("report only. Add --apply to copy the answers.")
        return
    append_tsv(JOINS, jcols, new_j, tag)
    append_tsv(CANNOT, ccols, new_c, tag)
    append_tsv(LABELS, lcols, new_l, tag)
    append_tsv(REVIEWS, rcols, new_r, tag)
    with get_engine().begin() as conn:
        n = 0
        for a, b in moved.items():
            n += conn.execute(text("""INSERT INTO subject_parents (subject_key, parent_tag_id, parent_p, options, raw,
                warnings, decided_by, tag_set_version, decided_at)
                SELECT :new, parent_tag_id, parent_p, options, raw, warnings, decided_by, tag_set_version, decided_at
                FROM subject_parents WHERE subject_key = :old ON CONFLICT (subject_key) DO NOTHING"""),
                {"new": b, "old": a}).rowcount
    print(f"applied. parent rows copied {n}. Backups end in .before_{tag}.tsv")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["snapshot", "sort"])
    ap.add_argument("--out", type=Path)
    ap.add_argument("--old", type=Path)
    ap.add_argument("--new", type=Path)
    ap.add_argument("--max-dist", type=float, default=MAX_DIST)
    ap.add_argument("--max-growth", type=float, default=MAX_GROWTH)
    ap.add_argument("--sample", type=int, default=15)
    ap.add_argument("--tag", help="suffix of the report and the backups (default: today)")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    {"snapshot": snapshot, "sort": sort}[args.command](args)


if __name__ == "__main__":
    main()
