"""Offline tests for the mpCode->person alias build (alias_build.py).

The one thing that matters here is never-guess: a code is aliased only when
(1) its resolvable printed name labels unanimously point at one person, AND
(2) that person's roster name is not refuted by the code's own DOMINANT
printed label -- the one with the most turns, counted over every label the
code ever carried, not just the ones that happened to resolve. The synthetic
minister block is never aliased, and presiding/crowd labels never vote or
count as a dominant label. No database, no network -- except for building
`_folded_key`/`_name_agreement` themselves, which come straight from
`debate_fetch` and are exercised for real, not stubbed, in the fixtures below
that freeze the actual T2 bug (internal_docs/036_THE_AUDIT_AND_FIX_LIST.md).
"""
from debate_fetch import _folded_key, _name_agreement, is_crowd_label, is_presiding_label

from alias_build import SYNTHETIC_MIN, build_aliases, is_synthetic_code

# ---------------------------------------------------------------------------
# Toy fixtures for the synthetic tests below. `_fold` is a deterministic
# stand-in, NOT the real `_folded_key` -- it only needs to be reproducible
# and land the test labels on PERSONS. `_agree` is the matching toy stand-in
# for `name_agreement`: it reuses the same hand-rolled table so these tests
# stay self-contained and exercise build_aliases's OWN wiring, not the real
# name-comparison algorithm (that is exercised for real further down).
# ---------------------------------------------------------------------------
PERSONS = {  # folded key (toy _fold) -> person id
    "bandyopadhyaysudip": 38,
    "devegowdahd": 3960,
    "swarajsushma": 3812,
}
PERSON_NAMES = {  # person id -> roster name, the reverse of PERSONS
    38: "Sudip Bandyopadhyay",
    3960: "H.D. Deve Gowda",
    3812: "Sushma Swaraj",
}
_NAME_TO_PID = {v: k for k, v in PERSON_NAMES.items()}


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


def _agree(label: str, roster_name: str) -> bool | None:
    """Toy name_agreement stand-in, built from the same table as `_fold`.

    True/False when the label's toy fold resolves to a known person (matching
    or not); None when the label's toy fold matches nobody at all -- "no
    evidence", the same three-state contract as the real
    debate_fetch._name_agreement.
    """
    pid = PERSONS.get(_fold(label))
    if pid is None:
        return None
    return pid == _NAME_TO_PID.get(roster_name)


def _never(_):  # is_presiding / is_crowd stub that says "no"
    return False


def test_unique_name_labels_alias():
    rows = [
        ("4495", "SHRI SUDIP BANDYOPADHYAY (KOLKATA UTTAR)", 100),
        ("4495", "SHRI SUDIP BANDYOPADHYAY", 56),
    ]
    aliases, dropped = build_aliases(rows, PERSONS, PERSON_NAMES, _fold, _never, _never, _agree)
    assert aliases == {"4495": {"person_id": 38, "evidence_turns": 156}}
    assert dropped == {}


def test_conflicting_labels_are_dropped_never_guessed():
    # Same code printed with two different people's names -> never guess.
    rows = [
        ("540", "SHRI SUDIP BANDYOPADHYAY", 1),
        ("540", "SMT SUSHMA SWARAJ", 1),
    ]
    aliases, dropped = build_aliases(rows, PERSONS, PERSON_NAMES, _fold, _never, _never, _agree)
    assert aliases == {}
    assert dropped["540"]["reason"] == "conflict"
    assert set(dropped["540"]["persons"]) == {38, 3812}


def test_synthetic_block_never_aliased():
    assert is_synthetic_code(str(SYNTHETIC_MIN)) is True
    assert is_synthetic_code("10008") is True
    assert is_synthetic_code("5836") is False
    rows = [("10008", "SHRI SUDIP BANDYOPADHYAY", 200)]
    aliases, dropped = build_aliases(rows, PERSONS, PERSON_NAMES, _fold, _never, _never, _agree)
    assert aliases == {} and dropped == {}


def test_presiding_and_crowd_labels_do_not_vote():
    # A stray presiding label on a personal code must not create a conflict nor
    # an alias of its own, nor be eligible as the dominant label; only the
    # real name label counts.
    def is_presiding(label):
        return "SPEAKER" in label

    rows = [
        ("572", "SHRI H.D. DEVE GOWDA", 161),
        ("572", "MR. SPEAKER", 5000),  # anchor-reuse stray, huge count -- still ignored
    ]
    aliases, dropped = build_aliases(rows, PERSONS, PERSON_NAMES, _fold, is_presiding, _never, _agree)
    assert aliases == {"572": {"person_id": 3960, "evidence_turns": 161}}
    assert dropped == {}


def test_non_ascii_synthetic_guard_is_safe():
    # A non-numeric code must not blow up is_synthetic_code.
    assert is_synthetic_code("abc") is False
    assert is_synthetic_code(None) is False


# ---------------------------------------------------------------------------
# The gate: real _folded_key / _name_agreement from debate_fetch, real
# label distributions pulled live from `turns` and frozen here (see
# internal_docs/036_THE_AUDIT_AND_FIX_LIST.md, T2, and the task report for
# how these were pulled). No stub-fold below this line.
# ---------------------------------------------------------------------------

# Every printed label ever recorded for mp_code 549, GROUP BY speaker_label,
# pulled live 2026-07-25. Every one names Arun Shourie -- a Rajya Sabha
# member, absent from `persons` entirely -- except one stray "MR.
# DEPUTY-SPEAKER" (presiding, excluded from voting either way).
MP_549_ARUN_SHOURIE_LABELS = [
    ("549", "SHRI ARUN SHOURIE", 344),
    (
        "549",
        "THE MINISTER OF COMMUNICATIONS AND INFORMATION TECHNOLOGY AND "
        "MINISTER OF DISINVESTMENT (SHRI ARUN SHOURIE)",
        9,
    ),
    ("549", "Shri  Arun Shourie", 5),
    ("549", "(SHRI ARUN SHOURIE)", 4),
    (
        "549",
        "THE MINISTER OF DISINVESTMENT, MINISTER OF DEVELOPMENT OF NORTH "
        "EASTERN REGION AND MINISTER OF COMMERCE AND INDUSTRY (SHRI ARUN "
        "SHOURIE)",
        3,
    ),
    (
        "549",
        "THE MINISTER OF DISINVESTMENT AND MINISTER OF DEVELOPMENT OF NORTH "
        "EASTERN REGION (SHRI ARUN SHOURIE)",
        3,
    ),
    ("549", "SHRI ARUN SHOURIE)", 1),
    (
        "549",
        "Sir, let me come to the cash flow discount method on which Shri Arun "
        "Shourie relied upon. Let me quote what Shri Kapil Sibal said in the "
        "Rajya Sabha on this issue. He said",
        1,
    ),
    ("549", "MR. DEPUTY-SPEAKER", 1),
    (
        "549",
        "MINISTER OF COMMUNICATIONS AND INFORMATION TECHNOLOGY AND MINISTER "
        "OF DISINVESTMENT (SHRI ARUN SHOURIE)",
        1,
    ),
    ("549", "*SHRI ARUN SHOURIE", 1),
]

# Every printed label ever recorded for mp_code 545, pulled live 2026-07-25.
# Every one names Ram Jethmalani -- also a Rajya Sabha member, also absent
# from `persons` -- except one stray sitting-time stamp ("1700 hrs").
MP_545_RAM_JETHMALANI_LABELS = [
    ("545", "SHRI RAM JETHMALANI", 56),
    ("545", "THE MINISTER OF LAW, JUSTICE AND COMPANY AFFAIRS (SHRI RAM JETHMALANI)", 26),
    ("545", '"> SHRI RAM JETHMALANI', 7),
    ("545", '">SHRI RAM JETHMALANI', 6),
    ("545", "SHR RAM JETHMALANI", 1),
    ("545", "1700 hrs", 1),
    ("545", "THE MINISTER FOR LAW, JUSTICE & COMPANY AFFAIRS (SHRI RAM JETHMALANI)", 1),
    ("545", '"> THE MINISTER OF LAW, JUSTICE AND COMPANY AFFAIRS (SHRI RAM JETHMALANI)', 1),
]

# Every printed label ever recorded for mp_code 4473, pulled live 2026-07-25.
# Every one -- Devanagari and Latin -- names Jagdish Sharma, an MP who IS in
# `persons` under his own different mpCode.
MP_4473_JAGDISH_SHARMA_LABELS = [
    ("4473", "श्री जगदीश शर्मा", 30),
    ("4473", "श्री जगदीश शर्मा (जहानाबाद)", 18),
    ("4473", "श्री जगदीश शर्मा ( जहानाबाद )", 6),
    ("4473", "Shri Jagdish Sharma", 1),
]

CHENNITHALA_PID, CHENNITHALA_NAME = 327, "Ramesh Chennithala"
AMBEDKAR_PID, AMBEDKAR_NAME = 54, "Prakash Yashwant Ambedkar"
PAL_PID, PAL_NAME = 1168, "Jagdambika Pal"

REAL_PERSON_NAMES = {
    CHENNITHALA_PID: CHENNITHALA_NAME,
    AMBEDKAR_PID: AMBEDKAR_NAME,
    PAL_PID: PAL_NAME,
    59: "Ananth Kumar",
    134: "Sudip Bandyopadhyay",
    419: "H.D. Devegowda",
    1729: "Kapil Sibal",
    1950: "Sushma Swaraj",
}


def test_alias_refused_when_label_disagrees_with_person():
    """mp_code 549: this is the actual T2 bug, reconstructed.

    IMPORTANT on the fixture: this task's investigation could NOT find any
    label currently in the corpus for mp_code 549 whose real `_folded_key`
    equals `_folded_key("Ramesh Chennithala")` -- not even the truncated
    body-of-speech line ("Sir, let me come to the cash flow discount
    method...", the natural suspect), whose fold is a ~100-character blob of
    every word in the sentence and cannot equal a two-word name key by
    construction. Exhaustive search (every label ever recorded for 549, and
    every turn anywhere naming Chennithala -- all of which already resolve
    correctly under his OWN mpCode 86) turned up nothing that could have cast
    the original stray vote; see the task report for the full account. The
    evidence has been consumed by at least one populate_turns.py re-run since
    the alias was built (mpcode_aliases is itself downstream of `turns`, and
    nothing preserves the pre-backfill state).

    So this fixture freezes the REAL Arun Shourie label distribution and
    adds ONE synthetic label that DOES fold-match Chennithala, standing in
    for whatever the lost original vote was. This is honest about being a
    reconstruction of the bug's SHAPE (one resolving vote, unopposed only
    because hundreds of contrary labels never resolved to anyone) rather
    than a byte-for-byte replay of history -- and it is exactly the shape
    the new gate exists to catch regardless of which literal string
    produced the stray vote.
    """
    rows = MP_549_ARUN_SHOURIE_LABELS + [("549", "SHRI RAMESH CHENNITHALA", 1)]
    upk = {_folded_key(CHENNITHALA_NAME): CHENNITHALA_PID}
    aliases, dropped = build_aliases(
        rows, upk, REAL_PERSON_NAMES, _folded_key, is_presiding_label, is_crowd_label, _name_agreement
    )
    assert aliases == {}
    assert dropped["549"]["reason"] == "outweighed"
    assert dropped["549"]["person_id"] == CHENNITHALA_PID
    assert dropped["549"]["dominant_label"] == "SHRI ARUN SHOURIE"
    # Sanity: the disagreement is real, not a fixture artefact.
    assert _name_agreement("SHRI ARUN SHOURIE", CHENNITHALA_NAME) is False


def test_alias_refused_when_label_disagrees_with_person_545():
    """mp_code 545: same class as 549, this time Ram Jethmalani / Ambedkar.

    Same caveat as the 549 test: no label currently on 545 folds to Prakash
    Yashwant Ambedkar under the real `_folded_key` (verified: neither "1700
    hrs" nor any Jethmalani spelling variant does), so the Ambedkar vote is
    synthetic, standing in for lost evidence.
    """
    rows = MP_545_RAM_JETHMALANI_LABELS + [("545", "SHRI PRAKASH YASHWANT AMBEDKAR", 1)]
    upk = {_folded_key(AMBEDKAR_NAME): AMBEDKAR_PID}
    aliases, dropped = build_aliases(
        rows, upk, REAL_PERSON_NAMES, _folded_key, is_presiding_label, is_crowd_label, _name_agreement
    )
    assert aliases == {}
    assert dropped["545"]["reason"] == "outweighed"
    assert dropped["545"]["person_id"] == AMBEDKAR_PID
    assert dropped["545"]["dominant_label"] == "SHRI RAM JETHMALANI"


def test_alias_refused_when_label_disagrees_with_person_4473():
    """mp_code 4473: Jagdish Sharma (Devanagari-dominant) / Jagdambika Pal.

    Same caveat again: no real label on 4473 folds to Jagdambika Pal (he
    already resolves correctly under his own mpCode 4295 everywhere he is
    printed by name); the Pal vote below is synthetic. Devanagari labels
    dominate here, unlike 549/545 -- this exercises the gate against a
    script the other two fixtures don't.
    """
    rows = MP_4473_JAGDISH_SHARMA_LABELS + [("4473", "SHRI JAGDAMBIKA PAL", 1)]
    upk = {_folded_key(PAL_NAME): PAL_PID}
    aliases, dropped = build_aliases(
        rows, upk, REAL_PERSON_NAMES, _folded_key, is_presiding_label, is_crowd_label, _name_agreement
    )
    assert aliases == {}
    assert dropped["4473"]["reason"] == "outweighed"
    assert dropped["4473"]["person_id"] == PAL_PID
    assert dropped["4473"]["dominant_label"] == "श्री जगदीश शर्मा"


def test_alias_refused_on_single_weak_evidence():
    """A code with evidence_turns=1 standing against dozens of contrary
    labels must not win -- internal_docs/036_THE_AUDIT_AND_FIX_LIST.md's own
    name for this case.

    Using the 545 fixture: the single Ambedkar vote (evidence_turns=1) is
    outnumbered 99-to-1 by real Ram Jethmalani labels. This is the same
    mechanism as test_alias_refused_when_label_disagrees_with_person_545 --
    deliberately so. The label-agreement gate closes this case on its own; a
    bare `evidence_turns >= N` threshold is a DIFFERENT, cruder rule that
    was measured and rejected (see the task report): it would also refuse
    six of the 29 currently-correct rows (579, 596, 597, 1200, 4280, 4888),
    every one of which has evidence_turns == 1 because its single printed
    label simply never had a reason to be repeated (e.g. a minister named
    once by full title). No bare-count rule is added here.
    """
    rows = MP_545_RAM_JETHMALANI_LABELS + [("545", "SHRI PRAKASH YASHWANT AMBEDKAR", 1)]
    upk = {_folded_key(AMBEDKAR_NAME): AMBEDKAR_PID}
    aliases, dropped = build_aliases(
        rows, upk, REAL_PERSON_NAMES, _folded_key, is_presiding_label, is_crowd_label, _name_agreement
    )
    assert aliases == {}
    assert "545" in dropped


def test_alias_still_mints_sudip_bandyopadhyay():
    """mp_code 4495, a currently-correct row: real dominant label agrees."""
    rows = [
        ("4495", "SHRI SUDIP BANDYOPADHYAY", 65),
        ("4495", "SHRI SUDIP BANDYOPADHYAY (KOLKATA UTTAR)", 54),
        (
            "4495",
            "THE MINISTER OF STATE IN THE MINISTRY OF HEALTH AND FAMILY "
            "WELFARE (SHRI SUDIP BANDYOPADHYAY)",
            21,
        ),
        ("4495", "श्री सुदीप बंदोपाध्याय", 4),
        ("4495", "Shri Sudip Bandyopadhyay", 3),
    ]
    upk = {_folded_key("Sudip Bandyopadhyay"): 134}
    aliases, dropped = build_aliases(
        rows, upk, REAL_PERSON_NAMES, _folded_key, is_presiding_label, is_crowd_label, _name_agreement
    )
    # evidence_turns counts only the labels that FOLD onto the person, which is
    # not every label printed for the code: "श्री सुदीप बंदोपाध्याय" (4 turns) is
    # a different Devanagari spelling that transliterates to a different fold
    # key, so it never becomes a vote. It is still counted as evidence by the
    # weight gate below -- agreeing and voting are separate questions, and
    # conflating them is what makes a number here mean less than it looks.
    assert aliases == {"4495": {"person_id": 134, "evidence_turns": 65 + 54 + 21 + 3}}
    assert dropped == {}


def test_alias_still_mints_kapil_sibal():
    """mp_code 575, a currently-correct row: clean two-label case, no script mixing."""
    rows = [
        ("575", "SHRI KAPIL SIBAL", 15),
        ("575", "SHRI KAPIL SIBAL (BIHAR)", 1),
    ]
    upk = {_folded_key("Kapil Sibal"): 1729}
    aliases, dropped = build_aliases(
        rows, upk, REAL_PERSON_NAMES, _folded_key, is_presiding_label, is_crowd_label, _name_agreement
    )
    assert aliases == {"575": {"person_id": 1729, "evidence_turns": 16}}
    assert dropped == {}


def test_alias_still_mints_sushma_swaraj_devanagari_dominant():
    """mp_code 586: Devanagari is the DOMINANT label here (253 of 398 turns),
    not just a minority variant -- this is the Devanagari coverage the T2
    task asked for, using the code where it actually decides the outcome.
    """
    rows = [
        ("586", "श्रीमती सुषमा स्वराज", 253),
        ("586", "स्वास्थ्य और परिवार कल्याण मंत्री तथा संसदीय कार्य मंत्री (श्रीमती सुषमा स्वराज)", 88),
        ("586", "SHRIMATI SUSHMA SWARAJ", 46),
        ("586", "सूचना और प्रसारण मंत्री (श्रीमती सुषमा स्वराज)", 6),
        (
            "586",
            "THE MINISTER OF HEALTH AND FAMILY WELFARE AND MINISTER OF "
            "PARLIAMENTARY AFFAIRS (SHRIMATI SUSHMA SWARAJ)",
            5,
        ),
    ]
    upk = {_folded_key("Sushma Swaraj"): 1950}
    aliases, dropped = build_aliases(
        rows, upk, REAL_PERSON_NAMES, _folded_key, is_presiding_label, is_crowd_label, _name_agreement
    )
    # Only the two Latin labels fold onto "Sushma Swaraj" (46 + 5 = 51); the
    # Devanagari ones transliterate to a near-but-not-equal key. So the winner
    # is minted on 51 votes even though the dominant label carries 253 turns --
    # and that is fine, because the dominant label AGREES with her (limb (a) of
    # the weight gate). Under limb (b) alone she would be refused: the 88-turn
    # Devanagari ministerial designation fails to collapse to the name inside
    # its brackets and reads as a refutation, 88 > 51. She is exactly why the
    # gate is a union of two tests rather than either one.
    assert aliases == {"586": {"person_id": 1950, "evidence_turns": 46 + 5}}
    assert dropped == {}


def test_alias_1200_ananth_kumar_has_no_reconstructible_evidence():
    """mp_code 1200 is one of the 29 CURRENTLY-CORRECT rows (per the task's
    own ground truth: Ananth Kumar, evidence_turns=1). But every turn ever
    recorded for 1200 in the live corpus (8 of them) carries the SAME
    presiding label, "MR. CHAIRMAN" -- nothing that could ever fold-match
    Ananth Kumar, and nothing left over once presiding labels are excluded
    from voting. Whatever originally produced this row's single vote is, by
    exhaustive search, no longer present anywhere in `turns` for this code.

    This is not a bug this gate introduces -- rebuilding fresh from today's
    `turns` under the OLD (pre-T2) build_aliases also fails to produce this
    row at all (verified live: a full rebuild today yields exactly one row,
    for an unrelated code, not 1200). It is flagged here as a genuine,
    surprising, out-of-task finding: this row's own evidence is already gone
    from the corpus, same as the three poisoned rows, except this one
    happens to be correct.
    """
    rows = [("1200", "MR. CHAIRMAN", 8)]
    upk = {_folded_key("Ananth Kumar"): 59}
    aliases, dropped = build_aliases(
        rows, upk, REAL_PERSON_NAMES, _folded_key, is_presiding_label, is_crowd_label, _name_agreement
    )
    # No vote is even cast: "MR. CHAIRMAN" is presiding and is excluded before
    # folding is attempted, so the code never becomes a candidate at all.
    assert aliases == {} and dropped == {}


def test_alias_build_is_reproducible():
    """Building twice from identical input yields identical output."""
    rows = MP_549_ARUN_SHOURIE_LABELS + [("549", "SHRI RAMESH CHENNITHALA", 1)]
    upk = {_folded_key(CHENNITHALA_NAME): CHENNITHALA_PID}
    args = (rows, upk, REAL_PERSON_NAMES, _folded_key, is_presiding_label, is_crowd_label, _name_agreement)
    first = build_aliases(*args)
    second = build_aliases(*args)
    assert first == second


def test_alias_still_mints_deve_gowda_despite_a_spelling_variant():
    """mp_code 572, a currently-correct row -- and the one the blunt version of
    this gate killed.

    H.D. Deve Gowda is a former Prime Minister with 161 turns of evidence under
    this code. The source prints him "SHRI H.D. DEVE GOWDA"; the roster spells
    him "H.D. Devegowda" -- one word against two. `_name_agreement` calls that
    a disagreement, and it is wrong to: the audit says of that function that it
    "flags orthographic variants as disagreements", so a False verdict is an
    upper bound on disagreement, never proof of a different human.

    A rule of "the dominant label must positively agree, or refuse" therefore
    discards a former PM's entire speaking history under this code. He is saved
    by limb (b): the labels that positively fold onto him (161 turns) outweigh
    the largest label that refutes him (121). Weight, not agreement, is what
    separates a spelling variant from the Arun Shourie poison, where a SINGLE
    turn stood against 344 contrary ones.
    """
    rows = [
        ("572", "SHRI H.D. DEVE GOWDA", 121),
        ("572", "श्री एच.डी. देवेगौड़ा", 40),
    ]
    upk = {
        _folded_key("SHRI H.D. DEVE GOWDA"): 419,
        _folded_key("श्री एच.डी. देवेगौड़ा"): 419,
    }
    aliases, dropped = build_aliases(
        rows, upk, REAL_PERSON_NAMES, _folded_key, is_presiding_label,
        is_crowd_label, _name_agreement,
    )
    assert aliases == {"572": {"person_id": 419, "evidence_turns": 161}}
    assert dropped == {}


def test_a_none_verdict_is_never_counted_as_a_refutation():
    """"Nothing was compared" must not be read as "they disagree".

    `_name_agreement` returns None when neither side yielded a usable name
    word. Counting that as refutation would let an unreadable label -- of which
    this corpus has tens of thousands -- veto a perfectly good alias. The
    mirror of the mistake already recorded in `_name_agreement`'s own
    docstring, where None was read as agreement and stamped one name across a
    whole sitting.
    """
    rows = [
        ("999", "SHRI KAPIL SIBAL", 3),
        ("999", "( ... )", 500),          # no name words at all -> verdict None
    ]
    upk = {_folded_key("Kapil Sibal"): 1729}
    aliases, dropped = build_aliases(
        rows, upk, REAL_PERSON_NAMES, _folded_key, is_presiding_label,
        is_crowd_label, _name_agreement,
    )
    assert aliases == {"999": {"person_id": 1729, "evidence_turns": 3}}, (
        "a 500-turn label that compares to nothing must not outvote 3 real ones"
    )


def test_a_bigger_refuting_label_outweighs_a_stray_vote():
    """The poison signature, in the abstract: one vote against many contrary
    printed labels. Neither limb of the gate holds, so the row is refused."""
    rows = [
        ("888", "SHRI KAPIL SIBAL", 1),
        ("888", "SHRI RAM JETHMALANI", 200),
    ]
    upk = {_folded_key("Kapil Sibal"): 1729}
    aliases, dropped = build_aliases(
        rows, upk, REAL_PERSON_NAMES, _folded_key, is_presiding_label,
        is_crowd_label, _name_agreement,
    )
    assert aliases == {}
    assert dropped["888"]["reason"] == "outweighed"
    assert dropped["888"]["refuting_turns"] == 200
    assert dropped["888"]["evidence_turns"] == 1
