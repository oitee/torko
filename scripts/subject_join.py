"""Join small subject groups that are one specific subject (step 2 after scripts/subject_groups.py).

A unit is a group of 2 or more names from subject_groups.py, or a single name with 2 or more speeches.
The centre of a unit is the normalised mean of its name vectors.
Candidate pairs: for each unit, its 5 nearest units by centre, when the cosine distance is below --max-dist.

Subcommands:
  candidates  Build the units and the candidate pairs. Write results/join_candidates_v1.tsv and a cache file.
  jobs        Write task files for an LLM judge (approach C) to a folder outside the repository.
  approach-a  Join the units of every pair with a centre distance below t, for several t. Score each t
              with the labelled name pairs of tags/subject_groups/eval/.
  ingest      Read the LLM answers (approach C), validate them, and write results/join_llm_v1.tsv.
  export-joins  Write the same answers to data/joins_v1.tsv, keyed by the entity name IDs of each unit, so that a later
              build does not depend on the pair IDs of one candidate run.
  subjects    Join the units of every pair in data/joins_v1.tsv. Write results/subjects_v1.tsv with one row per subject.
  label-jobs  Write task files for an LLM that writes a clean label for each subject with 2 or more names.
  chain-jobs  Write task files for an LLM that judges every pair of units inside a chain of 3 or more units
              that no earlier answer judged directly (the chain guard).
  compare     Score approach A (each limit t) and approach C on the labelled candidate pairs of
              tags/subject_groups/eval/ (join_labels_A.tsv, join_labels_B.tsv). Gold = pairs where both labels agree.
              Each gold pair counts for the candidate pairs of its distance band of 0.02.
It reads the database only. It calls no model and writes nothing to the database.

    source .venv/bin/activate && set -a && source .env && set +a
    python3 scripts/subject_join.py candidates --cache /tmp/units.pkl
"""
from __future__ import annotations

import argparse
import csv
import json
import pickle
import random
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.subject_groups import EXCLUDED_TYPES, find, group_with_guard, knn, load_names, load_vectors
from scripts.subject_groups_eval import BIN, EVAL_DIR, bin_pairs, edges_for, read_gold, score

RESULTS = Path(__file__).resolve().parent.parent / "tags" / "subject_groups" / "results"
JOINS = RESULTS.parent / "data" / "joins_v1.tsv"
D_GROUP, MAX_GROUP = 0.10, 15
N_NEAR = 5
MAX_DIST = 0.18
MAX_JOINED = 40
SHOW_NAMES = 12
JOB_BYTES = 14000
DECISIONS = ("same", "different")


def unit_line(names: list) -> str:
    """names: list of (name, speeches), most speeches first. Show at most SHOW_NAMES names."""
    shown = "; ".join(f"{n} ({s})" for n, s in names[:SHOW_NAMES])
    more = len(names) - SHOW_NAMES
    return shown + (f"; (+{more} more names)" if more > 0 else "")


def join_units(n_units: int, pairs: list, sizes: list, max_joined: int = MAX_JOINED) -> list:
    """pairs: (a, b, dist) to join, nearest first. Union-find over unit indexes. A join that makes a subject
    with more than max_joined names is skipped. Return a list of subjects (lists of unit indexes)."""
    parent = list(range(n_units))
    names = list(sizes)

    def root(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b, _ in sorted(pairs, key=lambda p: p[2]):
        ra, rb = root(a), root(b)
        if ra == rb or names[ra] + names[rb] > max_joined:
            continue
        parent[rb] = ra
        names[ra] += names[rb]
    out = defaultdict(list)
    for i in range(n_units):
        out[root(i)].append(i)
    return list(out.values())


def build(args) -> None:
    import numpy as np
    from sqlalchemy import text
    from db import get_engine
    with get_engine().connect() as conn:
        names = [r for r in load_names(conn) if r[2] not in EXCLUDED_TYPES and r[4]]
        ids = sorted(r[0] for r in names)
        neigh = knn(conn, ids, 15)
        mat = load_vectors(conn, ids)
        sp = dict(conn.execute(text("""SELECT entity_name_id, count(DISTINCT speech_id) FROM speech_items
            WHERE kept AND source IN ('llm', 'dictionary') AND entity_name_id IS NOT NULL GROUP BY 1""")).fetchall())
    info = {r[0]: (r[1], r[2], r[3]) for r in names}
    groups = group_with_guard(ids, edges_for(neigh, 15, True), D_GROUP, MAX_GROUP)
    units = [sorted(g, key=lambda m: (-sp.get(m, 0), info[m][0])) for g in groups
             if len(g) >= 2 or sum(sp.get(m, 0) for m in g) >= 2]
    pos = {m: i for i, m in enumerate(ids)}
    cen = np.stack([mat[[pos[m] for m in u]].mean(0) for u in units])
    cen /= np.linalg.norm(cen, axis=1, keepdims=True)
    pairs = {}
    for s in range(0, len(units), 2000):
        sim = cen[s:s + 2000] @ cen.T
        sim[np.arange(sim.shape[0]), np.arange(s, s + sim.shape[0])] = -2.0
        top = np.argpartition(-sim, N_NEAR, axis=1)[:, :N_NEAR]
        for r in range(sim.shape[0]):
            for j in top[r]:
                d = float(1.0 - sim[r, j])
                if d < args.max_dist:
                    pairs[tuple(sorted((s + r, int(j))))] = d
    with args.cache.open("wb") as f:
        pickle.dump({"ids": ids, "neigh": neigh, "info": info, "sp": sp, "units": units,
                     "pairs": sorted((a, b, d) for (a, b), d in pairs.items())}, f)
    RESULTS.mkdir(parents=True, exist_ok=True)
    with (RESULTS / "join_candidates_v1.tsv").open("w", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["pair_id", "unit_a", "unit_b", "centre_distance", "names_a", "names_b"])
        for n, (a, d) in enumerate(sorted(pairs.items(), key=lambda kv: kv[1]), 1):
            w.writerow([f"P{n:05d}", a[0], a[1], f"{d:.4f}",
                        unit_line([(info[m][0], sp.get(m, 0)) for m in units[a[0]]]),
                        unit_line([(info[m][0], sp.get(m, 0)) for m in units[a[1]]])])
    print(f"units {len(units)}, candidate pairs {len(pairs)} (centre distance < {args.max_dist})")


def jobs(args) -> None:
    rows = list(csv.DictReader((RESULTS / "join_candidates_v1.tsv").open(), delimiter="\t"))
    random.Random(5).shuffle(rows)
    out = args.folder / "jobs"
    out.mkdir(parents=True, exist_ok=True)
    (args.folder / "out").mkdir(exist_ok=True)
    n, buf, ids = 0, [], []

    def flush():
        nonlocal n, buf, ids
        if not ids:
            return
        n += 1
        name = f"j{n:04d}"
        head = (f"PAIRS: {' '.join(ids)}\nWrite one JSON line per pair, in this order, to "
                f"{args.folder / 'out' / (name + '.out.jsonl')}\n\n")
        (out / f"{name}.txt").write_text(head + "".join(buf), encoding="utf-8")
        buf, ids = [], []

    for r in rows:
        block = f"<<<PAIR {r['pair_id']}>>>\nA: {r['names_a']}\nB: {r['names_b']}\n<<<END {r['pair_id']}>>>\n\n"
        if ids and sum(len(b.encode()) for b in buf) + len(block.encode()) > JOB_BYTES:
            flush()
        buf.append(block)
        ids.append(r["pair_id"])
    flush()
    print(f"{n} job files in {out}")


def approach_a(args) -> None:
    data = pickle.load(args.cache.open("rb"))
    units, pairs, neigh = data["units"], data["pairs"], data["neigh"]
    gold4, agree, total = read_gold([EVAL_DIR / "labels_A.tsv", EVAL_DIR / "labels_B.tsv"])
    pop = {i: len(v) for i, v in bin_pairs(neigh).items()}
    n_in = defaultdict(int)
    for *_, dist in gold4:
        n_in[int(dist / BIN)] += 1
    gold = [(a, b, s, pop[int(dist / BIN)] / n_in[int(dist / BIN)]) for a, b, s, dist in gold4]
    sizes = [len(u) for u in units]
    rows = []
    for t100 in [None] + list(range(6, 19)):
        t = None if t100 is None else t100 / 100
        chosen = [] if t is None else [p for p in pairs if p[2] < t]
        subjects = join_units(len(units), chosen, sizes)
        groups = [[m for i in s for m in units[i]] for s in subjects]
        multi = [g for g in groups if len(g) >= 2]
        sc = score(multi, gold)
        rows.append({"t": "none" if t is None else t, "joins": len(chosen), "subjects": len(subjects),
                     "names_in_multi": sum(map(len, multi)), "largest": max(map(len, groups)),
                     **{k: round(v, 3) for k, v in sc.items()}})
    with (RESULTS / "join_approach_a_v1.tsv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter="\t")
        w.writeheader()
        w.writerows(rows)
    for r in rows:
        print(r)


def ingest(args) -> None:
    rows = {r["pair_id"]: r for r in csv.DictReader((RESULTS / "join_candidates_v1.tsv").open(), delimiter="\t")}
    got, bad = {}, []
    for p in sorted((args.folder / "out").glob("j*.out.jsonl")):
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                bad.append((p.name, line[:120]))
                continue
            pid, dec = obj.get("pair"), obj.get("decision")
            if pid in rows and dec in DECISIONS:
                got[pid] = (dec, obj.get("confidence", ""))
            else:
                bad.append((p.name, line[:120]))
    with (RESULTS / "join_llm_v1.tsv").open("w", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["pair_id", "centre_distance", "decision", "confidence"])
        for pid, r in rows.items():
            if pid in got:
                w.writerow([pid, r["centre_distance"], *got[pid]])
    print(f"answers {len(got)} of {len(rows)} pairs, bad lines {len(bad)}")


def weighted_pr(gold: list, predict) -> dict:
    """gold: (pair_id, distance, is_same, weight). predict(pair_id, distance) -> bool. Return precision, recall, joins share."""
    tp = fp = fn = 0.0
    for pid, dist, same, w in gold:
        hit = predict(pid, dist)
        tp += w * (hit and same)
        fp += w * (hit and not same)
        fn += w * (same and not hit)
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    return {"precision": round(p, 3), "recall": round(r, 3)}


def compare(args) -> None:
    ev = EVAL_DIR
    cand = {r["pair_id"]: float(r["centre_distance"]) for r in csv.DictReader((RESULTS / "join_candidates_v1.tsv").open(), delimiter="\t")}
    la = {r["pair_id"]: r["label"] for r in csv.DictReader((ev / "join_labels_A.tsv").open(), delimiter="\t")}
    lb = {r["pair_id"]: r["label"] for r in csv.DictReader((ev / "join_labels_B.tsv").open(), delimiter="\t")}
    agree = [p for p in la if la[p] == lb.get(p)]
    print(f"labelled {len(la)}, agree {len(agree)}, same {sum(la[p] == 'same' for p in agree)}")
    pop = defaultdict(int)
    for d in cand.values():
        pop[int(d / 0.02)] += 1
    n_in = defaultdict(int)
    for p in agree:
        n_in[int(cand[p] / 0.02)] += 1
    gold = [(p, cand[p], la[p] == "same", pop[int(cand[p] / 0.02)] / n_in[int(cand[p] / 0.02)]) for p in agree]
    for b in sorted(n_in):
        g = [x for x in gold if int(x[1] / 0.02) == b]
        print(f"band {b * 0.02:.2f}: gold {len(g)}, same {sum(x[2] for x in g)}, candidates {pop[b]}")
    for t100 in range(6, 19):
        t = t100 / 100
        print(f"A t={t:.2f}", weighted_pr(gold, lambda pid, d: d < t))
    llm_path = RESULTS / "join_llm_v1.tsv"
    if llm_path.exists():
        llm = {r["pair_id"]: r for r in csv.DictReader(llm_path.open(), delimiter="\t")}
        g = [x for x in gold if x[0] in llm]
        print(f"C answers for {len(g)} of {len(gold)} gold pairs")
        print("C same", weighted_pr(g, lambda pid, d: llm[pid]["decision"] == "same"))
        print("C same+high", weighted_pr(g, lambda pid, d: llm[pid]["decision"] == "same" and llm[pid]["confidence"] == "high"))
        for t100 in (12, 14, 16):
            print(f"C same and d<{t100 / 100}", weighted_pr(g, lambda pid, d: llm[pid]["decision"] == "same" and d < t100 / 100))


def write_jobs(folder: Path, blocks: list, item: str, max_bytes: int = JOB_BYTES) -> int:
    """blocks: list of (item_id, text). Write folder/jobs/jNNNN.txt with the ID list on line 1 and the output path on line 2."""
    out = folder / "jobs"
    out.mkdir(parents=True, exist_ok=True)
    (folder / "out").mkdir(exist_ok=True)
    n, buf, ids, size = 0, [], [], 0
    for iid, text in blocks + [(None, None)]:
        block = None if iid is None else f"<<<{item} {iid}>>>\n{text}\n<<<END {iid}>>>\n\n"
        if ids and (iid is None or size + len(block.encode()) > max_bytes):
            n += 1
            name = f"j{n:04d}"
            head = (f"{item}S: {' '.join(ids)}\nWrite one JSON line per {item.lower()}, in this order, to "
                    f"{folder / 'out' / (name + '.out.jsonl')}\n\n")
            (out / f"{name}.txt").write_text(head + "".join(buf), encoding="utf-8")
            buf, ids, size = [], [], 0
        if iid is not None:
            buf.append(block)
            ids.append(iid)
            size += len(block.encode())
    return n


def unit_key(unit) -> str:
    """A stable key for a unit: its entity name IDs, sorted and joined by spaces."""
    return " ".join(str(m) for m in sorted(unit))


def joins_to_pairs(units: list, rows: list) -> tuple[list, int]:
    """rows: dicts with name_ids_a, name_ids_b, centre_distance. Return (pairs of unit indexes, unmatched count).
    A row whose unit no longer exists (for example after a rebuild of the groups) is unmatched and skipped."""
    index = {unit_key(u): i for i, u in enumerate(units)}
    pairs, unmatched = [], 0
    for r in rows:
        a, b = index.get(r["name_ids_a"]), index.get(r["name_ids_b"])
        if a is None or b is None:
            unmatched += 1
        else:
            pairs.append((a, b, float(r["centre_distance"])))
    return pairs, unmatched


def llm_same_pairs(units: list) -> list:
    rows = list(csv.DictReader(JOINS.open(), delimiter="\t"))
    pairs, unmatched = joins_to_pairs(units, rows)
    if unmatched:
        print(f"warning: {unmatched} of {len(rows)} joins point to a unit that no longer exists", file=sys.stderr)
    return pairs


def export_joins(args) -> None:
    units = pickle.load(args.cache.open("rb"))["units"]
    cand = {r["pair_id"]: r for r in csv.DictReader((RESULTS / "join_candidates_v1.tsv").open(), delimiter="\t")}
    JOINS.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with JOINS.open("w", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["name_ids_a", "name_ids_b", "centre_distance", "confidence"])
        for r in csv.DictReader((RESULTS / "join_llm_v1.tsv").open(), delimiter="\t"):
            if r["decision"] != "same":
                continue
            c = cand[r["pair_id"]]
            w.writerow([unit_key(units[int(c["unit_a"])]), unit_key(units[int(c["unit_b"])]), c["centre_distance"], r["confidence"]])
            n += 1
    print(f"{n} joins written to {JOINS}")


def subjects(args) -> None:
    from db import get_engine
    from scripts.subject_groups import choose_parent, load_speeches
    data = pickle.load(args.cache.open("rb"))
    units, info = data["units"], data["info"]
    with get_engine().connect() as conn:
        speeches, debates = defaultdict(set), defaultdict(set)
        for nid, sid, did in load_speeches(conn):
            speeches[nid].add(sid)
            debates[nid].add(did)
    subs = join_units(len(units), llm_same_pairs(units), [len(u) for u in units])
    tag_of = {m: info[m][2] for u in units for m in u}
    rows = []
    for s in subs:
        members = sorted((m for i in s for m in units[i]), key=lambda m: (-len(speeches[m]), info[m][0]))
        parent, share, others = choose_parent(members, tag_of, speeches)
        rows.append({"units": "+".join(str(i) for i in sorted(s)), "n_units": len(s), "n_names": len(members),
                     "n_speeches": len(set().union(*(speeches[m] for m in members))),
                     "n_debates": len(set().union(*(debates[m] for m in members))),
                     "label_auto": info[members[0]][0], "parent_tag": parent or "", "parent_share": round(share, 3),
                     "other_tags": "; ".join(others),
                     "names": " | ".join(f"{info[m][0]} ({len(speeches[m])})" for m in members),
                     "name_ids": " ".join(str(m) for m in members)})
    rows.sort(key=lambda r: (-r["n_speeches"], r["label_auto"]))
    for n, r in enumerate(rows, 1):
        r["subject_id"] = f"S{n:05d}"
    cols = ["subject_id", "label_auto", "n_units", "n_names", "n_speeches", "n_debates", "parent_tag",
            "parent_share", "other_tags", "units", "names", "name_ids"]
    with (RESULTS / "subjects_v1.tsv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, delimiter="\t")
        w.writeheader()
        w.writerows(rows)
    print(f"subjects {len(rows)}, with 2+ names {sum(r['n_names'] >= 2 for r in rows)}, joined {sum(r['n_units'] > 1 for r in rows)}")


def label_jobs(args) -> None:
    rows = [r for r in csv.DictReader((RESULTS / "subjects_v1.tsv").open(), delimiter="\t") if int(r["n_names"]) >= 2]
    random.Random(9).shuffle(rows)
    blocks = []
    for r in rows:
        names = r["names"].split(" | ")
        shown = "; ".join(names[:15]) + (f"; (+{len(names) - 15} more names)" if len(names) > 15 else "")
        blocks.append((r["subject_id"], f"Names: {shown}"))
    print(f"{write_jobs(args.folder, blocks, 'SUBJECT', 12000)} job files for {len(blocks)} subjects")


def chain_jobs(args) -> None:
    data = pickle.load(args.cache.open("rb"))
    units, info, sp = data["units"], data["info"], data["sp"]
    judged = {(int(r["unit_a"]), int(r["unit_b"])) for r in csv.DictReader((RESULTS / "join_candidates_v1.tsv").open(), delimiter="\t")}
    subs = join_units(len(units), llm_same_pairs(units), [len(u) for u in units])
    rows, blocks = [], []
    for s in subs:
        if len(s) < 3:
            continue
        s = sorted(s)
        for x in range(len(s)):
            for y in range(x + 1, len(s)):
                a, b = s[x], s[y]
                if (a, b) in judged:
                    continue
                pid = f"C{len(rows) + 1:05d}"
                rows.append((pid, a, b))
                blocks.append((pid, "A: " + unit_line([(info[m][0], sp.get(m, 0)) for m in units[a]]) +
                               "\nB: " + unit_line([(info[m][0], sp.get(m, 0)) for m in units[b]])))
    with (RESULTS / "chain_pairs_v1.tsv").open("w", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["pair_id", "unit_a", "unit_b"])
        w.writerows(rows)
    rng = random.Random(13)
    rng.shuffle(blocks)
    print(f"{write_jobs(args.folder, blocks, 'PAIR', 12000)} job files for {len(blocks)} chain pairs")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["candidates", "jobs", "approach-a", "ingest", "export-joins", "compare", "subjects", "label-jobs", "chain-jobs"])
    ap.add_argument("--cache", type=Path)
    ap.add_argument("--folder", type=Path)
    ap.add_argument("--max-dist", type=float, default=MAX_DIST)
    args = ap.parse_args()
    {"candidates": build, "jobs": jobs, "approach-a": approach_a, "ingest": ingest, "export-joins": export_joins, "compare": compare,
     "subjects": subjects, "label-jobs": label_jobs, "chain-jobs": chain_jobs}[args.command](args)


if __name__ == "__main__":
    main()
