"""
Part 2 — splitting a MODERN transcript into speaker turns, plus the
per-speaker distribution aggregation.

Covers PARSING_STRATEGY.md §2.1–2.7 and the distribution roll-up:
  _leading_bold        — find the bold label past an empty anchor-wrapping bold
  _label_colon_pos     — bold-label-ending-in-colon detector
  _anchor_id           — read <A name="code*part">
  is_heading_label      — document headings ("Title:", "Motion Re:", a bare
                           timestamp) that print like a label but aren't one
  split_by_speaker     — the full paragraph walk
  speaker_distribution — aggregate turns per speaker
"""
from conftest import first_block

from debate_fetch import (
    _anchor_id,
    _label_colon_pos,
    _leading_bold,
    is_heading_label,
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
    """§2.1 / §2.3: a bold *or* ALL-CAPS label ending in a colon, within the
    200-char window. Either signal alone is enough; neither covers the corpus
    on its own."""

    def test_detects_bold_label_colon(self):
        p = first_block("<p><b>SHRI X (PLACE):</b> what they said</p>")
        plain = "SHRI X (PLACE): what they said"
        assert _label_colon_pos(p, plain) == plain.index(":")

    def test_detects_an_unbolded_caps_label(self):
        # LS14/12/9000 bolds only its Hindi labels and prints the English ones
        # as plain text. Bold-only, this turn is invisible and its speech gets
        # glued onto the previous speaker.
        plain = "SHRIMATI MANEKA GANDHI (PILIBHIT): Thank you for the opportunity."
        p = first_block(f"<p>{plain}</p>")
        assert _label_colon_pos(p, plain) == plain.index(":")

    def test_lowercase_prose_with_a_colon_is_not_a_label(self):
        # a mid-sentence colon in plain text must not look like a label
        p = first_block("<p>the ratio was 3:1 in favour</p>")
        assert _label_colon_pos(p, "the ratio was 3:1 in favour") is None

    def test_a_bold_devanagari_label_still_opens_a_turn(self):
        # the caps test is Latin-only (Devanagari has no case), so bold stays
        # the only signal that can see a Hindi label — it must keep working
        plain = "सभापति महोदया : कृपया समाप्त करें।"
        p = first_block(f"<p><b>सभापति महोदया :</b> कृपया समाप्त करें।</p>")
        assert _label_colon_pos(p, plain) == plain.index(":")

    def test_unbolded_devanagari_prose_is_not_a_label(self):
        # "no lowercase ASCII" is vacuously true of Hindi, so without the
        # letter check the caps test would open a turn on every Hindi line
        plain = "मैं यह कहना चाहता हूं: यह विधेयक अच्छा है।"
        p = first_block(f"<p>{plain}</p>")
        assert _label_colon_pos(p, plain) is None

    def test_colon_beyond_the_window_is_ignored(self):
        long_prefix = "A" * 250
        p = first_block(f"<p><b>{long_prefix}: tail</b></p>")
        assert _label_colon_pos(p, f"{long_prefix}: tail") is None

    def test_caps_colon_beyond_the_window_is_ignored(self):
        # the window applies to the caps signal too, not just the bold one
        plain = "SHRI " + "X" * 250 + ": tail"
        p = first_block(f"<p>{plain}</p>")
        assert _label_colon_pos(p, plain) is None


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

    def test_an_unbolded_caps_label_is_not_swallowed_by_the_previous_turn(self):
        # The shape of LS14/12/9000: the Hindi label is bold, the English one
        # that follows is plain text. Bold-only, the second turn never opens
        # and Suresh's words land inside the Hindi speaker's segment — while
        # every count still reports a clean parse, because a turn that was
        # never split never becomes a label to count as missing.
        html = (
            "<p><b>सभापति महोदया :</b> कृपया बोलिए।</p>"
            "<p>SHRI KODIKUNNIL SURESH: Suresh speaks.</p>"
        )
        hindi, suresh = split_by_speaker(html, ROSTER)
        assert hindi["speakerLabel"] == "सभापति महोदया"
        assert hindi["text"] == "कृपया बोलिए।"          # nothing extra glued on
        assert suresh["speakerLabel"] == "SHRI KODIKUNNIL SURESH"
        assert suresh["text"] == "Suresh speaks."
        assert suresh["mpCode"] == "100"                # and it still resolves

    def test_unbolded_prose_after_a_turn_is_still_a_continuation(self):
        # the caps rule must not turn ordinary sentences into phantom turns
        html = (
            '<p><b><a name="344*24"></a>SHRI A. RAJA:</b> First para.</p>'
            "<p>I would say this: the Bill is good.</p>"
        )
        (seg,) = split_by_speaker(html, ROSTER)
        assert seg["text"] == "First para.\n\nI would say this: the Bill is good."

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

    def test_title_line_is_not_a_turn(self):
        # T7 regression: the modern reader gained no equivalent of the
        # legacy reader's "Title:" guard, so every modern-path debate grew a
        # phantom speaker called "Title" whose speech was the debate's own
        # headline (1,946 turns in the live corpus).
        html = (
            "<p><b>Title:</b> Discussion on the situation arising out of "
            "drought in several parts of the country.</p>"
            "<p><b>SHRI KODIKUNNIL SURESH:</b> Hi.</p>"
        )
        segs = split_by_speaker(html, ROSTER)
        assert "Title" not in [s["speakerLabel"] for s in segs]
        (seg,) = [s for s in segs if s["speakerLabel"] == "SHRI KODIKUNNIL SURESH"]
        assert seg["text"] == "Hi."

    def test_title_line_does_not_glue_onto_the_previous_speaker(self):
        # A heading belongs to nobody -- it must not become body text for
        # whoever spoke before it, matching the legacy reader's `continue`.
        html = (
            '<p><b><a name="344*24"></a>SHRI A. RAJA:</b> First para.</p>'
            "<p><b>Title:</b> Discussion on drought.</p>"
        )
        (seg,) = split_by_speaker(html, ROSTER)
        assert seg["text"] == "First para."

    def test_motion_re_line_is_not_a_turn(self):
        html = (
            "<p><b>Motion Re:</b> Need for a comprehensive policy on drought "
            "relief.</p>"
            "<p><b>SHRI KODIKUNNIL SURESH:</b> Hi.</p>"
        )
        segs = split_by_speaker(html, ROSTER)
        assert "Motion Re" not in [s["speakerLabel"] for s in segs]
        assert [s["speakerLabel"] for s in segs] == ["SHRI KODIKUNNIL SURESH"]

    def test_timestamp_line_is_not_a_turn(self):
        html = (
            "<p><b>17.00 hrs:</b> The House then adjourned.</p>"
            "<p><b>SHRI KODIKUNNIL SURESH:</b> Hi.</p>"
        )
        segs = split_by_speaker(html, ROSTER)
        assert [s["speakerLabel"] for s in segs] == ["SHRI KODIKUNNIL SURESH"]

    def test_half_hrs_timestamp_line_is_not_a_turn(self):
        html = (
            "<p><b>11.00½ hrs:</b> The House re-assembled.</p>"
            "<p><b>SHRI KODIKUNNIL SURESH:</b> Hi.</p>"
        )
        segs = split_by_speaker(html, ROSTER)
        assert [s["speakerLabel"] for s in segs] == ["SHRI KODIKUNNIL SURESH"]

    def test_mp_named_title_is_unaffected(self):
        # The important negative test: the blocklist is exact-match on the
        # whole label, never a prefix or substring test, so a real label
        # that merely contains or resembles a blocked word must still open
        # a turn.
        html = (
            "<p><b>SHRI TITLE SINGH (PLACE):</b> Contrived but proves the "
            "exact-match rule.</p>"
            "<p><b>MOTION REDDY (ANANTAPUR):</b> A genuine member whose name "
            "merely starts with 'Motion'.</p>"
        )
        segs = split_by_speaker(html, ROSTER)
        assert [s["speakerLabel"] for s in segs] == [
            "SHRI TITLE SINGH (PLACE)",
            "MOTION REDDY (ANANTAPUR)",
        ]

    def test_heading_free_debate_is_unchanged(self):
        # anti-regression: a normal debate with no heading lines produces
        # exactly the same turns before and after the T7 fix.
        html = (
            '<p><b><a name="344*24"></a>SHRI A. RAJA (NILGIRIS):</b> First speaker.</p>'
            "<p>Continuation of first speaker.</p>"
            "<p><b>SHRI KODIKUNNIL SURESH:</b> Second speaker.</p>"
        )
        segs = split_by_speaker(html, ROSTER)
        assert [s["speakerLabel"] for s in segs] == [
            "SHRI A. RAJA (NILGIRIS)",
            "SHRI KODIKUNNIL SURESH",
        ]
        assert segs[0]["text"] == "First speaker.\n\nContinuation of first speaker."
        assert segs[1]["text"] == "Second speaker."


class TestIsHeadingLabel:
    """T7 (internal_docs/036_THE_AUDIT_AND_FIX_LIST.md): an exact-match
    blocklist of document headings that print like a speaker label — never a
    substring or prefix test."""

    def test_title_is_a_heading(self):
        assert is_heading_label("Title") is True

    def test_title_is_case_insensitive(self):
        assert is_heading_label("TITLE") is True

    def test_motion_re_is_a_heading(self):
        assert is_heading_label("Motion Re") is True

    def test_bare_timestamp_is_a_heading(self):
        assert is_heading_label("17.00 hrs") is True

    def test_half_past_timestamp_with_colon_separator_is_a_heading(self):
        assert is_heading_label("11.00½ hrs") is True

    def test_timestamp_with_trailing_period_is_a_heading(self):
        assert is_heading_label("17.00 hrs.") is True

    def test_label_merely_containing_title_is_not_a_heading(self):
        # exact-match only: "SHRI TITLE SINGH" contains "title" as a word but
        # is not the string "title"
        assert is_heading_label("SHRI TITLE SINGH") is False

    def test_label_merely_starting_with_motion_is_not_a_heading(self):
        assert is_heading_label("MOTION REDDY (ANANTAPUR)") is False

    def test_ordinary_label_is_not_a_heading(self):
        assert is_heading_label("SHRI A. RAJA (NILGIRIS)") is False

    def test_empty_label_is_not_a_heading(self):
        assert is_heading_label("") is False


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


class TestHeadingDoesNotLeakOntoThePreviousSpeaker:
    """Dropping a heading line must also CLOSE the open turn.

    The first version of the heading guard just skipped the paragraph. That is
    a poison bug wearing a noise bug's clothes: a heading's own body runs on
    into the paragraphs after it, and with the previous speaker's turn still
    open those paragraphs get appended to THEM. Measured over the corpus before
    this was fixed: 527 heading lines sit mid-document and 100 of them
    immediately follow an identified person -- in debate 53155, 286 words of
    "List Of Members Who Have Associated Themselves With The Issues Raised
    Under Matters Of Urgent Public Importance" would have become Rajmohan
    Unnithan's speech.

    Neither the unit tests nor an 88-debate random probe caught this; it took a
    corpus-wide count. Sampling a heavy tail, again.
    """

    HTML = """
    <html><body>
    <p><b>SHRI A. B. REAL (SOMEWHERE):</b> Sir, I want to raise an issue about
       the drought in my constituency, which has affected many farmers.</p>
    <p><b>Title:</b> List Of Members Who Have Associated Themselves With The
       Issues Raised Under Matters Of Urgent Public Importance.</p>
    <p>Shri One, Shri Two, Shri Three, Shri Four and Shri Five.</p>
    </body></html>
    """

    def _segments(self):
        return split_by_speaker(self.HTML, [])

    def test_the_heading_itself_is_not_a_turn(self):
        assert not any((s["speakerLabel"] or "").strip().rstrip(":").lower() == "title"
                       for s in self._segments())

    def test_the_heading_body_is_not_filed_under_the_previous_speaker(self):
        segs = self._segments()
        speaker = [s for s in segs if s["speakerLabel"] and "REAL" in s["speakerLabel"]]
        assert len(speaker) == 1
        text = speaker[0]["text"]
        assert "drought" in text, "the real speaker kept their own words"
        assert "Associated Themselves" not in text, (
            "the heading's own body leaked into a real MP's turn"
        )
        assert "Shri One" not in text, (
            "the paragraph AFTER the heading leaked into a real MP's turn"
        )

    def test_the_orphaned_body_survives_as_unattributed(self):
        """Loss, not silent deletion: the text is still in the corpus, just
        attributed to nobody -- which is what it is."""
        segs = self._segments()
        orphan = [s for s in segs if s["speakerLabel"] is None]
        assert orphan, "the heading's body should survive as an unattributed segment"
        assert any("Shri One" in s["text"] for s in orphan)
