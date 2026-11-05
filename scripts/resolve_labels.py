#!/usr/bin/env python3
"""Find the person behind each unnamed speaker label, and store each answer in label_resolutions.

A run is safe to repeat. It skips a label with a stored answer for the same prompt and options.

    set -a && source .env && set +a
    python3 scripts/resolve_labels.py --terms-labels cases.tsv --dry-run
    python3 scripts/resolve_labels.py --terms-labels cases.tsv
"""
from __future__ import annotations

import argparse
import csv
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from db import get_engine  # noqa: E402
from decision_model import MODEL, api_key, decide  # noqa: E402
from identity import gate, resolver, store  # noqa: E402
from identity.pacing import Pace  # noqa: E402
from identity.plan import plan_all  # noqa: E402


def selected(rows, path):
    if not path:
        return rows
    with open(path, encoding="utf-8", newline="") as f:
        wanted = {(int(r["term"]), " ".join(r["label"].split())) for r in csv.DictReader(f, delimiter="\t")}
    picked = [r for r in rows if (r.term, r.label) in wanted]
    missing = wanted - {(r.term, r.label) for r in picked}
    if missing:
        print(f"{len(missing)} listed labels are not unnamed now.", flush=True)
    return picked


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--terms-labels", help="a TSV file with columns term and label")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--per-second", type=float, default=13)
    ap.add_argument("--limit", type=float, default=gate.DEFAULT_LIMIT)
    ap.add_argument("--max-options", type=int, default=30, help="people in one question; tokens grow with this")
    ap.add_argument("--outside-options", type=int, default=10)
    ap.add_argument("--max-tokens", type=int, help="stop when the input tokens of this run reach this number")
    ap.add_argument("--max-failures", type=int, default=5, help="stop after this many failed calls in a row")
    ap.add_argument("--dry-run", action="store_true", help="build the options, call no model, store nothing")
    args = ap.parse_args()

    engine = get_engine()
    with engine.connect() as conn:
        rows = selected(store.unnamed_labels(conn), args.terms_labels)
        seated, outside = store.load_entries(conn)
        done = store.stored_hashes(conn, resolver.DECIDED_BY, resolver.PROMPT_VERSION)
    names = {e.key: e.name for e in outside}
    for term_entries in seated.values():
        names.update({e.key: e.name for e in term_entries})

    jobs, instant = [], []
    for plan in plan_all(rows, seated, outside, (args.max_options, args.outside_options)):
        if plan.answer:
            instant.append((plan.row, plan.parsed, plan.answer, plan.options))
        elif done.get((plan.row.term, plan.row.label)) != resolver.options_hash(plan.options):
            jobs.append((plan.row, plan.parsed, plan.options))
    jobs.sort(key=lambda job: -job[0].words)  # If the budget ends, the largest labels are done.
    print(f"{len(rows)} labels. By rule: {len(instant)}. For the model: {len(jobs)}.", flush=True)
    if args.dry_run:
        return

    with engine.begin() as conn:
        for row, parsed, answer, options in instant:
            status = gate.judge(answer, parsed, names.get(answer.key, ""), args.limit)
            store.save(conn, row, answer, status, len(options), resolver.options_hash(options), "rule_v1")

    key = api_key()
    pace = Pace(args.per_second)

    def call(state: str, questions: dict) -> dict:
        pace.wait()
        return decide(state, questions, key)

    def work(job):
        row, parsed, options = job
        return job, resolver.resolve(row, options, call)

    failed = finished = tokens = in_a_row = 0
    stop = ""
    with ThreadPoolExecutor(args.workers) as pool:
        futures = [pool.submit(work, job) for job in jobs]
        for future in as_completed(futures):
            try:
                (row, parsed, options), answer = future.result()
            except Exception as exc:  # One failed label must not stop the run. A repeat run retries it.
                failed += 1
                in_a_row += 1
                print(f"failed: {exc}", flush=True)
                if in_a_row >= args.max_failures:
                    stop = f"{in_a_row} failed calls in a row"
                    pool.shutdown(wait=False, cancel_futures=True)
                    break
                continue
            in_a_row = 0
            tokens += answer.tokens
            status = gate.judge(answer, parsed, names.get(answer.key, ""), args.limit)
            with engine.begin() as conn:
                store.save(conn, row, answer, status, len(options), resolver.options_hash(options), resolver.PROMPT_VERSION)
            finished += 1
            if finished % 100 == 0:
                print(f"{finished} of {len(jobs)}, {tokens:,} input tokens", flush=True)
            if args.max_tokens and tokens >= args.max_tokens:
                stop = f"the input tokens reached {tokens:,}"
                pool.shutdown(wait=False, cancel_futures=True)
                break
    print(f"Done. Model: {MODEL}. Answers: {finished} of {len(jobs)}. Failed: {failed}. Input tokens: {tokens:,}. "
          f"Stopped because: {stop or 'nothing, the run finished'}.", flush=True)


if __name__ == "__main__":
    main()
