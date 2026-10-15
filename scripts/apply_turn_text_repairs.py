"""
Put repaired text into turns whose old-font Hindi the readers decoded wrongly, from a tracked list.
Where the repaired text holds the speech of more than one person, split the turn into one turn
for each speaker.

Input: data/turn_text_repairs.tsv. One row for each part of a repaired turn:
  loksabha, session, dbslno, seq  the stable key of the turn that the parser writes. Turn ids
                                  change on a rebuild. This key does not.
  part                            0 = the parser's turn itself. 1, 2, ... = a new turn that comes
                                  right after it.
  garbled_sha256                  the SHA-256 of the garbled text that the parser writes for
                                  this turn. The same on every part of a turn.
  method                          'repair-llm' or 'repair-dict' (see db/init/19-turn-text-source.sql).
  speaker_label                   the printed label of the part. Empty on part 0 = keep the
                                  parser's label.
  mpsno                           the member code (persons.sansad_id) of the speaker, or empty.
  role_code                       a speaker_roles.code (speaker, deputy_speaker, chairman,
                                  members_crowd), or empty.
  name_source                     how the speaker was found. Empty on part 0 = keep the parser's
                                  speaker (person or role). On a new turn, empty mpsno and
                                  role_code = no speaker ('unresolved').
  text                            the repaired text of the part, without its label. A backslash,
                                  a new line, a tab, and a carriage return are written as \\, \n,
                                  \t, and \r.

Example: in term 13 the readers decode `¸ी Êवजय गोय±ा` instead of `श्री विजय गोयल`. The garbled
labels also hid the speaker changes from the parser. So the MR. SPEAKER turn 1 of debate 13-1-6579
also holds the motion of the Prime Minister. The list gives that turn two parts: part 0 for the
Speaker, and part 1 for Atal Bihari Vajpayee.

For each debate in the list, the script:
  1. finds each listed turn by its stable key.
  2. applies the parts only if the text of every listed turn in the debate has the stored hash.
     If the parser changes the garbled text, the hash does not match and the script skips the
     debate. So a repair never goes onto a different text.
  3. writes part 0 into the parser's turn, inserts the other parts after it, and moves the later
     turns of the debate down. It sets text, word_count, char_count, and text_source.
  4. sets the word_count and char_count of each speech that owns a changed turn to the sum over
     the turns of that speech. The new turns have no speech.

Rebuild order: run it after scripts/populate_turns.py and scripts/apply_turn_reassignments.py,
and before scripts/populate_speeches.py. The new turns need populate_speeches.py to join a
speech. Safe to run again: a second run finds every debate done.

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

# TSV columns: one row per part of a repaired turn. Part 0 is the parser's own turn.
# Parts 1 and up are new turns that follow it. Empty speaker fields on part 0 keep the parser's speaker.
# The key (loksabha, session, dbslno, seq) is stable. Turn ids change on a rebuild.
TSV = ROOT / "data" / "turn_text_repairs.tsv"
FIELDS = [
    "loksabha", "session", "dbslno", "seq", "part", "garbled_sha256", "method",
    "speaker_label", "mpsno", "role_code", "name_source", "text",
]
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


def read_rows(path: Path = TSV) -> dict[tuple, list[dict]]:
    turns: dict[tuple, list[dict]] = {}
    with open(path, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE):
            if r["method"] not in METHODS:
                raise SystemExit(f"unknown method {r['method']!r} in {r}")
            if r["mpsno"] and r["role_code"]:
                raise SystemExit(f"a part has both a member and a role: {r}")
            key = (int(r["loksabha"]), int(r["session"]), int(r["dbslno"]), int(r["seq"]))
            turns.setdefault(key, []).append(
                {
                    "part": int(r["part"]),
                    "garbled_sha256": r["garbled_sha256"],
                    "method": r["method"],
                    "speaker_label": decode_text(r["speaker_label"]),
                    "mpsno": r["mpsno"],
                    "role_code": r["role_code"],
                    "name_source": r["name_source"],
                    "text": decode_text(r["text"]),
                }
            )
    for key, parts in turns.items():
        if [p["part"] for p in parts] != list(range(len(parts))):
            raise SystemExit(f"the parts of {key} are not 0, 1, 2, ... in order")
        if len({(p["garbled_sha256"], p["method"]) for p in parts}) != 1:
            raise SystemExit(f"the parts of {key} do not have one hash and one method")
    return turns


def plan_debate(current: list[dict], listed: dict[int, list[dict]]) -> tuple[str, dict[int, str]]:
    # Per listed turn: apply (garbled text present), done (parts present), mismatch, or missing.
    # The debate is applied only if the hash of every listed turn matches, so a repair never lands on other text.
    by_seq = {t["seq"]: t["text"] for t in current}
    states: dict[int, str] = {}
    shift = 0
    for seq in sorted(listed):
        parts = listed[seq]
        if seq not in by_seq:
            states[seq] = "missing"
        elif text_hash(by_seq[seq]) == parts[0]["garbled_sha256"]:
            states[seq] = "apply"
        elif all(by_seq.get(seq + shift + i) == p["text"] for i, p in enumerate(parts)):
            states[seq] = "done"
        else:
            states[seq] = "mismatch"
        shift += len(parts) - 1
    kinds = set(states.values())
    if kinds == {"apply"}:
        return "apply", states
    if kinds == {"done"}:
        return "done", states
    return "skip", states


def new_layout(current: list[dict], listed: dict[int, list[dict]]) -> list[dict]:
    out = []
    for t in sorted(current, key=lambda t: t["seq"]):
        parts = listed.get(t["seq"])
        out.append({"id": t["id"], "part": parts[0] if parts else None})
        for p in (parts or [])[1:]:
            out.append({"id": None, "part": p})
    for seq, row in enumerate(out):
        row["seq"] = seq
    return out


def _speaker(part: dict, person_by_code: dict[str, int], roles: dict[str, tuple[int, str]]) -> dict:
    if part["mpsno"]:
        if part["mpsno"] not in person_by_code:
            raise SystemExit(f"no person with code {part['mpsno']}")
        return {"person_id": person_by_code[part["mpsno"]], "role_id": None, "role_kind": None,
                "name_source": part["name_source"]}
    if part["role_code"]:
        role_id, kind = roles[part["role_code"]]
        return {"person_id": None, "role_id": role_id, "role_kind": kind,
                "name_source": part["name_source"]}
    return {"person_id": None, "role_id": None, "role_kind": None,
            "name_source": part["name_source"] or "unresolved"}


def apply(turns: dict[tuple, list[dict]], dry_run: bool = False) -> dict[str, list]:
    debates: dict[tuple, dict[int, list[dict]]] = {}
    for key, parts in turns.items():
        debates.setdefault(key[:3], {})[key[3]] = parts

    result: dict[str, list] = {"apply": [], "done": [], "skip": [], "speeches": [], "new_turns": []}
    with get_engine().begin() as conn:
        person_by_code = {
            str(r.sansad_id): r.id
            for r in conn.execute(text("SELECT id, sansad_id FROM persons WHERE sansad_id IS NOT NULL"))
        }
        roles = {r.code: (r.id, r.kind) for r in conn.execute(text("SELECT id, code, kind FROM speaker_roles"))}
        speech_ids = set()
        for dkey in sorted(debates):
            listed = debates[dkey]
            debate_id = conn.execute(
                text("SELECT id FROM debates WHERE loksabha = :l AND session = :s AND dbslno = :d"),
                {"l": dkey[0], "s": dkey[1], "d": dkey[2]},
            ).scalar()
            current = []
            if debate_id is not None:
                current = [
                    dict(r._mapping)
                    for r in conn.execute(
                        text("SELECT id, seq, text, speech_id FROM turns WHERE debate_id = :d ORDER BY seq"),
                        {"d": debate_id},
                    )
                ]
            outcome, states = plan_debate(current, listed)
            result[outcome].append((dkey, states))
            if outcome != "apply":
                continue
            layout = new_layout(current, listed)
            result["new_turns"].append(sum(1 for row in layout if row["id"] is None))
            speech_ids |= {t["speech_id"] for t in current if t["seq"] in listed and t["speech_id"] is not None}
            if dry_run:
                continue
            # Move every turn of the debate out of the way first, so that UNIQUE (debate_id, seq)
            # holds at each step. Negative numbers never collide with the final 0, 1, 2, ...
            conn.execute(text("UPDATE turns SET seq = -seq - 1 WHERE debate_id = :d"), {"d": debate_id})
            for row in layout:
                part = row["part"]
                if row["id"] is not None and part is None:
                    conn.execute(text("UPDATE turns SET seq = :seq WHERE id = :id"), {"seq": row["seq"], "id": row["id"]})
                    continue
                values = {
                    "seq": row["seq"], "text": part["text"], "wc": len(part["text"].split()),
                    "cc": len(part["text"]), "method": part["method"],
                }
                if row["id"] is not None:
                    sets = "seq = :seq, text = :text, word_count = :wc, char_count = :cc, text_source = :method"
                    if part["speaker_label"]:
                        sets += ", speaker_label = :label"
                        values["label"] = part["speaker_label"]
                    if part["name_source"]:
                        sets += ", person_id = :person_id, role_id = :role_id, role_kind = :role_kind, name_source = :name_source"
                        values.update(_speaker(part, person_by_code, roles))
                    conn.execute(text(f"UPDATE turns SET {sets} WHERE id = :id"), {**values, "id": row["id"]})
                else:
                    conn.execute(
                        text(
                            """
                            INSERT INTO turns (debate_id, seq, speaker_label, person_id, role_id, role_kind,
                                               name_source, text, word_count, char_count, text_source)
                            VALUES (:debate_id, :seq, :label, :person_id, :role_id, :role_kind,
                                    :name_source, :text, :wc, :cc, :method)
                            """
                        ),
                        {**values, "debate_id": debate_id, "label": part["speaker_label"] or None,
                         **_speaker(part, person_by_code, roles)},
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
    turns = read_rows()
    result = apply(turns, dry_run=args.dry_run)
    verb = "would apply" if args.dry_run else "applied"
    n_turns = lambda kind: sum(len(states) for _, states in result[kind])  # noqa: E731
    print(
        f"{verb} {len(result['apply'])} debates ({n_turns('apply')} turns, {sum(result['new_turns'])} new turns), "
        f"already done {len(result['done'])} debates ({n_turns('done')} turns), "
        f"skipped {len(result['skip'])} debates, speeches recounted {len(result['speeches'])}",
        flush=True,
    )
    if sum(result["new_turns"]):
        print("Run scripts/populate_speeches.py next: the new turns have no speech.", flush=True)
    for dkey, states in result["skip"]:
        bad = {seq: s for seq, s in states.items() if s not in ("apply", "done")}
        print(f"  skipped: loksabha {dkey[0]} session {dkey[1]} dbslno {dkey[2]}: {bad or states}", flush=True)
    return 1 if result["skip"] else 0


if __name__ == "__main__":
    sys.exit(main())
