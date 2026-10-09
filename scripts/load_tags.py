"""Load the tag lists into the table `tags`. This script calls no model.

Sources: seed_v1 (tags/seed_tags_v1/results/seed_tags_v1.tsv) and places_v1 (tags/places/results/place_tags.tsv).
A tag that exists keeps its id and its source. The script deletes a tag only when its own source is loaded
and the file no longer holds the tag. It stops before any write on a duplicate name or on a tag that
entity_names still uses.

Columns of each file: tag, type, subtype, domain, description, aliases ('|'
between names, '-' for none), debate_count.

Safe to run again. The script matches a tag by its exact name. A tag that
exists gets the new values from the file and keeps its id and its source. A
new tag gets an id and the source of its list. A tag is deleted only when its
own source is loaded and the file of that source no longer holds the tag. A
tag from a source that is not in SOURCES is never deleted. A delete removes
the vectors of the tag too. A delete stops with an error when a row in
entity_names still points to the tag.

The script stops before any write in these cases:
- Two lists hold the same tag name. The script compares names with norm_name from
  scripts/link_entities.py.
- A file tag has the same name as a table tag from another source.
- A tag to delete is still used by a row in entity_names.
The script only reports (does not stop) when a name in one list equals an alias
in another list.

Run from the repo root, with .env loaded and db/init/10-tags.sql applied:

    python3 scripts/load_tags.py --dry-run          # print the plan, write nothing
    python3 scripts/load_tags.py                    # load all sources
    python3 scripts/load_tags.py --source places_v1 # load one source only
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from db import get_engine
from scripts.link_entities import norm_name

ROOT = Path(__file__).resolve().parent.parent
SEED_FILE = ROOT / "tags" / "seed_tags_v1" / "results" / "seed_tags_v1.tsv"
PLACES_FILE = ROOT / "tags" / "places" / "results" / "place_tags.tsv"
SOURCE = "seed_v1"

# (source name, file, status of the new tags).
# Each list had a manual review, so both lists load as 'reviewed'.
SOURCES = [
    ("seed_v1", SEED_FILE, "reviewed"),
    ("places_v1", PLACES_FILE, "reviewed"),
]
FIELDS = ("type", "subtype", "domain", "description", "aliases", "debate_count")


def parse_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE))
    out = []
    for r in rows:
        out.append({
            "tag": r["tag"],
            "type": r["type"],
            "subtype": r["subtype"] or None,
            "domain": None if r["domain"] in ("", "-") else r["domain"],
            "description": r["description"],
            "aliases": [] if r["aliases"] in ("", "-") else r["aliases"].split("|"),
            "debate_count": int(r["debate_count"]),
        })
    names = [r["tag"] for r in out]
    if len(set(names)) != len(names):
        raise SystemExit("the file holds the same tag name two times")
    if any(n != n.strip() or not n for n in names):
        raise SystemExit("a tag name is empty or has outer spaces. Run scripts/build_seed_tags.py first.")
    return out


def plan_load(files: dict[str, list[dict]], existing: list[dict], loaded: set[str]) -> dict:
    """Reads no database. Returns {"sources": {name: {insert, update, unchanged, delete}}, "errors": [...], "warnings": [...]}."""
    errors: list[str] = []
    warnings: list[str] = []
    # The same tag name in two lists.
    seen: dict[str, tuple[str, str]] = {}
    for src, rows in files.items():
        for r in rows:
            key = norm_name(r["tag"])
            if key in seen and seen[key][0] != src:
                errors.append(f"same name in {seen[key][0]} and {src}: {seen[key][1]!r} and {r['tag']!r}")
            seen.setdefault(key, (src, r["tag"]))
    # A name in one list equals an alias in another list.
    for src, rows in files.items():
        for other, orows in files.items():
            if other == src:
                continue
            names = {norm_name(r["tag"]): r["tag"] for r in rows}
            for o in orows:
                for a in o["aliases"]:
                    if norm_name(a) in names:
                        warnings.append(f"tag {names[norm_name(a)]!r} ({src}) is an alias of {o['tag']!r} ({other})")
    by_name = {e["tag"]: e for e in existing}
    by_norm = {norm_name(e["tag"]): e for e in existing}
    out: dict[str, dict] = {}
    for src in sorted(loaded):
        rows = files[src]
        res = {"insert": [], "update": [], "unchanged": 0, "delete": []}
        names = {r["tag"] for r in rows}
        for r in rows:
            e = by_name.get(r["tag"]) or by_norm.get(norm_name(r["tag"]))
            if e is None:
                res["insert"].append(r)
            elif e["source"] != src:
                errors.append(f"tag {r['tag']!r} of {src} exists in the table with source {e['source']!r}"
                              f" as {e['tag']!r}")
            elif e["tag"] != r["tag"]:
                errors.append(f"tag {r['tag']!r} of {src} differs only in spelling from the table tag {e['tag']!r}")
            elif any(e[f] != r[f] for f in FIELDS):
                res["update"].append(r)
            else:
                res["unchanged"] += 1
        res["delete"] = sorted(e["tag"] for e in existing if e["source"] == src and e["tag"] not in names)
        out[src] = res
    return {"sources": out, "errors": errors, "warnings": warnings}


def read_existing(conn) -> list[dict]:
    rows = conn.execute(text("SELECT tag, source, type, subtype, domain, description, aliases, debate_count FROM tags"))
    return [dict(r._mapping) for r in rows]


def print_plan(plan: dict) -> None:
    for src, res in plan["sources"].items():
        print(f"{src}: insert {len(res['insert'])}, update {len(res['update'])}, "
              f"unchanged {res['unchanged']}, delete {len(res['delete'])}", flush=True)
        for name in res["delete"][:20]:
            print(f"  will delete: {name!r}", flush=True)
    print(f"conflicts: {len(plan['errors'])}", flush=True)
    for e in plan["errors"][:50]:
        print(f"  CONFLICT: {e}", flush=True)
    print(f"alias warnings: {len(plan['warnings'])}", flush=True)
    for w in plan["warnings"][:50]:
        print(f"  warning: {w}", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="print the plan and write nothing")
    ap.add_argument("--source", choices=[s[0] for s in SOURCES], help="load only this source")
    args = ap.parse_args()

    files = {name: parse_rows(path) for name, path, _ in SOURCES}
    loaded = {args.source} if args.source else set(files)
    status = {name: st for name, _, st in SOURCES}
    engine = get_engine()
    with engine.begin() as conn:
        plan = plan_load(files, read_existing(conn), loaded)
        gone = [n for res in plan["sources"].values() for n in res["delete"]]
        used = conn.execute(text(
            "SELECT t.tag FROM tags t WHERE t.tag = ANY(:g) AND EXISTS (SELECT 1 FROM entity_names e WHERE e.tag_id = t.id)"),
            {"g": gone}).scalars().all() if gone else []
        for n in used:
            plan["errors"].append(f"tag {n!r} is to delete, but entity_names still points to it")
        print_plan(plan)
        if plan["errors"]:
            raise SystemExit("stopped before any write: fix the conflicts")
        if args.dry_run:
            print("dry run: nothing written", flush=True)
            return
        for src, res in plan["sources"].items():
            if res["insert"]:
                conn.execute(text("""
                    INSERT INTO tags (tag, type, subtype, domain, description, aliases, debate_count, source, status)
                    VALUES (:tag, :type, :subtype, :domain, :description, :aliases, :debate_count, :source, :status)
                """), [{**r, "source": src, "status": status[src]} for r in res["insert"]])
            if res["update"]:
                conn.execute(text("""
                    UPDATE tags SET type = :type, subtype = :subtype, domain = :domain,
                        description = :description, aliases = :aliases, debate_count = :debate_count
                    WHERE tag = :tag AND source = :source
                """), [{**r, "source": src} for r in res["update"]])
            if res["delete"]:
                conn.execute(text("DELETE FROM tags WHERE source = :s AND tag = ANY(:names)"),
                             {"s": src, "names": res["delete"]})
            total = conn.execute(text("SELECT count(*) FROM tags WHERE source = :s"), {"s": src}).scalar()
            if total != len(files[src]):
                raise SystemExit(f"count mismatch for {src}: file {len(files[src])}, table {total}")
            print(f"{src}: {len(files[src])} rows in the file, {total} in the table", flush=True)


if __name__ == "__main__":
    main()
