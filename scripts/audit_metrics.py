"""
Measure the corpus against the audit's headline numbers (internal_docs/036).

One script, one job: print the same set of numbers before and after a fix so a
regression is visible as a number that moved the wrong way. Every metric names
what it is counted OVER, because this project has repeatedly been bitten by a
check that reported confidently while measuring nothing (see CLAUDE.md).

Usage:
    python3 -u scripts/audit_metrics.py                 # print a table
    python3 -u scripts/audit_metrics.py --json out.json # machine-readable snapshot
    python3 -u scripts/audit_metrics.py --compare before.json   # show deltas
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from db import get_engine

# Each metric: key -> (human label, SQL returning ONE number, "direction")
# direction: "down" = lower is better, "up" = higher is better, "flat" = must not move.
METRICS: list[tuple[str, str, str, str]] = [
    # ---- corpus shape: these must NOT move. Any change is a regression. ----
    ("debates_total", "Debates in corpus", "SELECT count(*) FROM debates", "flat"),
    ("turns_total", "Turns total", "SELECT count(*) FROM turns", "flat-ish"),
    ("debates_with_turns", "Debates that produced turns",
     "SELECT count(DISTINCT debate_id) FROM turns", "up"),
    ("persons_total", "Persons in roster", "SELECT count(*) FROM persons", "flat"),

    # ---- T1: speeches stale / poisoned ----
    ("t1_linked_turns", "T1 · turns back-linked to a speech",
     "SELECT count(*) FROM turns WHERE speech_id IS NOT NULL", "up"),
    ("t1_speeches_total", "T1 · speeches total", "SELECT count(*) FROM speeches", "flat-ish"),
    ("t1_poison_different_human",
     "T1 · speeches naming a DIFFERENT human than their own first turn",
     """SELECT count(*) FROM speeches s
        JOIN turns t ON t.debate_id = s.debate_id AND t.seq = s.seq_start
        WHERE s.person_id IS NOT NULL AND t.person_id IS NOT NULL
          AND s.person_id <> t.person_id""", "down"),
    ("t1_owner_disagrees", "T1 · speeches whose owner disagrees with turns (incl. NULLs)",
     """SELECT count(*) FROM speeches s
        JOIN turns t ON t.debate_id = s.debate_id AND t.seq = s.seq_start
        WHERE s.person_id IS DISTINCT FROM t.person_id""", "down"),
    ("t1_sum_turn_count", "T1 · sum(speeches.turn_count) (must equal linked turns)",
     "SELECT coalesce(sum(turn_count),0) FROM speeches", "flat-ish"),

    # ---- T2: bad mpcode aliases ----
    ("t2_alias_rows", "T2 · mpcode_aliases rows", "SELECT count(*) FROM mpcode_aliases", "down"),
    ("t2_bad_alias_turns", "T2 · turns attributed via the 3 disproven alias codes",
     """SELECT count(*) FROM turns
        WHERE name_source = 'mpcode-alias' AND mp_code IN ('549','545','4473')""", "down"),
    ("t2_alias_turns_total", "T2 · turns attributed via any mpcode-alias",
     "SELECT count(*) FROM turns WHERE name_source = 'mpcode-alias'", "flat-ish"),

    # ---- T3: decoder damage already in the corpus ----
    ("t3_placed_in_library", "T3 · turns containing the destroyed 'Placed in Library'",
     "SELECT count(*) FROM turns WHERE text LIKE '%घ्थ्aहed%'", "down"),
    ("t3_devanagari_glued_to_latin", "T3 · turns with Devanagari glued to Latin letters",
     "SELECT count(*) FROM turns WHERE text ~ '[क-ह][a-zA-Z]|[a-zA-Z][क-ह]'", "down"),
    ("t3_ls13_no_para_breaks", "T3 · LS13 long turns that lost their paragraph breaks",
     """SELECT count(*) FROM turns t JOIN debates d ON d.id = t.debate_id
        WHERE d.loksabha = 13 AND t.char_count > 800 AND t.text NOT LIKE '%' || chr(10) || '%'""",
     "down"),

    # ---- T4: mojibake still stored ----
    ("t4_mojibake_turns", "T4 · turns whose stored text is still old-font gibberish",
     "SELECT count(*) FROM turns WHERE text ~ 'ÉÊ|BÉE|àÉ|ºÉ'", "down"),
    ("t4_mojibake_words", "T4 · words stored as old-font gibberish",
     "SELECT coalesce(sum(word_count),0) FROM turns WHERE text ~ 'ÉÊ|BÉE|àÉ|ºÉ'", "down"),
    ("t4_kisan_ls14", "T4 · LS14 turns matching किसान (Hindi search works?)",
     """SELECT count(*) FROM turns t JOIN debates d ON d.id = t.debate_id
        WHERE d.loksabha = 14 AND t.text LIKE '%किसान%'""", "up"),
    ("t4_kisan_ls15", "T4 · LS15 turns matching किसान (control, must not fall)",
     """SELECT count(*) FROM turns t JOIN debates d ON d.id = t.debate_id
        WHERE d.loksabha = 15 AND t.text LIKE '%किसान%'""", "flat-ish"),
    ("t4_mojibake_labels", "T4 · turns whose speaker LABEL is still gibberish",
     "SELECT count(*) FROM turns WHERE speaker_label ~ 'ÉÊ|BÉE|àÉ|ºÉ'", "down"),

    # ---- T7: junk labels parsed as speakers ----
    ("t7_title_turns", "T7 · turns whose speaker is the word 'Title'",
     "SELECT count(*) FROM turns WHERE speaker_label = 'Title'", "down"),
    ("t7_junk_label_turns", "T7 · turns under a known junk heading label",
     """SELECT count(*) FROM turns WHERE speaker_label IN ('Title','Motion Re')""", "down"),
    ("t7_timestamp_label_turns", "T7 · turns whose speaker is a bare timestamp",
     r"""SELECT count(*) FROM turns
         WHERE speaker_label ~ '^[0-9]{1,2}[.:][0-9]{2}(½)?\s*(hrs\.?|hours)$'""", "down"),

    # ---- attribution split: the numbers a regression would show up in ----
    ("attr_person_turns", "Attribution · turns attributed to a person",
     "SELECT count(*) FROM turns WHERE person_id IS NOT NULL", "up"),
    ("attr_person_words", "Attribution · words attributed to a person",
     "SELECT coalesce(sum(word_count),0) FROM turns WHERE person_id IS NOT NULL", "up"),
    ("attr_presiding_turns", "Attribution · turns attributed to a presiding office",
     "SELECT count(*) FROM turns WHERE role_kind = 'presiding'", "up"),
    ("attr_unresolved_turns", "Attribution · turns with a label we could not resolve",
     """SELECT count(*) FROM turns
        WHERE person_id IS NULL AND role_id IS NULL AND speaker_label IS NOT NULL""", "down"),
    ("attr_unresolved_words", "Attribution · words with a label we could not resolve",
     """SELECT coalesce(sum(word_count),0) FROM turns
        WHERE person_id IS NULL AND role_id IS NULL AND speaker_label IS NOT NULL""", "down"),
    ("attr_orphan_turns", "Attribution · turns with no label at all",
     "SELECT count(*) FROM turns WHERE speaker_label IS NULL", "down"),
    ("attr_total_words", "Attribution · total words captured in turns",
     "SELECT coalesce(sum(word_count),0) FROM turns", "up"),

    # ---- T9 third state (measured, not fixed here) ----
    ("t9_third_state", "T9 · turns holding an mpCode with no persons row",
     """SELECT count(*) FROM turns
        WHERE person_id IS NULL AND role_id IS NULL
          AND name_source IS NOT NULL AND name_source <> 'unresolved'""", "down"),
    ("both_person_and_role", "Invariant · turns carrying BOTH a person and a role",
     "SELECT count(*) FROM turns WHERE person_id IS NOT NULL AND role_id IS NOT NULL", "down"),
]


def collect() -> dict[str, int]:
    engine = get_engine()
    out: dict[str, int] = {}
    with engine.connect() as conn:
        for key, label, sql, _ in METRICS:
            try:
                out[key] = int(conn.execute(text(sql)).scalar() or 0)
            except Exception as exc:  # a table may not exist yet
                print(f"  ! {key}: {exc}", file=sys.stderr)
                out[key] = -1
            print(f"  {key:32s} {out[key]:>12,}", flush=True)
    return out


def compare(before: dict[str, int], after: dict[str, int]) -> int:
    """Print a before/after table. Returns the number of metrics that got worse."""
    worse = 0
    print(f"\n{'metric':34s} {'before':>12s} {'after':>12s} {'delta':>12s}  verdict")
    print("-" * 96)
    for key, label, _sql, direction in METRICS:
        b, a = before.get(key), after.get(key)
        if b is None or a is None:
            continue
        delta = a - b
        if delta == 0:
            verdict = "unchanged"
        elif direction == "down":
            verdict = "BETTER" if delta < 0 else "*** WORSE ***"
        elif direction == "up":
            verdict = "BETTER" if delta > 0 else "*** WORSE ***"
        elif direction == "flat":
            verdict = "*** CHANGED — MUST NOT ***"
        else:
            verdict = "moved (check)"
        if "WORSE" in verdict or "MUST NOT" in verdict:
            worse += 1
        print(f"{key:34s} {b:>12,} {a:>12,} {delta:>+12,}  {verdict}")
        print(f"    {label}")
    return worse


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", help="write the snapshot here")
    ap.add_argument("--compare", help="an earlier snapshot to diff against")
    args = ap.parse_args()

    print("Collecting corpus metrics …", flush=True)
    now = collect()

    if args.json:
        with open(args.json, "w") as fh:
            json.dump(now, fh, indent=2)
        print(f"\nwrote {args.json}", flush=True)

    if args.compare:
        with open(args.compare) as fh:
            before = json.load(fh)
        worse = compare(before, now)
        print(f"\n{worse} metric(s) moved the wrong way.")
        sys.exit(1 if worse else 0)


if __name__ == "__main__":
    main()
