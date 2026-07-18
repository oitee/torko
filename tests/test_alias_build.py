"""Offline tests for the mpCode->person alias build (alias_build.py).

The one thing that matters here is never-guess: a code is aliased only when its
printed name labels unanimously point at one person, the synthetic minister
block is never aliased, and presiding/crowd labels never vote on identity. No
database, no network.
"""
from alias_build import SYNTHETIC_MIN, build_aliases, is_synthetic_code

# A tiny folded index: folded name key -> person id.
PERSONS = {
    "bandyopadhyaysudip": 38,
    "devegowdahd": 3960,
    "swarajsushma": 3812,
}


def _fold(label: str) -> str:
    """Deterministic stand-in fold: map each test label straight to its person key.

    We only need it to be reproducible and to land the test labels on PERSONS;
    the real _folded_key (with its transliteration/collision behaviour) is
    exercised live, not here. Anything unknown folds to a key nobody owns.
    """
    return {
        "SHRI SUDIP BANDYOPADHYAY (KOLKATA UTTAR)": "bandyopadhyaysudip",
        "SHRI SUDIP BANDYOPADHYAY": "bandyopadhyaysudip",
        "SHRI H.D. DEVE GOWDA": "devegowdahd",
        "SMT SUSHMA SWARAJ": "swarajsushma",
    }.get(label, "__unmatched__")


def _never(_):  # is_presiding / is_crowd stub that says "no"
    return False


def test_unique_name_labels_alias():
    rows = [
        ("4495", "SHRI SUDIP BANDYOPADHYAY (KOLKATA UTTAR)", 100),
        ("4495", "SHRI SUDIP BANDYOPADHYAY", 56),
    ]
    aliases, dropped = build_aliases(rows, PERSONS, _fold, _never, _never)
    assert aliases == {"4495": {"person_id": 38, "evidence_turns": 156}}
    assert dropped == {}


def test_conflicting_labels_are_dropped_never_guessed():
    # Same code printed with two different people's names -> never guess.
    rows = [
        ("540", "SHRI SUDIP BANDYOPADHYAY", 1),
        ("540", "SMT SUSHMA SWARAJ", 1),
    ]
    aliases, dropped = build_aliases(rows, PERSONS, _fold, _never, _never)
    assert aliases == {}
    assert dropped["540"]["reason"] == "conflict"
    assert set(dropped["540"]["persons"]) == {38, 3812}


def test_synthetic_block_never_aliased():
    assert is_synthetic_code(str(SYNTHETIC_MIN)) is True
    assert is_synthetic_code("10008") is True
    assert is_synthetic_code("5836") is False
    rows = [("10008", "SHRI SUDIP BANDYOPADHYAY", 200)]
    aliases, dropped = build_aliases(rows, PERSONS, _fold, _never, _never)
    assert aliases == {} and dropped == {}


def test_presiding_and_crowd_labels_do_not_vote():
    # A stray presiding label on a personal code must not create a conflict nor
    # an alias of its own; only the real name label counts.
    def is_presiding(label):
        return "SPEAKER" in label

    rows = [
        ("572", "SHRI H.D. DEVE GOWDA", 161),
        ("572", "MR. SPEAKER", 5),  # anchor-reuse stray; must be ignored
    ]
    aliases, dropped = build_aliases(rows, PERSONS, _fold, is_presiding, _never)
    assert aliases == {"572": {"person_id": 3960, "evidence_turns": 161}}
    assert dropped == {}


def test_non_ascii_synthetic_guard_is_safe():
    # A non-numeric code must not blow up is_synthetic_code.
    assert is_synthetic_code("abc") is False
    assert is_synthetic_code(None) is False
