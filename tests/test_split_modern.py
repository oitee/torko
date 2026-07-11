"""
Part 2 — splitting a MODERN transcript into speaker turns, plus the
per-speaker distribution aggregation.

Covers PARSING_STRATEGY.md §2.1–2.7 and the distribution roll-up:
  _leading_bold        — find the bold label past an empty anchor-wrapping bold
  _label_colon_pos     — bold-label-ending-in-colon detector
  _anchor_id           — read <A name="code*part">
  split_by_speaker     — the full paragraph walk
  speaker_distribution — aggregate turns per speaker
"""
from conftest import first_block

from debate_fetch import (
    _anchor_id,
    _label_colon_pos,
    _leading_bold,
    speaker_distribution,
    split_by_speaker,
)

ROSTER = [
    {"mpName": "Shri Raja A", "mpCode": 344, "mpPartCode": 24},
    {"mpName": "Shri Kodikunnil Suresh", "mpCode": 100, "mpPartCode": 1},
]


class TestLeadingBold:
    """§2.2: the first *non-empty* bold run, only if the paragraph starts with it."""

    def test_skips_empty_bold_that_only_wraps_the_anchor(self):
        p = first_block('<p><b><a name="344*24"></a></b><b>SHRI X:</b> hi</p>')
        assert _leading_bold(p, "SHRI X: hi") == "SHRI X:"

    def test_returns_empty_when_bold_is_not_at_the_start(self):
        p = first_block("<p>intro text <b>SHRI X:</b></p>")
        assert _leading_bold(p, "intro text SHRI X:") == ""

    def test_returns_empty_when_no_bold(self):
        p = first_block("<p>plain paragraph</p>")
        assert _leading_bold(p, "plain paragraph") == ""


class TestLabelColonPos:
    """§2.1 / §2.3: a bold label ending in a colon within the 200-char window."""

    def test_detects_bold_label_colon(self):
        p = first_block("<p><b>SHRI X (PLACE):</b> what they said</p>")
        plain = "SHRI X (PLACE): what they said"
        assert _label_colon_pos(p, plain) == plain.index(":")

    def test_no_bold_means_no_label_even_with_a_colon(self):
        # a mid-sentence colon in plain text must not look like a label
        p = first_block("<p>the ratio was 3:1 in favour</p>")
        assert _label_colon_pos(p, "the ratio was 3:1 in favour") is None

    def test_colon_beyond_the_window_is_ignored(self):
        long_prefix = "A" * 250
        p = first_block(f"<p><b>{long_prefix}: tail</b></p>")
        assert _label_colon_pos(p, f"{long_prefix}: tail") is None


class TestAnchorId:
    """§2.7: read the (mpCode, mpPartCode) out of <A name="code*part">."""

    def test_reads_code_and_part(self):
        p = first_block('<p><a name="344*24"></a>text</p>')
        assert _anchor_id(p) == ("344", "24")

    def test_no_anchor_returns_none_pair(self):
        p = first_block("<p>text</p>")
        assert _anchor_id(p) == (None, None)


class TestSplitBySpeaker:
    """§2.6: the whole walk — new turns, continuations, IDs, star prefixes."""

    def test_anchored_turn_gets_official_name_and_part(self):
        html = '<p><b><a name="344*24"></a>SHRI A. RAJA (NILGIRIS):</b> Hello.</p>'
        (seg,) = split_by_speaker(html, ROSTER)
        assert seg["mpCode"] == "344"
        assert seg["mpPartCode"] == "24"
        assert seg["mpName"] == "Shri Raja A"        # canonical, from the roster
        assert seg["nameSource"] == "anchor"
        assert seg["text"] == "Hello."

    def test_continuation_paragraph_is_glued_to_current_turn(self):
        html = (
            '<p><b><a name="344*24"></a>SHRI A. RAJA:</b> First para.</p>'
            "<p>Second para.</p>"
        )
        (seg,) = split_by_speaker(html, ROSTER)
        assert seg["text"] == "First para.\n\nSecond para."

    def test_anchorless_bold_label_opens_a_new_turn(self):
        # §2.1 Signal B: the one-third of turns with no anchor still split
        html = (
            '<p><b><a name="344*24"></a>SHRI A. RAJA:</b> Raja speaks.</p>'
            "<p><b>SHRI KODIKUNNIL SURESH:</b> Suresh speaks.</p>"
        )
        segs = split_by_speaker(html, ROSTER)
        assert len(segs) == 2
        assert segs[1]["mpCode"] == "100"            # resolved by name, not anchor
        assert segs[1]["nameSource"] == "name-exact"
        assert segs[1]["text"] == "Suresh speaks."

    def test_star_prefix_is_stripped_from_the_label(self):
        # §2.5 — "*57 SHRI ..." editorial marker removed from the stored label
        html = "<p><b>*57 SHRI KODIKUNNIL SURESH:</b> Body.</p>"
        (seg,) = split_by_speaker(html, ROSTER)
        assert seg["speakerLabel"] == "SHRI KODIKUNNIL SURESH"

    def test_preamble_before_first_speaker_is_unattributed(self):
        html = "<p>11.00 hrs the House met.</p><p><b>SHRI KODIKUNNIL SURESH:</b> Hi.</p>"
        segs = split_by_speaker(html, ROSTER)
        assert segs[0]["speakerLabel"] is None
        assert segs[0]["mpName"] is None
        assert segs[0]["text"] == "11.00 hrs the House met."


class TestSpeakerDistribution:
    """The per-speaker roll-up used for the summary table."""

    def test_aggregates_words_and_interventions_by_speaker(self):
        html = (
            '<p><b><a name="344*24"></a>SHRI A. RAJA:</b> one two three.</p>'
            '<p><b><a name="344*25"></a>SHRI A. RAJA:</b> four five.</p>'
            '<p><b><a name="100*1"></a>SHRI KODIKUNNIL SURESH:</b> hi.</p>'
        )
        segs = split_by_speaker(html, ROSTER)
        dist = speaker_distribution(segs)
        raja = next(e for e in dist if e["mpCode"] == "344")
        assert raja["interventions"] == 2            # two anchored turns, same mpCode
        assert raja["words"] == 5
        assert raja["verified"] is True

    def test_sorted_by_word_count_descending(self):
        html = (
            '<p><b><a name="344*24"></a>SHRI A. RAJA:</b> a b c d.</p>'
            '<p><b><a name="100*1"></a>SHRI KODIKUNNIL SURESH:</b> x.</p>'
        )
        dist = speaker_distribution(split_by_speaker(html, ROSTER))
        assert [e["mpCode"] for e in dist] == ["344", "100"]

    def test_unattributed_and_anchorless_keep_separate_buckets(self):
        # an unresolved label keys on the label (not collapsed into "unattributed")
        html = (
            "<p>preamble.</p>"
            "<p><b>MR. SPEAKER:</b> order order.</p>"
        )
        dist = speaker_distribution(split_by_speaker(html, ROSTER))
        names = {e["mpName"] for e in dist}
        assert "(unattributed)" in names
        assert "MR. SPEAKER" in names
        assert all(e["verified"] is False for e in dist)
