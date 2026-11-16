"""Group the argument points of each bill and side (argument_group.py), with direct calls to the Gemini API.

    set -a && source .env && set +a
    python3 scripts/group_arguments.py --counts                 # the lists and their sizes, no call
    python3 scripts/group_arguments.py --singles                # store the lists with one point, no call
    python3 scripts/group_arguments.py --sample 8 --seed 1      # ask the model for 8 lists, write a review file
    python3 scripts/group_arguments.py --sample 8 --store       # the same, and store the checked answers

Each list gets the grouping call. A list with argument_group.MERGE_MIN_GROUPS groups or more also gets the
join call, which joins the groups that give the same reason. Only the final groups are stored.

A sample takes lists of different sizes: one quarter from each size band. The review file goes to
tags/arguments/results/, which git does not track. A refused answer is asked again, at most --tries times.
A list whose grouping or join answer stays refused is not stored.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

import argument_group as ag
from db import get_engine

DEFAULT_MODEL = "gemini-3.8-flash"
RESULTS = ag.ROOT / "tags" / "arguments" / "results"
SCHEMA = {"type": "object", "properties": {"groups": {"type": "array", "items": {
    "type": "object", "properties": {"label": {"type": "string"}, "points": {"type": "array", "items": {"type": "integer"}}},
    "required": ["label", "points"]}}}, "required": ["groups"]}
MERGE_SCHEMA = {"type": "object", "properties": {"joins": {"type": "array", "items": {
    "type": "object", "properties": {"groups": {"type": "array", "items": {"type": "integer"}}, "label": {"type": "string"}},
    "required": ["groups", "label"]}}}, "required": ["joins"]}
BANDS = [(2, 10), (11, 40), (41, 100), (101, 10 ** 6)]


def pick_sample(lists: dict, n: int, seed: int) -> list[str]:
    rng = random.Random(seed)
    out = []
    for lo, hi in BANDS:
        keys = sorted(k for k, v in lists.items() if lo <= len(v["ids"]) <= hi)
        rng.shuffle(keys)
        out += keys[:max(1, n // len(BANDS))]
    return out[:n]


def ask(model: str, system: str, body: str, schema: dict, check, key: str, tries: int, name: str):
    """One call, asked again while check() refuses the answer. Returns (checked answer, problems, tokens)."""
    from scripts.extract_entities import generate
    problems: list[str] = []
    for _ in range(tries):
        answer, tokens = generate(model, system, body, key, schema=schema)
        out, problems = check(answer)
        if not problems:
            return out, [], tokens
        print(f"  {name}: refused ({problems[:3]}), ask again", flush=True)
    return [], problems, {}


def group_list(model: str, prompts: dict, v: dict, item: dict, key: str, tries: int) -> tuple[list[dict], list[str], list[dict] | None]:
    """The grouping call, then the join call for a list with many groups. Returns (final groups, problems, joins).
    joins is None when the list got no join call."""
    groups, problems, _ = ask(model, prompts["group"], item["input"], SCHEMA,
                              lambda a: ag.check_answer(a, item["n"]), key, tries, item["id"])
    if problems or len(groups) < ag.MERGE_MIN_GROUPS:
        return groups, problems, None
    body, merge_order = ag.build_merge_input(v["bill"], v["year"], v["side"], groups, item["order"], v["points"])
    joins, problems, _ = ask(model, prompts["merge"], body, MERGE_SCHEMA,
                             lambda a: ag.check_joins(a, len(groups)), key, tries, item["id"] + " joins")
    if problems:
        return [], problems, []
    return ag.apply_joins(groups, merge_order, joins), [], joins


def stored_version(group_version: str, merge_version: str, had_join_call: bool) -> str:
    """The prompt_version of a stored list: both prompts when the list got the join call."""
    return f"{group_version}+{merge_version}" if had_join_call else group_version


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--counts", action="store_true")
    mode.add_argument("--singles", action="store_true")
    mode.add_argument("--sample", type=int)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--prompt", default=None, help="grouping prompt version, for example group_v2")
    ap.add_argument("--merge-prompt", default=None, help="join prompt version, for example merge_v1")
    ap.add_argument("--tries", type=int, default=3)
    ap.add_argument("--store", action="store_true")
    args = ap.parse_args()
    version = args.prompt or ag.latest_prompt_version("group")
    merge_version = args.merge_prompt or ag.latest_prompt_version("merge")
    eng = get_engine()
    with eng.connect() as conn:
        lists = ag.load_lists(conn)
    sizes = sorted(len(entry["ids"]) for entry in lists.values())
    if args.counts:
        print(f"{len(lists)} lists, {sum(sizes)} points, {sum(s == 1 for s in sizes)} with one point, largest {sizes[-1]}")
        return
    if args.singles:
        with eng.begin() as conn:
            n = 0
            for entry in lists.values():
                if len(entry["ids"]) == 1:
                    body = ag.build_input(entry["bill"], entry["year"], entry["side"], [entry["points"][entry["ids"][0]]])
                    ag.store(conn, entry["bill_id"], entry["side"], entry["ids"], [{"label": entry["points"][entry["ids"][0]], "points": [1]}],
                             None, version, ag.input_hash(body))
                    n += 1
        print(f"stored {n} lists with one point")
        return
    if args.sample > 15:
        raise SystemExit("A sample has at most 15 lists. Use the batch folder for a full run.")
    from tag_embed import api_key
    import bill_extract as be
    prompts = {list_name: (ag.PROMPTS / f"{entry}.md").read_text(encoding="utf-8")
               for list_name, entry in (("group", version), ("merge", merge_version))}
    key = api_key()
    keys = pick_sample(lists, args.sample, args.seed)
    review = []
    with eng.connect() as conn:
        for list_name in keys:
            entry = lists[list_name]
            item = ag.make_input(entry, ag.load_vectors(conn, entry["ids"]))
            started = time.time()
            groups, problems, joins = group_list(args.model, prompts, entry, item, key, args.tries)
            print(f"{list_name}: {item['n']} points -> {len(groups)} groups, {len(joins or [])} joins, "
                  f"{time.time() - started:.0f}s", flush=True)
            review.append({"list": list_name, "bill": f"{entry['bill']}, {entry['year']}", "side": entry["side"], "n": item["n"],
                           "problems": problems, "joins": [join["label"] for join in joins or []],
                           "groups": [{"label": group["label"],
                                       "points": [entry["points"][item["order"][n - 1]] for n in group["points"]]}
                                      for group in groups]})
            if args.store and not problems:
                with eng.begin() as write_conn:
                    ag.store(write_conn, entry["bill_id"], entry["side"], item["order"], groups, be.model_id(write_conn, args.model),
                             stored_version(version, merge_version, joins is not None), item["input_sha256"])
    RESULTS.mkdir(parents=True, exist_ok=True)
    out = RESULTS / f"groups_{version}_{merge_version}_{args.model}_s{args.seed}.json"
    out.write_text(json.dumps(review, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"review file: {out}")


if __name__ == "__main__":
    main()
