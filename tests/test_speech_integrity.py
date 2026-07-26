"""The speeches-vs-turns integrity check, and the bug it was written to catch.

Offline, no database. The numbers here are the six aggregates
`scripts/populate_speeches.py --verify` reads out of Postgres; feeding them in
directly is what lets the one failure mode that actually bit us be tested
without a corpus.

Background, in plain words. A *turn* is one block of speech the parser found. A
*speech* is one MP's whole intervention -- a span over several of their turns,
with heckles and the Chair's interjections passing through it. `speeches` is
built by grouping `turns`; each turn then carries a `speech_id` pointing back.

The bug: re-parsing a debate deletes and re-inserts its turns, and the new rows
come back with `speech_id = NULL`. The old integrity proof joined turns to
speeches ON that column, so after a re-parse it joined nothing, summed zero
against zero, and reported "exact" -- while 598 speeches were naming a different
human being than their own first turn. A check that cannot fail is not a check.
"""
import pytest

from speech_stitch import check_integrity, stitch_turns


def _healthy(**overrides):
    """A consistent set of aggregates; override one field to break it."""
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
    """THE regression test for the actual bug.

    Speeches exist; not one turn carries a speech_id. The word sums are both
    zero and therefore trivially equal -- which is exactly how the old check
    passed. This must FAIL, and it must say so in terms of staleness.
    """
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
    """Nothing measured is not the same as nothing wrong.

    Zero speeches and zero linked turns compares zero to zero and would pass any
    naive equality check. It proves nothing, so it fails.
    """
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
    """A speech naming a different human than its own first turn is the poison
    case -- distinct from the bookkeeping mismatches above."""
    failures = check_integrity(**_healthy(owner_disagreements=598))
    assert any("wrong human's mouth" in f for f in failures)


def test_emptiness_short_circuits_before_the_word_comparison():
    """Ordering is load-bearing: with no linked turns, the word comparison is
    meaningless and must not be the thing that is reported."""
    failures = check_integrity(
        **_healthy(linked_turn_count=0, linked_turn_words=0, owner_disagreements=598)
    )
    assert len(failures) == 1
    assert "speech_id" in failures[0]


# ---------------------------------------------------------------------------
# The other half of T1: a speech's owner must follow its turns when a re-parse
# changes them. stitch_turns is pure, so this is checkable directly.
# ---------------------------------------------------------------------------


def _turn(seq, person_id, words, role_kind=None):
    return {
        "seq": seq,
        "person_id": person_id,
        "role_kind": role_kind,
        "word_count": words,
        "char_count": words * 6,
    }


def test_speech_owner_follows_a_reattributed_turn():
    """The scenario that produced the 598 poisoned speeches.

    Commit 922a872 corrected 756 turns' `person_id` (the printed label beat a
    contradicting anchor code). Re-stitching the SAME seq layout with the new
    owner must yield a speech owned by the new person -- so a stored speech that
    still names the old one is provably stale, not merely different.
    """
    before = stitch_turns([_turn(0, 529, 319)])
    after = stitch_turns([_turn(0, 1124, 319)])

    assert before[0]["person_id"] == 529
    assert after[0]["person_id"] == 1124
    # Same span, same words -- only the human changed. This is why a word-sum
    # check can never detect the poison on its own.
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
    """A parser fix that legitimately stops emitting a turn (e.g. a heading
    line) changes speech spans. Nothing here should be surprising -- the point
    is that the stored table cannot possibly still be right, which is why
    populate_turns.py now deletes speeches for every debate it re-parses."""
    with_heading = stitch_turns([_turn(0, None, 40), _turn(1, 42, 400)])
    without = stitch_turns([_turn(0, 42, 400)])
    assert len(with_heading) == 2
    assert len(without) == 1
