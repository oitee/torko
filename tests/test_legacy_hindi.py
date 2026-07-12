"""
Part 5 — decoding the legacy CDAC-GIST/ISFOC "gibberish" Hindi font.

Covers legacy_hindi.decode_legacy_hindi and its wiring into the legacy parser:
the older transcripts store Hindi as pre-Unicode font glyph-sequences
("<ºÉBÉEä ¤ÉÉ®ä àÉå") that must be turned back into real Devanagari, while English
and already-Unicode text pass through untouched.
"""
from legacy_hindi import decode_legacy_hindi, looks_encoded
from debate_fetch_legacy import split_by_speaker_legacy


class TestLooksEncoded:
    """The cheap signature test that gates decoding."""

    def test_legacy_glyphs_are_encoded(self):
        assert looks_encoded("ºÉBÉEä") is True

    def test_plain_english_is_not_encoded(self):
        assert looks_encoded("MR. SPEAKER: Hello.") is False

    def test_unicode_devanagari_is_not_encoded(self):
        assert looks_encoded("श्री किरेन रिजिजू") is False

    def test_empty_is_not_encoded(self):
        assert looks_encoded("") is False


class TestDecodeLegacyHindi:
    """Archetypes of the substitution + structural fixes."""

    def test_basic_sentence(self):
        got = decode_legacy_hindi("<ºÉBÉEä ¤ÉÉ®ä àÉå àÉé BÉEcxÉÉ SÉÉcÚÆMÉÉ*")
        assert got == "इसके बारे में मैं कहना चाहूंगा।"

    def test_english_passes_through_untouched(self):
        assert decode_legacy_hindi("MR. SPEAKER: Hello.") == "MR. SPEAKER: Hello."

    def test_unicode_passes_through_untouched(self):
        assert decode_legacy_hindi("श्री किरेन रिजिजू") == "श्री किरेन रिजिजू"

    def test_sha_survives_the_soft_hyphen_cleanup(self):
        # ष is encoded via a soft-hyphen glyph; a naive cleanup drops it and
        # turns "दोषी" into "दोाी". The decoder must recover the ष.
        assert "दोषी" in decode_legacy_hindi("nÉä\xadÉÉÒ")
        assert "परिषद" in decode_legacy_hindi("{ÉÉÊ®\xadÉn")

    def test_english_wrapped_in_nonascii_punctuation_is_protected(self):
        # "…(Interruptions)" must not decode into "…(Iदterruptत्oदs)".
        assert decode_legacy_hindi("…(Interruptions)") == "…(Interruptions)"

    def test_star_becomes_danda_in_hindi_run(self):
        assert decode_legacy_hindi("cè*").endswith("है।")


class TestLegacyParserDecodesText:
    """The parser hands back real Devanagari, not glyph gibberish."""

    def test_hindi_turn_is_decoded_end_to_end(self):
        html = "<p>ºÉ®BÉEÉ® BÉE¤É ¤ÉªÉÉxÉ näMÉÉÒ*</p>"
        (seg,) = split_by_speaker_legacy(html, [])
        assert seg["text"] == "सरकार कब बयान देगी।"

    def test_english_label_and_speech_survive(self):
        html = "<p>MR. SPEAKER: Motion moved.</p>"
        (seg,) = split_by_speaker_legacy(html, [])
        assert seg["speakerLabel"] == "MR. SPEAKER"
        assert seg["text"] == "Motion moved."
