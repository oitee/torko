"""List the pairs of tags that split the stage 5 vote of an entity name.

Stage 5 links a name to a tag only when one tag gets probability 0.7 or more.
When two tags mean the same thing, the decision model divides its vote between them, and the name gets no tag.
This script reads the stored stage 5 answers of the names without a tag.
For each name, it takes the two tags with the highest probability.
It records the pair when the two together reach --min-sum and the second reaches --min-second.
It writes one row per pair, with counts, both descriptions, the distance of the two tag vectors, and example names.
It reads the database only. It calls no model and writes nothing to the database.

    set -a && source .env && set +a
    python3 scripts/split_vote_pairs.py
"""
from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from db import get_engine
from tag_embed import ARMS

OUT = Path(__file__).resolve().parent.parent / "tags" / "near_duplicates" / "results" / "split_pairs_v1.tsv"
NONE = "NONE"
MIN_SUM = 0.7
MIN_SECOND = 0.2
N_EXAMPLES = 5
TAG_TASK = ARMS["B"][0]
COLUMNS = [
    "pair_id", "tag_a", "tag_b", "n_names", "n_speeches", "mean_p_a", "mean_p_b", "distance",
    "type_a", "type_b", "domain_a", "domain_b", "description_a", "description_b", "examples",
]


def split_pair(probs: dict[str, float], min_sum: float = MIN_SUM, min_second: float = MIN_SECOND):
    """Return the two top tags as ((tag, p), (tag, p)) when they split the vote, else None. NONE is not a tag."""
    top = sorted(((p, t) for t, p in probs.items() if t != NONE), reverse=True)[:2]
    if len(top) < 2:
        return None
    (p1, t1), (p2, t2) = top
    if p2 < min_second or p1 + p2 < min_sum:
        return None
    return (t1, p1), (t2, p2)


def collect(rows, min_sum: float = MIN_SUM, min_second: float = MIN_SECOND) -> dict:
    """rows: (name, type, n_speeches, probabilities). Return {(tag_a, tag_b): stats}, with tag_a < tag_b."""
    pairs = defaultdict(lambda: {"names": [], "p_a": [], "p_b": []})
    for name, etype, n_speeches, probs in rows:
        hit = split_pair(probs or {}, min_sum, min_second)
        if hit is None:
            continue
        (t1, p1), (t2, p2) = sorted(hit)
        s = pairs[(t1, t2)]
        s["names"].append((n_speeches, name, etype))
        s["p_a"].append(p1)
        s["p_b"].append(p2)
    return pairs


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--min-sum", type=float, default=MIN_SUM)
    ap.add_argument("--min-second", type=float, default=MIN_SECOND)
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args()

    with get_engine().connect() as conn:
        rows = conn.execute(text("""
            SELECT en.name, en.type, coalesce(k.ns, 0), en.link_raw->'answers'->'link'->'probabilities'
            FROM entity_names en
            LEFT JOIN (SELECT entity_name_id, count(DISTINCT speech_id) ns FROM speech_items
                       WHERE kept GROUP BY 1) k ON k.entity_name_id = en.id
            WHERE en.link_status = 'none'
              AND en.link_raw->'answers'->'link'->>'choice' IS DISTINCT FROM 'NONE'
        """)).all()
        tags = {r.tag: r for r in conn.execute(text("SELECT id, tag, type, domain, description FROM tags")).all()}
        pairs = collect(rows, args.min_sum, args.min_second)
        ids = [(tags[a].id, tags[b].id) for a, b in pairs if a in tags and b in tags]
        dist = {}
        for ia, ib in ids:
            d = conn.execute(text("""
                SELECT x.embedding <=> y.embedding FROM tag_embeddings x, tag_embeddings y
                WHERE x.tag_id = :a AND y.tag_id = :b AND x.task_type = :t AND y.task_type = :t
            """), {"a": ia, "b": ib, "t": TAG_TASK}).scalar()
            dist[(ia, ib)] = d

    out = []
    for (a, b), s in pairs.items():
        ta, tb = tags.get(a), tags.get(b)
        d = dist.get((ta.id, tb.id)) if ta and tb else None
        ex = sorted(s["names"], reverse=True)[:N_EXAMPLES]
        out.append({
            "tag_a": a, "tag_b": b, "n_names": len(s["names"]), "n_speeches": sum(n for n, _, _ in s["names"]),
            "mean_p_a": f"{sum(s['p_a']) / len(s['p_a']):.2f}", "mean_p_b": f"{sum(s['p_b']) / len(s['p_b']):.2f}",
            "distance": "" if d is None else f"{d:.3f}",
            "type_a": ta.type if ta else "", "type_b": tb.type if tb else "",
            "domain_a": (ta.domain or "") if ta else "", "domain_b": (tb.domain or "") if tb else "",
            "description_a": (ta.description or "").replace("\t", " ").replace("\n", " ") if ta else "",
            "description_b": (tb.description or "").replace("\t", " ").replace("\n", " ") if tb else "",
            "examples": " | ".join(f"{name} ({etype}, {n})" for n, name, etype in ex),
        })
    out.sort(key=lambda r: (-r["n_speeches"], -r["n_names"], r["tag_a"], r["tag_b"]))
    for i, r in enumerate(out, 1):
        r["pair_id"] = i

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, delimiter="\t")
        w.writeheader()
        w.writerows(out)
    missing = sum(1 for r in out if not r["type_a"] or not r["type_b"])
    print(f"names read {len(rows)}, pairs {len(out)}, names in pairs {sum(r['n_names'] for r in out)}, "
          f"pairs with a tag not in the tags table {missing}, written {args.out}")


if __name__ == "__main__":
    main()
