"""Tests for speech_stitch.stitch_turns -- the turns->speeches grouping.

These are pure (no DB). They pin the two things that matter: the segmentation
rule (bridging across interruptions) and the invariant (a speech never carries
another person's words).
"""
from speech_stitch import BRIDGE_MAX_WORDS, stitch_turns


def T(seq, person_id=None, role_kind=None, word_count=100):
    return {
        "seq": seq,
        "person_id": person_id,
        "role_kind": role_kind,
        "word_count": word_count,
        "char_count": word_count * 6,
    }


def test_empty():
    assert stitch_turns([]) == []


def test_single_person_turn():
    sp = stitch_turns([T(0, person_id=5, word_count=200)])
    assert len(sp) == 1
    assert sp[0]["person_id"] == 5
    assert sp[0]["turn_count"] == 1
    assert sp[0]["word_count"] == 200


def test_presiding_interjection_does_not_break_a_speech():
    # A speaks, MR. SPEAKER calls order, A resumes -> ONE speech.
    turns = [
        T(0, person_id=5, word_count=300),
        T(1, role_kind="presiding", word_count=10),
        T(2, person_id=5, word_count=250),
    ]
    sp = stitch_turns(turns)
    assert len(sp) == 1
    assert sp[0]["person_id"] == 5
    assert sp[0]["turn_count"] == 2  # A's two turns
    assert sp[0]["interruption_count"] == 1  # the presiding turn
    assert sp[0]["word_count"] == 550  # ONLY A's words, never the presiding turn


def test_short_heckle_by_another_mp_bridges():
    # A -> B ("But Sir!", short) -> A  ==> one speech, per owner's call.
    turns = [
        T(0, person_id=5, word_count=300),
        T(1, person_id=9, word_count=8),  # heckle
        T(2, person_id=5, word_count=100),
    ]
    sp = stitch_turns(turns)
    assert len(sp) == 1
    assert sp[0]["person_id"] == 5
    assert sp[0]["word_count"] == 400  # B's 8 words are NOT in A's speech


def test_substantive_other_mp_breaks_the_speech():
    # A -> B (long, floor genuinely passes) -> A  ==> three speeches.
    turns = [
        T(0, person_id=5, word_count=300),
        T(1, person_id=9, word_count=200),  # takes the floor
        T(2, person_id=5, word_count=100),
    ]
    sp = stitch_turns(turns)
    assert [s["person_id"] for s in sp] == [5, 9, 5]


def test_bridge_threshold_boundary():
    at = stitch_turns([
        T(0, person_id=5, word_count=300),
        T(1, person_id=9, word_count=BRIDGE_MAX_WORDS),  # exactly at limit = bridge
        T(2, person_id=5, word_count=100),
    ])
    assert len(at) == 1
    over = stitch_turns([
        T(0, person_id=5, word_count=300),
        T(1, person_id=9, word_count=BRIDGE_MAX_WORDS + 1),  # over = break
        T(2, person_id=5, word_count=100),
    ])
    assert len(over) == 3


def test_unresolved_substantive_turn_is_a_singleton_speech():
    sp = stitch_turns([T(0, person_id=None, role_kind=None, word_count=469)])
    assert len(sp) == 1
    assert sp[0]["person_id"] is None


def test_never_stitch_across_two_unresolved_turns():
    # Two unknown speakers must NOT be merged -- we cannot prove they are one.
    sp = stitch_turns([
        T(0, person_id=None, word_count=200),
        T(1, person_id=None, word_count=200),
    ])
    assert len(sp) == 2


def test_short_unresolved_heckle_with_nothing_open_is_not_a_speech():
    sp = stitch_turns([T(0, person_id=None, word_count=5)])
    assert sp == []


def test_presiding_never_owns_a_speech():
    sp = stitch_turns([
        T(0, role_kind="presiding", word_count=500),
        T(1, role_kind="crowd", word_count=3),
    ])
    assert sp == []


def test_trailing_interruptions_are_not_counted_interior():
    # A speaks, then presiding + heckle, then a DIFFERENT speaker takes over.
    # The trailing bridges are not interior to A's speech.
    sp = stitch_turns([
        T(0, person_id=5, word_count=300),
        T(1, role_kind="presiding", word_count=10),
        T(2, person_id=9, word_count=8),
        T(3, person_id=7, word_count=400),  # new floor holder
    ])
    a = sp[0]
    assert a["person_id"] == 5
    assert a["interruption_count"] == 0  # bridges were trailing, not interior
    assert a["seq_end"] == 0


def test_a_speech_owns_only_its_owners_turns():
    # Invariant: word_count and turn_seqs contain ONLY the owner.
    sp = stitch_turns([
        T(0, person_id=5, word_count=100),
        T(1, role_kind="presiding", word_count=10),
        T(2, person_id=9, word_count=5),
        T(3, person_id=5, word_count=100),
    ])
    assert len(sp) == 1
    assert sp[0]["turn_seqs"] == [0, 3]  # never 1 or 2
    assert sp[0]["word_count"] == 200


def test_frozen_real_debate_28881():
    """A real, inspected debate (LS15 speaker 932 interrupted repeatedly by the
    presiding officer): the stitch must collapse 62 turns into 17 speeches and
    fold speaker 932's five scattered turns (seq 4-12) into ONE 1631-word speech.
    Frozen from the live corpus so a rule change can't silently reshape it."""
    import json, pathlib
    raw = json.loads((pathlib.Path(__file__).parent / "data" /
                      "stitch_debate_28881_turns.json").read_text())
    turns = [dict(seq=s, person_id=p, role_kind=rk, word_count=w, char_count=cc)
             for s, p, rk, w, cc in raw]
    sp = stitch_turns(turns)
    assert len(sp) == 17
    big = [s for s in sp if s["person_id"] == 932 and s["seq_start"] == 4][0]
    assert big["seq_end"] == 12
    assert big["turn_count"] == 5
    assert big["interruption_count"] == 4  # interior only (trailing bridges excluded)
    assert big["word_count"] == 1631
    # invariant: every speech's word_count equals the sum of ONLY its owner turns
    by_seq = {t["seq"]: t for t in turns}
    for s in sp:
        assert s["word_count"] == sum(by_seq[q]["word_count"] for q in s["turn_seqs"])
