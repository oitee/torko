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
    def test_drops_honorific_and_constituency(self):
        # "SHRI A. RAJA (NILGIRIS)" -> ["a", "raja"]
        assert _normalize_name("SHRI A. RAJA (NILGIRIS)") == ["a", "raja"]

    def test_roster_form_keeps_word_order_as_given(self):
        # "Shri Raja A" -> ["raja", "a"]  (different order from the label above)
        assert _normalize_name("Shri Raja A") == ["raja", "a"]

    def test_ministerial_title_extracts_name_inside_parentheses(self):
        # Special case: the real name lives inside the parens after an honorific
        assert _normalize_name("THE MINISTER OF STEEL (SHRI PRALHAD JOSHI)") == ["pralhad", "joshi"]

    def test_honorific_only_parenthetical_is_not_treated_as_the_name(self):
        # "(Smt.)" is a bare honorific, not a ministerial name.
        assert _normalize_name("Dr. (Smt.) V. Saroja") == ["v", "saroja"]

    def test_purely_honorific_label_normalises_to_empty(self):
        # nothing but honorifics -> no comparable tokens at all
        assert _normalize_name("Dr.") == []
        assert _normalize_name("Shri Smt") == []

    def test_devanagari_label_passes_through_without_romanising(self):
        # Indic script can't match the romanised roster;
        # it survives as (non-empty) tokens rather than crashing or vanishing.
        toks = _normalize_name("श्री किरेन रिजिजू")
        assert toks  # non-empty
        assert all(not t.isascii() for t in toks)


class TestBuildSpeakerIndex:
    def test_exposes_all_six_lookup_tables(self):
        idx = build_speaker_index(ROSTER)
        assert set(idx) == {
            "by_str",
            "by_join_ordered",
            "by_join_sorted",
            "tokenised",
            "by_folded",
            "by_folded_db",
        }

    def test_by_str_keys_on_space_joined_tokens(self):
        idx = build_speaker_index(ROSTER)
        assert "raja a" in idx["by_str"]

    def test_tokenised_has_one_entry_per_roster_member(self):
        idx = build_speaker_index(ROSTER)
        assert len(idx["tokenised"]) == len(ROSTER)


class TestResolveSpeaker:
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
        assert resolve_speaker("MR. SPEAKER", index) == (None, None)

    def test_empty_label_returns_none(self, index):
        assert resolve_speaker("Dr.", index) == (None, None)

    def test_empty_token_roster_entry_never_wildcard_matches(self):
        # A roster name with no tokens must not match every label.
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


class TestResolveTranslit:
    # Golden pairs drawn from real unresolved labels of sampled debates.
    GOLDEN_ROSTER = [
        {"mpName": "Shri Ram Kripal Yadav", "mpCode": 500, "mpPartCode": 1},
        {"mpName": "Shri Kodikunnil Suresh", "mpCode": 100, "mpPartCode": 1},
        {"mpName": "Shri Sharad Yadav", "mpCode": 501, "mpPartCode": 2},
        {"mpName": "Shrimati Meenakashi Lekhi", "mpCode": 502, "mpPartCode": 1},
        {"mpName": "Dr. Charan Das Mahant", "mpCode": 503, "mpPartCode": 1},
    ]

    @pytest.fixture
    def index(self):
        return build_speaker_index(self.GOLDEN_ROSTER)

    def test_devanagari_label_with_constituency_resolves(self, index):
        source, entry = resolve_speaker("श्री राम कृपाल यादव ( पाटलिपुत्र )", index)
        assert source == "name-translit"
        assert entry["mpCode"] == 500

    def test_devanagari_ministerial_wrapper_resolves(self, index):
        label = "कृषि मंत्रालय में राज्य मंत्री (डॉ. चरण दास महंत)"
        source, entry = resolve_speaker(label, index)
        assert source == "name-translit"
        assert entry["mpCode"] == 503

    def test_devanagari_label_without_constituency_resolves(self, index):
        source, entry = resolve_speaker("श्री शरद यादव", index)
        assert source == "name-translit"
        assert entry["mpCode"] == 501

    def test_inherent_a_inside_clusters_matches(self, index):
        # fold() drops the optional inherent "a" inside a consonant cluster.
        source, entry = resolve_speaker("श्रीमती मीनाक्षी लेखी ( नई दिल्ली )", index)
        assert source == "name-translit"
        assert entry["mpCode"] == 502

    def test_latin_exact_match_still_wins_the_earlier_tier(self, index):
        # the new tier is last: a plain roster-identical label keeps name-exact
        source, entry = resolve_speaker("SHRI KODIKUNNIL SURESH", index)
        assert source == "name-exact"

    def test_presiding_devanagari_label_stays_unmatched(self, index):
        assert resolve_speaker("माननीय सभापति", index) == (None, None)

    def test_singh_spelling_is_bridged_across_scripts(self):
        # "सिंह" transliterates to "sinha" and must fold to the roster "Singh".
        idx = build_speaker_index([{"mpName": "Shri Mohan Singh", "mpCode": 9, "mpPartCode": 1}])
        source, entry = resolve_speaker("श्री मोहन सिंह", idx)
        assert source == "name-translit"
        assert entry["mpCode"] == 9

    def test_folded_collision_between_two_mps_is_rejected(self):
        # Singh and Sinha fold to the same key, so the label matches nobody.
        roster = [
            {"mpName": "Shri Rakesh Singh", "mpCode": 1, "mpPartCode": 1},
            {"mpName": "Shri Rakesh Sinha", "mpCode": 2, "mpPartCode": 1},
        ]
        idx = build_speaker_index(roster)
        assert idx["by_folded"] == {}
        assert resolve_speaker("श्री राकेश सिंह", idx) == (None, None)

    def test_distinct_names_do_not_collide_after_cluster_folding(self):
        # The cluster-"a" rule shortens keys, so check it does not merge two
        # genuinely different people: both stay resolvable to themselves.
        roster = [
            {"mpName": "Shri Sharad Yadav", "mpCode": 11, "mpPartCode": 1},
            {"mpName": "Shri Sharda Yadav", "mpCode": 12, "mpPartCode": 1},
        ]
        idx = build_speaker_index(roster)
        assert len(idx["by_folded"]) == 2  # no key was poisoned
        assert resolve_speaker("श्री शरद यादव", idx)[1]["mpCode"] == 11

    def test_all_honorific_devanagari_label_never_wildcards(self, index):
        assert resolve_speaker("श्री", index) == (None, None)


class TestResolveDb:
    def test_fires_only_after_every_other_tier_fails(self):
        # Absent from the debate roster and present in the database roster.
        idx = build_speaker_index(
            [{"mpName": "Shri Someone Else", "mpCode": 1, "mpPartCode": 1}],
            db_roster=[{"mpCode": 9, "mpName": "Shri Mohan Singh"}],
        )
        source, entry = resolve_speaker("SHRI MOHAN SINGH", idx)
        assert source == "name-db"
        assert entry["mpCode"] == 9

    def test_never_overrides_an_earlier_tier(self):
        # The debate's own roster already has an exact match; a DB roster entry
        # for the same folded key must not steal the earlier tier's answer.
        idx = build_speaker_index(
            [{"mpName": "Shri Mohan Singh", "mpCode": 1, "mpPartCode": 1}],
            db_roster=[{"mpCode": 9, "mpName": "Shri Mohan Singh"}],
        )
        source, entry = resolve_speaker("SHRI MOHAN SINGH", idx)
        assert source == "name-exact"
        assert entry["mpCode"] == 1

    def test_collision_in_db_roster_is_dropped_never_guessed(self):
        # Two people share the folded key, so the label matches nobody.
        idx = build_speaker_index(
            [],
            db_roster=[
                {"mpCode": 1, "mpName": "Shri Rakesh Singh"},
                {"mpCode": 2, "mpName": "Shri Rakesh Sinha"},
            ],
        )
        assert idx["by_folded_db"] == {}
        assert resolve_speaker("श्री राकेश सिंह", idx) == (None, None)

    def test_db_roster_none_reproduces_todays_behaviour(self):
        # Without a database roster, a label absent from the debate roster stays unmatched.
        idx = build_speaker_index([{"mpName": "Shri Someone Else", "mpCode": 1, "mpPartCode": 1}])
        assert idx["by_folded_db"] == {}
        assert resolve_speaker("SHRI MOHAN SINGH", idx) == (None, None)


class TestAnnotateSpeakers:
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
        # An unrelated speaker must not take the name "Dr. (Smt.) V. Saroja".
        segs = [
            {"mpCode": None, "speakerLabel": "SHRI BIKRAM KESHARI DEO (KALAHANDI)",
             "mpName": "SHRI BIKRAM KESHARI DEO (KALAHANDI)"},
        ]
        annotate_speakers(segs, ROSTER)
        assert segs[0]["nameSource"] == "unresolved"
        assert segs[0]["mpName"] == "SHRI BIKRAM KESHARI DEO (KALAHANDI)"
