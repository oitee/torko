"""Ask an LLM for the arguments of each speech for or against its bill, through the Gemini API.

The input is one pair of a speech and a bill with the stance 'for' or 'against'. The answer lists up to 5 points.
argument_extract.check_answer checks each point against the speech text.
--sample takes random pairs with at least --min-words words. Each run writes a review file in tags/arguments/results/.
--no-store asks the model and stores nothing.

It needs GEMINI_API_KEY. Run from the repo root:

    set -a && source .env && set +a
    python3 scripts/extract_arguments.py --sample 20 --min-words 500 --model gemini-flash-lite-latest --no-store
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

import argument_extract as ae
from db import get_engine
from llm import ApiError, api_key, generate

RESULTS = Path(__file__).resolve().parent.parent / "tags" / "arguments" / "results"
MAX_SAMPLE = 20


def review(records: list[dict], model: str, version: str) -> str:
    out = [f"# Arguments review: {model}, prompt {version}, {date.today()}", ""]
    for record in records:
        item = record["item"]
        out += [f"## {item['id']} ({item['words']} words)", "", "```text", item["input"][:1200], "```", ""]
        if "error" in record:
            out += [f"FAILED: {record['error']}", ""]
            continue
        for point in record["points"]:
            out.append(f"- **{point['side']}**: {point['point']}  \n  quote{'' if point['quote_found'] else ' (NOT FOUND)'}: "
                       f"\"{point['quote']}\"")
        out += [f"- warnings: {'; '.join(record['warnings']) or '-'}", f"- tokens: {record['tokens']}", ""]
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, required=True)
    ap.add_argument("--min-words", type=int, default=0)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--model", default="gemini-3.8-flash")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--no-store", action="store_true")
    args = ap.parse_args()
    if args.sample > MAX_SAMPLE:
        ap.error(f"--sample is {MAX_SAMPLE} or less")
    version = ae.latest_prompt_version()
    system = (ae.PROMPTS / f"{version}.md").read_text(encoding="utf-8")
    engine = get_engine()
    with engine.connect() as conn:
        pairs = [point for point in conn.execute(text(ae.PAIRS_SQL)).all() if point.word_count >= args.min_words]
        picked = random.Random(args.seed).sample(pairs, args.sample)
        items = [ae.build_input(conn, point.speech_id, point.bill_id, point.stance) for point in picked]
    key = api_key()

    def one(item):
        try:
            answer, tokens = generate(args.model, system, item["input"], key, ae.SCHEMA)
        except (ApiError, json.JSONDecodeError, KeyError, IndexError) as exc:
            return {"item": item, "error": str(exc)}
        speech = item["input"].split("\nSpeech:\n", 1)[-1]
        if not args.no_store:
            with engine.begin() as conn:
                ae.store(conn, item["speech_id"], item["bill_id"], answer, args.model, version, item["input_sha256"], speech)
        points, warnings = ae.check_answer(answer, speech)
        return {"item": item, "answer": answer, "points": points, "warnings": warnings, "tokens": tokens}

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        records = list(pool.map(one, items))
    totals = {k: sum((record.get("tokens") or {}).get(k) or 0 for record in records) for k in ("input", "output", "thinking")}
    ok = [record for record in records if "error" not in record]
    pts = [point for record in ok for point in record["points"]]
    print(f"{len(ok)} of {len(records)} answered, {len(pts)} points, "
          f"{sum(not point['quote_found'] for point in pts)} quotes not found, {sum(not record['points'] for record in ok)} with no point.")
    print(f"Tokens: {totals['input']:,} input, {totals['output']:,} output, {totals['thinking']:,} thinking.")
    RESULTS.mkdir(parents=True, exist_ok=True)
    path = RESULTS / f"review_{args.model}_{version}_{date.today()}.md"
    path.write_text(review(records, args.model, version), encoding="utf-8")
    print(f"Review file: {path}")


if __name__ == "__main__":
    main()
