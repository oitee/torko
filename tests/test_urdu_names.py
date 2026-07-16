"""
Reading Urdu-script speaker labels.

A few members are recorded in Urdu rather than English or Devanagari. That is a
third script, and translit only knows Devanagari, so an Urdu label folds to no
usable name -- which is how Asaduddin Owaisi's speech came to be credited to
Kiren Rijiju before 5f9bd3c (see tests/test_anchor_reuse.py). These pin the
hand-verified lookup that reads them instead.

The labels below are the exact strings from LS18/3/1758 and LS17/5/5464,
"] " artifact and all -- not retyped Urdu, which would risk substituting a
visually identical character and testing something the corpus never contains.
"""
import pytest

import debate_fetch
from urdu_names import URDU_SPEAKER_NAMES, looks_urdu, urdu_label_to_name

# (label as printed, romanised name, sansad_id verified via the constituency)
REAL_LABELS = [
    ("جناب اسدالدین اویسی ( حیدرآباد )", "Asaduddin Owaisi", "4091"),
    ("] جناب ضیاءالرحمان ( سنبھل )", "Zia Ur Rehman", "5822"),
    ("] کنور دانش علی ( امروہہ )", "Kunwar Danish Ali", "5134"),
    ("] جناب حاجی فضل الرحمٰن صاحب ( سہارنپور )", "Haji Fazlur Rehman", "5161"),
]


class TestLooksUrdu:
    def test_arabic_script_label_is_urdu(self):
        assert looks_urdu("جناب اسدالدین اویسی ( حیدرآباد )") is True

    def test_devanagari_is_not_urdu(self):
        # the point of the check: Hindi labels must keep the Devanagari path
        assert looks_urdu("श्री असदुद्दीन ओवैसी") is False

    def test_english_is_not_urdu(self):
        assert looks_urdu("SHRI ASADUDDIN OWAISI (HYDERABAD)") is False

    def test_empty_is_not_urdu(self):
        assert looks_urdu("") is False


class TestUrduLabelToName:
    @pytest.mark.parametrize("label,expected,_id", REAL_LABELS)
    def test_real_labels_map_to_their_verified_name(self, label, expected, _id):
        assert urdu_label_to_name(label) == expected

    def test_an_unknown_urdu_name_is_none_not_a_guess(self):
        # the safety property that lets the table be incomplete: a name we have
        # not verified leaves the speaker unresolved, exactly as today. The
        # table can reduce misses; it can never introduce a wrong answer.
        assert urdu_label_to_name("جناب کوئی اور شخص ( کہیں )") is None

    def test_a_non_urdu_label_is_left_alone(self):
        assert urdu_label_to_name("SHRI ANURAG SINGH THAKUR") is None

    def test_the_leading_bracket_artifact_does_not_defeat_the_lookup(self):
        # several real labels open with a stray "]"; with and without it must
        # reach the same person
        assert urdu_label_to_name("] جناب اسدالدین اویسی ( حیدرآباد )") == (
            urdu_label_to_name("جناب اسدالدین اویسی ( حیدرآباد )")
        )

    def test_the_constituency_is_not_part_of_the_key(self):
        # Owaisi appears with and without a seat suffix across debates
        assert urdu_label_to_name("جناب اسدالدین اویسی") == "Asaduddin Owaisi"


class TestResolvesThroughTheOrdinaryTiers:
    """The lookup yields a NAME, not a member id, so every guard still runs."""

    def test_a_known_urdu_label_resolves_to_the_right_member(self):
        roster = [
            {"mpCode": "4091", "mpName": "Shri Asaduddin Owaisi"},
            {"mpCode": "5822", "mpName": "Shri Zia Ur Rehman"},
        ]
        index = debate_fetch.build_speaker_index(roster)
        source, entry = debate_fetch.resolve_speaker(
            "جناب اسدالدین اویسی ( حیدرآباد )", index
        )
        assert entry["mpCode"] == "4091"
        assert source == "name-exact"

    def test_an_unknown_urdu_label_still_resolves_to_nothing(self):
        index = debate_fetch.build_speaker_index(
            [{"mpCode": "4091", "mpName": "Shri Asaduddin Owaisi"}]
        )
        assert debate_fetch.resolve_speaker("جناب کوئی اور ( کہیں )", index) == (None, None)

    def test_the_never_guess_rule_still_applies_to_a_read_urdu_name(self):
        # Two different Owaisis both sat for Hyderabad -- Sultan Salahuddin
        # (13th) and Asaduddin (18th), father and son. Mapping to a name rather
        # than an id is what keeps that guard in play: if a reading ever lands
        # on a name two members share, it must resolve to nobody rather than
        # pick one.
        roster = [
            {"mpCode": "1", "mpName": "Asaduddin Owaisi"},
            {"mpCode": "2", "mpName": "Asaduddin Owaisi"},
        ]
        index = debate_fetch.build_speaker_index([], db_roster=roster)
        assert debate_fetch.resolve_speaker(
            "جناب اسدالدین اویسی ( حیدرآباد )", index
        ) == (None, None)


class TestTableHygiene:
    def test_every_key_is_stored_without_a_constituency_or_bracket(self):
        # keys are compared against _name_part output, so a key carrying a seat
        # suffix would silently never match
        for key in URDU_SPEAKER_NAMES:
            assert "(" not in key and "]" not in key
            assert key == key.strip()

    def test_every_value_is_romanised(self):
        for name in URDU_SPEAKER_NAMES.values():
            assert name.isascii(), f"{name!r} must be the roster's romanised spelling"
