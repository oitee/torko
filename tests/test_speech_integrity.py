import pytest

from speech_stitch import check_integrity, stitch_turns


def _healthy(**overrides):
    base = dict(
        speech_count=100,
        speech_turn_total=250,
        speech_word_total=50_000,
        linked_turn_count=250,
        linked_turn_words=50_000,
        owner_disagreements=0,
    )
    base.update(overrides)
    return base


def test_healthy_corpus_passes():
    assert check_integrity(**_healthy()) == []


def test_integrity_check_fails_on_empty_link_set():
    failures = check_integrity(
        **_healthy(
            speech_count=175_680,
            linked_turn_count=0,
            linked_turn_words=0,
            speech_turn_total=238_905,
            speech_word_total=45_000_000,
        )
    )
    assert failures, "an empty link set must never report healthy"
    assert "NOT ONE turn carries a speech_id" in failures[0]


def test_empty_everything_is_not_a_pass():
    failures = check_integrity(
        speech_count=0,
        speech_turn_total=0,
        speech_word_total=0,
        linked_turn_count=0,
        linked_turn_words=0,
        owner_disagreements=0,
    )
    assert failures
    assert "nothing was measured" in failures[0]


def test_turn_budget_mismatch_is_caught():
    failures = check_integrity(**_healthy(linked_turn_count=240))
    assert any("sum(speeches.turn_count)" in f for f in failures)


def test_word_mismatch_is_caught():
    failures = check_integrity(**_healthy(speech_word_total=49_000))
    assert any("speech words" in f for f in failures)


def test_owner_disagreement_is_reported_as_poison():
    failures = check_integrity(**_healthy(owner_disagreements=598))
    assert any("wrong human's mouth" in f for f in failures)


def test_emptiness_short_circuits_before_the_word_comparison():
    failures = check_integrity(
        **_healthy(linked_turn_count=0, linked_turn_words=0, owner_disagreements=598)
    )
    assert len(failures) == 1
    assert "speech_id" in failures[0]


# A speech owner must follow its turns when a re-parse changes them.


def _turn(seq, person_id, words, role_kind=None):
    return {
        "seq": seq,
        "person_id": person_id,
        "role_kind": role_kind,
        "word_count": words,
        "char_count": words * 6,
    }


def test_speech_owner_follows_a_reattributed_turn():
    before = stitch_turns([_turn(0, 529, 319)])
    after = stitch_turns([_turn(0, 1124, 319)])

    assert before[0]["person_id"] == 529
    assert after[0]["person_id"] == 1124
    # Same span and same words, different human: a word-sum check cannot detect this.
    assert before[0]["seq_start"] == after[0]["seq_start"]
    assert before[0]["word_count"] == after[0]["word_count"]


def test_stitch_is_deterministic():
    turns = [
        _turn(0, 42, 400),
        _turn(1, None, 5, role_kind="presiding"),
        _turn(2, 42, 300),
        _turn(3, 77, 900),
    ]
    assert stitch_turns(turns) == stitch_turns(list(reversed(turns)))


def test_dropping_a_turn_changes_the_speech_span():
    with_heading = stitch_turns([_turn(0, None, 40), _turn(1, 42, 400)])
    without = stitch_turns([_turn(0, 42, 400)])
    assert len(with_heading) == 2
    assert len(without) == 1
