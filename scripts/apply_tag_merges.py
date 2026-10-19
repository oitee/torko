"""Apply the accepted merges of near-duplicate tags to the database. This script calls no model.

For each group (tag_merges.py), the kept tag gets the names and aliases of the merged tags as aliases, and a new
name or type when the group has one. Each merged tag gets status 'merged' and merged_into = the kept tag.
Links of entity names, summary-tag items, and subject parents move from a merged tag to the kept tag.

An entity name with no tag is decided again by stage 5 when the vote of its stored options was split inside one
group: two or more tags of the group together reach --split-p. The script clears tag_set_version of these names,
so scripts/link_entities.py decides them again on its next run.

The script is safe to run again: a second run changes nothing. Run it after scripts/load_tags.py.

    source .venv/bin/activate && set -a && source .env && set +a
    python3 scripts/apply_tag_merges.py --dry-run
    python3 scripts/apply_tag_merges.py
"""
from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from db import get_engine
from scripts.link_entities import LINK_P, norm_name
from tag_merges import Group, load_groups, merged_aliases


def split_group(candidates: list[dict], group_of: dict[int, int], split_p: float) -> int | None:
    """candidates: the stored options of one entity name, each with tag_id and p. group_of: tag ID -> group number.
    Returns the group whose tags together reach split_p, with 2 or more of its tags among the options."""
    by_group: dict[int, list[float]] = defaultdict(list)
    for c in candidates:
        g = group_of.get(c.get("tag_id"))
        if g is not None:
            by_group[g].append(c.get("p") or 0.0)
    hits = [(sum(ps), g) for g, ps in by_group.items() if len(ps) >= 2 and sum(ps) >= split_p]
    return max(hits)[1] if hits else None


def check_names(groups: list[Group], tags: dict[str, dict]) -> list[str]:
    """A renamed kept tag is in the table under its old name before the first run, and under its new name after it."""
    errors = []
    for g in groups:
        for name in g.members:
            if name not in tags:
                errors.append(f"tag {name!r} is not in the table")
        if g.target not in tags and g.final_name not in tags:
            errors.append(f"tag {g.target!r} is not in the table")
        if g.new_name and g.target in tags and g.new_name in tags:
            errors.append(f"new name {g.new_name!r} is already the name of another tag")
    return errors


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="print the counts and write nothing")
    ap.add_argument("--split-p", type=float, default=LINK_P)
    args = ap.parse_args()
    groups = load_groups()
    engine = get_engine()
    with engine.begin() as conn:
        tags = {r.tag: dict(r._mapping) for r in conn.execute(text(
            "SELECT id, tag, type, aliases, status, merged_into FROM tags"))}
        errors = check_names(groups, tags)
        if errors:
            for e in errors:
                print(f"  ERROR: {e}")
            raise SystemExit("stopped before any write")
        counts = defaultdict(int)
        group_of: dict[int, int] = {}
        kept_ids, moves = [], {}
        for n, g in enumerate(groups):
            kept = tags.get(g.target) or tags[g.new_name]
            kept_ids.append(kept["id"])
            members = [tags[m] for m in g.members]
            for t in [kept, *members]:
                group_of[t["id"]] = n
            aliases = merged_aliases(kept["aliases"], kept["tag"], g.final_name,
                                     [(m["tag"], m["aliases"]) for m in members], norm_name)
            new_type = g.new_type or kept["type"]
            if (kept["tag"], kept["aliases"], kept["type"]) != (g.final_name, aliases, new_type):
                counts["kept tags changed"] += 1
                if not args.dry_run:
                    conn.execute(text("UPDATE tags SET tag = :name, aliases = :a, type = :ty WHERE id = :id"),
                                 {"name": g.final_name, "a": aliases, "ty": new_type, "id": kept["id"]})
            for m in members:
                moves[m["id"]] = kept["id"]
                if (m["status"], m["merged_into"]) != ("merged", kept["id"]):
                    counts["tags marked merged"] += 1
                    if not args.dry_run:
                        conn.execute(text("UPDATE tags SET status = 'merged', merged_into = :k WHERE id = :id"),
                                     {"k": kept["id"], "id": m["id"]})
        pairs = [{"f": f, "k": k} for f, k in moves.items()]
        # Counted through the move map, so the dry run gives the same number as a real run.
        counts["speeches with summary-tag rows of two tags of one group"] = conn.execute(text("""
            WITH m AS (SELECT unnest(CAST(:f AS int[])) AS f, unnest(CAST(:k AS int[])) AS k)
            SELECT count(*) FROM (
                SELECT i.speech_id, coalesce(m.k, i.tag_id) FROM speech_items i LEFT JOIN m ON m.f = i.tag_id
                WHERE i.source = 'summary_tag' AND coalesce(m.k, i.tag_id) = ANY(:kept)
                GROUP BY 1, 2 HAVING count(*) > 1) x"""),
            {"f": list(moves), "k": list(moves.values()), "kept": kept_ids}).scalar()
        for table, col in (("entity_names", "tag_id"), ("speech_items", "tag_id"), ("subjects", "parent_tag_id")):
            n = conn.execute(text(f"SELECT count(*) FROM {table} WHERE {col} = ANY(:ids)"),
                             {"ids": list(moves)}).scalar()
            counts[f"{table} rows moved"] = n
            if n and not args.dry_run:
                conn.execute(text(f"UPDATE {table} SET {col} = :k WHERE {col} = :f"), pairs)
        rerun = [r.id for r in conn.execute(text("""
            SELECT id, candidates FROM entity_names
            WHERE link_status = 'none' AND candidates IS NOT NULL AND tag_set_version IS NOT NULL""")).all()
                 if split_group(r.candidates, group_of, args.split_p) is not None]
        counts["names to decide again in stage 5"] = len(rerun)
        if rerun and not args.dry_run:
            conn.execute(text("UPDATE entity_names SET tag_set_version = NULL WHERE id = ANY(:ids)"), {"ids": rerun})
        for k, v in counts.items():
            print(f"{k}: {v}")
        print(f"groups {len(groups)}, merged tags {len(moves)}" + (" (dry run: nothing written)" if args.dry_run else ""))


if __name__ == "__main__":
    main()
