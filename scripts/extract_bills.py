"""Ask an LLM for the bill or bills of each government-bill debate, and what each bill does.

The script builds the input of each debate with bill_extract.build_input, calls the Gemini API once for
each debate, and gives the answer to bill_extract.check_and_store. The answers go to the tables
bill_extractions, debate_bills, and bills.

Scope: --sample N takes N random debates, spread over the six Lok Sabha terms (at most 15).
--term T --all takes every debate of one term. --all alone takes every debate.
A debate that has a row in bill_extractions is skipped. --force asks again and replaces the row.
--no-store asks every selected debate, also a debate with a row, and stores nothing. It only writes the
review file. Use it to compare a model or a prompt with the stored answers.
The prompts are in tags/bills/prompts/. --prompt v<N> picks a version. The default is the highest.

Each run writes a review file in tags/bills/results/: the input start, the answer, and the checks of
each debate. A debate with no kept bill also goes to no_bill_<date>.tsv for a manual look.

It needs GEMINI_API_KEY. Run from the repo root:

    set -a && source .env && set +a
    python3 scripts/extract_bills.py --sample 12
    python3 scripts/extract_bills.py --term 18 --all --dry-run
    python3 scripts/extract_bills.py --all --workers 8
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

import bill_extract as be
from db import get_engine
from scripts.extract_entities import ApiError, generate
from tag_embed import api_key

FOLDER = Path(__file__).resolve().parent.parent / "tags" / "bills"
PROMPTS = FOLDER / "prompts"
RESULTS = FOLDER / "results"
DEFAULT_MODEL = "gemini-3.8-flash"
MAX_SAMPLE = 15
TERMS = (13, 14, 15, 16, 17, 18)


def prompt_versions(folder: Path) -> dict[str, Path]:
    found = {}
    for path in folder.glob("v*.md"):
        if re.fullmatch(r"v\d+\.md", path.name):
            found[path.stem] = path
    return dict(sorted(found.items(), key=lambda kv: int(kv[0][1:])))


def all_debates(conn, term: int | None) -> list[tuple[int, int, int]]:
    """Every bill debate that has at least one turn, in date order."""
    rows = conn.execute(text("""
        SELECT d.loksabha, d.session, d.dbslno FROM debates d
        WHERE d.debate_type = ANY(:types) AND (CAST(:term AS int) IS NULL OR d.loksabha = :term)
          AND EXISTS (SELECT 1 FROM turns t WHERE t.debate_id = d.id)
        ORDER BY d.debate_date, d.loksabha, d.session, d.dbslno
    """), {"types": list(be.BILL_TYPES), "term": term}).all()
    return [tuple(r) for r in rows]


def spread_sample(debates: list[tuple[int, int, int]], n: int, seed: int) -> list[tuple[int, int, int]]:
    """n random debates, spread as evenly as possible over the terms. The same seed gives the same sample."""
    rng = random.Random(seed)
    by_term: dict[int, list] = {}
    for d in debates:
        by_term.setdefault(d[0], []).append(d)
    terms = sorted(by_term)
    shares = {t: n // len(terms) for t in terms}
    for t in rng.sample(terms, n % len(terms)):
        shares[t] += 1
    chosen = []
    for t in terms:
        chosen += rng.sample(by_term[t], min(shares[t], len(by_term[t])))
    return sorted(chosen)


def done_debates(conn) -> set[tuple[int, int, int]]:
    return {tuple(r) for r in conn.execute(text("SELECT loksabha, session, dbslno FROM bill_extractions")).all()}


def estimate(inputs: list[dict]) -> dict:
    words = sum(len(d["input"].split()) for d in inputs)
    return {"input": int(words * 2.0 + len(inputs) * 1200), "output": len(inputs) * 400}


def name(d: dict) -> str:
    return f"LS{d['loksabha']}-{d['session']}-{d['dbslno']}"


def review_markdown(records: list[dict], header: dict) -> str:
    out = [f"# Bill extraction review, {header['run_date']}", "",
           f"Model `{header['model']}`, prompt `{header['prompt_version']}`. {len(records)} debates, seed {header['seed']}.",
           "", "For each debate, write `ok`, or what is wrong, after `review:`.", ""]
    for i, record in enumerate(records, 1):
        debate = record["debate"]
        out += [f"## {i}. {name(debate)}: {debate['title'] or '(no title)'}", "",
                f"{debate['debate_date']}. [Source]({debate['source_url']}). {len(debate['input'].split())} input words.", ""]
        if record.get("error"):
            out += [f"**Error.** {record['error']}", "", "review: ", ""]
            continue
        answer = record["answer"]
        out += [f"**Outcome.** {answer.get('outcome')}. {answer.get('outcome_quote') or ''}", ""]
        if answer.get("none_reason"):
            out += [f"**No bill.** {answer['none_reason']}", ""]
        for bill in record["bills"]:
            status = "kept" if bill["kept"] else ("failed: " + ", ".join(bill["checks_failed"]) if bill["checks_failed"] else "not kept")
            out += [f"- **{bill['printed']}** ({bill['role']}, year {bill['year']}"
                    f"{', ordinal ' + bill['amendment_ordinal'] if bill['amendment_ordinal'] else ''}). {status}.",
                    f"  - Quote: {bill['quote']}"]
            if bill["summary"]:
                out.append(f"  - Summary: {bill['summary']}")
        if record["warnings"]:
            out += ["", "Warnings: " + "; ".join(record["warnings"])]
        out += ["", "<details><summary>Input</summary>", "", "```text", debate["input"].strip(), "```", "", "</details>",
                "", "review: ", ""]
    return "\n".join(out)


def free_path(stem: str, suffix: str) -> Path:
    path, n = RESULTS / f"{stem}{suffix}", 1
    while path.exists():
        n += 1
        path = RESULTS / f"{stem}_{n}{suffix}"
    return path


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    scope = ap.add_mutually_exclusive_group(required=True)
    scope.add_argument("--sample", type=int, help=f"random debates over the six terms, at most {MAX_SAMPLE}")
    scope.add_argument("--all", action="store_true", help="every bill debate of the scope")
    ap.add_argument("--term", type=int, help="with --all: one Lok Sabha term, for example 17")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--prompt", help="prompt version, for example v1 (default: the highest version in prompts/)")
    ap.add_argument("--workers", type=int, default=4, help="API calls at the same time (default 4)")
    ap.add_argument("--force", action="store_true", help="ask again for a debate that has a row")
    ap.add_argument("--no-store", action="store_true", help="ask every selected debate, write only the review file")
    ap.add_argument("--dry-run", action="store_true", help="print the counts and a token estimate, call no model")
    args = ap.parse_args()
    if args.sample is not None and not 1 <= args.sample <= MAX_SAMPLE:
        ap.error(f"--sample must be 1 to {MAX_SAMPLE}")
    if args.term is not None and not args.all:
        ap.error("--term needs --all")

    versions = prompt_versions(PROMPTS)
    version = args.prompt or next(reversed(versions))
    if version not in versions:
        ap.error(f"no prompt file for {version}. Known versions: {', '.join(versions)}")
    system = versions[version].read_text(encoding="utf-8")

    engine = get_engine()
    with engine.connect() as conn:
        debates = all_debates(conn, args.term)
        selected = spread_sample(debates, args.sample, args.seed) if args.sample else debates
        done = done_debates(conn)
        todo = [debate for debate in selected if args.force or args.no_store or debate not in done]
        inputs = [be.build_input(conn, debate) for debate in todo]
    est = estimate(inputs)
    print(f"{len(selected)} debates selected of {len(debates)}. Already done: {len(set(selected) & done)}"
          f"{', asked again (--force)' if args.force else ', asked again, not stored' if args.no_store else ', skipped'}. "
          f"To ask: {len(inputs)}.", flush=True)
    print(f"Prompt {version}. Estimate: about {est['input']:,} input tokens and {est['output']:,} output tokens "
          f"with {args.model}.", flush=True)
    if args.dry_run or not inputs:
        return

    key = api_key()
    records: list[dict] = []
    totals = {"input": 0, "output": 0, "thinking": 0}
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(generate, args.model, system, debate["input"], key, schema=be.SCHEMA): debate for debate in inputs}
        for fut in as_completed(futures):
            debate = futures[fut]
            try:
                answer, tokens = fut.result()
            except (ApiError, json.JSONDecodeError, KeyError, IndexError) as exc:
                print(f"  {name(debate)}: failed: {exc}", flush=True)
                records.append({"debate": debate, "error": str(exc)})
                continue
            if args.no_store:
                bills, warnings = be.check_answer(answer, debate["input"])
            else:
                with engine.begin() as conn:
                    bills, warnings = be.check_and_store(conn, debate, answer, args.model, version, tokens, replace=args.force)
            for k in totals:
                totals[k] += tokens.get(k) or 0
            kept = sum(bill["kept"] for bill in bills)
            print(f"  {name(debate)}: {len(bills)} bills, {kept} kept. {'; '.join(warnings)}", flush=True)
            records.append({"debate": debate, "answer": answer, "bills": bills, "warnings": warnings})

    records.sort(key=lambda record: (record["debate"]["loksabha"], record["debate"]["session"], record["debate"]["dbslno"]))
    RESULTS.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    review = free_path(f"review_{today}" + (f"_{args.model}_not_stored" if args.no_store else ""), ".md")
    review.write_text(review_markdown(records, {"run_date": today, "model": args.model,
                                                "prompt_version": version, "seed": args.seed}), encoding="utf-8")
    no_bill = [record for record in records if not record.get("error") and not any(bill["kept"] for bill in record["bills"])]
    if no_bill and not args.no_store:
        path = free_path(f"no_bill_{today}", ".tsv")
        lines = ["debate\ttitle\treason"] + [
            f"{name(record['debate'])}\t{record['debate']['title']}\t{record['answer'].get('none_reason') or '; '.join(record['warnings'])}"
            for record in no_bill]
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"No kept bill: {len(no_bill)} debates, in {path.relative_to(FOLDER.parent.parent)}")
    print(f"Tokens: {totals['input']:,} input, {totals['output']:,} output, {totals['thinking']:,} thinking.")
    print(f"Review: {review.relative_to(FOLDER.parent.parent)}")


if __name__ == "__main__":
    main()
