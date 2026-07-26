"""
Part 5b — the audit's three "decoder damages correct text" defects (T3 in
internal_docs/036_THE_AUDIT_AND_FIX_LIST.md).

Three independent bugs, each one where the decoder fires on -- or mangles --
text that was already correct:

  A. `_ENCODED_SIGNATURE` used to arm on ANY ISFOC_MAP key containing a
     Latin-1 supplement character, including single-glyph keys that are
     ordinary punctuation in real transcripts: half-hour timestamps ("½"),
     the registered-trademark sign ("®"), the degree sign ("°"). One of
     those in an otherwise-correct Unicode paragraph armed the decoder for
     the whole thing, and the visual-to-logical matra reordering then ran
     over text that never needed it.
  B. `decode_legacy_hindi` unconditionally deleted every newline before
     tokenising. English survives decoding only by being recognised as a
     whitespace-delimited, all-ASCII-letters token; deleting the blank line
     between two paragraphs glues the last word of one to the first word of
     the next, so the joined blob stops looking like English and gets
     transliterated.
  C. The protected-English branch ran `token.replace("*", "।")` -- turning a
     footnote-marker asterisk sitting on an English word into a Devanagari
     full stop.
"""
from legacy_hindi import decode_legacy_hindi, looks_encoded


class TestSingleGlyphKeysDoNotArmTheDecoder:
    """Problem A: a lone Latin-1 supplement char is ordinary punctuation."""

    def test_timestamp_glyph_does_not_arm_decoder(self):
        text = "The House assembled at 18.01½ hrs."
        assert decode_legacy_hindi(text) == text

    def test_registered_trademark_glyph_does_not_arm_decoder(self):
        text = "A registered trademark symbol ®"
        assert decode_legacy_hindi(text) == text

    def test_degree_sign_glyph_does_not_arm_decoder(self):
        text = "The temperature is 40° today"
        assert decode_legacy_hindi(text) == text

    def test_correct_devanagari_is_never_reordered(self):
        # The exact corruption from internal_docs/036: a genuinely-correct
        # Unicode sentence carrying a "½" timestamp elsewhere in the string
        # must survive completely untouched -- not just the timestamp, but
        # "निम्नलिखित" and "विषयों" must not be reordered either.
        text = "माननीय अध्यक्ष, निम्नलिखित विषयों पर चर्चा हो। 11.00½ hrs"
        assert decode_legacy_hindi(text) == text


class TestParagraphBreaksSurviveDecoding:
    """Problem B: newline stripping must not glue paragraphs together."""

    def test_paragraph_breaks_survive_decoding(self):
        # Genuinely mojibake on both sides of a blank line -- looks_encoded
        # must fire, and the blank line between the two paragraphs must
        # still be there afterwards.
        one = "<ºÉBÉEä ¤ÉÉ®ä àÉå àÉé BÉEcxÉÉ SÉÉcÚÆMÉÉ*"
        text = one + "\n\n" + one
        decoded = decode_legacy_hindi(text)
        assert "\n\n" in decoded
        assert decoded.count("इसके बारे में मैं कहना चाहूंगा।") == 2

    def test_english_adjacent_to_hindi_paragraph_is_not_transliterated(self):
        # The corpus case from internal_docs/036: a Hindi paragraph, a blank
        # line, then an English parenthetical. Before the fix, deleting the
        # newline glued "ज्ञापन।" to "(Placed" into one non-English-looking
        # token, and "Placed in Library" came out as "घ्थ्aहed in Library".
        text = "<ºÉBÉEä ¤ÉÉ®ä àÉå àÉé BÉEcxÉÉ SÉÉcÚÆMÉÉ*\n\n(Placed in Library, See No. LT-1234)"
        decoded = decode_legacy_hindi(text)
        assert "(Placed in Library, See No. LT-1234)" in decoded
        assert "घ्थ्" not in decoded


class TestAsteriskInEnglishIsNotADanda:
    """Problem C: a footnote-marker asterisk on an English word is not a danda."""

    def test_asterisk_in_english_is_not_a_danda(self):
        text = "See footnote * below"
        assert decode_legacy_hindi(text) == text

    def test_asterisk_glued_to_an_english_word_survives(self):
        # The branch this bug actually lives on: a token classified as
        # protected English (has ASCII letters) that also carries an
        # asterisk footnote marker with no separating space, arrived at
        # decode_legacy_hindi alongside genuine mojibake so the whole call
        # is armed and the protected-English branch actually runs.
        text = "<ºÉBÉEä ¤ÉÉ®ä àÉå* See footnote* below"
        decoded = decode_legacy_hindi(text)
        assert "footnote*" in decoded
        assert "footnote।" not in decoded


class TestLineContinuationCleanupStillWorks:
    """Guards fix B from over-deleting: "\\\\\\n" is copy-paste damage, not
    a paragraph break, and must still be removed so the two halves of a
    word split across it rejoin."""

    def test_line_continuation_join_still_removed(self):
        # "SÉÉcÚÆMÉÉ" (चाहूंगा) broken by a literal backslash-newline
        # continuation artifact. Removing exactly "\\\n" reconstitutes it;
        # leaving the backslash or newline behind would strand residue mid-word.
        text = "<ºÉBÉEä ¤ÉÉ®ä àÉå àÉé BÉEcxÉÉ SÉÉ\\\ncÚÆMÉÉ*"
        decoded = decode_legacy_hindi(text)
        assert decoded == "इसके बारे में मैं कहना चाहूंगा।"
        assert "\\" not in decoded


class TestRealMojibakeStillDecodesAfterTheFix:
    """The regression check: none of the three fixes may weaken real detection."""

    def test_real_mojibake_still_decodes(self):
        assert looks_encoded("àÉcÉänªÉÉ, ªÉc àÉé <ºÉÉÊãÉA BÉEc ®cÉ cÚÆ") is True
        got = decode_legacy_hindi("àÉcÉänªÉÉ, ªÉc àÉé <ºÉÉÊãÉA BÉEc ®cÉ cÚÆ")
        assert got == "महोदया, यह मैं इसलिए कह रहा हूं"
