"""Pure logic for building the mpCode -> person alias table (see
db/init/09-mpcode-aliases.sql and internal_docs 033).

No database, no network -- everything here is a function of its inputs, so the
never-guess rule can be unit-tested offline (tests/test_alias_build.py).

The bridge exists because debate transcripts number a speaker with `mpCode`
while our roster keys a person on `mpsno` (persons.sansad_id), and the two are
different, colliding namespaces. A code earns an alias only when the SOURCE's
own printed name labels for that code all point to exactly one roster person.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Callable

# Real member codes (mpsno) top out at 5836 in our roster; the source hands out
# a >=10000 block for ministers, and reuses one such code across DIFFERENT
# humans across terms (10008 = Ravi Shankar Prasad and Anbumani Ramadoss). They
# are role-slots, not people -- excluded wholesale, never aliased.
SYNTHETIC_MIN = 10000


def is_synthetic_code(mp_code: str) -> bool:
    """A minister role-slot code (>= 10000), which no single person can own."""
    try:
        return int(mp_code) >= SYNTHETIC_MIN
    except (TypeError, ValueError):
        return False


def build_aliases(
    label_rows,
    unique_person_by_key: dict[str, int],
    folded_key: Callable[[str], str],
    is_presiding: Callable[[str], bool],
    is_crowd: Callable[[str], bool],
) -> tuple[dict[str, dict], dict[str, dict]]:
    """Decide, per orphan mpCode, which single person (if any) it aliases to.

    `label_rows` is an iterable of (mp_code, speaker_label, turn_count) over the
    turns that are currently unresolved (no person, no role) and carry an
    mp_code. `unique_person_by_key` maps a folded roster-name key to a person id,
    already stripped of colliding keys (two people sharing a folded key are not
    in it) -- the same never-guess drop the matcher uses.

    Returns (aliases, dropped):
      aliases[mp_code] = {"person_id": int, "evidence_turns": int}
      dropped[mp_code] = {"reason": "conflict", "persons": {pid: turns}}

    A code is aliased only when every one of its resolvable NAME labels folds to
    the same single person. Presiding/crowd labels are ignored (a code may carry
    a stray "MR. SPEAKER" turn via anchor-reuse; that must not vote on identity).
    A code whose name labels point at two different people is dropped: never
    guess which one.
    """
    per_code: dict[str, dict[int, int]] = defaultdict(lambda: defaultdict(int))
    for mp_code, label, count in label_rows:
        code = str(mp_code)
        if is_synthetic_code(code):
            continue
        if not label or is_presiding(label) or is_crowd(label):
            continue
        pid = unique_person_by_key.get(folded_key(label))
        if pid is not None:
            per_code[code][pid] += count

    aliases: dict[str, dict] = {}
    dropped: dict[str, dict] = {}
    for code, pids in per_code.items():
        if len(pids) == 1:
            pid, turns = next(iter(pids.items()))
            aliases[code] = {"person_id": pid, "evidence_turns": turns}
        else:
            dropped[code] = {"reason": "conflict", "persons": dict(pids)}
    return aliases, dropped
