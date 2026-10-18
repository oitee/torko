"""Choose the settings of the subject groups (scripts/subject_groups.py) with labelled pairs of names.

Step 1, --prepare: find the 25 nearest names of each name once, save them to a cache file,
and write a stratified sample of name pairs for a blind manual label (same specific subject or not).
Step 2, --sweep: read the label files, keep the pairs where all labels agree, and score each setting.
A setting is: k (neighbours per name), mutual or one-way edges, the distance limit d, and the largest group size.
For each setting, precision = labelled-same pairs among the gold pairs that the setting puts in one group,
recall = gold same pairs that the setting puts in one group. F0.5 weights precision higher, because a wrong join is worse than a missed one.
It reads the database only. It calls no model and writes nothing to the database.

    source .venv/bin/activate && set -a && source .env && set +a
    python3 scripts/subject_groups_eval.py --prepare
    python3 scripts/subject_groups_eval.py --sweep
"""
from __future__ import annotations

import argparse
import csv
import pickle
import random
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.subject_groups import EXCLUDED_TYPES, find, group_with_guard, knn, load_names

EVAL_DIR = Path(__file__).resolve().parent.parent / "tags" / "subject_groups" / "eval"
K_MAX = 25
BIN = 0.02
N_BINS = 13
PER_BIN = 35
SEED = 7
LABELS = ("same", "different")


def bin_pairs(neigh: dict, bin_width: float = BIN, n_bins: int = N_BINS) -> dict:
    """Return {bin index: [(a, b, dist)]} for distinct pairs a < b in the neighbour lists. The distance of a pair is the smaller one seen."""
    best = {}
    for a, lst in neigh.items():
        for b, dist in lst:
            key = (min(a, b), max(a, b))
            if key not in best or dist < best[key]:
                best[key] = dist
    bins = defaultdict(list)
    for (a, b), dist in best.items():
        i = int(dist / bin_width)
        if i < n_bins:
            bins[i].append((a, b, dist))
    return bins


def edges_for(neigh: dict, k: int, mutual: bool) -> list:
    """Edges (a, b, dist) with a < b from the first k neighbours. mutual: both directions must be present. The edge distance is the larger one."""
    seen = {}
    for a, lst in neigh.items():
        for b, dist in lst[:k]:
            seen[(a, b)] = dist
    out = {}
    for (a, b), dist in seen.items():
        back = seen.get((b, a))
        if mutual and back is None:
            continue
        key = (min(a, b), max(a, b))
        d = max(dist, back) if back is not None else dist
        out[key] = min(d, out.get(key, d))
    return [(a, b, d) for (a, b), d in out.items()]


def score(groups: list, gold: list) -> dict:
    """gold: list of (a, b, is_same) or (a, b, is_same, weight). Return weighted tp, fp, fn, precision, recall, f05.
    The weight corrects the stratified sample: a pair counts for the pairs of its distance band in the population."""
    where = {m: i for i, g in enumerate(groups) for m in g}
    tp = fp = fn = 0.0
    for row in gold:
        a, b, same = row[:3]
        w = row[3] if len(row) > 3 else 1.0
        together = a in where and b in where and where[a] == where[b]
        if together and same:
            tp += w
        elif together:
            fp += w
        elif same:
            fn += w
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f = 1.25 * p * r / (0.25 * p + r) if p + r else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": p, "recall": r, "f05": f}


def prepare(cache: Path) -> None:
    from db import get_engine
    with get_engine().connect() as conn:
        names = [r for r in load_names(conn) if r[2] not in EXCLUDED_TYPES and r[4]]
        ids = sorted(r[0] for r in names)
        neigh = knn(conn, ids, K_MAX)
    info = {r[0]: (r[1], r[2], r[3]) for r in names}
    with cache.open("wb") as f:
        pickle.dump({"ids": ids, "neigh": neigh, "info": info}, f)
    bins = bin_pairs(neigh)
    rng = random.Random(SEED)
    sample = []
    for i in range(N_BINS):
        sample += rng.sample(bins[i], min(PER_BIN, len(bins[i])))
    rng.shuffle(sample)
    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    with (EVAL_DIR / "pairs_v1.tsv").open("w", newline="") as f, (EVAL_DIR / "pairs_v1_key.tsv").open("w", newline="") as g:
        w, wk = csv.writer(f, delimiter="\t"), csv.writer(g, delimiter="\t")
        w.writerow(["pair_id", "name_a", "type_a", "name_b", "type_b"])
        wk.writerow(["pair_id", "id_a", "id_b", "distance"])
        for n, (a, b, dist) in enumerate(sample, 1):
            w.writerow([n, info[a][0], info[a][1], info[b][0], info[b][1]])
            wk.writerow([n, a, b, f"{dist:.4f}"])
    print(f"cache {cache}, pairs {len(sample)}, bins {[len(bins[i]) for i in range(N_BINS)]}")


def read_gold(label_files: list) -> tuple[list, int, int]:
    key = {r["pair_id"]: r for r in csv.DictReader((EVAL_DIR / "pairs_v1_key.tsv").open(), delimiter="\t")}
    marks = defaultdict(list)
    for p in label_files:
        for r in csv.DictReader(p.open(), delimiter="\t"):
            marks[r["pair_id"]].append(r["label"].strip())
    gold, agree, total = [], 0, 0
    for pid, ls in marks.items():
        total += 1
        if len(ls) == len(label_files) and len(set(ls)) == 1 and ls[0] in LABELS:
            agree += 1
            k = key[pid]
            gold.append((int(k["id_a"]), int(k["id_b"]), ls[0] == "same", float(k["distance"])))
    return gold, agree, total


def sweep(cache: Path, label_files: list, out: Path) -> None:
    data = pickle.load(cache.open("rb"))
    ids, neigh = data["ids"], data["neigh"]
    gold4, agree, total = read_gold(label_files)
    pop = {i: len(v) for i, v in bin_pairs(neigh).items()}
    n_in = defaultdict(int)
    for *_, dist in gold4:
        n_in[int(dist / BIN)] += 1
    gold = [(a, b, s, pop[int(dist / BIN)] / n_in[int(dist / BIN)]) for a, b, s, dist in gold4]
    for i in sorted(n_in):
        same_i = [g for g in gold4 if int(g[3] / BIN) == i]
        print(f"band {i * BIN:.2f}-{(i + 1) * BIN:.2f}: gold {len(same_i)}, same {sum(g[2] for g in same_i)}")
    print(f"pairs {total}, all labels agree {agree}, gold same {sum(1 for g in gold if g[2])}")
    rows = []
    for k in (10, 15, 25):
        for mutual in (True, False):
            edges = edges_for(neigh, k, mutual)
            for d100 in range(6, 23):
                d = d100 / 100
                for max_size in (15, 25, 40, 100000):
                    groups = group_with_guard(ids, edges, d, max_size)
                    multi = [g for g in groups if len(g) >= 2]
                    s = score(multi, gold)
                    rows.append({"k": k, "mutual": mutual, "d": d, "max_size": max_size,
                                 "groups": len(multi), "names_grouped": sum(map(len, multi)),
                                 "largest": max(map(len, multi)) if multi else 0, **s})
    rows.sort(key=lambda r: -r["f05"])
    with out.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter="\t")
        w.writeheader()
        for r in rows:
            w.writerow({c: (f"{v:.3f}" if isinstance(v, float) else v) for c, v in r.items()})
    for r in rows[:15]:
        print({c: (round(v, 3) if isinstance(v, float) else v) for c, v in r.items()})


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--prepare", action="store_true")
    ap.add_argument("--sweep", action="store_true")
    ap.add_argument("--cache", type=Path, required=True)
    ap.add_argument("--labels", type=Path, nargs="*", default=[])
    args = ap.parse_args()
    if args.prepare:
        prepare(args.cache)
    if args.sweep:
        sweep(args.cache, args.labels, EVAL_DIR / "sweep_v1.tsv")


if __name__ == "__main__":
    main()
