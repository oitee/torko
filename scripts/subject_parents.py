"""Choose the parent tag of each subject with the decision model.

A subject is a group of entity names that mean one specific subject (table subjects). Its parent is the tag that
means the same thing as the subject, or the tag that the subject is one part of. A tag that is only one part of the
subject is not a parent. For example, the subject "Sugarcane farmers' arrears" has the parent Arrears, and the
subject "Religious tourism development" does not have the parent PRASAD Scheme, which is one scheme of it.

The options for one subject are the tags of its linked names (at most --max-linked, most speeches first), the
--near tags nearest to the centre of its name vectors, and NONE. The subject gets a parent only when the top option
is a tag with probability of at least --link-p. A subject is decided again when its decided_by value changed, or
when it has no parent and the tag set grew. --force decides every subject again.

Each answer goes into the table subject_parents by subject key, and the parent goes into subjects.parent_tag_id.
It needs TYPESAFE_API_KEY and numpy.

    source .venv/bin/activate && set -a && source .env && set +a
    python3 scripts/subject_parents.py --dry-run
    python3 scripts/subject_parents.py --labels "Pradhan Mantri Shram Yogi Maandhan" "Wage arrears" --review
    python3 scripts/subject_parents.py
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from decision_model import MODEL, DecisionError, api_key, choice_probabilities, choice_q, decide, sum_is_off
from scripts.extract_entities import free_stem
from scripts.link_entities import LINK_P, NONE, decide_link, examples_for, option_text
from scripts.load_subjects import SYNC_PARENTS
from tag_embed import ARMS, MODEL as EMBED_MODEL

QUESTIONS_VERSION = "p1"
TAG_TASK = ARMS["B"][0]
MAX_LINKED = 10
N_NEAR = 3
SHOW_NAMES = 10
N_EXAMPLES = 3
NONE_TEXT = "no option covers the whole subject, or each option is only one part of the subject"
RESULTS = Path(__file__).resolve().parent.parent / "tags" / "subject_groups" / "results"


def decided_by(model: str) -> str:
    return f"{model} {QUESTIONS_VERSION}"


def needs_decision(row: dict | None, version: str, tag_set: int, force: bool = False) -> bool:
    if force or row is None or row["decided_by"] != version:
        return True
    return row["parent_tag_id"] is None and row["tag_set_version"] < tag_set


def build_candidates(linked: Counter, near: list[tuple[int, float]], max_linked: int = MAX_LINKED,
                     n_near: int = N_NEAR) -> list[dict]:
    """linked: tag ID -> speeches of the linked names of the subject. near: (tag ID, distance), nearest first.
    The linked tags come first, then the nearest tags that are not linked tags."""
    out = [{"tag_id": t, "source": "linked", "speeches": n, "distance": None}
           for t, n in sorted(linked.items(), key=lambda kv: (-kv[1], kv[0]))[:max_linked]]
    seen = {c["tag_id"] for c in out}
    dist = dict(near)
    for c in out:
        c["distance"] = dist.get(c["tag_id"])
    added = 0
    for t, d in near:
        if added == n_near:
            break
        if t not in seen:
            seen.add(t)
            out.append({"tag_id": t, "source": "near", "speeches": 0, "distance": d})
            added += 1
    return out


def parent_question(label: str, options: dict[str, str]) -> dict:
    return choice_q(f"Which option covers the subject «{label}» in these speeches? An option covers the subject "
                    f"when it means the same thing as the subject, or when the subject is one part of the option. "
                    f"An option that is only one part of the subject does not cover it.",
                    {**options, NONE: NONE_TEXT})


def parent_state(label: str, names: list[dict], n_speeches: int, examples: list[dict]) -> str:
    lines = [f"Subject: {label}", f"It appears in {n_speeches} speeches in the Lok Sabha, under these names:"]
    lines += [f"- {n['name']} ({n['n_speeches']} speeches)" for n in names[:SHOW_NAMES]]
    if len(names) > SHOW_NAMES:
        lines.append(f"- and {len(names) - SHOW_NAMES} other names")
    if examples:
        lines.append("Examples:")
        for i, ex in enumerate(examples, 1):
            lines.append(f"{i}. Words of the speech: \"{ex['mention']}\"")
            lines.append(f"   Summary of the speech: {ex['summary']}")
    return "\n".join(lines)


def pick_examples(names: list[dict], by_name: dict[int, list[dict]], n: int = N_EXAMPLES) -> list[dict]:
    """One example from each name, most speeches first, then more from the same names, without a repeated speech."""
    out, seen = [], set()
    for round_ in range(n):
        for nm in names:
            exs = by_name.get(nm["id"], [])
            if round_ < len(exs) and exs[round_]["speech_id"] not in seen:
                seen.add(exs[round_]["speech_id"])
                out.append(exs[round_])
                if len(out) == n:
                    return out
    return out


def load(conn) -> tuple[list[dict], dict[int, dict], int]:
    subjects = {r.id: {"id": r.id, "key": r.subject_key, "label": r.label, "n_speeches": r.n_speeches, "names": []}
                for r in conn.execute(text("SELECT id, subject_key, label, n_speeches FROM subjects"))}
    for r in conn.execute(text("""
        SELECT sn.subject_id, e.id, e.name, e.n_speeches, e.tag_id, e.embedding_query IS NOT NULL AS has_vec
        FROM subject_names sn JOIN entity_names e ON e.id = sn.entity_name_id
        ORDER BY e.n_speeches DESC, e.id""")):
        subjects[r.subject_id]["names"].append({"id": r.id, "name": r.name, "n_speeches": r.n_speeches,
                                                "tag_id": r.tag_id, "has_vec": r.has_vec})
    tags = {r.id: {"id": r.id, "tag": r.tag, "type": r.type, "description": r.description}
            for r in conn.execute(text("SELECT id, tag, type, description FROM tags "
                                       "WHERE status NOT IN ('rejected', 'merged')"))}
    version = conn.execute(text("SELECT coalesce(max(id), 0) FROM tags")).scalar()
    return list(subjects.values()), tags, version


def nearest_tags(conn, subjects: list[dict], tags: dict[int, dict], k: int) -> dict[int, list[tuple[int, float]]]:
    """Subject ID -> the k + MAX_LINKED nearest tags to the centre of its name vectors, by cosine distance."""
    import numpy as np
    from scripts.subject_groups import load_vectors
    ids = sorted({n["id"] for s in subjects for n in s["names"] if n["has_vec"]})
    if not ids:
        return {}
    mat = load_vectors(conn, ids)
    pos = {nid: i for i, nid in enumerate(ids)}
    rows = conn.execute(text("SELECT tag_id, embedding::text FROM tag_embeddings WHERE model = :m AND task_type = :t"),
                        {"m": EMBED_MODEL, "t": TAG_TASK}).all()
    rows = [r for r in rows if r.tag_id in tags]
    tag_ids = [r.tag_id for r in rows]
    tmat = np.array([np.array(r.embedding[1:-1].split(","), dtype=np.float32) for r in rows])
    tmat /= np.linalg.norm(tmat, axis=1, keepdims=True)
    out = {}
    for s in subjects:
        rows_ = [pos[n["id"]] for n in s["names"] if n["has_vec"]]
        if not rows_:
            continue
        c = mat[rows_].mean(0)
        c /= np.linalg.norm(c)
        dist = 1.0 - tmat @ c
        top = np.argsort(dist)[:k + MAX_LINKED]
        out[s["id"]] = [(tag_ids[j], float(dist[j])) for j in top]
    return out


def ask(state: str, label: str, options: dict[str, str], key: str, model: str) -> tuple[dict, dict, list[str]]:
    data = decide(state, {"parent": parent_question(label, options)}, key, model)
    probs = choice_probabilities(data["answers"]["parent"], [*options, NONE])
    warnings = []
    if sum_is_off(list(probs.values())):
        warnings.append(f"option probabilities sum to {sum(probs.values()):.3f}")
    return probs, data, warnings


def write_review(rows: list[dict]) -> Path:
    RESULTS.mkdir(parents=True, exist_ok=True)
    stem = free_stem(RESULTS, f"parents_{QUESTIONS_VERSION}_{date.today().isoformat()}")
    path = RESULTS / f"{stem}.tsv"
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["subject_key", "label", "n_names", "n_speeches", "vote_parent", "parent", "p", "options", "review"])
        for r in sorted(rows, key=lambda r: -r["n_speeches"]):
            w.writerow([r["key"], r["label"], r["n_names"], r["n_speeches"], r["vote_parent"] or "", r["parent"] or NONE,
                        f"{r['p']:.2f}", r["options"], ""])
    return path


def main() -> None:
    from db import get_engine
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default=MODEL)
    ap.add_argument("--link-p", type=float, default=LINK_P)
    ap.add_argument("--near", type=int, default=N_NEAR)
    ap.add_argument("--max-linked", type=int, default=MAX_LINKED)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--limit", type=int, help="decide at most this many subjects (most speeches first)")
    ap.add_argument("--labels", nargs="+", help="decide only the subjects with these labels")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry-run", action="store_true", help="print the counts and a token estimate, call no model")
    ap.add_argument("--review", action="store_true", help="also write a review file of the decided subjects")
    args = ap.parse_args()
    version = decided_by(args.model)
    engine = get_engine()
    with engine.connect() as conn:
        subjects, tags, tag_set = load(conn)
        done = {r.subject_key: dict(r._mapping) for r in conn.execute(text(
            "SELECT subject_key, parent_tag_id, decided_by, tag_set_version FROM subject_parents"))}
        todo = [s for s in subjects if needs_decision(done.get(s["key"]), version, tag_set, args.force)]
        if args.labels:
            todo = [s for s in todo if s["label"] in set(args.labels)]
        todo.sort(key=lambda s: (-s["n_speeches"], s["id"]))
        if args.limit:
            todo = todo[:args.limit]
        near = nearest_tags(conn, todo, tags, args.near)
        vote = dict(conn.execute(text("SELECT subject_key, parent_tag_id FROM subjects")).all())
        jobs, skipped = [], 0
        for s in todo:
            linked = Counter()
            for n in s["names"]:
                if n["tag_id"] in tags:
                    linked[n["tag_id"]] += n["n_speeches"]
            cands = build_candidates(linked, near.get(s["id"], []), args.max_linked, args.near)
            if not cands:
                skipped += 1
                continue
            jobs.append((s, cands))
        examples = examples_for(conn, [n["id"] for s, _ in jobs for n in s["names"][:SHOW_NAMES]]) if jobs else {}
    states = {s["id"]: parent_state(s["label"], s["names"], s["n_speeches"], pick_examples(s["names"], examples))
              for s, _ in jobs}
    print(f"{len(subjects)} subjects, {len(done)} decided before. To decide with {version}: {len(jobs)} "
          f"({skipped} have no option). Tag set version {tag_set}.", flush=True)
    if args.dry_run:
        chars = sum(len(states[s["id"]]) + sum(len(option_text(tags[c["tag_id"]])) + 40 for c in cands) + 400
                    for s, cands in jobs)
        print(f"dry run: about {chars // 4} input tokens (4 characters per token). Nothing sent, nothing written.")
        return
    key = api_key()
    counts, review = Counter(), []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {}
        for s, cands in jobs:
            options = {tags[c["tag_id"]]["tag"]: option_text(tags[c["tag_id"]]) for c in cands}
            futures[pool.submit(ask, states[s["id"]], s["label"], options, key, args.model)] = (s, cands)
        for fut in as_completed(futures):
            s, cands = futures[fut]
            try:
                probs, data, warnings = fut.result()
            except DecisionError as exc:
                counts["failed"] += 1
                print(f"  {s['label']!r}: failed, nothing written ({exc!s:.200})", flush=True)
                continue
            status, tag, p = decide_link(probs, args.link_p)
            stored = [{**c, "tag": tags[c["tag_id"]]["tag"], "p": probs[tags[c["tag_id"]]["tag"]]} for c in cands]
            stored.append({"tag_id": None, "tag": NONE, "source": "none", "speeches": 0, "distance": None,
                           "p": probs[NONE]})
            tid = next(c["tag_id"] for c in cands if tags[c["tag_id"]]["tag"] == tag) if tag else None
            with engine.begin() as conn:
                conn.execute(text("""
                    INSERT INTO subject_parents (subject_key, parent_tag_id, parent_p, options, raw, warnings,
                                                 decided_by, tag_set_version, decided_at)
                    VALUES (:k, :t, :p, CAST(:o AS jsonb), CAST(:raw AS jsonb), :w, :by, :tsv, now())
                    ON CONFLICT (subject_key) DO UPDATE SET parent_tag_id = EXCLUDED.parent_tag_id,
                        parent_p = EXCLUDED.parent_p, options = EXCLUDED.options, raw = EXCLUDED.raw,
                        warnings = EXCLUDED.warnings, decided_by = EXCLUDED.decided_by,
                        tag_set_version = EXCLUDED.tag_set_version, decided_at = now()
                """), {"k": s["key"], "t": tid, "p": p, "o": json.dumps(stored, ensure_ascii=False),
                       "raw": json.dumps(data, ensure_ascii=False), "w": warnings, "by": version, "tsv": tag_set})
            counts["parent" if tag else "none"] += 1
            print(f"  {s['label'][:50]:50} -> {tag or NONE} ({p:.2f})", flush=True)
            ranked = sorted(stored, key=lambda c: -c["p"])[:4]
            review.append({"key": s["key"], "label": s["label"], "n_names": len(s["names"]),
                           "n_speeches": s["n_speeches"], "parent": tag, "p": p,
                           "vote_parent": tags.get(vote.get(s["key"]), {}).get("tag"),
                           "options": " | ".join(f"{c['tag']} {c['p']:.2f} ({c['source']})" for c in ranked)})
    with engine.begin() as conn:
        synced = conn.execute(text(SYNC_PARENTS)).rowcount
    print(f"decided {counts['parent'] + counts['none']} subjects: parent {counts['parent']}, none {counts['none']}, "
          f"failed {counts['failed']}. subjects.parent_tag_id changed for {synced} subjects.", flush=True)
    if args.review and review:
        print(f"review file: {write_review(review)}")


if __name__ == "__main__":
    main()
