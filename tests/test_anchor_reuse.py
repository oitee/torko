from debate_fetch import (
    _name_agreement,
    anchor_contradicts_label,
    labels_name_same_person,
    reuse_anchors,
    split_by_speaker,
)

ROSTER = [{"mpName": "Shri Kodikunnil Suresh", "mpCode": 100, "mpPartCode": 1}]


class TestNameAgreement:
    def test_identical_names_agree(self):
        assert _name_agreement("SHRI A. RAJA", "Shri A. Raja") is True

    def test_initials_in_label_count_towards_coverage(self):
        # "S.K." supplies the initials, "KHARVENTHAN" the whole-word match
        assert _name_agreement(
            "S.K. KHARVENTHAN", "Salarapatty Kuppusamy Kharventhan"
        ) is True

    def test_only_initials_is_not_enough(self):
        # no whole word matches, so the anchor is not believed
        assert _name_agreement("S. K.", "Salarapatty Kuppusamy") is False

    def test_different_people_disagree(self):
        assert _name_agreement("SHRI RAM KUMAR", "Shri Shyam Verma") is False

    def test_no_usable_name_is_none_not_a_verdict(self):
        # Nothing was compared, so the result is None, not False.
        assert _name_agreement("MR. SPEAKER", "") is None


class TestNoEvidenceIsNotAgreement:
    def test_an_undecodable_label_names_nobody(self):
        # raw legacy-font bytes: fold to no usable word at all
        raw_a = "gÉÉÒ xÉÉÒiÉÉÒ¶É BÉÖEàÉÉ®"        # श्री नीतीश कुमार
        raw_b = "gÉÉÒ àÉÉäcxÉ ÉËºÉc (nä´ÉÉÊ®ªÉÉ)"  # श्री मोहन सिंह (देवरिया)
        assert _name_agreement(raw_a, raw_b) is None
        assert labels_name_same_person(raw_a, raw_b) is False

    def test_no_evidence_never_claims_a_new_attribution(self):
        assert labels_name_same_person("MR. SPEAKER", "") is False

    def test_no_evidence_never_discards_a_printed_anchor(self):
        # the opposite call: an anchor is the source's own evidence, so only a
        # positive disagreement may throw it away
        assert anchor_contradicts_label("MR. SPEAKER", "") is False

    def test_a_real_disagreement_still_discards_the_anchor(self):
        assert anchor_contradicts_label("SHRI RAM KUMAR", "Shri Shyam Verma") is True

    def test_reuse_does_not_stamp_one_name_across_undecodable_labels(self):
        # End to end, in miniature.
        segs = [
            {"mpCode": "77", "speakerLabel": "gÉÉÒ àÉÉäcxÉ ÉËºÉc",
             "mpName": "Shri Mohan Singh", "nameSource": "name-translit"},
            {"mpCode": None, "speakerLabel": "gÉÉÒ xÉÉÒiÉÉÒ¶É BÉÖEàÉÉ®", "mpName": None},
            {"mpCode": None, "speakerLabel": "+ÉvªÉFÉ àÉcÉänªÉ", "mpName": None},
        ]
        reuse_anchors(segs)
        assert [s["mpCode"] for s in segs] == ["77", None, None]


class TestReuseAnchors:
    def test_propagates_mpcode_to_later_unanchored_turn(self):
        segs = [
            {"mpCode": "500", "speakerLabel": "SHRI NEW MEMBER", "mpName": "Shri New Member"},
            {"mpCode": None, "speakerLabel": "SHRI NEW MEMBER", "mpName": "SHRI NEW MEMBER"},
        ]
        reuse_anchors(segs)
        assert segs[1]["mpCode"] == "500"
        assert segs[1]["mpName"] == "Shri New Member"
        assert segs[1]["nameSource"] == "anchor-reuse"

    def test_label_anchored_to_two_people_is_left_untouched(self):
        segs = [
            {"mpCode": "1", "speakerLabel": "SHRI KUMAR", "mpName": "Shri Ram Kumar"},
            {"mpCode": "2", "speakerLabel": "SHRI KUMAR", "mpName": "Shri Shyam Kumar"},
            {"mpCode": None, "speakerLabel": "SHRI KUMAR", "mpName": "SHRI KUMAR"},
        ]
        reuse_anchors(segs)
        assert segs[2]["mpCode"] is None

    def test_unrelated_label_is_not_resolved(self):
        segs = [
            {"mpCode": "500", "speakerLabel": "SHRI NEW MEMBER", "mpName": "Shri New Member"},
            {"mpCode": None, "speakerLabel": "MR. SPEAKER", "mpName": "MR. SPEAKER"},
        ]
        reuse_anchors(segs)
        assert segs[1]["mpCode"] is None

    def test_this_debates_anchor_beats_a_last_resort_name_db_match(self):
        # The name-db tier can claim a turn that an anchor in the same debate also names. The anchor must win.
        segs = [
            {
                "mpCode": "500",
                "speakerLabel": "SHRI NEW MEMBER",
                "mpName": "Shri New Member",
                "nameSource": "anchor",
            },
            {
                "mpCode": "777",
                "speakerLabel": "SHRI NEW MEMBER",
                "mpName": "Shri New Member",
                "nameSource": "name-db",
            },
        ]
        reuse_anchors(segs)
        assert segs[1]["mpCode"] == "500"
        assert segs[1]["nameSource"] == "anchor-reuse"

    def test_a_name_db_match_never_makes_a_label_look_ambiguous(self):
        # A name-db guess must not seed the anchored-label map.
        segs = [
            {
                "mpCode": "500",
                "speakerLabel": "SHRI NEW MEMBER",
                "mpName": "Shri New Member",
                "nameSource": "anchor",
            },
            {
                "mpCode": "777",
                "speakerLabel": "SHRI NEW MEMBER",
                "mpName": "Shri New Member",
                "nameSource": "name-db",
            },
            {"mpCode": None, "speakerLabel": "SHRI NEW MEMBER", "mpName": "SHRI NEW MEMBER"},
        ]
        reuse_anchors(segs)
        assert segs[2]["mpCode"] == "500"

    def test_an_earlier_tiers_match_is_never_overridden(self):
        # Only "name-db" is reconsidered; a name-exact answer keeps its code.
        segs = [
            {
                "mpCode": "500",
                "speakerLabel": "SHRI NEW MEMBER",
                "mpName": "Shri New Member",
                "nameSource": "anchor",
            },
            {
                "mpCode": "600",
                "speakerLabel": "SHRI NEW MEMBER",
                "mpName": "Shri New Member",
                "nameSource": "name-exact",
            },
        ]
        reuse_anchors(segs)
        assert segs[1]["mpCode"] == "600"
        assert segs[1]["nameSource"] == "name-exact"


class TestCarriedAnchor:
    def test_anchor_in_empty_p_is_carried_to_the_speech(self):
        html = (
            '<p><a name="100*1"></a></p>'
            "<p><b>SHRI KODIKUNNIL SURESH:</b> The speech.</p>"
        )
        (seg,) = split_by_speaker(html, ROSTER)
        assert seg["mpCode"] == "100"
        assert seg["text"] == "The speech."

    def test_carried_anchor_is_rejected_when_the_name_disagrees(self):
        # anchor names person 100, but the next paragraph is a different speaker
        html = (
            '<p><a name="100*1"></a></p>'
            "<p><b>SHRI SOMEONE ELSE:</b> Not Suresh.</p>"
        )
        (seg,) = split_by_speaker(html, ROSTER)
        assert seg["mpCode"] is None
        assert seg["anchorRejected"] == "100"
