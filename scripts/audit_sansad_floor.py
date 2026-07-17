"""
Check that every MP in a debate's mpPartDetailList is covered by our speakers, or missing for a named reason.

Usage:
    python3 scripts/audit_sansad_floor.py --limit 2000
    python3 scripts/audit_sansad_floor.py --all --workers 8
The check passes when UNEXPLAINED is 0.
"""
from __future__ import annotations

import argparse
import multiprocessing as mp
import sys
from collections import Counter

# Closed set of reasons a tagged MP may be missing from our speakers.
# Do not add a reason without a deliberate decision.
REASON_NOT_PRINTED = "not_printed"       # their name is nowhere in the debate text
REASON_FOLD_COLLISION = "fold_collision"  # their key names >1 person: dropped, never guessed
REASON_ROLE_ONLY = "role_only"           # present only as the Chair / a crowd label
REASON_UNEXPLAINED = "unexplained"       # <- the bug bucket. Must be zero.


def _lazy():
    import debate_fetch
    import debate_fetch_legacy
    from db_roster import load_db_roster

    return debate_fetch, debate_fetch_legacy, load_db_roster


_ROSTER: dict[int, list] = {}


def _roster(term):
    if term not in _ROSTER:
        _, _, load_db_roster = _lazy()
        _ROSTER[term] = load_db_roster(term)
    return _ROSTER[term]


def audit_debate(loksabha, session, dbslno, raw_html, mp_list):
    """Return (Counter of reasons, list of unexplained (loksabha, session, dbslno, mpCode, mpName, key))."""
    import html as html_mod
    import re

    debate_fetch, legacy, _ = _lazy()
    from debate_fetch import _folded_key, _name_parts

    if not mp_list:
        return Counter(no_tagged_mps=1), []

    if legacy.looks_legacy(raw_html):
        segments = legacy.split_by_speaker_legacy(raw_html, mp_list, _roster(loksabha))
    else:
        segments = debate_fetch.split_by_speaker(raw_html, mp_list, _roster(loksabha))

    tagged = {str(m["mpCode"]): m["mpName"] for m in mp_list}
    covered = {str(s["mpCode"]) for s in segments if s.get("mpCode")}

    # Folded keys that name more than one tagged person are dropped on purpose.
    keys = Counter(_folded_key(n) for n in tagged.values() if _folded_key(n))
    colliding = {k for k, n in keys.items() if n > 1}

    # Labels we read as an office rather than a person.
    role_keys = set()
    for seg in segments:
        label = seg.get("speakerLabel")
        if label and seg.get("nameSource") in ("presiding", "crowd"):
            key = _folded_key(debate_fetch.decode_legacy_hindi(label))
            if key:
                role_keys.add(key)

    # Look for label positions in the document itself, independent of the parser.
    # A label position is a paragraph that opens with a short text and a colon.
    # Do not search the whole body: the Chair naming a member is not that member speaking.
    # Decode entities first. The source stores old-font glyphs as named entities and Devanagari as numeric ones.
    text_body = debate_fetch.html_to_clean_text(html_mod.unescape(raw_html))
    printed_labels = set()
    for block in text_body.split("\n\n"):
        head = block.split(":", 1)[0]
        if not head or len(head) > 120 or head == block:
            continue  # no colon, or a whole paragraph: not a label
        key = _folded_key(debate_fetch.decode_legacy_hindi(head))
        if key:
            printed_labels.add(key)

    reasons = Counter()
    unexplained = []
    for code, name in tagged.items():
        if code in covered:
            reasons["covered"] += 1
            continue
        key = _folded_key(name)
        if key and key in colliding:
            reasons[REASON_FOLD_COLLISION] += 1
        elif key and key in role_keys:
            reasons[REASON_ROLE_ONLY] += 1
        elif key and key in printed_labels:
            # The document prints this MP as a speaker but we attributed nothing to them.
            # Either the resolver failed or the splitter never opened the turn.
            reasons[REASON_UNEXPLAINED] += 1
            unexplained.append((loksabha, session, dbslno, code, name, key))
        else:
            reasons[REASON_NOT_PRINTED] += 1
    return reasons, unexplained


def _job(args):
    try:
        return audit_debate(*args)
    except Exception as exc:  # a crash is not a pass
        return Counter(error=1), [(args[0], args[1], args[2], "-", f"ERROR {exc!r}", "-")]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=2000)
    ap.add_argument("--all", action="store_true", help="every debate in the corpus")
    ap.add_argument("--seed", type=float, default=0.42)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--term", type=int, help="restrict to one Lok Sabha")
    args = ap.parse_args()

    from sqlalchemy import text

    from db import get_engine

    where = "WHERE mp_list_raw <> '[]'::jsonb"
    if args.term:
        where += f" AND loksabha = {int(args.term)}"
    sql = f"SELECT loksabha, session, dbslno, raw_html, mp_list_raw FROM debates {where}"
    if not args.all:
        sql += " ORDER BY random() LIMIT :n"

    with get_engine().connect() as conn:
        conn.execute(text("SELECT setseed(:s)"), {"s": args.seed})
        rows = conn.execute(text(sql), {"n": args.limit}).all()

    jobs = [(r[0], r[1], r[2], r[3], r[4] or []) for r in rows]
    total, unexplained = Counter(), []
    with mp.Pool(args.workers) as pool:
        for reasons, bad in pool.imap_unordered(_job, jobs, chunksize=4):
            total.update(reasons)
            unexplained += bad

    tagged = sum(v for k, v in total.items() if k not in ("no_tagged_mps", "error"))
    print(f"debates audited      {len(jobs)}")
    print(f"tagged MP slots      {tagged}   <- the denominator, stated")
    for k, v in total.most_common():
        pct = f"{100 * v / tagged:5.1f}%" if tagged else "  -  "
        print(f"  {k:16s} {v:7d}  {pct}")

    print()
    if unexplained:
        print(f"FLOOR BREACHED: {len(unexplained)} tagged MPs missing with no reason")
        for u in unexplained[:25]:
            print(f"   LS{u[0]}/{u[1]}/{u[2]} mpCode={u[3]} {u[4]!r} printed as {u[5]!r}")
        return 1
    print("FLOOR HOLDS: every tagged MP is covered, or missing for a named reason.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
