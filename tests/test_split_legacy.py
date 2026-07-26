"""
Part 4 — the LEGACY parser for older (pre-~2004) transcripts.

Covers PARSING_STRATEGY.md §4.0–4.5:
  looks_legacy            — modern vs legacy format detection
  _sanitize_legacy_html   — defuse the unclosed-<A> landmine
  _is_caps_label          — the ALL-CAPS label signal (no bold to lean on)
  _label_colon_pos        — bold-colon OR caps-colon, within the window
  _anchor_id              — read the part-less <A name="209">
  split_by_speaker_legacy — the full walk over <p> + <h6> blocks
"""
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
    """§4.5: modern debates carry a code*part anchor; legacy ones never do."""

    def test_modern_anchor_is_not_legacy(self):
        assert looks_legacy('<p><A name="3972*1">text</p>') is False

    def test_partless_anchor_is_legacy(self):
        assert looks_legacy('<p><A name="209">text</p>') is True

    def test_no_anchors_at_all_is_legacy(self):
        assert looks_legacy("<p>just text</p>") is True

    def test_empty_html_is_not_legacy(self):
        assert looks_legacy("") is False


class TestSanitizeLegacyHtml:
    """§4.2: self-close every <A name="..."> before parsing."""

    def test_self_closes_a_partless_anchor(self):
        assert _sanitize_legacy_html('<p><A name="209">text') == '<p><A name="209"/>text'

    def test_leaves_already_closed_markup_untouched(self):
        assert _sanitize_legacy_html("<p>no anchors here</p>") == "<p>no anchors here</p>"

    def test_is_case_insensitive(self):
        assert _sanitize_legacy_html('<a NAME="7">') == '<a NAME="7"/>'


class TestIsCapsLabel:
    """§4.4: a label has letters but none of them lowercase."""

    def test_all_caps_name_is_a_label(self):
        assert _is_caps_label("SHRI RUPCHAND PAL (HOOGHLY)") is True

    def test_sentence_with_lowercase_is_not_a_label(self):
        assert _is_caps_label("Sir, I want to oppose") is False

    def test_digits_and_punctuation_only_is_not_a_label(self):
        # "11.09" needs at least one ASCII letter to count
        assert _is_caps_label("11.09 hrs") is False


class TestLegacyLabelColonPos:
    """§4.4: open a turn on a caps-colon (or bold-colon) within the window."""

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
    """§4.3: read the part-less mpCode."""

    def test_reads_partless_code(self):
        p = first_block('<p><a name="209"></a></p>')
        assert _anchor_id(p) == "209"

    def test_no_anchor_returns_none(self):
        p = first_block("<p>text</p>")
        assert _anchor_id(p) is None


class TestSplitBySpeakerLegacy:
    """§4.0–4.4: the full legacy walk on synthetic old-format HTML."""

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
        # §4.4 quirk: <p><A name="209"></p> then the speech in the NEXT block
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
        # §4.4 quirk: Hindi passages were wrapped in <h6>, not <p>
        html = "<p>SHRI A: first.<h6>SHRI B: second.</h6>"
        segs = split_by_speaker_legacy(html, [])
        assert [s["speakerLabel"] for s in segs] == ["SHRI A", "SHRI B"]

    def test_bold_title_line_is_skipped(self):
        # §4.4 quirk: the document's own "Title:" header is not a speaker turn
        html = "<p><b>Title:</b> Money Laundering Bill</p><p>MR. SPEAKER: Hello.</p>"
        segs = split_by_speaker_legacy(html, [])
        assert [s["speakerLabel"] for s in segs] == ["MR. SPEAKER"]

    def test_legacy_title_guard_unchanged(self):
        # T7: the guard moved into the shared is_heading_label helper, but
        # the legacy reader's original behaviour -- drop the "Title:" line
        # entirely, don't glue it onto the previous speaker -- must not
        # regress. (Bold, like test_bold_title_line_is_skipped above: a
        # mixed-case "Title:" has no ALL-CAPS signal of its own, so bold is
        # what makes it a label candidate at all in the legacy path.)
        html = (
            "<p>MR. SPEAKER: Motion moved.</p>"
            "<p><b>Title:</b> Discussion on drought in several parts of the country.</p>"
        )
        segs = split_by_speaker_legacy(html, [])
        assert [s["speakerLabel"] for s in segs] == ["MR. SPEAKER"]
        assert segs[0]["text"] == "Motion moved."   # heading not glued on

    def test_motion_re_line_is_not_a_turn(self):
        html = (
            "<p><b>Motion Re:</b> Need for a comprehensive policy on drought relief.</p>"
            "<p>MR. SPEAKER: Hello.</p>"
        )
        segs = split_by_speaker_legacy(html, [])
        assert [s["speakerLabel"] for s in segs] == ["MR. SPEAKER"]

    def test_timestamp_line_is_not_a_turn(self):
        html = "<p><b>17.00 hrs:</b> The House then adjourned.</p><p>MR. SPEAKER: Hello.</p>"
        segs = split_by_speaker_legacy(html, [])
        assert [s["speakerLabel"] for s in segs] == ["MR. SPEAKER"]

    def test_mp_named_title_is_unaffected(self):
        html = "<p>SHRI TITLE SINGH: Contrived but proves the exact-match rule.</p>"
        (seg,) = split_by_speaker_legacy(html, [])
        assert seg["speakerLabel"] == "SHRI TITLE SINGH"

    def test_star_prefix_stripped_in_legacy_caps_label(self):
        html = "<p>*57 SHRI N. K. PREMACHANDRAN (KOLLAM): My speech.</p>"
        (seg,) = split_by_speaker_legacy(html, [])
        assert seg["speakerLabel"] == "SHRI N. K. PREMACHANDRAN (KOLLAM)"
