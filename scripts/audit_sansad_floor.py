"""
The Sansad floor: is our corpus at least as good as the source it came from?

Every debate ships with `mpPartDetailList` -- the source's OWN list of the MPs
who took part, with their mpCodes. That list is Sansad's answer to "who is in
this debate". This script asks whether ours covers it.

WHY THIS IS A GUARANTEE AND NOT A METRIC. Everything else this project counts
is coverage, and coverage cannot tell right from wrong (see
internal_docs/020_GLOSSARY.md). This check is different in kind: it is the one
floor below which the dataset would be *worse than the source we built it from*,
and at that point nothing else about it matters.

THE NAIVE VERSION IS FALSE, AND FORCING IT TO PASS WOULD MEAN GUESSING.
`mpPartDetailList` is who PARTICIPATED. That is not the same set as who has a
speaking turn we can honestly attribute:

  - an MP may be tagged and appear only as the Chair ("MR. SPEAKER:"), which
    names an office and not a person, on purpose;
  - an MP's name may fold onto another member's, in which case never-guess
    drops it rather than pick -- a ceiling, not a bug;
  - an MP may be tagged and simply never printed in the body at all.

So "we cover every tagged MP" is not achievable without abandoning the
invariant. The guarantee is stated one notch differently, and the notch is the
whole point:

    Every tagged MP we do NOT cover has a named reason, from a closed set.

An unexplained miss is a bug. An explained miss is a known ceiling. What is
forbidden is a miss nobody can account for -- which is exactly what a coverage
percentage hides.

    UNEXPLAINED == 0 is the assertion. Everything else here is bookkeeping.

HOW THE MISSING ARE JUDGED, AND WHY IT IS NOT THE OBVIOUS WAY. The first
version of this script decided "is this MP's name printed?" by looking at the
speaker labels the parser had already found. That check was decoration: it
could not fail. If a label folds to the MP's key and the key is unique, the
resolver's own fold table matches it, so the MP is covered; if the key is not
unique, it is a collision and caught earlier. There was no reachable path into
the bug bucket -- an audit that always passes, in a project whose docs warn
about exactly that, three times over.

So the question is asked of the DEBATE TEXT instead: does this MP's name appear
in the body at all? That is a question the parser has no say in, which is the
entire point -- it can catch a resolution failure AND a turn the splitter never
opened, neither of which can be seen by asking the parser what it found.

WHICH READER. This script routes each debate with `looks_legacy`, the same test
the readers themselves use. That is a CHOICE, and it is worth knowing it is one:
the project has no single pipeline yet -- `debate_fetch.py` always reads a
debate as modern, `debate_fetch_legacy.py` always reads it as legacy, and
nothing has ever had to decide for the corpus as a whole. The floor is therefore
measured against the routing rule, and it has already found that the rule loses
people: LS13/1/6679 routes to the legacy reader, which covers more codes overall
but drops Saroja (403) and Ambedkar (18), both of whom the modern reader
resolves. A coverage percentage cannot see that. A per-person floor can.

Run:  python3 scripts/audit_sansad_floor.py --limit 2000
      python3 scripts/audit_sansad_floor.py --all --workers 8
"""
from __future__ import annotations

import argparse
import multiprocessing as mp
import sys
from collections import Counter

# Reasons a tagged MP may legitimately not appear in our speakers. CLOSED SET --
# adding to it is a decision about what we are willing to call acceptable, so it
# should be argued for in internal_docs, not slipped in here.
REASON_NOT_PRINTED = "not_printed"       # their name is nowhere in the debate text
REASON_FOLD_COLLISION = "fold_collision"  # their key names >1 person: dropped, never guessed
REASON_ROLE_ONLY = "role_only"           # present only as the Chair / a crowd label
REASON_UNEXPLAINED = "unexplained"       # <- the bug bucket. Must be zero.


def _lazy():
    """Imported inside the workers so `--help` needs no DB and no bs4."""
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
    """Return (Counter of reasons, list of unexplained (mpCode, mpName, label)).

    Pure given its inputs, so it is testable without a database or a network.
    """
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

    # Which folded keys name more than one tagged person? Those are the ones
    # never-guess drops on purpose.
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

    # Every LABEL POSITION in the debate's text, folded -- asked of the document
    # itself, with no help from the parser.
    #
    # Not "does this name appear in the body": that conflates being talked about
    # with talking. The Chair saying "the House will hear Shri Kiren Rijiju" is
    # not Shri Kiren Rijiju speaking, and a body-text check calls it a bug.
    # A label position is a paragraph that opens with a short piece of text and
    # a colon, which is how this source prints a speaker and nothing else.
    #
    # Independent of BOTH things that could be wrong: the splitter's bold/caps
    # rules (a swallowed turn is invisible to the parser by definition) and the
    # resolver's tiers. That independence is the only reason this can fail.
    #
    # Decode entities FIRST -- this source stores old-font glyphs as named
    # entities and Devanagari as numeric ones, so a check that skips this
    # measures ~1% of the corpus, confidently (internal_docs/023_THE_CENSUS.md).
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
            # The document prints this MP as a speaker, their key names nobody
            # else, and we attributed nothing to them. Either the resolver
            # failed or the splitter never opened the turn. Both are bugs, and
            # this is the only bucket that is one.
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
