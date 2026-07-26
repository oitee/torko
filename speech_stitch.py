from __future__ import annotations

from typing import Optional, TypedDict

# A turn this short, or any presiding or crowd turn, does not end an open speech.
BRIDGE_MAX_WORDS = 25


class Turn(TypedDict):
    seq: int
    person_id: Optional[int]
    role_kind: Optional[str]  # 'presiding' | 'crowd' | None
    word_count: int
    char_count: int


class Speech(TypedDict):
    person_id: Optional[int]  # None => an unresolved (unknown-human) speech
    seq_start: int            # seq of the first owned turn
    seq_end: int              # seq of the last owned turn
    turn_seqs: list[int]      # the OWNER's turns only (never bridges)
    turn_count: int           # len(turn_seqs)
    interruption_count: int   # bridge turns falling inside [seq_start, seq_end]
    word_count: int           # sum over owned turns only
    char_count: int           # sum over owned turns only


def _open(turn: Turn) -> Speech:
    return {
        "person_id": turn["person_id"],
        "seq_start": turn["seq"],
        "seq_end": turn["seq"],
        "turn_seqs": [turn["seq"]],
        "turn_count": 1,
        "interruption_count": 0,
        "word_count": turn["word_count"],
        "char_count": turn["char_count"],
    }


def _extend(sp: Speech, turn: Turn) -> None:
    sp["seq_end"] = turn["seq"]
    sp["turn_seqs"].append(turn["seq"])
    sp["turn_count"] += 1
    sp["word_count"] += turn["word_count"]
    sp["char_count"] += turn["char_count"]


def stitch_turns(turns: list[Turn]) -> list[Speech]:
    speeches: list[Speech] = []
    cur: Optional[Speech] = None
    pending = 0  # bridge turns seen since cur's last owned turn; folded in only
                 # if the owner returns (so interruption_count is interior only)

    for t in sorted(turns, key=lambda x: x["seq"]):
        pid = t["person_id"]
        is_role = t["role_kind"] is not None

        # Same identified owner continues an open speech.
        if cur is not None and pid is not None and pid == cur["person_id"]:
            cur["interruption_count"] += pending
            pending = 0
            _extend(cur, t)
            continue

        # Bridge? (only meaningful while a speech is open)
        if cur is not None:
            is_bridge = is_role or t["word_count"] <= BRIDGE_MAX_WORDS
            if is_bridge:
                pending += 1
                continue

        # This turn ends the open speech, so the pending bridges were trailing. Drop them.
        pending = 0
        if is_role:
            # Presiding and crowd turns never own a speech.
            cur = None
            continue

        if pid is not None:
            cur = _open(t)
            speeches.append(cur)
        elif t["word_count"] > BRIDGE_MAX_WORDS:
            # Unresolved speech: a singleton that never absorbs later turns.
            speeches.append(_open(t))
            cur = None
        else:
            # A short unresolved turn with nothing open is not a speech.
            cur = None

    return speeches


def check_integrity(
    *,
    speech_count: int,
    speech_turn_total: int,
    speech_word_total: int,
    linked_turn_count: int,
    linked_turn_words: int,
    owner_disagreements: int,
) -> list[str]:
    """Return the failure messages. An empty list means the tables agree."""
    failures: list[str] = []

    # Check emptiness first: sums over an empty set always agree.
    if speech_count > 0 and linked_turn_count == 0:
        failures.append(
            f"{speech_count:,} speeches exist but NOT ONE turn carries a speech_id -- "
            "speeches are stale w.r.t. turns (re-run scripts/populate_speeches.py). "
            "This is the exact condition the old word-sum check could not see."
        )
        return failures  # everything below would compare against an empty set

    if speech_count == 0 and linked_turn_count == 0:
        failures.append(
            "no speeches and no linked turns: nothing was measured, so nothing is proven"
        )
        return failures

    if linked_turn_count != speech_turn_total:
        failures.append(
            f"linked turns ({linked_turn_count:,}) != sum(speeches.turn_count) "
            f"({speech_turn_total:,}): {abs(linked_turn_count - speech_turn_total):,} "
            "turns are claimed by a speech that does not hold them, or vice versa"
        )

    if linked_turn_words != speech_word_total:
        failures.append(
            f"speech words ({speech_word_total:,}) != linked turn words "
            f"({linked_turn_words:,}), delta {speech_word_total - linked_turn_words:+,}"
        )

    if owner_disagreements:
        failures.append(
            f"{owner_disagreements:,} speeches name a different person than the turn "
            "at their own seq_start -- these put words in the wrong human's mouth"
        )

    return failures
