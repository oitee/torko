"""Group the argument points of each bill and side (argument_group.py), with direct calls to the Gemini API.

    set -a && source .env && set +a
    python3 scripts/group_arguments.py --counts                 # the lists and their sizes, no call
    python3 scripts/group_arguments.py --singles                # store the lists with one point, no call
    python3 scripts/group_arguments.py --sample 8 --seed 1      # ask the model for 8 lists, write a review file
    python3 scripts/group_arguments.py --sample 8 --store       # the same, and store the checked answers

A sample takes lists of different sizes: one quarter from each size band. The review file goes to
tags/arguments/results/, which git does not track. A list with a refused answer is asked again, at most
--tries times.
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
BANDS = [(2, 10), (11, 40), (41, 100), (101, 10 ** 6)]


def pick_sample(lists: dict, n: int, seed: int) -> list[str]:
    rng = random.Random(seed)
    out = []
    for lo, hi in BANDS:
        keys = sorted(k for k, v in lists.items() if lo <= len(v["ids"]) <= hi)
        rng.shuffle(keys)
        out += keys[:max(1, n // len(BANDS))]
    return out[:n]


def ask(model: str, system: str, item: dict, key: str, tries: int) -> tuple[list[dict], list[str], dict, int]:
    from scripts.extract_entities import generate
    problems: list[str] = []
    for attempt in range(1, tries + 1):
        answer, tokens = generate(model, system, item["input"], key, schema=SCHEMA)
        groups, problems = ag.check_answer(answer, item["n"])
        if not problems:
            return groups, [], tokens, attempt
        print(f"  {item['id']}: refused ({problems[:3]}), ask again", flush=True)
    return [], problems, {}, tries


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--counts", action="store_true")
    mode.add_argument("--singles", action="store_true")
    mode.add_argument("--sample", type=int)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--prompt", default=None, help="prompt version, for example group_v1")
    ap.add_argument("--tries", type=int, default=3)
    ap.add_argument("--store", action="store_true")
    args = ap.parse_args()
    version = args.prompt or ag.latest_prompt_version()
    eng = get_engine()
    with eng.connect() as conn:
        lists = ag.load_lists(conn)
    sizes = sorted(len(entry["ids"]) for entry in lists.values())
    if args.counts:
        print(f"{len(lists)} lists, {sum(sizes)} points, {sum(s == 1 for s in sizes)} with one point, largest {sizes[-1]}")
        return
    if args.singles:
        import bill_extract as be  # noqa: F401
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
    system = (ag.PROMPTS / f"{version}.md").read_text(encoding="utf-8")
    key = api_key()
    keys = pick_sample(lists, args.sample, args.seed)
    review = []
    with eng.connect() as conn:
        for list_name in keys:
            entry = lists[list_name]
            item = ag.make_input(entry, ag.load_vectors(conn, entry["ids"]))
            started = time.time()
            groups, problems, tokens, tries = ask(args.model, system, item, key, args.tries)
            print(f"{list_name}: {item['n']} points -> {len(groups)} groups, tries {tries}, {time.time() - started:.0f}s, "
                  f"tokens {tokens.get('total', tokens)}", flush=True)
            review.append({"list": list_name, "bill": f"{entry['bill']}, {entry['year']}", "side": entry["side"], "n": item["n"],
                           "problems": problems, "tokens": tokens,
                           "groups": [{"label": group["label"],
                                       "points": [entry["points"][item["order"][n - 1]] for n in group["points"]]}
                                      for group in groups]})
            if args.store and not problems:
                with eng.begin() as write_conn:
                    ag.store(write_conn, entry["bill_id"], entry["side"], item["order"], groups, be.model_id(write_conn, args.model), version,
                             item["input_sha256"])
    RESULTS.mkdir(parents=True, exist_ok=True)
    out = RESULTS / f"groups_{version}_{args.model}_s{args.seed}.json"
    out.write_text(json.dumps(review, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"review file: {out}")


if __name__ == "__main__":
    main()
