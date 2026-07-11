from conftest import first_block

from debate_fetch_legacy import (
    _anchor_id,
    _is_caps_label,
    _label_colon_pos,
    _sanitize_legacy_html,
    looks_legacy,
    split_by_speaker_legacy,
)


class TestLooksLegacy:
    def test_modern_anchor_is_not_legacy(self):
        assert looks_legacy('<p><A name="3972*1">text</p>') is False

    def test_partless_anchor_is_legacy(self):
        assert looks_legacy('<p><A name="209">text</p>') is True

    def test_no_anchors_at_all_is_legacy(self):
        assert looks_legacy("<p>just text</p>") is True

    def test_empty_html_is_not_legacy(self):
        assert looks_legacy("") is False


class TestSanitizeLegacyHtml:
    def test_self_closes_a_partless_anchor(self):
        assert _sanitize_legacy_html('<p><A name="209">text') == '<p><A name="209"/>text'

    def test_leaves_already_closed_markup_untouched(self):
        assert _sanitize_legacy_html("<p>no anchors here</p>") == "<p>no anchors here</p>"

    def test_is_case_insensitive(self):
        assert _sanitize_legacy_html('<a NAME="7">') == '<a NAME="7"/>'


class TestIsCapsLabel:
    def test_all_caps_name_is_a_label(self):
        assert _is_caps_label("SHRI RUPCHAND PAL (HOOGHLY)") is True

    def test_sentence_with_lowercase_is_not_a_label(self):
        assert _is_caps_label("Sir, I want to oppose") is False

    def test_digits_and_punctuation_only_is_not_a_label(self):
        # "11.09" needs at least one ASCII letter to count
        assert _is_caps_label("11.09 hrs") is False


class TestLegacyLabelColonPos:
    def test_caps_label_before_colon_is_detected(self):
        plain = "MR. SPEAKER: Motion moved."
        p = first_block(f"<p>{plain}</p>")
        assert _label_colon_pos(p, plain) == plain.index(":")

    def test_lowercase_line_is_not_a_label(self):
        plain = "Sir, I want to oppose the Bill on two grounds."
        p = first_block(f"<p>{plain}</p>")
        assert _label_colon_pos(p, plain) is None

    def test_no_colon_means_no_label(self):
        plain = "SHRI RUPCHAND PAL SPEAKS AT LENGTH"
        p = first_block(f"<p>{plain}</p>")
        assert _label_colon_pos(p, plain) is None


class TestLegacyAnchorId:
    def test_reads_partless_code(self):
        p = first_block('<p><a name="209"></a></p>')
        assert _anchor_id(p) == "209"

    def test_no_anchor_returns_none(self):
        p = first_block("<p>text</p>")
        assert _anchor_id(p) is None


class TestSplitBySpeakerLegacy:
    ROSTER = [{"mpName": "Shri V. Dhananjaya Kumar", "mpCode": 209, "mpPartCode": None}]

    def test_caps_label_opens_a_turn(self):
        segs = split_by_speaker_legacy("<p>MR. SPEAKER: Motion moved.</p>", [])
        assert len(segs) == 1
        assert segs[0]["speakerLabel"] == "MR. SPEAKER"
        assert segs[0]["text"] == "Motion moved."

    def test_lowercase_line_is_a_continuation_not_a_new_turn(self):
        html = "<p>MR. SPEAKER: Motion moved.</p><p>Sir, I oppose the Bill.</p>"
        segs = split_by_speaker_legacy(html, [])
        assert len(segs) == 1
        assert segs[0]["text"] == "Motion moved.\n\nSir, I oppose the Bill."

    def test_pending_anchor_on_empty_paragraph_attaches_to_next_block(self):
        # Quirk: <p><A name="209"></p> then the speech in the NEXT block
        html = (
            '<p><A name="209"></p>'
            "<p>THE MINISTER (SHRI V. DHANANJAYA KUMAR): I beg to move.</p>"
        )
        segs = split_by_speaker_legacy(html, self.ROSTER)
        (seg,) = segs
        assert seg["mpCode"] == "209"
        assert seg["mpName"] == "Shri V. Dhananjaya Kumar"   # resolved via anchor
        assert seg["nameSource"] == "anchor"
        assert seg["text"] == "I beg to move."

    def test_h6_blocks_are_walked_too(self):
        # Quirk: Hindi passages were wrapped in <h6>, not <p>
        html = "<p>SHRI A: first.<h6>SHRI B: second.</h6>"
        segs = split_by_speaker_legacy(html, [])
        assert [s["speakerLabel"] for s in segs] == ["SHRI A", "SHRI B"]

    def test_bold_title_line_is_skipped(self):
        # Quirk: the document's own "Title:" header is not a speaker turn
        html = "<p><b>Title:</b> Money Laundering Bill</p><p>MR. SPEAKER: Hello.</p>"
        segs = split_by_speaker_legacy(html, [])
        assert [s["speakerLabel"] for s in segs] == ["MR. SPEAKER"]

    def test_star_prefix_stripped_in_legacy_caps_label(self):
        html = "<p>*57 SHRI N. K. PREMACHANDRAN (KOLLAM): My speech.</p>"
        (seg,) = split_by_speaker_legacy(html, [])
        assert seg["speakerLabel"] == "SHRI N. K. PREMACHANDRAN (KOLLAM)"
