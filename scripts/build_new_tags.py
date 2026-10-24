"""Build the list of new tags from the reviewed subjects with no tag.

An LLM review batch and a manual review decided each large subject with no parent tag
(tags/subject_groups/data/new_tag_reviews_v1.tsv). A row with decision `new` proposes a tag. A manual edit is in the
column review_note as `field=value` pairs, for example `decision=new | name=Road Infrastructure`. Two rows can propose
the same tag. Then the values of an edited row win, and a field with two different values stops the build.

Two files of tags/new_tags/data/ add what the reviews do not hold:
- fills_v1.tsv: a type or domain for a tag whose rows have none (tag, field, value, note).
- descriptions_v1.tsv: one description for each tag, written by an LLM (`describe`).

`build` calls no model. It writes results/new_tags_v1.tsv with the columns of the seed list, for scripts/load_tags.py.

    source .venv/bin/activate && set -a && source .env && set +a
    python3 scripts/build_new_tags.py describe --dry-run
    python3 scripts/build_new_tags.py describe
    python3 scripts/build_new_tags.py build
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

ROOT = Path(__file__).resolve().parent.parent
REVIEWS = ROOT / "tags" / "subject_groups" / "data" / "new_tag_reviews_v1.tsv"
FOLDER = ROOT / "tags" / "new_tags"
FILLS = FOLDER / "data" / "fills_v1.tsv"
DESCRIPTIONS = FOLDER / "data" / "descriptions_v1.tsv"
OUT = FOLDER / "results" / "new_tags_v1.tsv"
COLUMNS = ("tag", "type", "subtype", "domain", "description", "aliases", "debate_count")
FIELDS = ("decision", "tag", "name", "type", "domain", "aliases", "rename_tag")
TYPES = {"topic", "institution", "law", "place", "scheme", "group", "role", "person"}
MODEL = "gemini-3.8-flash"
BATCH = 40
SHOW_NAMES = 6
SYSTEM = """You write one short description for each tag of a subject list. The tags label speeches in the Lok Sabha, the lower house of India's parliament.
Rules for each description:
- One sentence, at most 20 words, in simple English. No semicolons.
- Say what the thing is, in the Indian context when it is Indian. Do not start with "This tag" or the tag name.
- Write it like a dictionary definition, for example "Building or improving roads and highways." or "Indian political party based in West Bengal." Do not start with "A subject concerning", "A body functioning as", or a similar phrase.
- Fit the type: a law is an act or a bill, a scheme is a government programme, an institution is a body, a group is a group of people, a role is an office.
- Use only facts that you are sure of. When a name is ambiguous, use the example names to choose the meaning.
Return each tag name exactly as given."""
SCHEMA = {"type": "array", "items": {"type": "object", "properties": {
    "tag": {"type": "string"}, "description": {"type": "string"}}, "required": ["tag", "description"]}}


def read_tsv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def parse_edit(note: str) -> dict[str, str]:
    """The `field=value` pairs of a review note. The text after `reason:` and any other part are ignored."""
    out = {}
    for part in note.split(" | "):
        m = re.match(r"^(?:keep )?(" + "|".join(FIELDS) + r")=(.*)$", part.strip())
        if m:
            out[m.group(1)] = m.group(2).strip()
    return out


def final_rows(reviews: list[dict]) -> list[dict]:
    """Each review row with the manual edit applied. A row keeps an `edited` flag."""
    out = []
    for r in reviews:
        f = {k: r.get(k, "") for k in ("decision", "tag", "name", "type", "domain")}
        f["aliases"], f["rename_tag"] = "", ""
        edited = r.get("review") == "edit"
        if edited:
            f.update(parse_edit(r.get("review_note", "")))
        out.append({**f, "edited": edited, "name_ids": r.get("name_ids", "")})
    return out


def new_tags(rows: list[dict], fills: list[dict]) -> tuple[list[dict], list[str]]:
    """One tag for each distinct name of the rows with decision `new`. Returns the tags and the problems."""
    groups: dict[str, list[dict]] = {}
    for r in rows:
        if r["decision"] == "new":
            groups.setdefault(r["name"].strip().casefold(), []).append(r)
    fill = {(f["tag"].casefold(), f["field"]): f["value"] for f in fills}
    tags, problems = [], []
    for key, rs in groups.items():
        rs = sorted(rs, key=lambda r: not r["edited"])
        name = rs[0]["name"].strip()
        tag = {"tag": name, "subtype": "", "debate_count": "0", "name_ids": [r["name_ids"] for r in rs]}
        for field in ("type", "domain"):
            if (key, field) in fill:
                tag[field] = fill[(key, field)]
                continue
            edited = {r[field] for r in rs if r["edited"] and r[field]}
            other = {r[field] for r in rs if not r["edited"] and r[field]}
            values = edited or other
            if len(values) > 1:
                problems.append(f"{name!r}: two values for {field}: {sorted(values)}")
            tag[field] = next(iter(sorted(values)), "")
            if not tag[field]:
                problems.append(f"{name!r}: no {field}")
        if tag["type"] and tag["type"] not in TYPES:
            problems.append(f"{name!r}: unknown type {tag['type']!r}")
        aliases = []
        for r in rs:
            for a in (x.strip() for x in r["aliases"].split("|") if x.strip()):
                if a.casefold() != key and a not in aliases:
                    aliases.append(a)
        tag["aliases"] = aliases
        tags.append(tag)
    return sorted(tags, key=lambda t: t["tag"].casefold()), problems


def check_domains(tags: list[dict], domains: set[str]) -> list[str]:
    return [f"{t['tag']!r}: unknown domain {t['domain']!r}" for t in tags if t["domain"] and t["domain"] not in domains]


def check_names(tags: list[dict], other_lists: list[dict]) -> list[str]:
    """other_lists: the rows of the other tag lists, with tag and aliases ("a|b" or "-"). A new name must not equal
    one of their names or aliases, after norm, or the loader cannot tell the tags apart."""
    from scripts.link_entities import norm_name
    taken = {}
    for r in other_lists:
        for n in [r["tag"], *([] if r["aliases"] in ("", "-") else r["aliases"].split("|"))]:
            taken.setdefault(norm_name(n), r["tag"])
    return [f"{t['tag']!r}: equals the name or an alias of the tag {taken[norm_name(t['tag'])]!r}"
            for t in tags if norm_name(t["tag"]) in taken]


def to_row(t: dict, description: str) -> dict:
    return {"tag": t["tag"], "type": t["type"], "subtype": t["subtype"], "domain": t["domain"] or "-",
            "description": description, "aliases": "|".join(t["aliases"]) or "-", "debate_count": t["debate_count"]}


def load_state() -> tuple[list[dict], list[str], dict[str, str]]:
    tags, problems = new_tags(final_rows(read_tsv(REVIEWS)), read_tsv(FILLS))
    descriptions = {r["tag"]: r["description"] for r in read_tsv(DESCRIPTIONS)}
    return tags, problems, descriptions


def examples(conn, tags: list[dict]) -> dict[str, list[str]]:
    from sqlalchemy import text
    out = {}
    for t in tags:
        ids = sorted({int(x) for ids in t["name_ids"] for x in ids.split()})
        rows = conn.execute(text("SELECT name FROM entity_names WHERE id = ANY(:ids) ORDER BY n_speeches DESC LIMIT :n"),
                            {"ids": ids, "n": SHOW_NAMES}).scalars().all()
        out[t["tag"]] = list(rows)
    return out


def describe(args) -> None:
    from db import get_engine
    from scripts.extract_entities import generate
    tags, problems, descriptions = load_state()
    todo = [t for t in tags if t["tag"] not in descriptions]
    print(f"{len(tags)} new tags, {len(todo)} without a description", flush=True)
    if args.limit:
        todo = todo[:args.limit]
    if args.dry_run or not todo:
        return
    with get_engine().connect() as conn:
        ex = examples(conn, todo)
    key = os.environ.get("GEMINI_API_KEY", "")
    if not key:
        raise SystemExit("GEMINI_API_KEY is not set. Add it to .env, then run: set -a && source .env && set +a")
    new = not DESCRIPTIONS.exists()
    with DESCRIPTIONS.open("a", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        if new:
            w.writerow(["tag", "description", "model"])
        for i in range(0, len(todo), BATCH):
            batch = todo[i:i + BATCH]
            body = "\n".join(f"- tag: {t['tag']} | type: {t['type']} | domain: {t['domain']} | example names from "
                             f"speeches: {'; '.join(ex[t['tag']])}" for t in batch)
            answer, tokens = generate(args.model, SYSTEM, body, key, schema=SCHEMA)
            got = {a["tag"]: " ".join(a["description"].split()) for a in answer}
            for t in batch:
                if got.get(t["tag"]):
                    w.writerow([t["tag"], got[t["tag"]], args.model])
            f.flush()
            missing = [t["tag"] for t in batch if not got.get(t["tag"])]
            print(f"  batch {i // BATCH + 1}: {len(batch) - len(missing)} described, {len(missing)} missing, "
                  f"tokens {tokens}", flush=True)


def build(args) -> None:
    from db import get_engine
    from sqlalchemy import text
    tags, problems, descriptions = load_state()
    with get_engine().connect() as conn:
        domains = {d for (d,) in conn.execute(text("SELECT DISTINCT domain FROM tags WHERE domain IS NOT NULL"))}
    problems += check_domains(tags, domains)
    problems += check_names(tags, read_tsv(ROOT / "tags" / "seed_tags_v1" / "results" / "seed_tags_v1.tsv")
                            + read_tsv(ROOT / "tags" / "places" / "results" / "place_tags.tsv"))
    problems += [f"{t['tag']!r}: no description" for t in tags if not descriptions.get(t["tag"])]
    for p in problems:
        print("  problem:", p)
    if problems:
        raise SystemExit(f"stopped: {len(problems)} problems, nothing written")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, delimiter="\t", lineterminator="\n", quoting=csv.QUOTE_NONE)
        w.writeheader()
        w.writerows(to_row(t, descriptions[t["tag"]]) for t in tags)
    print(f"{len(tags)} new tags written to {OUT}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("describe", help="ask the LLM for the missing descriptions")
    d.add_argument("--model", default=MODEL)
    d.add_argument("--dry-run", action="store_true")
    d.add_argument("--limit", type=int, help="describe at most this many tags")
    sub.add_parser("build", help="write the list of new tags, no model call")
    args = ap.parse_args()
    {"describe": describe, "build": build}[args.cmd](args)


if __name__ == "__main__":
    main()
