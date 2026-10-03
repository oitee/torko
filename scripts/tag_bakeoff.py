from __future__ import annotations

import csv
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from db import get_engine
from tag_embed import ARMS, MODEL, embed_texts, to_pgvector

FOLDER = Path(__file__).resolve().parent.parent / "tags" / "embedding_v1"
PAIRS_FILE = FOLDER / "data" / "test_pairs_v1.tsv"
OUT_FILE = FOLDER / "results" / "bakeoff_v1.tsv"
TOP_N = 10


def read_pairs(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE))
    for r in rows:
        r["acceptable"] = [t.strip() for t in r["acceptable_tags"].split("|")]
    return rows


def best_rank(ranked: list[str], acceptable: list[str]) -> int | None:
    """Returns None when no tag is acceptable."""
    wanted = {t for t in acceptable if t != "NONE"}
    if not wanted:
        return None
    for i, tag in enumerate(ranked, 1):
        if tag in wanted:
            return i
    raise ValueError(f"no acceptable tag is in the table: {sorted(wanted)}")


def rate(ranks: list[int], limit: int) -> str:
    if not ranks:
        return "-"
    hit = sum(1 for r in ranks if r <= limit)
    return f"{hit}/{len(ranks)} ({100 * hit / len(ranks):.0f}%)"


def main() -> None:
    pairs = read_pairs(PAIRS_FILE)
    engine = get_engine()
    with engine.connect() as conn:
        known = set(conn.execute(text("SELECT tag FROM tags")).scalars())
        for arm, (tag_task, _) in ARMS.items():
            n = conn.execute(text("SELECT count(*) FROM tag_embeddings WHERE model = :m AND task_type = :t"),
                             {"m": MODEL, "t": tag_task}).scalar()
            if n == 0:
                raise SystemExit(f"arm {arm}: no tag vectors for {tag_task}. Run scripts/embed_tags.py first.")
    missing = [(p["entity_text"], t) for p in pairs for t in p["acceptable"] if t != "NONE" and t not in known]
    if missing:
        raise SystemExit(f"test pairs name tags that are not in the table: {missing}")

    results: dict[str, list[dict]] = {}
    for arm, (tag_task, entity_task) in ARMS.items():
        print(f"arm {arm}: entities with {entity_task}, tags with {tag_task}", flush=True)
        vectors = embed_texts([p["entity_text"] for p in pairs], entity_task)
        rows = []
        with engine.connect() as conn:
            for p, v in zip(pairs, vectors):
                ranked = conn.execute(text("""
                    SELECT t.tag, e.embedding <=> CAST(:v AS vector) AS distance
                    FROM tag_embeddings e JOIN tags t ON t.id = e.tag_id
                    WHERE e.model = :m AND e.task_type = :t
                    ORDER BY distance
                """), {"v": to_pgvector(v), "m": MODEL, "t": tag_task}).all()
                names = [r.tag for r in ranked]
                rank = best_rank(names, p["acceptable"])
                rows.append({"rank": rank, "top3": " | ".join(names[:3]),
                             "nearest": ranked[0].distance,
                             "hit_distance": ranked[rank - 1].distance if rank else None})
        results[arm] = rows

    with OUT_FILE.open("w", encoding="utf-8") as f:
        f.write("\t".join(["entity_text", "acceptable_tags", "kind", "rank_A", "rank_B",
                           "distance_A", "distance_B", "top3_A", "top3_B"]) + "\n")
        for i, p in enumerate(pairs):
            a, b = results["A"][i], results["B"][i]
            def dist(r):
                return f"{(r['hit_distance'] if r['rank'] else r['nearest']):.4f}"
            f.write("\t".join([p["entity_text"], p["acceptable_tags"], p["kind"],
                               str(a["rank"] or "-"), str(b["rank"] or "-"), dist(a), dist(b),
                               a["top3"], b["top3"]]) + "\n")

    print(f"\n{len(pairs)} pairs. Rates are counted over the pairs that have an acceptable tag (NONE-only pairs left out).")
    for arm in ARMS:
        ranks = [r["rank"] for r in results[arm] if r["rank"]]
        print(f"arm {arm}: top-1 {rate(ranks, 1)}, top-{TOP_N} {rate(ranks, TOP_N)}")
    print("\nBy kind (top-10, A then B):")
    by_kind: dict[str, dict[str, list[int]]] = defaultdict(lambda: defaultdict(list))
    for arm in ARMS:
        for p, r in zip(pairs, results[arm]):
            if r["rank"]:
                by_kind[p["kind"]][arm].append(r["rank"])
    for kind in sorted(by_kind):
        print(f"  {kind:12} A {rate(by_kind[kind]['A'], TOP_N):14} B {rate(by_kind[kind]['B'], TOP_N)}")
    print("\nNONE-only pairs, distance to the nearest tag (A, B):")
    for p, a, b in zip(pairs, results["A"], results["B"]):
        if a["rank"] is None:
            print(f"  {p['entity_text']:30} {a['nearest']:.4f}  {b['nearest']:.4f}  ({a['top3'].split(' | ')[0]})")
    for arm in ARMS:
        hits = [r["hit_distance"] for r in results[arm] if r["rank"] and r["rank"] <= TOP_N]
        if hits:
            print(f"arm {arm}: distance of a correct match in the top {TOP_N}: min {min(hits):.4f}, max {max(hits):.4f}")
    print(f"\nwritten: {OUT_FILE}")


if __name__ == "__main__":
    main()
