from legacy_hindi import decode_legacy_hindi, looks_encoded
from debate_fetch_legacy import split_by_speaker_legacy


class TestLooksEncoded:
    def test_legacy_glyphs_are_encoded(self):
        assert looks_encoded("ºÉBÉEä") is True

    def test_plain_english_is_not_encoded(self):
        assert looks_encoded("MR. SPEAKER: Hello.") is False

    def test_unicode_devanagari_is_not_encoded(self):
        assert looks_encoded("श्री किरेन रिजिजू") is False

    def test_empty_is_not_encoded(self):
        assert looks_encoded("") is False


class TestDecodeLegacyHindi:
    def test_basic_sentence(self):
        got = decode_legacy_hindi("<ºÉBÉEä ¤ÉÉ®ä àÉå àÉé BÉEcxÉÉ SÉÉcÚÆMÉÉ*")
        assert got == "इसके बारे में मैं कहना चाहूंगा।"

    def test_english_passes_through_untouched(self):
        assert decode_legacy_hindi("MR. SPEAKER: Hello.") == "MR. SPEAKER: Hello."

    def test_unicode_passes_through_untouched(self):
        assert decode_legacy_hindi("श्री किरेन रिजिजू") == "श्री किरेन रिजिजू"

    def test_sha_survives_the_soft_hyphen_cleanup(self):
        # ष is encoded as a soft-hyphen glyph. Cleanup must not drop it.
        assert "दोषी" in decode_legacy_hindi("nÉä\xadÉÉÒ")
        assert "परिषद" in decode_legacy_hindi("{ÉÉÊ®\xadÉn")

    def test_english_wrapped_in_nonascii_punctuation_is_protected(self):
        # "…(Interruptions)" must not decode into "…(Iदterruptत्oदs)".
        assert decode_legacy_hindi("…(Interruptions)") == "…(Interruptions)"

    def test_star_becomes_danda_in_hindi_run(self):
        assert decode_legacy_hindi("cè*").endswith("है।")

    def test_pre_base_short_i_with_anusvara_becomes_singh(self):
        # ÉË is the pre-base glyph for ि and ं.
        assert decode_legacy_hindi("ÉËºÉc") == "सिंह"

    def test_pre_base_short_i_with_anusvara_in_a_full_label(self):
        assert decode_legacy_hindi("gÉÉÒ ®ÉVÉxÉÉlÉ ÉËºÉc") == "श्री राजनाथ सिंह"
        assert decode_legacy_hindi("gÉÉÒ ®ÉàÉVÉÉÒ´ÉxÉ ÉËºÉc") == "श्री रामजीवन सिंह"

    def test_bare_short_i_still_shifts_after_its_consonant(self):
        # ÉÊ alone must land after its consonant, including across a conjunct.
        assert decode_legacy_hindi("ÉÊºÉc") == "सिह"
        assert decode_legacy_hindi("ÉÊBÉEºÉÉxÉ") == "किसान"


class TestLegacyParserDecodesText:
    def test_hindi_turn_is_decoded_end_to_end(self):
        html = "<p>ºÉ®BÉEÉ® BÉE¤É ¤ÉªÉÉxÉ näMÉÉÒ*</p>"
        (seg,) = split_by_speaker_legacy(html, [])
        assert seg["text"] == "सरकार कब बयान देगी।"

    def test_english_label_and_speech_survive(self):
        html = "<p>MR. SPEAKER: Motion moved.</p>"
        (seg,) = split_by_speaker_legacy(html, [])
        assert seg["speakerLabel"] == "MR. SPEAKER"
        assert seg["text"] == "Motion moved."
