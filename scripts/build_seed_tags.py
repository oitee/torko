from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "tags" / "seed_tags_v1"
CHUNK_SIZE = 400       # rows in each stage 1 input file
PACK_SIZE = 350        # largest stage 2 input file, in rows
EDIT_FILES = ("fixes_assembly.tsv", "fixes_types.tsv", "review.tsv")
COLUMNS = ("tag", "type", "subtype", "domain", "description", "aliases", "debate_count")


def read_tsv(path: Path) -> list[list[str]]:
    return [line.split("\t") for line in path.read_text(encoding="utf-8").split("\n") if line]


def norm(name: str) -> str:
    return re.sub(r"\s+", " ", name).strip().casefold()


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


# ---------- stage inputs ----------

def split_chunks(raw: list[list[str]]) -> dict[str, list[str]]:
    lines = ["\t".join(r) for r in raw]
    return {f"chunk_{i // CHUNK_SIZE:02d}": lines[i:i + CHUNK_SIZE] for i in range(0, len(lines), CHUNK_SIZE)}


def pack_merge_input(classified: list[list[str]], counts: dict[str, int]) -> dict[str, list[str]]:
    groups: dict[tuple[str, str], list[list[str]]] = {}
    for tag, typ, domain, desc, hint in classified:
        # A tag that stage 1 respelled has no count and gets "?".
        groups.setdefault((typ, domain), []).append([tag, str(counts.get(tag, "?")), domain, desc, hint])
    files: dict[str, list[str]] = {}
    for typ in dict.fromkeys(t for t, _ in groups):
        ordered = sorted(((k, v) for k, v in groups.items() if k[0] == typ), key=lambda kv: -len(kv[1]))
        bins: list[list] = []
        for key, rows in ordered:
            for b in bins:
                if sum(len(r) for _, r in b) + len(rows) <= PACK_SIZE:
                    b.append((key, rows))
                    break
            else:
                bins.append([(key, rows)])
        for b in bins:
            name = f"{typ}__{slug(b[0][0][1])}" + (f"_plus{len(b) - 1}" if len(b) > 1 else "")
            files[name] = ["\t".join(r) for _, rows in b for r in rows]
    return files


# ---------- assembly ----------

def assemble(merged: list[list[str]], counts: dict[str, int]) -> tuple[list[dict], list[str]]:
    log: list[str] = []
    groups: dict[str, dict] = {}
    for tag, typ, domain, desc, aliases, _count in merged:
        alias_list = [] if aliases == "-" else aliases.split("|")
        if tag in groups:
            log.append(f"same canonical name: {tag!r}, groups joined")
            groups[tag]["aliases"] += alias_list
            groups[tag].update(type=typ, domain=domain, description=desc)
            continue
        groups[tag] = {"tag": tag, "type": typ, "subtype": "", "domain": domain,
                       "description": desc, "aliases": alias_list}

    seen: set[str] = set()
    for g in list(groups.values()):
        kept = []
        for name in g["aliases"]:
            if name in seen or name == g["tag"]:
                log.append(f"double: {name!r} dropped from {g['tag']!r}")
                continue
            seen.add(name)
            kept.append(name)
        g["aliases"] = kept
        if g["tag"] not in seen:
            seen.add(g["tag"])
        elif kept:
            log.append(f"double canonical name: {g['tag']!r} is in an earlier group. Its aliases stay here.")
        else:
            log.append(f"double canonical name: {g['tag']!r} is in an earlier group. Group removed.")
            del groups[g["tag"]]

    for name in counts:
        if name in seen:
            continue
        hit = next((g for g in groups.values() if norm(name) in {norm(n) for n in [g["tag"]] + g["aliases"]}), None)
        if hit:
            hit["aliases"].append(name)
            seen.add(name)
            log.append(f"attached: {name!r} -> {hit['tag']!r}")
        else:
            log.append(f"UNATTACHED: {name!r}")

    # Some sansad.in keywords start or end with a space, for example " Caste Census".
    # The tag name loses the spaces. The source spelling stays as an alias, so the
    # cover check still finds the keyword.
    for g in list(groups.values()):
        clean = g["tag"].strip()
        if clean == g["tag"]:
            continue
        if clean in groups:
            raise SystemExit(f"outer spaces: {g['tag']!r} without its spaces is the name of another group")
        log.append(f"outer spaces removed: {g['tag']!r} -> {clean!r}")
        del groups[g["tag"]]
        g["aliases"].insert(0, g["tag"])
        g["tag"] = clean
        groups[clean] = g
    return list(groups.values()), log


def apply_edit(groups: dict[str, dict], tag: str, field: str, value: str) -> list[str]:
    if field == "todo":
        return []
    if tag not in groups:
        raise SystemExit(f"edit for unknown tag {tag!r} ({field})")
    g = groups[tag]
    if field in ("type", "subtype", "domain", "description"):
        g[field] = value
    elif field == "aliases":
        g["aliases"] = [] if value == "-" else value.split("|")
    elif field == "add_alias":
        g["aliases"].append(value)
    elif field == "merge":
        if value not in groups:
            raise SystemExit(f"merge target {value!r} not found")
        target = groups[value]
        for name in [g["tag"]] + g["aliases"]:
            if name not in target["aliases"] and name != target["tag"]:
                target["aliases"].append(name)
        del groups[tag]
    elif field == "split":
        if value not in g["aliases"]:
            raise SystemExit(f"split: {value!r} is not an alias of {tag!r}")
        if value in groups:
            raise SystemExit(f"split: a group named {value!r} exists already")
        g["aliases"].remove(value)
        groups[value] = {"tag": value, "type": g["type"], "subtype": g["subtype"], "domain": g["domain"],
                         "description": "Meaning not reviewed.", "aliases": []}
    elif field == "drop":
        del groups[tag]
        return [g["tag"]] + g["aliases"]
    else:
        raise SystemExit(f"unknown edit field {field!r} for {tag!r}")
    return []


def finish(groups: list[dict], counts: dict[str, int]) -> list[dict]:
    for g in groups:
        g["debate_count"] = sum(counts.get(n, 0) for n in [g["tag"]] + g["aliases"])
    return sorted(groups, key=lambda g: (-g["debate_count"], g["tag"]))


def check_cover(groups: list[dict], counts: dict[str, int], dropped: frozenset[str] = frozenset()) -> list[str]:
    problems = []
    seen: dict[str, int] = {}
    for n in (n for g in groups for n in [g["tag"]] + g["aliases"] if n in counts):
        seen[n] = seen.get(n, 0) + 1
    problems += [f"keyword in {c} groups: {n!r}" for n, c in seen.items() if c > 1]
    problems += [f"keyword in no group: {n!r}" for n in counts if n not in seen and n not in dropped]
    problems += [f"dropped keyword still in a group: {n!r}" for n in seen if n in dropped]
    total = sum(g["debate_count"] for g in groups)
    expected = sum(c for n, c in counts.items() if n not in dropped)
    if total != expected:
        problems.append(f"debate counts do not balance: {total} != {expected}")
    return problems


def to_row(g: dict) -> str:
    aliases = "|".join(g["aliases"]) or "-"
    return "\t".join([g["tag"], g["type"], g["subtype"], g["domain"], g["description"], aliases, str(g["debate_count"])])


def atlas_json(groups: list[dict]) -> dict:
    """Each name list is sorted and each row holds indexes into the lists."""
    types = sorted({g["type"] for g in groups})
    domains = sorted({g["domain"] for g in groups})
    subs = sorted({g["subtype"] for g in groups})
    return {"types": types, "domains": domains, "subs": subs,
            "rows": [[g["tag"], types.index(g["type"]), domains.index(g["domain"]), g["description"],
                      "|".join(g["aliases"]), g["debate_count"], subs.index(g["subtype"])] for g in groups]}


def write_files(folder: Path, files: dict[str, list[str]], suffix: str = "") -> None:
    folder.mkdir(parents=True, exist_ok=True)
    for old in folder.iterdir():
        old.unlink()
    for name, lines in files.items():
        (folder / f"{name}{suffix}").write_text("".join(l + "\n" for l in lines), encoding="utf-8")


def main() -> None:
    data, results = ROOT / "data", ROOT / "results"
    raw = read_tsv(data / "tags_raw.tsv")
    counts = {tag: int(n) for tag, n in raw}
    classified = [r for f in sorted((data / "llm_classify").glob("*.tsv")) for r in read_tsv(f)]
    merged = [r for f in sorted((data / "llm_merge").glob("*.tsv")) for r in read_tsv(f)]

    write_files(results / "chunks", split_chunks(raw))
    write_files(results / "merge_in", pack_merge_input(classified, counts), ".tsv")

    groups_list, log = assemble(merged, counts)
    groups = {g["tag"]: g for g in groups_list}
    dropped: set[str] = set()
    for name in EDIT_FILES:
        rows = read_tsv(data / name)[1:]
        for row in rows:
            tag, field, value = (row + ["", ""])[:3]
            dropped.update(n for n in apply_edit(groups, tag, field, value) if n in counts)
        log.append(f"applied {len(rows)} edits from {name}")
    final = finish(list(groups.values()), counts)

    if dropped:
        log.append(f"dropped {len(dropped)} keywords on purpose: {sorted(dropped)!r}")
    problems = check_cover(final, counts, frozenset(dropped))
    log += problems
    (results / "assembly_log.txt").write_text("".join(l + "\n" for l in log), encoding="utf-8")
    (results / "seed_tags_v1.tsv").write_text(
        "\t".join(COLUMNS) + "\n" + "".join(to_row(g) + "\n" for g in final), encoding="utf-8")
    (ROOT / "atlas" / "tags.json").write_text(
        json.dumps(atlas_json(final), separators=(",", ":"), ensure_ascii=False), encoding="utf-8")

    print(f"{len(raw)} keywords -> {len(final)} tags, {sum(g['debate_count'] for g in final)} keyword-debate links")
    print(f"log: {results / 'assembly_log.txt'}")
    if problems:
        print(f"{len(problems)} coverage problems. See the log.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
