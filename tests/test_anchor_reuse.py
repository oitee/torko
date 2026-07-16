"""
Carrying and reusing speaker anchors across paragraphs.

sansad.in anchors a speaker only on their first turn (and often parks that
anchor in an empty <p> just before the speech). These helpers spread that
anchor to the speaker's later, unanchored turns:

  anchor_agrees_with_label — do two names refer to the same person?
  reuse_anchors            — propagate an anchored mpCode to matching turns
  split_by_speaker         — carrying an anchor from an empty <p> to the text
"""
from debate_fetch import (
    anchor_agrees_with_label,
    reuse_anchors,
    split_by_speaker,
)

ROSTER = [{"mpName": "Shri Kodikunnil Suresh", "mpCode": 100, "mpPartCode": 1}]


class TestAnchorAgreesWithLabel:
    """A whole-word match is required; initials only pad the coverage."""

    def test_identical_names_agree(self):
        assert anchor_agrees_with_label("SHRI A. RAJA", "Shri A. Raja") is True

    def test_initials_in_label_count_towards_coverage(self):
        # "S.K." supplies the initials, "KHARVENTHAN" the whole-word match
        assert anchor_agrees_with_label(
            "S.K. KHARVENTHAN", "Salarapatty Kuppusamy Kharventhan"
        ) is True

    def test_only_initials_is_not_enough(self):
        # no whole word matches, so the anchor is not believed
        assert anchor_agrees_with_label("S. K.", "Salarapatty Kuppusamy") is False

    def test_different_people_disagree(self):
        assert anchor_agrees_with_label("SHRI RAM KUMAR", "Shri Shyam Verma") is False

    def test_empty_name_on_one_side_never_contradicts(self):
        assert anchor_agrees_with_label("MR. SPEAKER", "") is True


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
        # annotate_speakers runs before this pass, so the "name-db" tier can
        # claim a turn that an anchor printed in this very debate also names.
        # The anchor is the stronger evidence and must win.
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
        # A name-db guess must not seed the anchored-label map: if it did, the
        # label would look anchored to two people and reuse would bail out,
        # silently costing a resolution the anchor alone would have made.
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
    """An anchor alone in an empty <p> attaches to the next paragraph with text."""

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
