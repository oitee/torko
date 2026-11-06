"""Score /api/ask on the questions of tags/ask_eval/questions_v1.jsonl.

A question is correct when the answer holds each filter of the line, with the same values, and no other filter.
A filter in "optional" may be there or not. For a filter of the line, the optional value is also correct. The search words (q) do not count.
--rules scores the rules alone, with no LLM call. Without it, the LLM is used where the rules ask for it,
and each call counts against the daily limit.

    source .venv/bin/activate && set -a && source .env && set +a
    python3 scripts/ask_eval.py --rules
    python3 scripts/ask_eval.py
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pages.ask import ask  # noqa: E402
from pages.common import engine  # noqa: E402

QUESTIONS = Path(__file__).resolve().parent.parent / "tags" / "ask_eval" / "questions_v1.jsonl"


def values(v):
    return sorted(str(v).split(","))


def correct(params, gold, optional):
    """Return (True, "") or (False, the first difference)."""
    got = {k: v for k, v in params.items() if k != "q"}
    for k, v in gold.items():
        also = k in optional and values(got.get(k, "")) == values(optional[k])
        if values(got.get(k, "")) != values(v) and not also:
            return False, f"{k}: wanted {v}, got {got.get(k)}"
    for k, v in got.items():
        if k not in gold and not (k in optional and values(v) == values(optional[k])):
            return False, f"{k}: not wanted, got {v}"
    return True, ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rules", action="store_true", help="the rules alone, with no LLM call")
    ap.add_argument("--file", default=str(QUESTIONS), help="a file of questions, one JSON object per line")
    args = ap.parse_args()
    rows = [json.loads(line) for line in Path(args.file).open() if line.strip()]
    by_lang = {}
    with engine().connect() as conn:
        for r in rows:
            out = ask(conn, r["question"], use_llm=not args.rules)
            ok, why = correct(out["params"], r["filters"], r.get("optional", {}))
            n, good = by_lang.get(r["lang"], (0, 0))
            by_lang[r["lang"]] = (n + 1, good + ok)
            mark = "ok  " if ok else "FAIL"
            print(f"{mark} {r['id']} [{out['llm']}] {r['question']}")
            if not ok:
                print(f"       {why} | q={out['params'].get('q', '')!r}")
    total = sum(n for n, _ in by_lang.values())
    good = sum(g for _, g in by_lang.values())
    print(f"\ncorrect {good} of {total} ({100 * good / total:.0f}%)")
    for lang, (n, g) in sorted(by_lang.items()):
        print(f"  {lang}: {g} of {n}")


if __name__ == "__main__":
    main()
