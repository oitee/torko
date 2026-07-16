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

    def test_pre_base_short_i_with_anusvara_becomes_singh(self):
        # "ÉË" is the pre-base glyph for "ि" + "ं". Unmapped, it fell through
        # as a literal "Ë" and left "ाËसह" — the name never reached the roster.
        assert decode_legacy_hindi("ÉËºÉc") == "सिंह"

    def test_pre_base_short_i_with_anusvara_in_a_full_label(self):
        assert decode_legacy_hindi("gÉÉÒ ®ÉVÉxÉÉlÉ ÉËºÉc") == "श्री राजनाथ सिंह"
        assert decode_legacy_hindi("gÉÉÒ ®ÉàÉVÉÉÒ´ÉxÉ ÉËºÉc") == "श्री रामजीवन सिंह"

    def test_bare_short_i_still_shifts_after_its_consonant(self):
        # Guards the anusvara-carrying shift regex against regressing the plain
        # short-i case it subsumes: "ÉÊ" alone must still land after its
        # consonant, including across a conjunct.
        assert decode_legacy_hindi("ÉÊºÉc") == "सिह"
        assert decode_legacy_hindi("ÉÊBÉEºÉÉxÉ") == "किसान"


class TestSecondPassIsANoOp:
    """decode_legacy_hindi must be safe to call on its own output.

    The short-i shift is a one-way transform: running it twice on text that
    is already correctly ordered swaps the matra back onto the wrong side
    (e.g. a correct "...िण" becomes "...णि"). A decoded label can also carry
    residue -- a glyph with no ISFOC_MAP entry, left untranslated -- and that
    residue must not by itself convince looks_encoded the text needs another
    pass.
    """

    def test_looks_encoded_is_false_on_decoded_output_even_with_residue(self):
        # "Ê" and "Ò" have no ISFOC_MAP entry, so they survive the first
        # decode as leftover Latin-1 residue sitting next to real Devanagari.
        # Under the old signature (any Latin-1 char) that residue alone kept
        # looks_encoded True forever.
        decoded = decode_legacy_hindi("ÉÊnFÉhÉ ÊnããÉÒ")
        assert "Ê" in decoded and "Ò" in decoded  # sanity: residue is present
        assert looks_encoded(decoded) is False

    def test_repeated_decoding_does_not_drift(self):
        raw = "ÉÊnFÉhÉ ÊnããÉÒ"
        once = decode_legacy_hindi(raw)
        twice = decode_legacy_hindi(once)
        thrice = decode_legacy_hindi(twice)
        assert once == twice == thrice

    def test_singh_is_not_re_broken_by_a_second_pass(self):
        # The exact corpus case: a speaker label decoded once by the legacy
        # parser, then decoded again downstream. "सिंह" (Singh) must not
        # become "सहिं".
        once = decode_legacy_hindi("gÉÉÒ. ºÉÉÉÊcÉ¤É ÉËºÉc ´ÉàÉÉÇ")
        twice = decode_legacy_hindi(once)
        assert "सिंह" in once
        assert once == twice

    def test_decoded_matra_order_is_not_swapped_by_a_second_pass(self):
        # "दक्षिण" (south) is exactly the shape the shift regex must not
        # re-fire on: a matra correctly followed by the next syllable's
        # consonant looks, superficially, like the pre-shift pattern.
        first_pass = decode_legacy_hindi("nÉÊFÉhÉ")
        second_pass = decode_legacy_hindi(first_pass)
        assert first_pass == second_pass


class TestOnlyRealEncodedSequencesArmTheDecoder:
    """A lone Latin-1 character is not evidence of the legacy font.

    The signature used to be "any Latin-1 supplement character", which swept in
    text that merely *contains* one -- most damagingly the invisible soft
    hyphen (U+00AD). Decoding blanket-replaces that with ष, on purpose (it is
    genuinely how this font stores ष), so arming the decoder on a stray soft
    hyphen turned invisible formatting into invented letters and mangled the
    surrounding words. The signature now needs a real ISFOC_MAP key.
    """

    def test_english_with_an_invisible_soft_hyphen_is_left_alone(self):
        # a real block from LS14/5/2711: soft hyphens used as line-break hints
        # inside English. Before, this decoded to "Rajya Sabha ग्emषडers ...".
        text = "Rajya Sabha Mem\xadbers are present"
        assert decode_legacy_hindi(text) == text

    def test_a_run_of_soft_hyphens_is_not_invented_into_letters(self):
        assert decode_legacy_hindi("\xad" * 3 + "_") == "\xad\xad\xad_"

    def test_but_soft_hyphen_still_means_sha_inside_real_encoded_text(self):
        # The counterweight, and the reason this can't just strip U+00AD: in
        # genuinely encoded text the soft hyphen IS ष, and dropping it makes
        # the letter vanish ("सुषमा" -> "सुामा"). Other keys in the run arm
        # the decoder, so ष still resolves. If this ever fails, the signature
        # has been tightened too far.
        assert decode_legacy_hindi("ºÉÖ\xadÉàÉÉ") == "सुषमा"

    def test_already_unicode_hindi_is_not_re_shifted(self):
        # A real block from LS16/4/5083 -- a 2015 debate, never legacy-encoded.
        # It reached the decoder carrying a stray Latin-1 char, armed the old
        # signature, and had its matras shifted: मल्लिकार्जुन -> मल्लकिार्जुन.
        text = "श्री मल्लिकार्जुन खड़गे: मैडम, डिवीजन के लिए हमने पूछा।"
        assert decode_legacy_hindi(text) == text


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
