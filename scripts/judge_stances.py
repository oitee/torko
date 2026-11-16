"""Ask the decision model for the stance of each speech on each kept bill of its debate.

Two modes:
- --test-set FILE: a TSV with the columns speech_id, bill_id and expected (for, against, mixed, unclear).
  It writes nothing to the database. It writes a review file in tags/stance/results/ and prints the score.
- --all: every pair of a speech and a kept bill. It writes one row of speech_stances for each pair.
  A pair with a row of the current question version is skipped, so a stopped run can start again.
  The run stops after --max-failures failed calls in a row, or when the input tokens reach --max-tokens.

When a speech is too long for the model, the state holds the summary of the speech in its place.

It needs TYPESAFE_API_KEY. Run from the repo root:

    set -a && source .env && set +a
    python3 scripts/judge_stances.py --test-set tags/stance/data/test_set_v1.tsv
    python3 scripts/judge_stances.py --all --dry-run
    python3 scripts/judge_stances.py --all --workers 12 --max-tokens 55000000
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import stance as st
from db import get_engine
from sqlalchemy import text

from decision_model import MODEL, DecisionError, StateTooLong, api_key, decide

RESULTS = Path(__file__).resolve().parent.parent / "tags" / "stance" / "results"
# Measured on the 42 pairs of the first test: 93,491 input tokens for 30,655 words of speech.
TOKENS_PER_WORD = 3.05


def ask(pair: dict, key: str) -> dict:
    qs = st.questions(pair["bill"])
    try:
        data, kind = decide(st.state(pair, pair["text"]), qs, key), "speech"
    except StateTooLong:
        if not pair["speech_summary"]:
            raise
        data, kind = decide(st.state(pair, pair["speech_summary"], "summary"), qs, key), "summary"
    out = st.parse(data["answers"])
    out.update(state_source=kind, tokens=(data.get("usage") or {}).get("input_tokens") or 0)
    return out


def expected_level(probs: list[float], levels: list[str]) -> str:
    return levels[max(range(len(levels)), key=lambda i: probs[i])]


def store(conn, pair: dict, a: dict, limit: float) -> None:
    conn.execute(text("""
        INSERT INTO speech_stances (speech_id, bill_id, loksabha, session, dbslno, question_version, model,
                                    state_source, stance_p, stance, reasons_p, on_bill_p, tokens)
        VALUES (:sid, :bid, :ls, :se, :no, :v, :m, :src, :sp, :st, :rp, :op, :tok)
        ON CONFLICT (speech_id, bill_id) DO UPDATE SET question_version = EXCLUDED.question_version,
            model = EXCLUDED.model, state_source = EXCLUDED.state_source, stance_p = EXCLUDED.stance_p,
            stance = EXCLUDED.stance, reasons_p = EXCLUDED.reasons_p, on_bill_p = EXCLUDED.on_bill_p,
            tokens = EXCLUDED.tokens, judged_at = now()"""),
        {"sid": pair["speech_id"], "bid": pair["bill_id"], "ls": pair["loksabha"], "se": pair["session"], "no": pair["dbslno"],
         "v": st.QUESTIONS_VERSION, "m": MODEL, "src": a["state_source"],
         "sp": [a["stance_p"][s] for s in st.STANCES], "st": st.pick_stance(a["stance_p"], limit),
         "rp": a["reasons_p"], "op": a["on_bill_p"], "tok": a["tokens"]})


def run_all(args) -> None:
    engine = get_engine()
    with engine.connect() as conn:
        pairs = conn.execute(text(st.PAIRS_SQL)).all()
        done = set(conn.execute(text("SELECT speech_id, bill_id FROM speech_stances WHERE question_version = :v"),
                                {"v": st.QUESTIONS_VERSION}).all())
    todo = [pair_row for pair_row in pairs if (pair_row.speech_id, pair_row.bill_id) not in done][:args.first]
    words = sum(pair_row.word_count for pair_row in todo)
    print(f"{len(pairs):,} pairs, {len(done):,} done, {len(todo):,} to ask, {words:,} words. "
          f"Estimate: about {int(words * TOKENS_PER_WORD):,} input tokens.", flush=True)
    if args.dry_run or not todo:
        return
    key = api_key()

    def one(pair_row):
        with engine.connect() as conn:
            pair = st.load_pair(conn, pair_row.speech_id, pair_row.bill_id)
        answer = ask(pair, key)
        with engine.begin() as conn:
            store(conn, pair, answer, args.limit)
        return answer["tokens"], answer["state_source"]

    tokens, stored, fails, in_row, summaries, stop = 0, 0, 0, 0, 0, ""
    for start in range(0, len(todo), 500):
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = [pool.submit(one, pair_row) for pair_row in todo[start:start + 500]]
            for f in as_completed(futures):
                try:
                    used, src = f.result()
                    tokens, stored, in_row, summaries = tokens + used, stored + 1, 0, summaries + (src == "summary")
                except (DecisionError, ValueError) as exc:
                    fails, in_row = fails + 1, in_row + 1
                    print(f"  failed: {str(exc)[:200]}", flush=True)
                    if in_row >= args.max_failures:
                        stop = f"{in_row} failed calls in a row"
        print(f"  {stored:,} stored, {fails} failed, {tokens:,} input tokens", flush=True)
        if not stop and tokens >= args.max_tokens:
            stop = f"the input tokens reached {tokens:,}"
        if stop:
            print(f"STOP: {stop}. The pairs not reached stay unjudged. Run again to continue.", flush=True)
            break
    print(f"Done: {stored:,} stored, {fails} failed, {summaries} with the speech summary, {tokens:,} input tokens.")


def main() -> None:
    ap = argparse.ArgumentParser()
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--test-set")
    mode.add_argument("--all", action="store_true")
    ap.add_argument("--max-tokens", type=int, default=55_000_000)
    ap.add_argument("--max-failures", type=int, default=5)
    ap.add_argument("--first", type=int, default=None, help="with --all: ask only the first N pairs that are not done")
    ap.add_argument("--limit", type=float, default=st.STANCE_P, help="the lowest probability for a stance")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--dry-run", action="store_true", help="print the first state and the word count, call no model")
    args = ap.parse_args()
    if args.all:
        run_all(args)
        return

    with open(args.test_set, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    with get_engine().connect() as conn:
        pairs = [st.load_pair(conn, int(row["speech_id"]), int(row["bill_id"])) | {"expected": row["expected"],
                 "case": row.get("case", "")} for row in rows]
    words = sum(pair["words"] for pair in pairs)
    print(f"{len(pairs)} pairs, {words:,} words of speech, questions {st.QUESTIONS_VERSION}", flush=True)
    if args.dry_run:
        print(st.state(pairs[0], pairs[0]["text"])[:1500])
        print(json.dumps(st.questions(pairs[0]["bill"]), indent=1, ensure_ascii=False))
        return

    key = api_key()
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        answers = list(pool.map(lambda pair: ask(pair, key), pairs))

    RESULTS.mkdir(parents=True, exist_ok=True)
    out = RESULTS / f"test_{Path(args.test_set).stem}_{st.QUESTIONS_VERSION}_{date.today()}.tsv"
    right, confusion, tokens = 0, Counter(), 0
    with open(out, "w", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(["speech_id", "bill_id", "debate", "member", "words", "case", "expected", "got", "ok",
                    *[f"p_{s}" for s in st.STANCES], "reasons", "on_bill", "state", "bill"])
        for pair, answer in zip(pairs, answers):
            got = st.pick_stance(answer["stance_p"], args.limit)
            ok = got == pair["expected"]
            right += ok
            confusion[(pair["expected"], got)] += 1
            tokens += answer["tokens"]
            writer.writerow([pair["speech_id"], pair["bill_id"], pair["debate"], pair["member"], pair["words"], pair["case"],
                        pair["expected"], got, "yes" if ok else "NO", *[f"{answer['stance_p'][s]:.2f}" for s in st.STANCES],
                        expected_level(answer["reasons_p"], st.REASON_LEVELS),
                        expected_level(answer["on_bill_p"], st.ON_BILL_LEVELS), answer["state_source"], pair["bill"]])
    print(f"\n{right} of {len(pairs)} correct at limit {args.limit}. {tokens:,} input tokens with {MODEL}.")
    print("expected -> got: " + ", ".join(f"{e}->{g} {n}" for (e, g), n in sorted(confusion.items()) if e != g))
    print(f"Review file: {out}")


if __name__ == "__main__":
    main()
