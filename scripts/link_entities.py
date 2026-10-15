"""Stage 5 of the tag pipeline: link each distinct entity name (norm_name, type) to one tag, or to no tag.

A name that matches the name or alias of exactly one tag links to it without a model call.
For other names, the decision model chooses between the 20 nearest tags and NONE.
The name links only when the top option is a tag with probability of at least --link-p.
A name is decided again only when its linked_by value or the tag set changed. --force decides every name again.
--test-pairs runs the steps on the hand-made test pairs and writes nothing to the database.
--dry-run prints the counts and calls no model.

It needs TYPESAFE_API_KEY and GEMINI_API_KEY. Run from the repo root:

    set -a && source .env && set +a
    python3 scripts/link_entities.py --test-pairs
    python3 scripts/link_entities.py --dry-run
    python3 scripts/link_entities.py
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import unicodedata
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from db import get_engine
from decision_model import MODEL, DecisionError, api_key, choice_probabilities, choice_q, decide, sum_is_off
from scripts.extract_entities import cell, free_stem
from scripts.tag_bakeoff import read_pairs
from tag_embed import ARMS, MODEL as EMBED_MODEL, embed_texts, to_pgvector

FOLDER = Path(__file__).resolve().parent.parent / "tags" / "linking"
PAIRS_FILE = Path(__file__).resolve().parent.parent / "tags" / "embedding_v1" / "data" / "test_pairs_v1.tsv"
QUESTIONS_VERSION = "q1"
EXACT_VERSION = "exact-match-v1"
EXACT_MATCH, MODEL_REASON = "exact_match", "model"
TAG_TASK, QUERY_TASK = ARMS["B"]
N_VECTOR = 20
MAX_OPTIONS = 21
N_EXAMPLES = 3
LINK_P = 0.7
NONE = "NONE"
NONE_TEXT = "no option means the same thing as this name"
# Place names that are also ordinary words. The exact match rule skips them, so the decision model decides.
MODEL_ONLY = frozenset({
    "basti", "mandi", "krishna", "daman", "guna", "banda", "sagar", "pali", "sham", "dhar", "mau", "mon",
    "surat", "kota", "gaya", "agar", "anand", "dang", "samba", "korea", "patan", "panna",
})
PAIR_TYPES = {"group", "law", "person", "place", "role", "scheme"}


def linked_by(model: str) -> str:
    return f"{model} {QUESTIONS_VERSION}"


def norm_name(name: str) -> str:
    """Lower case, single spaces. Strips only Unicode punctuation and symbols, so a Hindi vowel sign at the end stays."""
    s = " ".join(name.split()).casefold()
    def outer(ch: str) -> bool:
        return unicodedata.category(ch)[0] in "PS" or ch.isspace()
    start, end = 0, len(s)
    while start < end and outer(s[start]):
        start += 1
    while end > start and outer(s[end - 1]):
        end -= 1
    return s[start:end]


def exact_tag(exact: dict[str, list[int]], norm: str) -> int | None:
    """Returns None when no tag or two or more tags match. A name in MODEL_ONLY always gives None."""
    ids = set(exact.get(norm, []))
    # No type guard: the law "Unlawful Activities" matches the alias of the topic tag "Illegal Activities".
    return next(iter(ids)) if len(ids) == 1 and norm not in MODEL_ONLY else None


def needs_decision(row: dict, version: str, tag_set: int, force: bool = False,
                   exact: int | None = None) -> bool:
    if exact is not None:
        version = EXACT_VERSION
        if row["link_status"] != "linked" or row.get("tag_id") != exact:
            return True
    if force or row["link_status"] == "pending" or row["linked_by"] != version:
        return True
    return row["link_status"] == "none" and (row["tag_set_version"] or 0) < tag_set


def merge_candidates(exact: list[int], vector: list[tuple[int, float]], limit: int = MAX_OPTIONS) -> list[dict]:
    out, seen = [], set()
    for tid in exact:
        if tid not in seen:
            seen.add(tid)
            out.append({"tag_id": tid, "source": "exact", "distance": None})
    for tid, dist in vector:
        if tid in seen:
            for c in out:
                if c["tag_id"] == tid:
                    c["distance"] = dist
            continue
        seen.add(tid)
        out.append({"tag_id": tid, "source": "vector", "distance": dist})
    return out[:limit]


def option_text(tag: dict) -> str:
    return f"{tag['description'].strip().rstrip('.')}. Type: {tag['type']}."


def link_question(name: str, type_: str, options: dict[str, str]) -> dict:
    return choice_q(f"Which option means the same thing as the {type_} «{name}» in these speeches?",
                    {**options, NONE: NONE_TEXT})


def link_state(name: str, type_: str, n_speeches: int, examples: list[dict]) -> str:
    lines = [f"Entity name: {name}", f"Type: {type_}"]
    if examples:
        lines.append(f"It appears in {n_speeches} speeches in the Lok Sabha. Examples:")
        for n, ex in enumerate(examples, 1):
            lines.append(f"{n}. Words of the speech: \"{ex['mention']}\"")
            lines.append(f"   Summary of the speech: {ex['summary']}")
    return "\n".join(lines)


def decide_link(probs: dict[str, float], link_p: float = LINK_P) -> tuple[str, str | None, float]:
    """Returns (link_status, tag name or None, probability of the top option)."""
    top = max(probs, key=probs.get)
    if top != NONE and probs[top] >= link_p:
        return "linked", top, probs[top]
    return "none", None, probs[top]


def outcome(linked_tag: str | None, acceptable: list[str]) -> str:
    if linked_tag is None:
        return "correct none" if NONE in acceptable else "missed link"
    return "correct link" if linked_tag in acceptable else "wrong link"


class Tags:
    def __init__(self, conn):
        rows = conn.execute(text("SELECT id, tag, type, description, aliases FROM tags WHERE status <> 'rejected'")).all()
        self.by_id = {r.id: {"id": r.id, "tag": r.tag, "type": r.type, "description": r.description} for r in rows}
        self.exact: dict[str, list[int]] = {}
        for r in rows:
            for n in {norm_name(r.tag), *(norm_name(a) for a in r.aliases)}:
                if n and r.id not in self.exact.setdefault(n, []):
                    self.exact[n].append(r.id)
        self.version = conn.execute(text("SELECT coalesce(max(id), 0) FROM tags")).scalar()

    def nearest(self, conn, vector: list[float], n: int = N_VECTOR) -> list[tuple[int, float]]:
        return [(r.tag_id, r.distance) for r in conn.execute(text("""
            SELECT e.tag_id, e.embedding <=> CAST(:v AS vector) AS distance
            FROM tag_embeddings e JOIN tags t ON t.id = e.tag_id
            WHERE e.model = :m AND e.task_type = :t AND t.status <> 'rejected'
            ORDER BY distance LIMIT :n
        """), {"v": to_pgvector(vector), "m": EMBED_MODEL, "t": TAG_TASK, "n": n})]


def build_options(tags: Tags, candidates: list[dict]) -> dict[str, str]:
    return {tags.by_id[c["tag_id"]]["tag"]: option_text(tags.by_id[c["tag_id"]]) for c in candidates}


def ask(state: str, name: str, type_: str, options: dict[str, str], key: str, model: str) -> tuple[dict, dict, list[str]]:
    data = decide(state, {"link": link_question(name, type_, options)}, key, model)
    probs = choice_probabilities(data["answers"]["link"], [*options, NONE])
    warnings = []
    if sum_is_off(list(probs.values())):
        warnings.append(f"option probabilities sum to {sum(probs.values()):.3f}")
    return probs, data, warnings


def register(conn) -> int:
    pointed = conn.execute(text("""
        SELECT i.id, i.name, coalesce(i.judge_type, i.type) AS type, i.kept, e.norm_name, e.type AS e_type
        FROM speech_items i JOIN entity_names e ON e.id = i.entity_name_id
    """)).all()
    stale = [{"id": r.id} for r in pointed
             if not r.kept or (norm_name(r.name), r.type) != (r.norm_name, r.e_type)]
    if stale:
        conn.execute(text("UPDATE speech_items SET entity_name_id = NULL WHERE id = :id"), stale)
    items = conn.execute(text(
        "SELECT id, name, coalesce(judge_type, type) AS type FROM speech_items "
        "WHERE kept AND entity_name_id IS NULL AND source <> 'summary_tag'")).all()
    for it in items:
        n = norm_name(it.name)
        if not n:
            continue
        eid = conn.execute(text("""
            INSERT INTO entity_names (norm_name, type, name) VALUES (:n, :t, :name)
            ON CONFLICT (norm_name, type) DO UPDATE SET norm_name = EXCLUDED.norm_name
            RETURNING id
        """), {"n": n, "t": it.type, "name": it.name.strip()}).scalar()
        conn.execute(text("UPDATE speech_items SET entity_name_id = :e WHERE id = :id"), {"e": eid, "id": it.id})
    conn.execute(text("""
        UPDATE entity_names e SET n_speeches = coalesce(c.n, 0), name = coalesce(c.name, e.name)
        FROM entity_names e2 LEFT JOIN (
            SELECT entity_name_id, count(DISTINCT speech_id) AS n, mode() WITHIN GROUP (ORDER BY trim(name)) AS name
            FROM speech_items WHERE kept AND entity_name_id IS NOT NULL GROUP BY entity_name_id
        ) c ON c.entity_name_id = e2.id
        WHERE e.id = e2.id
    """))
    return len(items)


def examples_for(conn, entity_ids: list[int]) -> dict[int, list[dict]]:
    rows = conn.execute(text("""
        SELECT DISTINCT ON (i.entity_name_id, i.speech_id) i.entity_name_id, i.speech_id, i.mention, x.summary
        FROM speech_items i JOIN speech_extractions x ON x.id = i.extraction_id
        WHERE i.kept AND i.entity_name_id = ANY(:ids)
        ORDER BY i.entity_name_id, i.speech_id, i.position
    """), {"ids": entity_ids}).all()
    out: dict[int, list[dict]] = {}
    for r in rows:
        lst = out.setdefault(r.entity_name_id, [])
        if len(lst) < N_EXAMPLES:
            lst.append({"speech_id": r.speech_id, "mention": r.mention, "summary": r.summary})
    return out


def embed_missing(conn, rows: list[dict]) -> None:
    missing = [r for r in rows if r["embedding_query"] is None]
    if not missing:
        return
    vectors = embed_texts([r["name"] for r in missing], QUERY_TASK)
    for r, v in zip(missing, vectors):
        conn.execute(text("UPDATE entity_names SET embedding_query = CAST(:v AS vector) WHERE id = :id"),
                     {"v": to_pgvector(v), "id": r["id"]})


def split_by_rule(rows: list[dict], exact: dict[str, list[int]]) -> tuple[list[dict], list[dict]]:
    return ([r for r in rows if exact_tag(exact, r["norm_name"]) is not None],
            [r for r in rows if exact_tag(exact, r["norm_name"]) is None])


def write_exact_link(conn, row: dict, tags: Tags) -> None:
    tid = exact_tag(tags.exact, row["norm_name"])
    cand = [{"tag_id": tid, "tag": tags.by_id[tid]["tag"], "source": "exact", "distance": None, "p": None}]
    conn.execute(text("""
        UPDATE entity_names SET link_status = 'linked', tag_id = :tid, link_p = NULL,
               candidates = CAST(:c AS jsonb), link_raw = NULL, link_warnings = '{}',
               linked_by = :by, linked_at = now(), tag_set_version = :tsv, link_reason = :why
        WHERE id = :id
    """), {"tid": tid, "c": json.dumps(cand, ensure_ascii=False), "by": EXACT_VERSION,
           "tsv": tags.version, "why": EXACT_MATCH, "id": row["id"]})


def rule_report(rows: list[dict], tags: Tags) -> dict:
    one, many, mismatches, model_only = [], [], [], []
    for r in rows:
        ids = set(tags.exact.get(r["norm_name"], []))
        if len(ids) == 1 and r["norm_name"] in MODEL_ONLY:
            model_only.append(r)
        elif len(ids) == 1:
            one.append(r)
            t = tags.by_id[next(iter(ids))]
            if t["type"] != r["type"]:
                mismatches.append((r["name"], r["type"], t["tag"], t["type"]))
        elif len(ids) > 1:
            many.append(r)
    return {"names": len(rows), "one": one, "many": many, "mismatches": mismatches, "model_only": model_only}


def print_rule_report(rows: list[dict], tags: Tags, todo: list[dict]) -> None:
    rep_ = rule_report(rows, tags)
    to_rule = sum(exact_tag(tags.exact, r["norm_name"]) is not None for r in todo)
    print(f"Exact match rule over {rep_['names']} names: {len(rep_['one'])} have exactly one exact tag (would link), "
          f"{len(rep_['many'])} have 2 or more (go to the model). {len(rep_['model_only'])} have exactly one but "
          f"are on the MODEL_ONLY list (go to the model). Of the names to decide now, "
          f"{to_rule} link by the rule and {len(todo) - to_rule} need a model call. "
          f"Exact links where the entity type differs from the tag type: {len(rep_['mismatches'])}.")
    for name, type_, tag, tag_type in rep_["mismatches"]:
        print(f"  mismatch: {name!r} ({type_}) -> {tag!r} ({tag_type})")


def run_links(engine, args) -> None:
    version = linked_by(args.model)
    with engine.begin() as conn:
        registered = register(conn) if not args.dry_run else 0
        tags = Tags(conn)
        rows = [dict(r._mapping) for r in conn.execute(text("""
            SELECT id, norm_name, type, name, n_speeches, link_status, linked_by, tag_set_version, tag_id
            FROM entity_names WHERE n_speeches > 0 ORDER BY n_speeches DESC, id
        """))]
    todo = [r for r in rows
            if needs_decision(r, version, tags.version, args.force, exact_tag(tags.exact, r["norm_name"]))]
    unregistered = 0
    with engine.connect() as conn:
        unregistered = conn.execute(text(
            "SELECT count(*) FROM speech_items WHERE kept AND entity_name_id IS NULL")).scalar()
    print(f"{len(rows)} entity names with a kept item ({registered} items registered now, "
          f"{unregistered} kept items not registered). To decide with {version}: {len(todo)}. "
          f"Tag set version {tags.version}.", flush=True)
    if args.dry_run:
        print_rule_report(rows, tags, todo)
    if args.dry_run or not todo:
        return
    if args.limit:
        todo = todo[:args.limit]

    by_rule, todo = split_by_rule(todo, tags.exact)
    with engine.begin() as conn:
        for r in by_rule:
            write_exact_link(conn, r, tags)
            print(f"  {r['type']:11} {r['name'][:40]:40} -> {tags.by_id[exact_tag(tags.exact, r['norm_name'])]['tag']} (exact match)",
                  flush=True)
    if by_rule:
        print(f"linked {len(by_rule)} names by the exact match rule, without the decision model.", flush=True)
    if not todo:
        if not args.no_review:
            path = write_review(engine, [r["id"] for r in by_rule])
            print(f"review files: {path}.md and {path}.tsv", flush=True)
        return

    with engine.begin() as conn:
        vec_rows = conn.execute(text("SELECT id, name, embedding_query FROM entity_names WHERE id = ANY(:ids)"),
                                {"ids": [r["id"] for r in todo]}).all()
        embed_missing(conn, [dict(r._mapping) for r in vec_rows])
    with engine.connect() as conn:
        examples = examples_for(conn, [r["id"] for r in todo])
        linked = {r.norm_name: r.tag_id for r in conn.execute(text(
            "SELECT norm_name, tag_id FROM entity_names WHERE link_status = 'linked'"))}
        jobs = []
        for r in todo:
            vector = json.loads(conn.execute(text("SELECT embedding_query::text FROM entity_names WHERE id = :id"),
                                             {"id": r["id"]}).scalar())
            exact = tags.exact.get(r["norm_name"], []) + ([linked[r["norm_name"]]] if r["norm_name"] in linked else [])
            cands = merge_candidates(exact, tags.nearest(conn, vector))
            jobs.append((r, cands, link_state(r["name"], r["type"], r["n_speeches"], examples.get(r["id"], []))))

    key = api_key()
    counts = Counter()
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(ask, state, r["name"], r["type"], build_options(tags, cands), key, args.model): (r, cands)
                   for r, cands, state in jobs}
        for fut in as_completed(futures):
            r, cands = futures[fut]
            try:
                probs, data, warnings = fut.result()
            except DecisionError as exc:
                counts["failed"] += 1
                print(f"  {r['name']!r}: failed, nothing written ({exc!s:.200})", flush=True)
                continue
            status, tag, p = decide_link(probs, args.link_p)
            by_name = {tags.by_id[c["tag_id"]]["tag"]: c for c in cands}
            for name_, c in by_name.items():
                c["tag"], c["p"] = name_, probs[name_]
            stored = [*by_name.values(), {"tag_id": None, "tag": NONE, "source": "none", "distance": None, "p": probs[NONE]}]
            with engine.begin() as conn:
                conn.execute(text("""
                    UPDATE entity_names SET link_status = :st, tag_id = :tid, link_p = :p,
                           candidates = CAST(:c AS jsonb), link_raw = CAST(:raw AS jsonb), link_warnings = :w,
                           linked_by = :by, linked_at = now(), tag_set_version = :tsv, link_reason = 'model'
                    WHERE id = :id
                """), {"st": status, "tid": by_name[tag]["tag_id"] if tag else None, "p": p,
                       "c": json.dumps(stored, ensure_ascii=False), "raw": json.dumps(data, ensure_ascii=False),
                       "w": warnings, "by": version, "tsv": tags.version, "id": r["id"]})
            counts[status] += 1
            print(f"  {r['type']:11} {r['name'][:40]:40} -> {tag or NONE} ({p:.2f})", flush=True)
    print(f"decided {counts['linked'] + counts['none']} names: linked {counts['linked']}, none {counts['none']}, "
          f"failed {counts['failed']}.", flush=True)
    if not args.no_review:
        path = write_review(engine, [r["id"] for r in by_rule] + [r["id"] for r, _, _ in jobs])
        print(f"review files: {path}.md and {path}.tsv", flush=True)


def write_review(engine, ids: list[int]) -> Path:
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT e.id, e.name, e.type, e.n_speeches, e.link_status, e.link_p, e.link_reason, t.tag,
                   t.type AS tag_type, e.candidates
            FROM entity_names e LEFT JOIN tags t ON t.id = e.tag_id
            WHERE e.id = ANY(:ids) ORDER BY e.link_status, e.n_speeches DESC, e.name
        """), {"ids": ids}).all()
    out_dir = FOLDER / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = free_stem(out_dir, f"links_{QUESTIONS_VERSION}_{date.today().isoformat()}")
    md = [f"# Link review", "", f"{len(rows)} entity names decided on {date.today().isoformat()}. "
          f"Write right, wrong, or missed (NONE where a tag fits) in the `review` column of `{stem}.tsv`.", "",
          "| Status | Reason | P | Type | Name | Speeches | Tag | Next options |", "|---|---|---|---|---|---|---|---|"]
    mismatches = [r for r in rows if r.link_reason == EXACT_MATCH and r.link_status == "linked" and r.tag_type != r.type]
    with (out_dir / f"{stem}.tsv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["entity_name_id", "type", "name", "n_speeches", "status", "reason", "p", "tag", "tag_type",
                    "next_options", "review"])
        for r in rows:
            ranked = sorted(r.candidates or [], key=lambda c: -(c.get("p") or 0))
            nxt = ", ".join(f"{c['tag']} {c['p']:.2f}" for c in ranked if c["tag"] != r.tag and c.get("p") is not None)
            nxt = ", ".join(nxt.split(", ")[:3])
            p = "-" if r.link_p is None else f"{r.link_p:.2f}"
            md.append(f"| {r.link_status} | {r.link_reason or '-'} | {p} | {r.type} | {cell(r.name)} | {r.n_speeches} | "
                      f"{cell(r.tag or '-')} | {cell(nxt)} |")
            w.writerow([r.id, r.type, r.name, r.n_speeches, r.link_status, r.link_reason or "", p, r.tag or "",
                        r.tag_type or "", nxt, ""])
    md += ["", "## Exact links where the entity type differs from the tag type", "",
           f"{len(mismatches)} exact links. The rule has no type guard. A manual review decides.", ""]
    if mismatches:
        md += ["| Name | Entity type | Tag | Tag type |", "|---|---|---|---|"]
        md += [f"| {cell(r.name)} | {r.type} | {cell(r.tag)} | {r.tag_type} |" for r in mismatches]
    (out_dir / f"{stem}.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    return out_dir / stem


def run_test_pairs(engine, args) -> None:
    pairs = read_pairs(PAIRS_FILE)
    with engine.connect() as conn:
        tags = Tags(conn)
        known = {t["tag"] for t in tags.by_id.values()}
        missing = [(p["entity_text"], t) for p in pairs for t in p["acceptable"] if t != NONE and t not in known]
        if missing:
            raise SystemExit(f"test pairs name tags that are not in the table: {missing}")
        by_rule = {p["entity_text"]: exact_tag(tags.exact, norm_name(p["entity_text"])) for p in pairs}
        by_rule = {k: v for k, v in by_rule.items() if v is not None}
        rest = [p for p in pairs if p["entity_text"] not in by_rule]
        print(f"{len(by_rule)} of {len(pairs)} test pairs link by the exact match rule. "
              f"{len(rest)} pairs need one embedding call and one model call each.", flush=True)
        if args.count_only:
            return
        vectors = embed_texts([p["entity_text"] for p in rest], QUERY_TASK) if rest else []
        jobs = []
        for p, v in zip(rest, vectors):
            type_ = p["kind"] if p["kind"] in PAIR_TYPES else "topic"
            cands = merge_candidates(tags.exact.get(norm_name(p["entity_text"]), []), tags.nearest(conn, v))
            jobs.append((p, type_, cands))
    key = api_key() if jobs else None
    results = []
    for p in pairs:
        if p["entity_text"] in by_rule:
            tag = tags.by_id[by_rule[p["entity_text"]]]["tag"]
            results.append({"entity_text": p["entity_text"], "kind": p["kind"],
                            "type": p["kind"] if p["kind"] in PAIR_TYPES else "topic",
                            "acceptable_tags": p["acceptable_tags"], "linked": tag, "p": "",
                            "outcome": outcome(tag, p["acceptable"]), "acceptable_in_options": "",
                            "top3": "", "warnings": "", "reason": EXACT_MATCH})
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(ask, link_state(p["entity_text"], type_, 0, []), p["entity_text"], type_,
                               build_options(tags, cands), key, args.model): (p, type_, cands)
                   for p, type_, cands in jobs}
        for fut in as_completed(futures):
            p, type_, cands = futures[fut]
            try:
                probs, _, warnings = fut.result()
            except DecisionError as exc:
                print(f"  {p['entity_text']!r}: failed ({exc!s:.200})", flush=True)
                results.append({"entity_text": p["entity_text"], "kind": p["kind"], "type": type_,
                                "acceptable_tags": p["acceptable_tags"], "linked": "", "p": "",
                                "outcome": "failed", "acceptable_in_options": "", "top3": "", "warnings": str(exc)[:200],
                                "reason": MODEL_REASON})
                continue
            status, tag, top_p = decide_link(probs, args.link_p)
            ranked = sorted(probs.items(), key=lambda kv: -kv[1])
            in_options = any(t in probs for t in p["acceptable"] if t != NONE)
            results.append({"entity_text": p["entity_text"], "kind": p["kind"], "type": type_,
                            "acceptable_tags": p["acceptable_tags"], "linked": tag or NONE, "p": f"{top_p:.2f}",
                            "outcome": outcome(tag, p["acceptable"]),
                            "acceptable_in_options": "yes" if in_options else "no",
                            "top3": " | ".join(f"{t} {q:.2f}" for t, q in ranked[:3]),
                            "warnings": "; ".join(warnings), "reason": MODEL_REASON})
    order = {p["entity_text"]: i for i, p in enumerate(pairs)}
    results.sort(key=lambda r: order[r["entity_text"]])
    out_dir = FOLDER / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = free_stem(out_dir, f"test_pairs_{args.model}_{QUESTIONS_VERSION}_{date.today().isoformat()}")
    with (out_dir / f"{stem}.tsv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(results[0]), delimiter="\t")
        w.writeheader()
        w.writerows(results)
    c = Counter(r["outcome"] for r in results)
    print(f"\n{len(results)} test pairs, link at p >= {args.link_p}:")
    for k in ("correct link", "wrong link", "missed link", "correct none", "failed"):
        print(f"  {k:13} {c[k]}")
    asked = [r for r in results if r["reason"] == MODEL_REASON]
    print(f"An acceptable tag was among the options for {sum(r['acceptable_in_options'] == 'yes' for r in asked)} "
          f"of the {sum(any(t != NONE for t in r['acceptable_tags'].split('|')) for r in asked)} model-decided pairs that have one.")
    ruled = [r for r in results if r["reason"] == EXACT_MATCH]
    right = sum(r["outcome"] == "correct link" for r in ruled)
    print(f"Linked by the exact match rule: {len(ruled)}. Right: {right}. Wrong: {len(ruled) - right}.")
    for r in ruled:
        print(f"  {'right' if r['outcome'] == 'correct link' else 'WRONG'}: {r['entity_text']!r} -> {r['linked']!r} "
              f"(acceptable: {r['acceptable_tags']})")
    print(f"results: {out_dir / stem}.tsv")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default=MODEL)
    ap.add_argument("--link-p", type=float, default=LINK_P)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--limit", type=int, help="decide at most this many names (the most frequent first)")
    ap.add_argument("--force", action="store_true", help="decide again every name, also those done with this version")
    ap.add_argument("--dry-run", action="store_true", help="print the counts, register nothing, call no model")
    ap.add_argument("--no-review", action="store_true", help="write no review file")
    ap.add_argument("--count-only", action="store_true",
                    help="with --test-pairs: print how many pairs link by the rule and how many need a model call, then stop")
    ap.add_argument("--test-pairs", action="store_true", help="run on the hand-made test pairs, write nothing to the database")
    args = ap.parse_args()
    engine = get_engine()
    if args.test_pairs:
        run_test_pairs(engine, args)
    else:
        run_links(engine, args)


if __name__ == "__main__":
    main()
