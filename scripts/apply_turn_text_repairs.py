"""
Put repaired text into turns whose old-font Hindi the readers decoded wrongly, from a tracked list.

Input: data/turn_text_repairs.tsv. One row for each turn:
  loksabha, session, dbslno, seq  the stable key of the turn. Turn ids change on a rebuild.
                                  This key does not.
  garbled_sha256                  the SHA-256 of the garbled text that the parser writes for
                                  this turn.
  method                          'repair-llm' or 'repair-dict' (see db/init/19-turn-text-source.sql).
  text                            the repaired text. A backslash, a new line, a tab, and a
                                  carriage return are written as \\, \n, \t, and \r.

Example: in term 13 the readers decode `¸ी Êवजय गोय±ा` instead of `श्री विजय गोयल`. The list holds
the readable text of 1,413 such turns.

For each row, the script:
  1. finds the turn by its stable key.
  2. replaces its text, word_count and char_count, and sets text_source, only if the current text
     has the stored hash. If the parser changes the garbled text, the hash does not match and the
     script skips the turn. So a repair never goes onto a different text.
  3. sets the word_count and char_count of each speech that owns a changed turn to the sum over
     the turns of that speech. The speech ids do not change.

Rebuild order: run it after scripts/populate_turns.py and scripts/apply_turn_reassignments.py,
and before scripts/populate_speeches.py. Safe to run again: a second run finds every turn done.

Run from the repo root:

    python3 -m scripts.apply_turn_text_repairs [--dry-run]
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import sys
from pathlib import Path

from sqlalchemy import text

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from db import get_engine  # noqa: E402
from speech_stitch import BRIDGE_MAX_WORDS  # noqa: E402

# TSV columns: one row per part of a repaired turn. Part 0 is the parser's own turn.
# Parts 1 and up are new turns that follow it. Empty speaker fields on part 0 keep the parser's speaker.
# The key (loksabha, session, dbslno, seq) is stable. Turn ids change on a rebuild.
TSV = ROOT / "data" / "turn_text_repairs.tsv"
FIELDS = ["loksabha", "session", "dbslno", "seq", "garbled_sha256", "method", "text"]
METHODS = {"repair-llm", "repair-dict"}

_ESCAPES = {"\\": "\\\\", "\n": "\\n", "\t": "\\t", "\r": "\\r"}
_UNESCAPES = {"\\": "\\", "n": "\n", "t": "\t", "r": "\r"}


def encode_text(s: str) -> str:
    return "".join(_ESCAPES.get(ch, ch) for ch in s)


def decode_text(s: str) -> str:
    out, i = [], 0
    while i < len(s):
        if s[i] == "\\" and i + 1 < len(s) and s[i + 1] in _UNESCAPES:
            out.append(_UNESCAPES[s[i + 1]])
            i += 2
        else:
            out.append(s[i])
            i += 1
    return "".join(out)


def text_hash(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def read_rows(path: Path = TSV) -> list[dict]:
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE)
        rows = []
        for r in reader:
            if r["method"] not in METHODS:
                raise SystemExit(f"unknown method {r['method']!r} in {r}")
            rows.append(
                {
                    "key": (int(r["loksabha"]), int(r["session"]), int(r["dbslno"]), int(r["seq"])),
                    "garbled_sha256": r["garbled_sha256"],
                    "method": r["method"],
                    "text": decode_text(r["text"]),
                }
            )
    return rows


def decide(current_text: str | None, row: dict) -> str:
    """What to do with one turn: 'apply', 'done' (already repaired), 'mismatch', or 'missing'."""
    if current_text is None:
        return "missing"
    if current_text == row["text"]:
        return "done"
    if text_hash(current_text) == row["garbled_sha256"]:
        return "apply"
    return "mismatch"


def apply(rows: list[dict], dry_run: bool = False) -> dict[str, list]:
    keys = [r["key"] for r in rows]
    with get_engine().begin() as conn:
        found = conn.execute(
            text(
                """
                SELECT d.loksabha, d.session, d.dbslno, t.seq, t.id, t.text, t.word_count,
                       t.speech_id, t.text_source
                FROM unnest(CAST(:ls AS int[]), CAST(:se AS int[]), CAST(:db AS int[]), CAST(:sq AS int[]))
                     AS k(loksabha, session, dbslno, seq)
                JOIN debates d ON (d.loksabha, d.session, d.dbslno) = (k.loksabha, k.session, k.dbslno)
                JOIN turns t ON t.debate_id = d.id AND t.seq = k.seq
                """
            ),
            {
                "ls": [k[0] for k in keys],
                "se": [k[1] for k in keys],
                "db": [k[2] for k in keys],
                "sq": [k[3] for k in keys],
            },
        ).fetchall()
        by_key = {(f.loksabha, f.session, f.dbslno, f.seq): f for f in found}

        result: dict[str, list] = {"apply": [], "done": [], "mismatch": [], "missing": [], "bridge_change": []}
        speech_ids = set()
        for r in rows:
            cur = by_key.get(r["key"])
            outcome = decide(cur.text if cur else None, r)
            if outcome == "done" and cur.text_source != r["method"]:
                outcome = "apply"
            result[outcome].append(r["key"])
            if outcome != "apply":
                continue
            words = len(r["text"].split())
            if (cur.word_count <= BRIDGE_MAX_WORDS) != (words <= BRIDGE_MAX_WORDS):
                result["bridge_change"].append(r["key"])
            if cur.speech_id is not None:
                speech_ids.add(cur.speech_id)
            if not dry_run:
                conn.execute(
                    text(
                        """
                        UPDATE turns SET text = :text, word_count = :wc, char_count = :cc,
                                         text_source = :method
                        WHERE id = :id
                        """
                    ),
                    {"text": r["text"], "wc": words, "cc": len(r["text"]), "method": r["method"], "id": cur.id},
                )

        if speech_ids and not dry_run:
            conn.execute(
                text(
                    """
                    UPDATE speeches s SET word_count = x.wc, char_count = x.cc
                    FROM (SELECT speech_id, sum(word_count) AS wc, sum(char_count) AS cc
                          FROM turns WHERE speech_id = ANY(:ids) GROUP BY speech_id) x
                    WHERE s.id = x.speech_id
                    """
                ),
                {"ids": list(speech_ids)},
            )
        result["speeches"] = sorted(speech_ids)
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="report what would change, write nothing")
    args = ap.parse_args()
    result = apply(read_rows(), dry_run=args.dry_run)
    verb = "would apply" if args.dry_run else "applied"
    print(
        f"{verb} {len(result['apply'])}, already done {len(result['done'])}, "
        f"hash mismatch {len(result['mismatch'])}, turn not found {len(result['missing'])}, "
        f"speeches recounted {len(result['speeches'])}",
        flush=True,
    )
    if result["bridge_change"]:
        print(
            f"{len(result['bridge_change'])} turns crossed the bridge limit of {BRIDGE_MAX_WORDS} words. "
            "scripts/populate_speeches.py can group their debates differently.",
            flush=True,
        )
    for kind in ("mismatch", "missing"):
        for key in result[kind]:
            print(f"  {kind}: loksabha {key[0]} session {key[1]} dbslno {key[2]} seq {key[3]}", flush=True)
    return 1 if result["mismatch"] or result["missing"] else 0


if __name__ == "__main__":
    sys.exit(main())
