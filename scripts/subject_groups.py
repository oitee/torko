"""Group similar entity names into subjects under a tag. Read-only prototype.

A broad tag such as Arrears holds many specific subjects. This script groups entity names that mean the same specific subject.
It groups names with and without a tag. It reads the database only. It calls no model and no API.
It writes nothing to the database. It needs numpy for the exact nearest-name search (not in requirements.txt).

Method:
1. Load the names with a vector and at least one kept item of source llm or dictionary. Skip the types place and person.
2. For each name, find the K nearest names by cosine distance, with an exact search in numpy.
3. Make an edge between two names when the distance is below d and each name is in the neighbour list of the other (mutual edge).
4. Join the edges with union-find.
5. Chaining guard: a group above MAX_SIZE names splits again with a stricter d (d minus STEP), until each part fits or d reaches MIN_D.
6. Per group: counts, parent tag, label and members.

    source .venv/bin/activate && set -a && source .env && set +a
    python3 scripts/subject_groups.py
"""
from __future__ import annotations

import argparse
import csv
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from db import get_engine

OUT_DIR = Path(__file__).resolve().parent.parent / "tags" / "subject_groups" / "results"
EXCLUDED_TYPES = ("place", "person")
K = 15
DEFAULT_D = 0.10
MAX_SIZE = 15
STEP = 0.02
MIN_D = 0.04
BATCH = 2000
COLUMNS = [
    "group_id", "label", "n_names", "n_speeches", "n_debates", "n_linked_names",
    "parent_tag", "parent_share", "other_tags", "members",
]


# ---------- pure functions ----------

def find(parent: dict, x):
    """Return the root of x. Compress the path."""
    root = x
    while parent[root] != root:
        root = parent[root]
    while parent[x] != root:
        parent[x], x = root, parent[x]
    return root


def union_groups(ids, edges):
    """Join ids with union-find. edges is a list of (a, b). Return a list of groups (lists of ids), sorted by smallest id."""
    parent = {i: i for i in ids}
    for a, b in edges:
        if a in parent and b in parent:
            ra, rb = find(parent, a), find(parent, b)
            if ra != rb:
                parent[max(ra, rb)] = min(ra, rb)
    groups = defaultdict(list)
    for i in ids:
        groups[find(parent, i)].append(i)
    return sorted((sorted(g) for g in groups.values()), key=lambda g: g[0])


def mutual_edges(neighbours, d):
    """neighbours: dict id -> list of (other_id, distance). Return (a, b, dist) with a < b, both directions present and dist < d."""
    seen = {}
    for a, lst in neighbours.items():
        for b, dist in lst:
            if a != b and dist < d:
                seen[(a, b)] = dist
    out = []
    for (a, b), dist in seen.items():
        if a < b and (b, a) in seen:
            out.append((a, b, max(dist, seen[(b, a)])))
    return sorted(out)


def group_with_guard(ids, edges, d, max_size=MAX_SIZE, step=STEP, min_d=MIN_D):
    """edges: list of (a, b, dist). Use edges with dist < d. A group above max_size splits again with d - step.
    At min_d the group stays whole. Return a list of groups (lists of ids)."""
    kept = [(a, b) for a, b, dist in edges if dist < d]
    result = []
    for g in union_groups(ids, kept):
        if len(g) <= max_size or d - step < min_d:
            result.append(g)
            continue
        inside = set(g)
        sub = [(a, b, dist) for a, b, dist in edges if a in inside and b in inside]
        result.extend(group_with_guard(g, sub, d - step, max_size, step, min_d))
    return result


def choose_parent(members, tag_of, speeches_of):
    """members: ids. tag_of: id -> tag or None. speeches_of: id -> set of speech ids.
    Return (parent_tag, parent_share, other_tags). The parent has the most distinct speeches among linked members.
    Ties go to the tag with the smaller name. parent_share is over the distinct speeches of linked members."""
    by_tag = defaultdict(set)
    for m in members:
        if tag_of.get(m):
            by_tag[tag_of[m]] |= speeches_of[m]
    if not by_tag:
        return None, 0.0, []
    total = set().union(*by_tag.values())
    ranked = sorted(by_tag.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    parent = ranked[0][0]
    return parent, len(by_tag[parent]) / len(total), [t for t, _ in ranked[1:]]


def choose_label(members, name_of, n_speeches_of):
    """The member name with the most speeches. Ties go to the shorter name, then alphabetical."""
    best = sorted(members, key=lambda m: (-n_speeches_of[m], len(name_of[m]), name_of[m]))
    return name_of[best[0]]


# ---------- database ----------

def load_names(conn):
    rows = conn.execute(text("""
        SELECT e.id, e.name, e.type, t.tag, (e.embedding_query IS NOT NULL) AS has_vec
        FROM entity_names e
        LEFT JOIN tags t ON t.id = e.tag_id AND e.link_status = 'linked'
        WHERE EXISTS (SELECT 1 FROM speech_items s WHERE s.entity_name_id = e.id AND s.kept
                      AND s.source IN ('llm', 'dictionary'))
    """)).fetchall()
    return rows


def load_speeches(conn):
    rows = conn.execute(text("""
        SELECT DISTINCT s.entity_name_id, s.speech_id, sp.debate_id
        FROM speech_items s JOIN speeches sp ON sp.id = s.speech_id
        WHERE s.kept AND s.source IN ('llm', 'dictionary') AND s.entity_name_id IS NOT NULL
    """)).fetchall()
    return rows


def load_vectors(conn, ids):
    """Return a float32 matrix with one normalised row per id, in the order of ids."""
    import numpy as np
    pos = {nid: i for i, nid in enumerate(ids)}
    mat = np.zeros((len(ids), 1536), dtype=np.float32)
    rows = conn.execute(text("SELECT id, embedding_query::text FROM entity_names WHERE id = ANY(:ids)"), {"ids": ids})
    for nid, vec in rows:
        mat[pos[nid]] = np.array(vec[1:-1].split(","), dtype=np.float32)
    mat /= np.linalg.norm(mat, axis=1, keepdims=True)
    return mat


def knn(conn, ids, k=K):
    """Return dict id -> list of (other_id, cosine distance), nearest first, without self. Exact search with numpy."""
    import numpy as np
    mat = load_vectors(conn, ids)
    out = {}
    for i in range(0, len(ids), BATCH):
        sim = mat[i:i + BATCH] @ mat.T
        sim[np.arange(sim.shape[0]), np.arange(i, i + sim.shape[0])] = -2.0
        top = np.argpartition(-sim, k, axis=1)[:, :k]
        for r in range(sim.shape[0]):
            out[ids[i + r]] = sorted(((ids[j], float(1.0 - sim[r, j])) for j in top[r]), key=lambda x: x[1])
        print(f"  knn {min(i + BATCH, len(ids))}/{len(ids)}", file=sys.stderr)
    return out


def build_rows(groups, name_of, type_of, tag_of, speeches_of, debates_of):
    rows = []
    n_sp = {m: len(speeches_of[m]) for m in name_of}
    for g in groups:
        if len(g) < 2:
            continue
        sp = set().union(*(speeches_of[m] for m in g))
        deb = set().union(*(debates_of[m] for m in g))
        parent, share, others = choose_parent(g, tag_of, speeches_of)
        members = sorted(g, key=lambda m: (-n_sp[m], name_of[m]))
        rows.append({
            "label": choose_label(g, name_of, n_sp),
            "n_names": len(g), "n_speeches": len(sp), "n_debates": len(deb),
            "n_linked_names": sum(1 for m in g if tag_of.get(m)),
            "parent_tag": parent or "", "parent_share": round(share, 3),
            "other_tags": "; ".join(others),
            "members": " | ".join(f"{name_of[m]} ({n_sp[m]}, {tag_of.get(m) or '-'})" for m in members),
            "_ids": members,
        })
    rows.sort(key=lambda r: (-r["n_speeches"], r["label"]))
    for i, r in enumerate(rows, 1):
        r["group_id"] = i
    return rows


def size_bucket(n):
    return "2" if n == 2 else "3-5" if n <= 5 else "6-20" if n <= 20 else "21+"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--d", type=float, default=DEFAULT_D)
    ap.add_argument("--try-d", type=float, nargs="*", default=[0.08, 0.10, 0.14])
    ap.add_argument("--max-size", type=int, default=MAX_SIZE)
    args = ap.parse_args()
    t0 = time.time()
    engine = get_engine()
    with engine.begin() as conn:
        names = load_names(conn)
        print(f"names with a kept item: {len(names)}")
        excluded_type = [r for r in names if r[2] in EXCLUDED_TYPES]
        no_vec = [r for r in names if r[2] not in EXCLUDED_TYPES and not r[4]]
        used = [r for r in names if r[2] not in EXCLUDED_TYPES and r[4]]
        print(f"excluded by type (place, person): {len(excluded_type)}; excluded for no vector: {len(no_vec)}; grouped pool: {len(used)}")
        name_of = {r[0]: r[1] for r in used}
        type_of = {r[0]: r[2] for r in used}
        tag_of = {r[0]: r[3] for r in used}
        speeches_of, debates_of = defaultdict(set), defaultdict(set)
        for nid, sid, did in load_speeches(conn):
            if nid in name_of:
                speeches_of[nid].add(sid)
                debates_of[nid].add(did)
        ids = sorted(name_of)
        neigh = knn(conn, ids)
        print(f"knn done at {time.time() - t0:.0f}s")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    dmax = max(args.try_d + [args.d])
    for d in sorted(set(args.try_d + [args.d])):
        edges = mutual_edges(neigh, d)
        groups = group_with_guard(ids, edges, d, args.max_size)
        multi = [g for g in groups if len(g) >= 2]
        buckets = Counter(size_bucket(len(g)) for g in multi)
        top = sorted((len(g) for g in multi), reverse=True)[:8]
        print(f"d={d}: edges={len(edges)} groups2+={len(multi)} names_grouped={sum(map(len, multi))} buckets={dict(buckets)} largest={top}")
        rows = build_rows(groups, name_of, type_of, tag_of, speeches_of, debates_of)
        with open(OUT_DIR / f"groups_d{d:.2f}.tsv", "w", newline="") as f:
            w = csv.writer(f, delimiter="\t")
            w.writerow(COLUMNS)
            for r in rows:
                w.writerow([r[c] for c in COLUMNS])
        if abs(d - args.d) < 1e-9:
            chosen = rows
    with open(OUT_DIR / "groups_v1.tsv", "w", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(COLUMNS)
        for r in chosen:
            w.writerow([r[c] for c in COLUMNS])
    write_reviews(chosen, name_of, tag_of, speeches_of, args.d, args.max_size, len(names), len(excluded_type), len(no_vec), len(used))
    print(f"done in {time.time() - t0:.0f}s")


def header(d, max_size, n_all, n_type, n_novec, n_used, rows):
    in_group = {m for r in rows for m in r["_ids"]}
    return (
        f"Method: exact nearest-neighbour search in numpy (cosine distance, k={K}). An edge joins two names when each is in the neighbour list of the other and the distance is below d={d}. "
        f"Union-find joins the edges into groups.\n\n"
        f"Chaining guard: a group above {max_size} names splits again with d reduced by {STEP}, down to {MIN_D}.\n\n"
        f"Denominators: {n_all} names have a kept item (source llm or dictionary). {n_type} are excluded by type (place, person). {n_novec} have no vector. "
        f"{n_used} names are in the pool. {len(in_group)} of them are in a group of 2 or more names ({len(rows)} groups). "
        f"n_names counts entity names. n_speeches counts distinct speeches with a kept item of any member. n_debates counts distinct debates of those speeches. "
        f"Tag counts use linked names only.\n\n"
    )


def member_str(r, limit=8):
    parts = r["members"].split(" | ")[:limit]
    more = f" (+{r['n_names'] - limit} more)" if r["n_names"] > limit else ""
    return "; ".join(parts) + more


def write_reviews(rows, name_of, tag_of, speeches_of, d, max_size, n_all, n_type, n_novec, n_used):
    head = header(d, max_size, n_all, n_type, n_novec, n_used, rows)
    in_group = {m for r in rows for m in r["_ids"]}
    linked = [m for m in name_of if tag_of.get(m)]
    by_tag_names = Counter(tag_of[m] for m in linked)
    top_tags = [t for t, _ in by_tag_names.most_common(30)]
    if "Arrears" not in top_tags:
        top_tags = top_tags[:29] + ["Arrears"]
    by_parent = defaultdict(list)
    for r in rows:
        if r["parent_tag"]:
            by_parent[r["parent_tag"]].append(r)
    lines = ["# Subjects under the 30 tags with the most linked names (v1)\n", head,
             "Each subject shows: label, n_names, n_speeches, n_debates, parent_share (the share of linked speeches that carry the parent tag), and up to 8 members as `name (speeches, tag)`.\n"]
    for t in top_tags:
        lines.append(f"\n## {t}\n")
        lines.append(f"{by_tag_names[t]} linked names carry this tag. {len(by_parent[t])} subjects have it as parent.\n")
        for r in sorted(by_parent[t], key=lambda r: -r["n_speeches"]):
            lines.append(f"- **{r['label']}**: {r['n_names']} names, {r['n_speeches']} speeches, {r['n_debates']} debates, share {r['parent_share']}. {member_str(r)}")
        lone = [m for m in linked if tag_of[m] == t and m not in in_group]
        lone.sort(key=lambda m: -len(speeches_of[m]))
        ex = "; ".join(f"{name_of[m]} ({len(speeches_of[m])})" for m in lone[:5])
        lines.append(f"\nLinked names of this tag in no group of 2 or more names: {len(lone)}. Examples: {ex}\n")
    (OUT_DIR / "review_tags_v1.md").write_text("\n".join(lines))
    un = [r for r in rows if r["n_linked_names"] == 0]
    un.sort(key=lambda r: (-r["n_names"], -r["n_speeches"]))
    lines = ["# Largest groups with no linked name (v1)\n", head,
             f"{len(un)} groups have no linked member. The list shows the 50 largest by n_names. These are candidates for new tags.\n"]
    for r in un[:50]:
        lines.append(f"- **{r['label']}**: {r['n_names']} names, {r['n_speeches']} speeches, {r['n_debates']} debates. {member_str(r)}")
    (OUT_DIR / "review_untagged_v1.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
