"""Attribute a ministerial turn by the name in its OWN label, never by the
shared minister-slot mpCode (see internal_docs 033).

The synthetic block (mpCode >= 10000) is a role-slot the source reuses across
people -- 10008 is Ravi Shankar Prasad in one turn and Anbumani Ramadoss in
another. So the code cannot name the speaker; the label must, per turn, matched
uniquely against the roster and dropped when ambiguous.

These use the REAL _folded_key / is_presiding_label / is_crowd_label (all pure,
no DB) so they assert real behaviour, over a tiny hand-built roster index.
"""
from debate_fetch import _folded_key, is_crowd_label, is_presiding_label
from label_attribution import build_unique_index, resolve_label_to_person

# pid -> canonical roster name. Two Chandra Shekhars on purpose (a real ceiling).
ROSTER = {
    1288: "Shivraj V. Patil",
    1426: "Anbumani Ramadoss",
    1349: "Ravi Shankar Prasad",
    615: "Smriti Zubin Irani",
    5551: "Piyush Vedprakash Goyal",
    72: "Chandra Shekhar",
    5647: "Chandra Shekhar",
}
INDEX = build_unique_index(ROSTER, _folded_key)


def _resolve(label):
    return resolve_label_to_person(label, INDEX, _folded_key, is_presiding_label, is_crowd_label)


# ---- the never-guess core: the index itself ----

def test_index_drops_colliding_key():
    # Chandra Shekhar folds to one key shared by two people -> not in the index.
    assert _folded_key("Chandra Shekhar") not in INDEX


def test_index_keeps_unique_key():
    assert INDEX[_folded_key("Shivraj V. Patil")] == 1288


# ---- resolution by the turn's own label ----

def test_plain_english_name_resolves():
    assert _resolve("SHRI SHIVRAJ V. PATIL") == 1288


def test_ministerial_title_paren_name_resolves():
    assert _resolve("THE MINISTER OF HOME AFFAIRS (SHRI SHIVRAJ V. PATIL)") == 1288


def test_long_multi_portfolio_title_resolves():
    assert _resolve(
        "THE MINISTER OF LAW AND JUSTICE AND MINISTER OF ELECTRONICS AND IT "
        "(SHRI RAVI SHANKAR PRASAD)"
    ) == 1349


def test_same_slot_code_two_people_prasad_side():
    # In the corpus this label carries mpCode 10008.
    assert _resolve("SHRI RAVI SHANKAR PRASAD") == 1349


def test_same_slot_code_two_people_ramadoss_side():
    # SAME mpCode 10008, different turn, different human -- resolved by label.
    assert _resolve("DR. ANBUMANI RAMADOSS") == 1426


def test_devanagari_label_that_folds_uniquely_resolves():
    # Folds to the same key as the roster spelling; no transliteration edit needed.
    assert _resolve("श्री रवि शंकर प्रसाद") == 1349


def test_rajya_sabha_minister_absent_from_roster_drops():
    # Jaitley is not in this roster (a real RS member) -> never guessed.
    assert _resolve("SHRI ARUN JAITLEY") is None


def test_name_form_mismatch_drops_safely():
    # Label "Piyush Goyal" folds differently from roster "Piyush Vedprakash Goyal".
    assert _resolve("SHRI PIYUSH GOYAL") is None


def test_presiding_label_never_attributed():
    assert _resolve("माननीय अध्यक्ष") is None
    assert _resolve("MR. SPEAKER") is None


def test_crowd_label_never_attributed():
    assert _resolve("अनेक माननीय सदस्य") is None


def test_honorific_only_label_drops():
    # No name token -> empty fold key -> must not wildcard-match anyone.
    assert _resolve("SHRI") is None


def test_empty_and_none_labels_drop():
    assert _resolve("") is None
    assert _resolve(None) is None


def test_colliding_name_label_drops_never_guessed():
    # Two Chandra Shekhars: the label names one of two people -> refuse.
    assert _resolve("SHRI CHANDRA SHEKHAR") is None
