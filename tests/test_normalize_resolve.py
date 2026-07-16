"""
Part 3 — standardising speaker names against the mpPartDetailList roster.

Covers PARSING_STRATEGY.md §3.1–3.3:
  _normalize_name      — reduce a label to bare comparable name-tokens
  build_speaker_index  — pre-built lookup tables
  resolve_speaker      — four-tier fuzzy matcher
  annotate_speakers    — write the canonical name + nameSource back onto turns

Includes the regression test for the "empty-token wildcard" bug where an MP
whose name normalised to nothing (e.g. "Dr. (Smt.) V. Saroja" collapsing to [])
matched *every* unresolved label.
"""
import pytest

from debate_fetch import (
    _normalize_name,
    annotate_speakers,
    build_speaker_index,
    resolve_speaker,
)


# A small stand-in roster covering the interesting name shapes.
ROSTER = [
    {"mpName": "Shri Raja A", "mpCode": 344, "mpPartCode": 24},
    {"mpName": "Shri Kodikunnil Suresh", "mpCode": 100, "mpPartCode": 1},
    {"mpName": "Shri Lavu Sri Krishna Devarayalu", "mpCode": 200, "mpPartCode": 3},
    {"mpName": "Dr. (Smt.) V. Saroja", "mpCode": 403, "mpPartCode": 1},
]


class TestNormalizeName:
    """§3.1: label -> lowercase name-token list, honorifics/constituency dropped."""

    def test_drops_honorific_and_constituency(self):
        # "SHRI A. RAJA (NILGIRIS)" -> ["a", "raja"]
        assert _normalize_name("SHRI A. RAJA (NILGIRIS)") == ["a", "raja"]

    def test_roster_form_keeps_word_order_as_given(self):
        # "Shri Raja A" -> ["raja", "a"]  (different order from the label above)
        assert _normalize_name("Shri Raja A") == ["raja", "a"]

    def test_ministerial_title_extracts_name_inside_parentheses(self):
        # §3.1 special case: the real name lives inside the parens after an honorific
        assert _normalize_name("THE MINISTER OF STEEL (SHRI PRALHAD JOSHI)") == ["pralhad", "joshi"]

    def test_honorific_only_parenthetical_is_not_treated_as_the_name(self):
        # Regression (fix 2): "(Smt.)" is a bare honorific, NOT a ministerial name.
        # It must be dropped as a constituency, leaving the outer "V. Saroja".
        assert _normalize_name("Dr. (Smt.) V. Saroja") == ["v", "saroja"]

    def test_purely_honorific_label_normalises_to_empty(self):
        # nothing but honorifics -> no comparable tokens at all
        assert _normalize_name("Dr.") == []
        assert _normalize_name("Shri Smt") == []

    def test_devanagari_label_passes_through_without_romanising(self):
        # §3.1 / open-question 1: Indic script can't match the romanised roster;
        # it survives as (non-empty) tokens rather than crashing or vanishing.
        toks = _normalize_name("श्री किरेन रिजिजू")
        assert toks  # non-empty
        assert all(not t.isascii() for t in toks)


class TestBuildSpeakerIndex:
    """§3.2: the four pre-built lookup tables."""

    def test_exposes_all_four_lookup_tables(self):
        idx = build_speaker_index(ROSTER)
        assert set(idx) == {"by_str", "by_join_ordered", "by_join_sorted", "tokenised"}

    def test_by_str_keys_on_space_joined_tokens(self):
        idx = build_speaker_index(ROSTER)
        assert "raja a" in idx["by_str"]

    def test_tokenised_has_one_entry_per_roster_member(self):
        idx = build_speaker_index(ROSTER)
        assert len(idx["tokenised"]) == len(ROSTER)


class TestResolveSpeaker:
    """§3.2: the four confidence tiers + the ambiguity / empty guards."""

    @pytest.fixture
    def index(self):
        return build_speaker_index(ROSTER)

    def test_tier1_name_exact(self, index):
        source, entry = resolve_speaker("SHRI KODIKUNNIL SURESH", index)
        assert source == "name-exact"
        assert entry["mpCode"] == 100

    def test_tier2_name_join_ignores_word_order(self, index):
        # "SHRI A. RAJA" (a, raja) vs roster "Shri Raja A" (raja, a): sorted-equal
        source, entry = resolve_speaker("SHRI A. RAJA (NILGIRIS)", index)
        assert source == "name-join"
        assert entry["mpCode"] == 344

    def test_tier2_name_join_ignores_spacing(self, index):
        # "SRIKRISHNA" glued vs roster "Sri Krishna": equal once spacing removed
        source, entry = resolve_speaker("SHRI LAVU SRIKRISHNA DEVARAYALU", index)
        assert source == "name-join"
        assert entry["mpCode"] == 200

    def test_tier3_name_partial_subset_unique(self, index):
        # "SURESH" is a subset of exactly one roster name -> partial match
        source, entry = resolve_speaker("SHRI SURESH KODIKUNNIL EXTRA", index)
        assert source == "name-partial"
        assert entry["mpCode"] == 100

    def test_unmatched_label_returns_none(self, index):
        # presiding officer isn't in the roster (open-question 2)
        assert resolve_speaker("MR. SPEAKER", index) == (None, None)

    def test_empty_label_returns_none(self, index):
        assert resolve_speaker("Dr.", index) == (None, None)

    def test_empty_token_roster_entry_never_wildcard_matches(self):
        # Regression (fix 1): a roster name that normalises to [] must NOT become
        # a subset-of-everything wildcard. Here the only roster entry is all
        # honorifics; an unrelated label must stay unmatched.
        idx = build_speaker_index([{"mpName": "Dr.", "mpCode": 999, "mpPartCode": 1}])
        assert resolve_speaker("SHRI BIKRAM KESHARI DEO (KALAHANDI)", idx) == (None, None)

    def test_ambiguous_partial_match_is_rejected(self):
        # "Kumar" is a subset of two DIFFERENT people -> not confident -> None
        roster = [
            {"mpName": "Shri Ram Kumar", "mpCode": 1, "mpPartCode": 1},
            {"mpName": "Shri Shyam Kumar", "mpCode": 2, "mpPartCode": 1},
        ]
        idx = build_speaker_index(roster)
        assert resolve_speaker("SHRI KUMAR", idx) == (None, None)


class TestAnnotateSpeakers:
    """§3.3: write canonical name + nameSource onto each turn."""

    def test_anchored_turn_is_tagged_anchor_and_left_alone(self):
        segs = [{"mpCode": "344", "speakerLabel": "SHRI A. RAJA", "mpName": "Shri Raja A"}]
        annotate_speakers(segs, ROSTER)
        assert segs[0]["nameSource"] == "anchor"

    def test_anchorless_match_inherits_official_id_and_name(self):
        segs = [{"mpCode": None, "speakerLabel": "SHRI KODIKUNNIL SURESH", "mpName": "SHRI KODIKUNNIL SURESH"}]
        annotate_speakers(segs, ROSTER)
        assert segs[0]["mpCode"] == "100"
        assert segs[0]["mpName"] == "Shri Kodikunnil Suresh"
        assert segs[0]["nameSource"] == "name-exact"

    def test_unmatched_label_kept_as_unresolved(self):
        segs = [{"mpCode": None, "speakerLabel": "SHRI NOBODY SPECIAL", "mpName": "SHRI NOBODY SPECIAL"}]
        annotate_speakers(segs, ROSTER)
        assert segs[0]["nameSource"] == "unresolved"
        assert segs[0]["mpName"] == "SHRI NOBODY SPECIAL"  # raw label preserved

    def test_labelless_segment_gets_none_source(self):
        segs = [{"mpCode": None, "speakerLabel": None, "mpName": None}]
        annotate_speakers(segs, ROSTER)
        assert segs[0]["nameSource"] is None

    def test_saroja_regression_end_to_end(self):
        # The exact shape of the original bug: an unrelated speaker must NOT be
        # relabelled as "Dr. (Smt.) V. Saroja" just because she is in the roster.
        segs = [
            {"mpCode": None, "speakerLabel": "SHRI BIKRAM KESHARI DEO (KALAHANDI)",
             "mpName": "SHRI BIKRAM KESHARI DEO (KALAHANDI)"},
        ]
        annotate_speakers(segs, ROSTER)
        assert segs[0]["nameSource"] == "unresolved"
        assert segs[0]["mpName"] == "SHRI BIKRAM KESHARI DEO (KALAHANDI)"
