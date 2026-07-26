from legacy_hindi import decode_legacy_hindi, looks_encoded


class TestSingleGlyphKeysDoNotArmTheDecoder:
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
        # A correct Unicode sentence with a "½" timestamp must stay untouched.
        text = "माननीय अध्यक्ष, निम्नलिखित विषयों पर चर्चा हो। 11.00½ hrs"
        assert decode_legacy_hindi(text) == text


class TestParagraphBreaksSurviveDecoding:
    def test_paragraph_breaks_survive_decoding(self):
        one = "<ºÉBÉEä ¤ÉÉ®ä àÉå àÉé BÉEcxÉÉ SÉÉcÚÆMÉÉ*"
        text = one + "\n\n" + one
        decoded = decode_legacy_hindi(text)
        assert "\n\n" in decoded
        assert decoded.count("इसके बारे में मैं कहना चाहूंगा।") == 2

    def test_english_adjacent_to_hindi_paragraph_is_not_transliterated(self):
        # Real corpus case: a Hindi paragraph, a blank line, then an English parenthetical.
        text = "<ºÉBÉEä ¤ÉÉ®ä àÉå àÉé BÉEcxÉÉ SÉÉcÚÆMÉÉ*\n\n(Placed in Library, See No. LT-1234)"
        decoded = decode_legacy_hindi(text)
        assert "(Placed in Library, See No. LT-1234)" in decoded
        assert "घ्थ्" not in decoded


class TestAsteriskInEnglishIsNotADanda:
    def test_asterisk_in_english_is_not_a_danda(self):
        text = "See footnote * below"
        assert decode_legacy_hindi(text) == text

    def test_asterisk_glued_to_an_english_word_survives(self):
        # A protected English token with an asterisk footnote marker and no separating space.
        text = "<ºÉBÉEä ¤ÉÉ®ä àÉå* See footnote* below"
        decoded = decode_legacy_hindi(text)
        assert "footnote*" in decoded
        assert "footnote।" not in decoded


class TestLineContinuationCleanupStillWorks:
    def test_line_continuation_join_still_removed(self):
        # Mojibake broken by a literal backslash-newline continuation.
        text = "<ºÉBÉEä ¤ÉÉ®ä àÉå àÉé BÉEcxÉÉ SÉÉ\\\ncÚÆMÉÉ*"
        decoded = decode_legacy_hindi(text)
        assert decoded == "इसके बारे में मैं कहना चाहूंगा।"
        assert "\\" not in decoded


class TestRealMojibakeStillDecodesAfterTheFix:
    def test_real_mojibake_still_decodes(self):
        assert looks_encoded("àÉcÉänªÉÉ, ªÉc àÉé <ºÉÉÊãÉA BÉEc ®cÉ cÚÆ") is True
        got = decode_legacy_hindi("àÉcÉänªÉÉ, ªÉc àÉé <ºÉÉÊãÉA BÉEc ®cÉ cÚÆ")
        assert got == "महोदया, यह मैं इसलिए कह रहा हूं"
