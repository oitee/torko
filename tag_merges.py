"""Resolve the accepted merges of near-duplicate tags into one kept tag for each group.

A merge row says that tag_from means the same thing as tag_into. Rows can join into chains or loops,
for example A -> B -> C. All tags that the rows join form one group, and the whole group goes into one kept tag.
A group with exactly one tag that is never a tag_from keeps that tag. Any other group needs a row in the
group targets file, which names its kept tag. A target row can also give the kept tag a new name.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MERGES_FILE = ROOT / "tags" / "near_duplicates" / "data" / "merges_v1.tsv"
TARGETS_FILE = ROOT / "tags" / "near_duplicates" / "data" / "group_targets_v1.tsv"


@dataclass
class Group:
    target: str
    members: list[str]                      # the merged tags, without the target
    new_name: str | None = None
    new_type: str | None = None
    notes: list[str] = field(default_factory=list)

    @property
    def final_name(self) -> str:
        return self.new_name or self.target


def read_tsv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def resolve(merges: list[dict], targets: list[dict]) -> list[Group]:
    """merges: rows with tag_from, tag_into, new_name, new_type. targets: rows with target and new_name.
    Raises ValueError when a group has no clear target, or when a rename or type change conflicts."""
    parent: dict[str, str] = {}

    def find(x: str) -> str:
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for r in merges:
        parent[find(r["tag_from"])] = find(r["tag_into"])
    groups: dict[str, set[str]] = {}
    for r in merges:
        groups.setdefault(find(r["tag_from"]), set()).update((r["tag_from"], r["tag_into"]))
    sources = {r["tag_from"] for r in merges}
    chosen = {t["target"]: t for t in targets}
    used_targets: set[str] = set()
    out = []
    for tags in groups.values():
        named = sorted(tags & set(chosen))
        if len(named) > 1:
            raise ValueError(f"the group {sorted(tags)} has two target rows: {named}")
        if named:
            target = named[0]
            used_targets.add(target)
        else:
            sinks = sorted(tags - sources)
            if len(sinks) != 1:
                raise ValueError(f"the group {sorted(tags)} needs a row in the group targets file")
            target = sinks[0]
        rows = [r for r in merges if r["tag_from"] in tags]
        names = {r["new_name"] for r in rows if r.get("new_name")} - {target}
        if named and chosen[target].get("new_name"):
            names = {chosen[target]["new_name"]}
        types = {r["new_type"] for r in rows if r.get("new_type")}
        if len(names) > 1 or len(types) > 1:
            raise ValueError(f"the group {sorted(tags)} has conflicting new names {names} or types {types}")
        out.append(Group(target=target, members=sorted(tags - {target}),
                         new_name=next(iter(names), None), new_type=next(iter(types), None),
                         notes=[r["note"] for r in rows if r.get("note")]))
    unused = sorted(set(chosen) - used_targets)
    if unused:
        raise ValueError(f"target rows name tags that are in no group: {unused}")
    return sorted(out, key=lambda g: g.final_name.casefold())


def load_groups(merges_file: Path = MERGES_FILE, targets_file: Path = TARGETS_FILE) -> list[Group]:
    return resolve(read_tsv(merges_file), read_tsv(targets_file))


def merged_aliases(target_aliases: list[str], target_name: str, final_name: str,
                   members: list[tuple[str, list[str]]], norm) -> list[str]:
    """The aliases of the kept tag after the merge: its own aliases, its old name when it is renamed, and the name
    and aliases of each merged tag. norm: the name normaliser of the link step. A duplicate after norm is dropped,
    and so is any alias equal to the final name."""
    out, seen = [], {norm(final_name)}
    extra = [target_name] if target_name != final_name else []
    for a in [*target_aliases, *extra, *(x for name, aliases in members for x in (name, *aliases))]:
        n = norm(a)
        if n and n not in seen:
            seen.add(n)
            out.append(a)
    return out
