#!/usr/bin/env python3
"""Compare the model's answers with a baseline, by probability band. Reads only.

    python3 scripts/compare_label_answers.py --baseline a,b --out disagreements.tsv
A later baseline name wins over an earlier one for the same label.
"""
from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sqlalchemy import text  # noqa: E402

from db import get_engine  # noqa: E402

BANDS = [(1.0, 1.01), (0.95, 1.0), (0.9, 0.95), (0.8, 0.9), (0.7, 0.8), (0.5, 0.7), (0.0, 0.5)]


def same_answer(a: str, b: str, rajya_sabha_of: dict[str, str]) -> bool:
    """A person in Torko and the same person's row on the Rajya Sabha list are one answer."""
    return rajya_sabha_of.get(a, a) == rajya_sabha_of.get(b, b)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--out")
    args = ap.parse_args()
    deciders = args.baseline.split(",")
    with get_engine().connect() as conn:
        rows = conn.execute(text("SELECT loksabha, speaker_label, decided_by, answer, probability FROM label_resolutions")).all()
        words = {(r.term, " ".join((r.label or "").split())): int(r.words) for r in conn.execute(text(
            "SELECT d.loksabha AS term, t.speaker_label AS label, coalesce(sum(t.word_count),0) AS words FROM turns t "
            "JOIN debates d ON d.id = t.debate_id WHERE t.person_id IS NULL AND t.role_id IS NULL GROUP BY 1, 2"))}
        linked = {f"P{r.id}": f"RS{r.rajya_sabha_id}" for r in conn.execute(text(
            "SELECT id, rajya_sabha_id FROM persons WHERE rajya_sabha_id IS NOT NULL"))}
        names = {f"P{r.id}": r.name for r in conn.execute(text("SELECT id, name FROM persons"))}
    baseline: dict[tuple, str] = {}
    model: dict[tuple, tuple] = {}
    for d in deciders:
        baseline.update({(r.loksabha, r.speaker_label): r.answer for r in rows if r.decided_by == d})
    for r in rows:
        if r.decided_by == "decision-model":
            model[(r.loksabha, r.speaker_label)] = (r.answer, r.probability)
        elif r.decided_by == "rule":  # A rule has no probability, so it shows in the top band.
            model.setdefault((r.loksabha, r.speaker_label), (r.answer, 1.0))
    table = defaultdict(lambda: [0, 0, 0, 0])
    out = []
    for key, (answer, p) in model.items():
        if key not in baseline:
            continue
        band = next(b for b in BANDS if b[0] <= p < b[1])
        agree = same_answer(answer, baseline[key], linked)
        w = words.get(key, 0)
        cell = table[band]
        cell[0 if agree else 1] += 1
        cell[2 if agree else 3] += w
        if not agree:
            out.append([key[0], key[1], w, baseline[key], names.get(baseline[key], ""), answer, names.get(answer, ""), round(p, 3)])
    print("band       agree  differ  words agree  words differ")
    for band in BANDS:
        c = table[band]
        print(f"{band[0]:.2f}-{min(band[1], 1):.2f}  {c[0]:5d}  {c[1]:6d}  {c[2]:11,d}  {c[3]:12,d}")
    print(f"Compared: {sum(c[0] + c[1] for c in table.values())}. Differ: {len(out)}.")
    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f, delimiter="\t", lineterminator="\n")
            w.writerow(["term", "label", "words", "baseline", "baseline_name", "model", "model_name", "probability"])
            w.writerows(sorted(out, key=lambda r: -r[2]))


if __name__ == "__main__":
    main()
