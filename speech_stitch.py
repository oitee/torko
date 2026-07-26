"""
Stitch parser `turns` into `speeches`.

A *turn* is a parse artifact: one contiguous block the parser attributed to one
label. A single intervention by one MP is routinely split into many turns by the
presiding officer calling order, by heckles, by "yield for a question". A
*speech* is what a person actually did: the whole intervention, interruptions
and all.

THE ONE INVARIANT THAT MAKES THIS SAFE
--------------------------------------
A speech is a *span*, never a text-merge across speakers. A speech owned by
person P contains only P's own turns; every interjection inside the span stays
its own turn and is counted only as an interruption. So bridging across an
interruption can NEVER move another person's words into P's mouth -- there is no
attribution decision here at all, only a segmentation one. Where the bridge
threshold falls changes how many speeches P gets, never whose words they are.
This is never-guess applied to the stitcher: chunk boundaries stay a subset of
speech boundaries.

THE RULE (v1 -- see internal_docs for the sampling that chose it)
----------------------------------------------------------------
Walk turns in `seq` order, holding at most one open speech owned by a person P:

  - A turn by P extends P's open speech.
  - A "bridge" turn does NOT close P's speech; it is recorded as an interruption
    and its words are NOT added to P's speech. A turn is a bridge (relative to
    the open speech) when it is
        * a presiding-officer or crowd turn (role_kind is not None), OR
        * a short interjection by anyone else: word_count <= BRIDGE_MAX_WORDS.
  - A substantive turn (> BRIDGE_MAX_WORDS) by a *different* identified person
    closes P's speech and opens theirs.
  - A substantive turn we could not resolve to a person (person_id is None,
    role_id is None) is a real speech by an unknown human: it becomes a
    singleton speech with person_id = None. We never stitch across two
    unresolved turns -- we cannot prove they are the same human, and guessing
    they are is exactly the sin we refuse.

Presiding/crowd turns never OWN a speech (they are procedural, ~33% of all
turns and not speeches in any analytical sense). They only bridge, or -- with no
speech open -- are skipped (speech_id stays NULL).

BRIDGE_MAX_WORDS = 25 was chosen from a 400-debate sample: other-MP wedges
between one speaker's turns are bimodal -- ~75% are <=25-word heckles ("But
Sir!"), a clear tail of >=100-word turns are genuine floor-passing. Presiding
wedges are always bridged regardless of length (median 10, max 71 words): a
presiding officer manages the floor, never debates. The threshold is a
segmentation knob with zero poison risk (see above), so it is safe to pick one
and document it.
"""
from __future__ import annotations

from typing import Optional, TypedDict

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
    """Group one debate's turns (any order) into speeches. Pure; no DB."""
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

        # Not a bridge (or nothing open): this turn settles the open speech.
        # Its own words end the prior owner's speech, so any pending bridges were
        # trailing, not interior -- discard them.
        pending = 0
        if is_role:
            # Presiding/crowd never own a speech, and a long presiding turn with
            # nothing open is just skipped.
            cur = None
            continue

        if pid is not None:
            cur = _open(t)
            speeches.append(cur)
        elif t["word_count"] > BRIDGE_MAX_WORDS:
            # Substantive unresolved turn: a real speech by an unknown human.
            # Singleton; never stitched across, never absorbs following bridges.
            speeches.append(_open(t))
            cur = None
        else:
            # A short unresolved heckle with nothing open: not a speech.
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
    """Is the stored `speeches` table still true about the stored `turns`?

    Pure: takes six already-counted numbers and returns a list of human-readable
    failures (empty list == healthy). Kept out of the DB layer so the one case
    that actually bit us can be unit-tested with no Postgres running.

    WHY THIS FUNCTION EXISTS, AND WHY THE ORDER OF THE CHECKS IS LOAD-BEARING
    ------------------------------------------------------------------------
    The old integrity proof was "the words in `speeches` equal the words in the
    turns linked to them, exactly", computed by joining `turns` to `speeches` on
    `turns.speech_id`. `scripts/populate_turns.py` deletes and re-inserts every
    turn of a debate it re-parses, and the fresh rows carry `speech_id = NULL`.
    After a re-parse, therefore, NOTHING was linked -- the join matched no rows,
    both sides of the comparison summed to zero, zero equalled zero, and the
    check reported "exact" while `speeches` described turns that no longer
    existed. 598 speeches were naming a different human than their own first
    turn at the time this was written, and the check said everything was fine.

    So the emptiness checks come FIRST and are unconditional. A comparison over
    an empty set is not evidence of agreement; it is evidence of nothing, and
    this project has now been bitten six times by a number that measured
    nothing while reading like a proof (see CLAUDE.md, "coverage is not
    accuracy"). `linked_turn_count == 0` while `speech_count > 0` is a hard
    failure here, not a pass.
    """
    failures: list[str] = []

    # -- emptiness first: a vacuous comparison must never be able to pass -----
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

    # -- then the shape: does every speech's turn budget actually exist? ------
    if linked_turn_count != speech_turn_total:
        failures.append(
            f"linked turns ({linked_turn_count:,}) != sum(speeches.turn_count) "
            f"({speech_turn_total:,}): {abs(linked_turn_count - speech_turn_total):,} "
            "turns are claimed by a speech that does not hold them, or vice versa"
        )

    # -- only now is the word comparison meaningful --------------------------
    if linked_turn_words != speech_word_total:
        failures.append(
            f"speech words ({speech_word_total:,}) != linked turn words "
            f"({linked_turn_words:,}), delta {speech_word_total - linked_turn_words:+,}"
        )

    # -- and the one that is poison rather than bookkeeping ------------------
    if owner_disagreements:
        failures.append(
            f"{owner_disagreements:,} speeches name a different person than the turn "
            "at their own seq_start -- these put words in the wrong human's mouth"
        )

    return failures
