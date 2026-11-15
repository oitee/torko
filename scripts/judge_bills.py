"""Step 4 of the bill step: ask the decision model if the House considers each bill name in its debate.

The extraction model gives each bill name the role "moved" or "mentioned". This step checks that role. For each
debate, the decision model reads the same input text as the extraction model (bill_extract.build_input). It
answers one question for each name that passed the script checks: moved, mentioned, or unsure.
A name is kept when "moved" has a probability of KEEP_P or more. The decision model has the final word:
- the extraction says moved, and the decision model does not reach KEEP_P: the name is not kept.
- the extraction says mentioned, and the decision model reaches KEEP_P: the name is kept, with no summary.

The answers go to debate_bills.judge_role_p (moved, mentioned, unsure) and debate_bills.judged_by.
A name that the current model and question version judged is skipped. --force judges it again.
--rethreshold computes `kept` again from the stored probabilities and calls no model.
Each run with model calls writes a review file in tags/bills/results/.

It needs TYPESAFE_API_KEY. Run from the repo root:

    set -a && source .env && set +a
    python3 scripts/judge_bills.py --only 18-7-5634,13-3-225 --dry-run
    python3 scripts/judge_bills.py --sample 12
    python3 scripts/judge_bills.py --all --workers 8
    python3 scripts/judge_bills.py --rethreshold --keep-p 0.6
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

import bill_extract as be
from db import get_engine
from decision_model import MODEL, DecisionError, StateTooLong, api_key, choice_probabilities, choice_q, decide, sum_is_off

RESULTS = Path(__file__).resolve().parent.parent / "tags" / "bills" / "results"
QUESTIONS_VERSION = "b4"
KEEP_P = 0.7
ROLES = {
    "moved": "This bill is before the House in this debate. A member moves a motion on it in this debate (to "
             "introduce it, to take it into consideration, to pass it, to withdraw it, or to agree to amendments "
             "to it), or the House continues the discussion of such a motion from an earlier day. It counts even "
             "when the debate stops before a vote.",
    "mentioned": "A speaker only names it. This includes the existing Act that a bill of this debate amends or "
                 "repeals: that Act is mentioned, not moved, because the motion is on the bill and not on the Act. "
                 "It also includes an earlier law, and a bill of another debate.",
    "unsure": "The text does not show if this bill is before the House in this debate.",
}


def judged_by(model: str = MODEL, questions: str = QUESTIONS_VERSION) -> str:
    return f"{model} {questions}"


def question_key(row_id: int) -> str:
    return f"role_{row_id}"


def questions_for(names: list[dict]) -> dict[str, dict]:
    """One choice question for each name. names holds the debate_bills id and the printed name."""
    return {question_key(n["id"]): choice_q(f"Is «{n['printed']}» a bill that is before the House in this debate?", ROLES)
            for n in names}


def role_p(answer: dict) -> list[float]:
    """The probabilities in the order of judge_role_p: moved, mentioned, unsure."""
    probs = choice_probabilities(answer, list(ROLES))
    return [probs[r] for r in ROLES]


def keep(checks_failed: list[str], p: list[float] | None, keep_p: float = KEEP_P) -> bool:
    """A name is kept when it passed the script checks and "moved" reaches keep_p."""
    return not checks_failed and p is not None and p[0] >= keep_p


def scope_rows(conn, keys: list[tuple[int, int, int]] | None, force: bool) -> dict[tuple, list[dict]]:
    """The names to judge, grouped by debate. Only the names that passed the script checks."""
    rows = conn.execute(text("""
        SELECT d.id, d.loksabha, d.session, d.dbslno, d.printed, d.extracted_role, d.judged_by
        FROM debate_bills d
        WHERE d.checks_failed = '{}'
        ORDER BY d.loksabha, d.session, d.dbslno, d.position
    """)).mappings().all()
    wanted = set(keys) if keys is not None else None
    out: dict[tuple, list[dict]] = {}
    for r in rows:
        key = (r["loksabha"], r["session"], r["dbslno"])
        if wanted is not None and key not in wanted:
            continue
        if not force and r["judged_by"] == judged_by():
            continue
        out.setdefault(key, []).append(dict(r))
    return out


def all_judged_keys(conn) -> list[tuple[int, int, int]]:
    rows = conn.execute(text("SELECT DISTINCT loksabha, session, dbslno FROM debate_bills WHERE checks_failed = '{}'")).all()
    return sorted(tuple(r) for r in rows)


def store(conn, debate: dict, names: list[dict], answers: dict, keep_p: float) -> tuple[int, list[str]]:
    """Writes the probabilities and the keep decision of each name. Returns the kept count and the warnings."""
    checked = None   # the checked answer of the debate, read only when a name needs a new bills row
    kept_n, warnings = 0, []
    for name in names:
        probs = role_p(answers[question_key(name["id"])])
        if sum_is_off(probs):
            warnings.append(f"{name['printed']!r}: probabilities sum to {sum(probs):.3f}")
        kept = keep([], probs, keep_p)
        # A name that is not kept keeps its bill row, so that --rethreshold can keep it again with no call.
        bid = conn.execute(text("SELECT bill_id FROM debate_bills WHERE id = :id"), {"id": name["id"]}).scalar()
        if kept:
            if bid is None:
                if checked is None:
                    raw = conn.execute(text("SELECT e.raw FROM bill_extractions e JOIN debate_bills d "
                                            "ON d.extraction_id = e.id WHERE d.id = :id"), {"id": name["id"]}).scalar()
                    checked, _ = be.check_answer(raw, debate["input"])
                match = [bill for bill in checked if bill["printed"] == name["printed"] and bill["bill_key"]]
                if match:
                    bid = be.bill_id(conn, match[0], debate["loksabha"])
                else:
                    kept = False
                    warnings.append(f"{name['printed']!r}: no bill key, not kept")
        conn.execute(text("""
            UPDATE debate_bills SET judge_role_p = :p, judged_by = :by, kept = :k, bill_id = :bid WHERE id = :id
        """), {"p": probs, "by": judged_by(), "k": kept, "bid": bid, "id": name["id"]})
        kept_n += kept
    return kept_n, warnings


def delete_unused_bills(conn) -> int:
    return conn.execute(text("""
        DELETE FROM bills b
        WHERE NOT EXISTS (SELECT 1 FROM debate_bills d WHERE d.bill_id = b.id)
          AND NOT EXISTS (SELECT 1 FROM bills x WHERE x.merged_into = b.id)
    """)).rowcount


def rethreshold(conn, keep_p: float) -> dict[str, int]:
    rows = conn.execute(text("SELECT id, checks_failed, judge_role_p, kept FROM debate_bills "
                             "WHERE judge_role_p IS NOT NULL")).mappings().all()
    changed = 0
    for row in rows:
        kept = keep(list(row["checks_failed"]), list(row["judge_role_p"]), keep_p)
        if kept != row["kept"]:
            changed += 1
            if kept and conn.execute(text("SELECT bill_id FROM debate_bills WHERE id = :id"), {"id": row["id"]}).scalar() is None:
                print(f"  row {row['id']}: now kept, but it has no bill row. Judge it again with --force.")
                continue
            conn.execute(text("UPDATE debate_bills SET kept = :k WHERE id = :id"), {"k": kept, "id": row["id"]})
    return {"judged": len(rows), "changed": changed}


def review_markdown(records: list[dict], header: dict) -> str:
    out = [f"# Bill role review (decision model), {header['run_date']}", "",
           f"Model `{header['model']}`, questions `{QUESTIONS_VERSION}`, keep when moved >= {header['keep_p']}. "
           f"{len(records)} debates.", "",
           "| Debate | Bill | Extraction role | moved | mentioned | unsure | Kept |", "|---|---|---|---|---|---|---|"]
    for r in records:
        for n in r["names"]:
            p = n.get("p") or [None, None, None]
            cells = [f"{x:.2f}" if x is not None else "-" for x in p]
            out.append(f"| {r['name']} | {n['printed'].replace('|', '/')} | {n['extracted_role']} | "
                       f"{' | '.join(cells)} | {'yes' if n.get('kept') else 'no'} |")
    return "\n".join(out) + "\n"


def parse_only(value: str) -> list[tuple[int, int, int]]:
    return [tuple(int(x) for x in part.strip().split("-")) for part in value.split(",")]


def judge_debate(conn_factory, key: tuple, names: list[dict], api: str) -> tuple[dict, dict]:
    with conn_factory() as conn:
        debate = be.build_input(conn, key)
    return debate, decide(debate["input"], questions_for(names), api)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    scope = ap.add_mutually_exclusive_group(required=True)
    scope.add_argument("--all", action="store_true", help="every debate with a name that passed the checks")
    scope.add_argument("--sample", type=int, help="random debates, at most 15")
    scope.add_argument("--only", help="a list of debates, for example 18-7-5634,13-3-225")
    scope.add_argument("--rethreshold", action="store_true", help="compute kept again from the stored answers")
    ap.add_argument("--keep-p", type=float, default=KEEP_P)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--force", action="store_true", help="judge again a name that this version judged")
    ap.add_argument("--dry-run", action="store_true", help="print the counts and a token estimate, call no model")
    args = ap.parse_args()
    if args.sample is not None and not 1 <= args.sample <= 15:
        ap.error("--sample must be 1 to 15")

    engine = get_engine()
    if args.rethreshold:
        with engine.begin() as conn:
            counts = rethreshold(conn, args.keep_p)
            counts["unused bills deleted"] = delete_unused_bills(conn)
        print(", ".join(f"{debate_key}: {v}" for debate_key, v in counts.items()))
        return

    with engine.connect() as conn:
        keys = None
        if args.only:
            keys = parse_only(args.only)
        elif args.sample:
            keys = sorted(random.Random(args.seed).sample(all_judged_keys(conn), args.sample))
        todo = scope_rows(conn, keys, args.force)
        words = sum(len(be.build_input(conn, debate_key)["input"].split()) for debate_key in list(todo)[:50])
    est_words = words * len(todo) / max(1, min(50, len(todo)))
    print(f"{len(todo)} debates, {sum(len(v) for v in todo.values())} names to judge. "
          f"Estimate: about {int(est_words * 2):,} input tokens with {MODEL}.", flush=True)
    if args.dry_run or not todo:
        return

    key_ = api_key()
    records, kept_total, failed = [], 0, 0
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(judge_debate, engine.connect, debate_key, names, key_): (debate_key, names) for debate_key, names in todo.items()}
        for fut in as_completed(futures):
            debate_key, names = futures[fut]
            label = f"LS{debate_key[0]}-{debate_key[1]}-{debate_key[2]}"
            try:
                debate, data = fut.result()
            except (StateTooLong, DecisionError) as exc:
                failed += 1
                print(f"  {label}: failed: {str(exc)[:200]}", flush=True)
                continue
            with engine.begin() as conn:
                kept_n, warnings = store(conn, debate, names, data["answers"], args.keep_p)
            kept_total += kept_n
            for n in names:
                n["p"] = role_p(data["answers"][question_key(n["id"])])
                n["kept"] = keep([], n["p"], args.keep_p)
            records.append({"name": label, "names": names})
            print(f"  {label}: {len(names)} names, {kept_n} kept. {'; '.join(warnings)}", flush=True)
    with engine.begin() as conn:
        unused = delete_unused_bills(conn)
    records.sort(key=lambda r: r["name"])
    RESULTS.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    path = RESULTS / f"judge_{today}.md"
    n = 1
    while path.exists():
        n += 1
        path = RESULTS / f"judge_{today}_{n}.md"
    path.write_text(review_markdown(records, {"run_date": today, "model": MODEL, "keep_p": args.keep_p}), encoding="utf-8")
    print(f"Judged {len(records)} debates, {kept_total} names kept, {failed} failed calls. "
          f"Unused bills deleted: {unused}. Review: {path.relative_to(RESULTS.parent.parent.parent)}")


if __name__ == "__main__":
    main()
