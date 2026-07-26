"""
Part 5 — decoding the legacy CDAC-GIST/ISFOC "gibberish" Hindi font.

Covers legacy_hindi.decode_legacy_hindi and its wiring into the legacy parser:
the older transcripts store Hindi as pre-Unicode font glyph-sequences
("<ºÉBÉEä ¤ÉÉ®ä àÉå") that must be turned back into real Devanagari, while English
and already-Unicode text pass through untouched.
"""
from legacy_hindi import decode_legacy_hindi, looks_encoded
from debate_fetch_legacy import split_by_speaker_legacy

# The smallest genuine piece of this font that a real transcript always
# supplies: "gÉÉÒ" is the whole-word glyph sequence for श्री, the honorific that
# opens essentially every Hindi speaker label.
_CARRIER = "gÉÉÒ "
_CARRIER_DECODED = "श्री "


def decode_fragment(fragment: str) -> str:
    """Decode a word too short to arm the decoder on its own.

    The decoder only fires when it sees a *multi-glyph* ISFOC cluster (see
    legacy_hindi._ENCODED_SIGNATURE). It used to fire on any single glyph too,
    and that was a bug: `½` is how this source writes a half-past timestamp
    ("11.00½ hrs"), `®` is a trademark sign, `°` a degree sign, and arming on
    one of those ran the visual-to-logical matra reordering over already-correct
    Unicode Devanagari and scrambled it. Measured over the whole corpus, the
    restriction stopped the decoder touching 1,987 turns of plain English and
    lost zero genuine detections.

    A few tests below pin an ISFOC_MAP row using a two- or three-glyph word
    built entirely from single-glyph keys ("cÚÄ" = हूँ, "uÉ®É" = द्वारा). Those
    fragments no longer arm the decoder — correctly, because such a call cannot
    occur in production: the decoder is only ever handed a whole turn or a whole
    speaker label, and either always carries a cluster somewhere. So the row is
    still worth pinning; the bare fragment is not the way to reach it. This
    helper supplies the carrier a real transcript would have supplied and strips
    the decoded carrier back off, leaving the assertion about the row intact.
    """
    out = decode_legacy_hindi(_CARRIER + fragment)
    assert out.startswith(_CARRIER_DECODED), f"carrier itself failed to decode: {out!r}"
    return out[len(_CARRIER_DECODED):]


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
        # Inside a Hindi run "*" is the danda (।). On the English side it is a
        # footnote marker and is now left alone -- see the safety suite.
        assert decode_fragment("cè*").endswith("है।")

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


class TestTableGapsThatStrandedResidue:
    """Glyphs that had no ISFOC_MAP row and fell through as literal Latin-1.

    Every sequence below was taken from a real 13th/14th-LS transcript; the
    comment on each gives the word as the source prints it. A missing row here
    is not cosmetic: it strands residue in the middle of a name, so the label
    never matches a member -- and (before the signature fix) that same residue
    re-armed the decoder and corrupted the text on a second pass.
    """

    def test_a_plus_pre_base_short_i_is_not_swallowed_by_aa(self):
        # The headline gap. "अ" + pre-base "ि" and "आ" are both "+É" followed by
        # a glyph opening with "É", so longest-first let "+ÉÉ" (आ) eat the "É"
        # that "ÉÊ" (ि) needed: "अनिल" decoded as "आÊनल".
        assert decode_legacy_hindi("+ÉÉÊxÉãÉ ¤ÉºÉÖ") == "अनिल बसु"
        assert decode_legacy_hindi("+ÉÉÊJÉãÉä¶É") == "अखिलेश"
        assert decode_legacy_hindi("+ÉÉÊvÉBÉEÉ®") == "अधिकार"

    def test_a_plus_other_pre_base_glyphs_are_not_swallowed_either(self):
        assert decode_legacy_hindi("+ÉÉÎºiÉi´É") == "अस्तित्व"
        assert decode_legacy_hindi("+ÉÉËcºÉÉ") == "अहिंसा"
        assert decode_legacy_hindi("+ÉÉì{É®SªÉÖÉÊxÉ]ÉÒ") == "ऑपरच्युनिटी"

    def test_a_real_aa_followed_by_short_i_still_takes_the_aa_branch(self):
        # The control for the two tests above, and the case they could break: a
        # genuine "आ" + "ि" carries one more "É" and must NOT read as "अ" + "ि".
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
        # "ÉÉä" (ो) is a longer key than "¥É" (ब्र), so it consumes the "É" and
        # leaves the bare half-form -- which must therefore be mapped too, just
        # as "¤É" (ब) needs "¤" (ब्). The halant-merge then rejoins them.
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
        assert decode_fragment("cÚÄ") == "हूँ"
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
        # क is drawn "B".."E" and फ is "{".."E"; a below-base matra goes BETWEEN
        # the halves, so the closing half was left stranded as a literal "E".
        assert decode_legacy_hindi("BÉÖEÆ´É®") == "कुंवर"
        assert decode_legacy_hindi("BÉÖEàÉÉ®ÉÒ") == "कुमारी"
        assert decode_legacy_hindi("BÉßE{ÉÉ") == "कृपा"
        assert decode_legacy_hindi("{ÉÖEãÉ") == "फुल"

    def test_chha_still_works_through_the_closing_half(self):
        # "EU" (closing half + छ) is what makes "BÉÖEU" decode today. Adding the
        # "BÉÖE" row above consumes that "E" first, so छ must stand on its own
        # too -- and कुछ must still come out the other side either way.
        assert decode_legacy_hindi("BÉÖEU") == "कुछ"
        assert decode_legacy_hindi("+ÉSUÉÒ") == "अच्छी"

    def test_da_conjuncts(self):
        assert decode_fragment("uÉ®É") == "द्वारा"
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
