"""
Mode C — tagging presiding officers (the Chair) as a role, not an MP.

Covers is_presiding_label plus its wiring into both parsers:
  * a chair label gets nameSource "presiding" and never an mpCode,
  * anchored segments are never downgraded to the role tag,
  * reuse_anchors never overwrites a "presiding" tag,
  * the legacy parser re-tags Devanagari chair labels after CDAC decoding.
"""
import pytest

from debate_fetch import (
    annotate_speakers,
    is_presiding_label,
    reuse_anchors,
    split_by_speaker,
)
from debate_fetch_legacy import split_by_speaker_legacy


class TestIsPresidingLabel:
    """Every positive form below appears verbatim in 008_UNVERIFIED_SPEAKERS_SAMPLE.md."""

    @pytest.mark.parametrize("label", [
        "MR. SPEAKER",
        "MADAM SPEAKER",
        "SPEAKER",
        "MR. DEPUTY-SPEAKER",
        "MR. CHAIRMAN",
        "MR.CHAIRMAN",          # no space after the honorific
        "HON. CHAIRPERSON",
        "अध्यक्ष महोदय",
        "उपाध्यक्ष महोदय",
        "सभापति महोदय",
        "सभापति महोदया",
        "माननीय सभापति",
        "माननीय अध्यक्ष",
    ])
    def test_chair_forms_match(self, label):
        assert is_presiding_label(label) is True

    @pytest.mark.parametrize("label", [
        "SEVERAL HON. MEMBERS",           # a crowd, not the Chair
        "अनेक माननीय सदस्य",
        "एक माननीय सदस्य",
        "THE DEPUTY MINISTER OF DEFENCE",  # historical title; "deputy" alone must not match
        "SHRI A. RAJA (NILGIRIS)",
        "श्री राम कृपाल यादव ( पाटलिपुत्र )",
        "Secretary-General",
        "",
    ])
    def test_non_chair_forms_do_not_match(self, label):
        assert is_presiding_label(label) is False

    def test_none_label_is_false(self):
        assert is_presiding_label(None) is False


ROSTER = [{"mpName": "Shri Kodikunnil Suresh", "mpCode": 100, "mpPartCode": 1}]


class TestAnnotatePresiding:
    def test_chair_label_is_tagged_presiding_with_no_mpcode(self):
        segs = [{"mpCode": None, "speakerLabel": "MR. SPEAKER", "mpName": "MR. SPEAKER"}]
        annotate_speakers(segs, ROSTER)
        assert segs[0]["nameSource"] == "presiding"
        assert segs[0]["mpCode"] is None
        assert segs[0]["mpName"] == "MR. SPEAKER"

    def test_anchored_segment_is_never_downgraded(self):
        # Owner's decision: role over person applies to UNANCHORED chair labels;
        # an anchored segment keeps its anchor attribution untouched.
        segs = [{"mpCode": "100", "speakerLabel": "MR. SPEAKER", "mpName": "Shri Kodikunnil Suresh"}]
        annotate_speakers(segs, ROSTER)
        assert segs[0]["nameSource"] == "anchor"
        assert segs[0]["mpCode"] == "100"

    def test_chair_label_is_never_roster_matched(self):
        # An MP whose roster name shares tokens with a chair form must not be
        # matched to it: presiding runs before resolve_speaker entirely.
        roster = [{"mpName": "Shri Speaker Kumar", "mpCode": 7, "mpPartCode": 1}]
        segs = [{"mpCode": None, "speakerLabel": "MR. SPEAKER", "mpName": "MR. SPEAKER"}]
        annotate_speakers(segs, roster)
        assert segs[0]["nameSource"] == "presiding"
        assert segs[0]["mpCode"] is None


class TestReuseAnchorsKeepsPresiding:
    def test_presiding_tag_survives_a_same_label_anchor(self):
        # Even if some anchored segment carries the same label, pass 2 must
        # skip segments already tagged presiding.
        segs = [
            {"mpCode": "100", "speakerLabel": "MR. SPEAKER", "mpName": "Shri Kodikunnil Suresh"},
            {"mpCode": None, "speakerLabel": "MR. SPEAKER", "mpName": "MR. SPEAKER",
             "nameSource": "presiding"},
        ]
        reuse_anchors(segs)
        assert segs[1]["nameSource"] == "presiding"
        assert segs[1]["mpCode"] is None


class TestEndToEnd:
    def test_modern_chair_turn_is_presiding_and_member_stays_anchored(self):
        html = (
            '<p><b><a name="100*1"></a>SHRI KODIKUNNIL SURESH:</b> A point.</p>'
            "<p><b>MR. SPEAKER:</b> Order, order.</p>"
        )
        member, chair = split_by_speaker(html, ROSTER)
        assert member["nameSource"] == "anchor"
        assert chair["nameSource"] == "presiding"
        assert chair["mpCode"] is None

    def test_legacy_cdac_devanagari_chair_is_retagged_after_decoding(self):
        # "+ÉvªÉFÉ àÉcÉänªÉ" is authentic CDAC-font gibberish for अध्यक्ष महोदय;
        # at annotate time it is still gibberish, so only the post-decode
        # re-tag loop can catch it.
        html = "<p><b>+ÉvªÉFÉ àÉcÉänªÉ :</b> BÉEÉÊlÉiÉ ¤ÉÉiÉ*</p>"
        (seg,) = split_by_speaker_legacy(html, [])
        assert seg["speakerLabel"] == "अध्यक्ष महोदय"
        assert seg["nameSource"] == "presiding"
        assert seg["mpCode"] is None
