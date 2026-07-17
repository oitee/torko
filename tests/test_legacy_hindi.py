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


class TestTableGapsThatStrandedResidue:
    def test_a_plus_pre_base_short_i_is_not_swallowed_by_aa(self):
        # अ plus pre-base ि must not read as आ.
        assert decode_legacy_hindi("+ÉÉÊxÉãÉ ¤ÉºÉÖ") == "अनिल बसु"
        assert decode_legacy_hindi("+ÉÉÊJÉãÉä¶É") == "अखिलेश"
        assert decode_legacy_hindi("+ÉÉÊvÉBÉEÉ®") == "अधिकार"

    def test_a_plus_other_pre_base_glyphs_are_not_swallowed_either(self):
        assert decode_legacy_hindi("+ÉÉÎºiÉi´É") == "अस्तित्व"
        assert decode_legacy_hindi("+ÉÉËcºÉÉ") == "अहिंसा"
        assert decode_legacy_hindi("+ÉÉì{É®SªÉÖÉÊxÉ]ÉÒ") == "ऑपरच्युनिटी"

    def test_a_real_aa_followed_by_short_i_still_takes_the_aa_branch(self):
        # A genuine आ plus ि has one more É and must not read as अ plus ि.
        assert decode_legacy_hindi("+ÉÉÉÊn") == "आदि"

    def test_candra_o_matra(self):
        assert decode_legacy_hindi("bÉì.") == "डॉ."
        assert decode_legacy_hindi("BÉEÉìàÉxÉ´ÉèãlÉ") == "कॉमनवैल्थ"

    def test_wide_pre_base_short_i_variants_shift_like_the_narrow_ones(self):
        # "ÉÎ"/"ÉÏ" are the same matras as "ÉÊ"/"ÉË" drawn wider to reach over a
        # conjunct. They are separate glyphs, and shift identically.
        assert decode_legacy_hindi("¤ÉÉÎãBÉE") == "बल्कि"
        assert decode_legacy_hindi("ÉÎºlÉiÉ") == "स्थित"
        assert decode_legacy_hindi("ÉÊ¤ÉÉÏãbMÉ") == "बिल्डिंग"

    def test_r_conjuncts_are_single_glyphs(self):
        assert decode_legacy_hindi("+ÉÉµÉEàÉhÉ") == "आक्रमण"
        assert decode_legacy_hindi("|ÉEÉÆºÉ") == "फ्रांस"
        assert decode_legacy_hindi("{Éè]ÅÉäãÉ") == "पैट्रोल"
        assert decode_legacy_hindi("BÉEÉÆº]ÉÒ]áÉÚ¶ÉxÉ") == "कांस्टीट्यूशन"

    def test_conjunct_half_forms_rejoin_a_following_o_matra(self):
        # ÉÉä (ो) is a longer key than ¥É (ब्र), so the bare half-form must also be mapped.
        assert decode_legacy_hindi("¥ÉÉÆb") == "ब्रांड"
        assert decode_legacy_hindi("¥ÉÉäBÉEºÉÇ") == "ब्रोकर्स"
        assert decode_legacy_hindi("»ÉÉäiÉ") == "स्रोत"
        assert decode_legacy_hindi("§ÉÉÊàÉiÉ") == "भ्रमित"

    def test_ha_half_form_has_its_own_glyph(self):
        assert decode_legacy_hindi("ÿªÉÚàÉxÉ") == "ह्यूमन"
        assert decode_legacy_hindi("ºÉÖ¥ÉÿàÉhªÉàÉ") == "सुब्रह्मण्यम"

    def test_second_dha_with_nukta_glyph(self):
        assert decode_legacy_hindi("SÉÆbÉÒMÉfÃ") == "चंडीगढ़"
        assert decode_legacy_hindi("{ÉfÃxÉä") == "पढ़ने"

    def test_candrabindu(self):
        assert decode_legacy_hindi("cÚÄ") == "हूँ"
        assert decode_legacy_hindi("+ÉÉÄJÉÉå") == "आँखों"

    def test_independent_uu_and_ru(self):
        assert decode_legacy_hindi(">ó{É®") == "ऊपर"
        assert decode_legacy_hindi("âó{ÉªÉä") == "रुपये"

    def test_matras_that_carry_the_reph_place_it_on_the_right_letter(self):
        # These glyphs are a matra and a reph at once. The reph must still land
        # on the consonant it belongs to, which is not the one it is typed after.
        assert decode_legacy_hindi("{ÉÉ]ÉÔ") == "पार्टी"
        assert decode_legacy_hindi("SÉ]VÉÉÔ") == "चटर्जी"
        assert decode_legacy_hindi("àÉÉBÉEæ]") == "मार्केट"
        assert decode_legacy_hindi("ÉÊxÉnæ¶É") == "निर्देश"
        assert decode_legacy_hindi("ºÉ´ÉÉæSSÉ") == "सर्वोच्च"
        assert decode_legacy_hindi("vÉàÉÉÈiÉ®hÉ") == "धर्मांतरण"

    def test_below_base_matra_typed_inside_a_two_half_glyph(self):
        # A below-base matra goes between the two halves of क and फ.
        assert decode_legacy_hindi("BÉÖEÆ´É®") == "कुंवर"
        assert decode_legacy_hindi("BÉÖEàÉÉ®ÉÒ") == "कुमारी"
        assert decode_legacy_hindi("BÉßE{ÉÉ") == "कृपा"
        assert decode_legacy_hindi("{ÉÖEãÉ") == "फुल"

    def test_chha_still_works_through_the_closing_half(self):
        # छ must stand on its own so that BÉÖEU still decodes.
        assert decode_legacy_hindi("BÉÖEU") == "कुछ"
        assert decode_legacy_hindi("+ÉSUÉÒ") == "अच्छी"

    def test_da_conjuncts(self):
        assert decode_legacy_hindi("uÉ®É") == "द्वारा"
        assert decode_legacy_hindi("ÉÊuiÉÉÒªÉ") == "द्वितीय"
        assert decode_legacy_hindi("´ÉètÉ") == "वैद्य"
        assert decode_legacy_hindi("ÉÊ´É¶´ÉÉÊ´ÉtÉÉãÉªÉ") == "विश्वविद्यालय"
        assert decode_legacy_hindi("=qä¶ªÉÉå") == "उद्देश्यों"

    def test_double_ta_conjunct(self):
        assert decode_legacy_hindi("MÉÖhÉ´ÉkÉÉ") == "गुणवत्ता"

    def test_o_carrying_reph_is_built_like_the_plain_o(self):
        # "Éæ" is to "æ" what "Éä" (ो) is to "ä" (े) -- this font builds ो as
        # ा + े, and the reph-bearing pair follows the same construction.
        assert decode_legacy_hindi("ºÉ´ÉÉæSSÉ") == "सर्वोच्च"   # Éæ -> reph + ो
        assert decode_legacy_hindi("àÉÉBÉEæ]") == "मार्केट"      # æ  -> reph + े


class TestSecondPassIsANoOp:
    def test_looks_encoded_is_false_on_decoded_output_even_with_residue(self):
        # Ê and Ò have no ISFOC_MAP entry, so they stay as Latin-1 residue next to Devanagari.
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
        # A label decoded twice must not change. सिंह must not become सहिं.
        once = decode_legacy_hindi("gÉÉÒ. ºÉÉÉÊcÉ¤É ÉËºÉc ´ÉàÉÉÇ")
        twice = decode_legacy_hindi(once)
        assert "सिंह" in once
        assert once == twice

    def test_decoded_matra_order_is_not_swapped_by_a_second_pass(self):
        # A matra followed by the next consonant must not be shifted again (दक्षिण).
        first_pass = decode_legacy_hindi("nÉÊFÉhÉ")
        second_pass = decode_legacy_hindi(first_pass)
        assert first_pass == second_pass


class TestOnlyRealEncodedSequencesArmTheDecoder:
    def test_english_with_an_invisible_soft_hyphen_is_left_alone(self):
        # Real case: LS14/5/2711. Soft hyphens as line-break hints inside English.
        text = "Rajya Sabha Mem\xadbers are present"
        assert decode_legacy_hindi(text) == text

    def test_a_run_of_soft_hyphens_is_not_invented_into_letters(self):
        assert decode_legacy_hindi("\xad" * 3 + "_") == "\xad\xad\xad_"

    def test_but_soft_hyphen_still_means_sha_inside_real_encoded_text(self):
        # In encoded text the soft hyphen is ष, so it must not be stripped.
        assert decode_legacy_hindi("ºÉÖ\xadÉàÉÉ") == "सुषमा"

    def test_already_unicode_hindi_is_not_re_shifted(self):
        # Real case: LS16/4/5083. A 2015 debate, never legacy-encoded, with a stray Latin-1 char.
        text = "श्री मल्लिकार्जुन खड़गे: मैडम, डिवीजन के लिए हमने पूछा।"
        assert decode_legacy_hindi(text) == text


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
