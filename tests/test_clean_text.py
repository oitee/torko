from debate_fetch import _clean_inline, html_to_clean_text


class TestCleanInline:
    def test_collapses_runs_of_whitespace(self):
        # Many spaces / newlines / tabs inside a paragraph -> one space
        assert _clean_inline("Thank    you,\n   Chairman   Sir") == "Thank you, Chairman Sir"

    def test_converts_nbsp_to_space_then_collapses(self):
        # \xa0 (&nbsp;) is treated as ordinary space and squashed
        assert _clean_inline("Constitution.\xa0\xa0\xa0\xa0 I am one") == "Constitution. I am one"

    def test_strips_space_before_ascii_punctuation(self):
        # Floating gap before , . ; : ? ! is removed
        assert _clean_inline("Sir , I agree .") == "Sir, I agree."

    def test_strips_space_before_devanagari_danda(self):
        # The Hindi full-stop "।" (danda) gets the same treatment
        assert _clean_inline("बैठे हैं ।") == "बैठे हैं।"

    def test_trims_leading_and_trailing_whitespace(self):
        assert _clean_inline("   hello   ") == "hello"

    def test_empty_input_stays_empty(self):
        assert _clean_inline("   ") == ""


class TestHtmlToCleanText:
    def test_keeps_paragraph_break_between_p_blocks(self):
        # two <p> blocks -> two paragraphs joined by a blank line
        out = html_to_clean_text("<p>First para</p><p>Second para</p>")
        assert out == "First para\n\nSecond para"

    def test_br_is_treated_as_a_real_break(self):
        # <br> is one of the two "real boundary" markers, like </p>
        out = html_to_clean_text("<p>line a<br>line b</p>")
        assert out == "line a\n\nline b"

    def test_collapses_hard_wraps_inside_a_paragraph(self):
        # the mid-sentence newline wraps (no tag) are just layout noise -> space
        html = "<p>Thank you, Chairman Sir\nfor giving me\nthis opportunity.</p>"
        assert html_to_clean_text(html) == "Thank you, Chairman Sir for giving me this opportunity."

    def test_strips_tags_and_nbsp(self):
        out = html_to_clean_text("<p><b><span>A&nbsp;RAJA</span></b> spoke</p>")
        assert out == "A RAJA spoke"

    def test_drops_empty_paragraphs(self):
        out = html_to_clean_text("<p>real</p><p>   </p><p>text</p>")
        assert out == "real\n\ntext"
