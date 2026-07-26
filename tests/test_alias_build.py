from debate_fetch import _folded_key, _name_agreement, is_crowd_label, is_presiding_label

from alias_build import SYNTHETIC_MIN, build_aliases, is_synthetic_code

# Toy fixtures. _fold and _agree are stand-ins, not the real functions.
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
    return {
        "SHRI SUDIP BANDYOPADHYAY (KOLKATA UTTAR)": "bandyopadhyaysudip",
        "SHRI SUDIP BANDYOPADHYAY": "bandyopadhyaysudip",
        "SHRI H.D. DEVE GOWDA": "devegowdahd",
        "SMT SUSHMA SWARAJ": "swarajsushma",
    }.get(label, "__unmatched__")


def _agree(label: str, roster_name: str) -> bool | None:
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


# Real _folded_key and _name_agreement with label counts frozen from the database.

# Real labels for mp_code 549 (Arun Shourie, not in persons), plus one presiding label.
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

# Real labels for mp_code 545 (Ram Jethmalani, not in persons), plus one time stamp.
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

# Real labels for mp_code 4473 (Jagdish Sharma, who is in persons under another code).
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
    rows = MP_549_ARUN_SHOURIE_LABELS + [("549", "SHRI RAMESH CHENNITHALA", 1)]
    upk = {_folded_key(CHENNITHALA_NAME): CHENNITHALA_PID}
    aliases, dropped = build_aliases(
        rows, upk, REAL_PERSON_NAMES, _folded_key, is_presiding_label, is_crowd_label, _name_agreement
    )
    assert aliases == {}
    assert dropped["549"]["reason"] == "outweighed"
    assert dropped["549"]["person_id"] == CHENNITHALA_PID
    assert dropped["549"]["dominant_label"] == "SHRI ARUN SHOURIE"
    assert _name_agreement("SHRI ARUN SHOURIE", CHENNITHALA_NAME) is False


def test_alias_refused_when_label_disagrees_with_person_545():
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
    rows = MP_545_RAM_JETHMALANI_LABELS + [("545", "SHRI PRAKASH YASHWANT AMBEDKAR", 1)]
    upk = {_folded_key(AMBEDKAR_NAME): AMBEDKAR_PID}
    aliases, dropped = build_aliases(
        rows, upk, REAL_PERSON_NAMES, _folded_key, is_presiding_label, is_crowd_label, _name_agreement
    )
    assert aliases == {}
    assert "545" in dropped


def test_alias_still_mints_sudip_bandyopadhyay():
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
    # evidence_turns counts only the labels that fold onto the person.
    assert aliases == {"4495": {"person_id": 134, "evidence_turns": 65 + 54 + 21 + 3}}
    assert dropped == {}


def test_alias_still_mints_kapil_sibal():
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
    # Only the two Latin labels fold onto Sushma Swaraj (46 + 5 = 51). The dominant label has 253 turns and agrees with her.
    assert aliases == {"586": {"person_id": 1950, "evidence_turns": 46 + 5}}
    assert dropped == {}


def test_alias_1200_ananth_kumar_has_no_reconstructible_evidence():
    rows = [("1200", "MR. CHAIRMAN", 8)]
    upk = {_folded_key("Ananth Kumar"): 59}
    aliases, dropped = build_aliases(
        rows, upk, REAL_PERSON_NAMES, _folded_key, is_presiding_label, is_crowd_label, _name_agreement
    )
    # Presiding labels are excluded before folding, so no vote is cast.
    assert aliases == {} and dropped == {}


def test_alias_build_is_reproducible():
    rows = MP_549_ARUN_SHOURIE_LABELS + [("549", "SHRI RAMESH CHENNITHALA", 1)]
    upk = {_folded_key(CHENNITHALA_NAME): CHENNITHALA_PID}
    args = (rows, upk, REAL_PERSON_NAMES, _folded_key, is_presiding_label, is_crowd_label, _name_agreement)
    first = build_aliases(*args)
    second = build_aliases(*args)
    assert first == second


def test_alias_still_mints_deve_gowda_despite_a_spelling_variant():
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
