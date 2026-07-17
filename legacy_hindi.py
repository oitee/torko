"""
Decode the legacy-font "gibberish" Hindi found in older sansad.in transcripts
back into real Unicode Devanagari.

The 13th Lok Sabha debates (≈1999-2004) store Hindi in a pre-Unicode CDAC-GIST /
ISFOC font encoding (the bilingual "EN" variant, a cousin of DV-TTSurekh). In it,
Latin byte-sequences are glyph indices that only render as Hindi when the exact
font is installed; copied out, they read as `<ºÉBÉEä ¤ÉÉ®ä àÉå` where the intended
text is `इसके बारे में`. English runs in the same document are already fine.

This module is deliberately self-contained (no third-party converter): every
public tool we tried was hard-wired to a *different* font's table and silently
corrupted very common letters — notably `c` (our ह) which they read as ड़, so
"है" became "ड़ै" everywhere. See ARTICLE_legacy_hindi_decoding.md for the story.

Decoding is a longest-sequence-first substitution over ISFOC_MAP, plus a few
structural rules that reflect how Devanagari (and this font) work:
  * a full consonant is drawn as a half-form + a vertical-bar connector, so
    orphaned halants next to a matra are merged;
  * the short-i matra "ि" is stored to the LEFT of its consonant (visual order)
    and must be shifted to its logical position after it, together with any
    anusvara typed as part of the same pre-base glyph ("ÉË" -> "िं" -> "सिं");
  * "reph" (र्) is typed after its consonant and must be moved before it;
  * Latin words are left untouched so interleaved English survives verbatim.
"""
import re

# Reph's private-use marker, defined here because several ISFOC_MAP rows below
# decode to it; see the "Ç" entry for what it is for.
_REPH = ""

# ---------------------------------------------------------------------------
# The mapping table for this exact font variant. Multi-character keys are
# applied longest-first (see decode_legacy_hindi) so clusters like "BÉE"→क are
# consumed before their component glyphs. A handful of whole-word entries at the
# top pin down sequences the generic rules would otherwise mangle.
# ---------------------------------------------------------------------------
ISFOC_MAP = {
    # High-priority whole-word / cluster corrections
    "gÉÉÒ": "श्री",
    "ÉÊµÉEÉÎ¶SÉªÉxÉ": "क्रिश्चियन",
    "ÉÊµÉEÉÎ¶SÉªÉxºÉ": "क्रिश्चियन्स",
    "¤ÉÉÉÊãÉBÉEÉ": "बालिका",
    "|É": "प्र",
    "vÉàÉBÉEÉA": "धमकाए",
    "´ÉBÉDiÉBªÉ": "वक्तव्य",
    "BÉEÉÊàÉ]àÉé]": "कमिटमेंट",
    "BªÉ´ÉvÉÉxÉ": "व्यवधान",
    "BÉEÉªÉÇ´ÉÉcÉÒ": "कार्रवाई",

    # Full consonants & half bases
    "BÉE": "क", "BÉD": "क्", "B": "क्",
    # क and फ are drawn as two halves ("B".."E", "{".."E") and a BELOW-base matra
    # is typed *between* them rather than after the pair. Unmapped, the closing
    # half was stranded as a literal "E": "BÉÖEÆ´É®" (कुंवर) decoded as "कुEंवर".
    "BÉÖE": "कु", "BÉßE": "कृ", "{ÉÖE": "फु",
    "JÉ": "ख", "J": "ख्",
    "MÉ": "ग", "M": "ग्",
    "PÉ": "घ", "P": "घ्",
    "b": "ड", "½": "ड़",
    "SÉ": "च", "S": "च्",
    # "EU" is really the closing half of क/फ plus छ -- it is what lets "BÉÖEU"
    # (कुछ) work today. छ on its own still needs its own row: "+ÉSUÉÒ" -> अच्छी.
    "EU": "छ", "U": "छ",
    "VÉ": "ज", "V": "ज्",
    "ZÉ": "झ", "Z": "झ्",
    "g½": "ढ़", "gÉ": "ढ", "g": "ढ",
    # A second ढ़ glyph, distinct from "g½": "SÉÆbÉÒMÉfÃ" -> चंडीगढ़, "{ÉfÃxÉä" -> पढ़ने.
    "fÃ": "ढ़",
    "]": "ट",
    "~": "ठ",
    "hÉ": "ण", "h": "ण्",
    "iÉ": "त", "i": "त्",
    "kÉ": "त्त",   # "MÉÖhÉ´ÉkÉÉ" -> गुणवत्ता
    "lÉ": "थ", "l": "थ्",
    "n": "द",
    # द-conjuncts, each its own glyph. Note "u" carries its connector but "tÉ"
    # takes the separate "É": "uÉ®É" -> द्वारा, "ÉÊuiÉÉÒªÉ" -> द्वितीय, but
    # "´ÉètÉ" -> वैद्य and "ÉÊ´É¶´ÉÉÊ´ÉtÉÉãÉªÉ" -> विश्वविद्यालय.
    "u": "द्व", "tÉ": "द्य", "q": "द्द",
    # ह's half-form has its own glyph; "c" is only the full letter. Seen in
    # "ÿªÉÚàÉxÉ" -> ह्यूमन and "ºÉÖ¥ÉÿàÉhªÉàÉ" -> सुब्रह्मण्यम.
    "ÿ": "ह्",
    "vÉ": "ध", "v": "ध्",
    "xÉ": "न", "x": "न्",
    "{É": "प", "{": "प्",
    "{ÉE": "फ", "{ÉD": "फ्",
    "¤É": "ब", "¤": "ब्",
    # ब्र/भ्र/स्र are each a single glyph, not two letters: "¥ÉÉÆb" -> ब्रांड,
    # "ÉÊn¶ÉÉ§ÉÉÊàÉiÉ" -> दिशाभ्रमित, "»ÉÉäiÉ" -> स्रोत. Each needs its bare half-form
    # too -- exactly as "¤É" (ब) needs "¤" (ब्) -- because a following "ÉÉä" (ो)
    # is a longer key and consumes the "É" first, leaving the half-form alone;
    # the halant-merge below then rejoins them ("स्र्" + "ो" -> "स्रो").
    "¥É": "ब्र", "¥": "ब्र्",
    "§É": "भ्र", "§": "भ्र्",
    "»É": "स्र", "»": "स्र्",
    "£É": "भ", "£": "भ्",
    "àÉ": "म", "à": "म्",
    "ªÉ": "य", "ª": "य्",
    "®": "र",
    "ãÉ": "ल", "ã": "ल्",
    "´É": "व", "´": "व्",
    "¶É": "श", "¶": "श्",
    "wÉ": "ष", "w": "ष्",
    "ºÉ": "स", "º": "स्",
    "c": "ह",

    # Ligatures & independent vowels
    "FÉ": "क्ष", "F": "क्ष्",
    "jÉ": "त्र", "j": "त्र्",
    "YÉ": "ज्ञ", "Y": "ज्ञ्",
    "©É": "म्र", "OÉ": "ग्र",
    # More r-conjuncts, each a single glyph in this font. "µÉE" is already
    # implied by the "ÉÊµÉEÉÎ¶SÉªÉxÉ" -> क्रिश्चियन entry above; spelling it out
    # generalises it: "+ÉÉµÉEàÉhÉ" -> आक्रमण, "µÉEÉÆÉÊiÉ" -> क्रांति.
    "µÉE": "क्र",
    "|ÉE": "फ्र",   # "|ÉEÉÆºÉ" -> फ्रांस, "BÉEÉìxÉ|ÉEäxºÉ" -> कॉन्फ्रेंस
    # A subscript र typed after the consonant it joins: "{Éè]ÅÉäãÉ" -> पैट्रोल.
    "Å": "्र",
    "á": "्य",     # the same idea for य: "<Æ]ÅÉäbáÉÚºÉ" -> इंट्रोड्यूस
    "<Ç": "ई", "<": "इ", ">ó": "ऊ", ">": "ई", "=": "उ",
    "Aä": "ऐ", "A": "ए",
    "+ÉÉä": "ओ", "+ÉÉè": "औ", "+ÉÉ": "आ", "+É": "अ",
    # "अ" followed by the pre-base "ि" collides with "आ": both are "+É" plus a
    # glyph opening with "É". Longest-first would otherwise let "+ÉÉ" (आ) eat
    # the "É" that "ÉÊ" (ि) needs, stranding a bare "Ê" -- which is exactly how
    # "+ÉÉÊxÉãÉ" (अनिल) used to decode as "आÊनल". Spelling the pair out keeps
    # them apart; a real "आ" + "ि" carries one more "É" ("+ÉÉÉÊn" -> आदि) and
    # still takes the "+ÉÉ" branch.
    "+ÉÉÊ": "अि",
    # Same collision, same fix, for the other glyphs that open with "É":
    # "+ÉÉìxÉ®äÉÊ®ªÉàÉ" -> ऑनरेरियम, "+ÉÉÎºiÉi´É" -> अस्तित्व, "+ÉÉËcºÉÉ" -> अहिंसा.
    "+ÉÉì": "ऑ", "+ÉÉÎ": "अि", "+ÉÉË": "अिं",

    # Matras (vowel signs)
    "ÉÉä": "ो", "Éä": "ो", "ÉÉè": "ौ", "Éè": "ौ",
    "ÉÓ": "ीं", "ÉÒ": "ी", "ÉÊ": "ि", "ÉÚ": "ू", "ÉÖ": "ु",
    # pre-base short-i carrying an anusvara ("ÉËºÉc" -> "सिंह"); like "ÉÊ" it is
    # stored left of its consonant, so the shift regex below moves both along.
    "ÉË": "िं",
    # The pre-base short-i is drawn at several widths, to reach over whatever
    # follows it, and each width is its own glyph. "ÉÎ"/"ÉÏ" are the wide
    # variants of "ÉÊ"/"ÉË", used before a conjunct: "¤ÉÉÎãBÉE" -> बल्कि,
    # "ÉÊ¤ÉÉÏãbMÉ" -> बिल्डिंग. They shift exactly like the narrow ones.
    "ÉÎ": "ि", "ÉÏ": "िं",
    "Éì": "ॉ",     # "bÉì." -> डॉ., "BÉEÉìàÉxÉ´ÉèãlÉ" -> कॉमनवैल्थ
    "ä": "े", "è": "ै", "É": "ा",

    # Modifiers
    "Æ": "ं", "Ó": "ं", "&": "ः", "Þ": "ृ", "ß": "ृ",
    "Ä": "ँ",      # "cÚÄ" -> हूँ, "+ÉÉÄJÉÉå" -> आँखों
    "å": "ें", "é": "ैं", "ÉÆ": "ां", "Éå": "ों", "Éé": "ौं",
    "°ô": "रु", "°": "रू", "âó": "रु", "ç": "्", "Ì": "र्ि",

    # Reph is parked on a private-use marker so the later regex can shift it
    # left safely without colliding with a real "र्"; then it becomes "र्".
    "Ç": _REPH,
    # A matra can carry the reph in the same glyph. These decode to both at once
    # and let the same regex do the placing: "{ÉÉ]ÉÔ" -> पार्टी, "àÉÉBÉEæ]" -> मार्केट.
    # "Éæ" is to "æ" what "Éä" (ो) is to "ä" (े) -- this font builds ो as ा + े.
    "ÉÔ": _REPH + "ी",
    "Éæ": _REPH + "ो",
    "æ": _REPH + "े",
    "ÉÈ": _REPH + "ां",    # "ºÉ´ÉÉÈMÉÉÒhÉ" -> सर्वांगीण, "vÉàÉÉÈiÉ®hÉ" -> धर्मांतरण
    # Deliberately NOT mapped: "ÉÍ" ("¶ÉÉÍàÉnÉ" -> शर्मिंदा). It carries a reph
    # AND a pre-base "िं", and unlike the entries above its reph belongs to the
    # consonant that FOLLOWS it, so it is already in place and must not shift.
    # The two structural regexes below would fight over it (the reph rule drags
    # it left past the wrong letter, giving "र्शमिंदा"). Getting it right needs
    # a second, non-shifting reph marker, which is more machinery than 5 sightings
    # justify -- so it stays visible residue, which is what it is today.
    "Â": "",       # invisible filler glyph
    "*": "।",
}

_SORTED_KEYS = sorted(ISFOC_MAP, key=len, reverse=True)

# Signature of the legacy encoding. This used to be "any Latin-1 supplement
# character", on the theory that Unicode Devanagari and plain ASCII never
# contain one. That's true of genuinely-encoded input, but not of decoder
# *output*: a glyph with no ISFOC_MAP entry survives a decode untranslated and
# sits in the result as leftover Latin-1 residue (e.g. "Ê", "Ò" in the CDAC
# "EN" font). Residue alone then pinned looks_encoded True forever, so a
# second decode pass ran on already-correct text and re-triggered the
# visual-to-logical matra reordering below -- which is NOT safe to run twice
# (it can swap an already-correct "...िण" back into "...णि").
#
# So the signature now requires an actual encoded *sequence*: a literal
# ISFOC_MAP key, not just any character that happens to occur inside one. A
# lone unmapped residue glyph -- one with no ISFOC_MAP entry at all, like the
# bare "Ê"/"Ò" above -- can never equal a full key on its own, so it can't
# falsely re-arm the decoder. That holds regardless of which glyphs
# ISFOC_MAP does or doesn't cover yet.
#
# That alone isn't quite enough, though: a handful of ISFOC_MAP's own keys
# (e.g. "®" -> र, "°" -> रू, "à"/"è"/"é"/"ç" for various half-consonants) are
# ordinary Latin-1 punctuation or loanword letters that show up in genuine
# English -- a trademark mark, a degree sign, a citation -- and residue left
# behind by the *English-protection* skip below (an unmapped glyph next to an
# ASCII letter, classified as "English" and passed through untouched) can
# leave one sitting right next to real Devanagari, e.g. "n®" surviving in the
# middle of an otherwise-decoded sentence. So the signature is evaluated
# per-token using the exact same English/Hindi split decode_legacy_hindi
# uses: a token skipped there because its letters are all ASCII can never be
# touched by a second decode pass either, so it must not count as evidence
# that one is needed.
#
# The keys considered are further limited to ones containing an actual
# Latin-1 supplement character. Plenty of ISFOC_MAP keys are pure ASCII
# (e.g. "*" -> "।", used for redaction markers) and appear constantly in
# ordinary English transcript text that has nothing to do with this font;
# without this restriction, a bare "*" on its own line would arm the decoder
# for a passage that was never encoded to begin with.
_ENCODED_SIGNATURE = re.compile(
    "|".join(
        re.escape(k) for k in _SORTED_KEYS if any("¡" <= ch <= "ÿ" for ch in k)
    )
)


def _is_protected_english_token(token: str) -> bool:
    """True for a whitespace-delimited run decode_legacy_hindi leaves alone.

    Judged by LETTERS only (see decode_legacy_hindi) so English wrapped in
    non-ASCII punctuation, e.g. the ellipsis in "…(Interruptions)", still
    counts as English.
    """
    letters = [c for c in token if c.isalpha()]
    return bool(letters) and all(ord(c) < 128 for c in letters)


def looks_encoded(text: str) -> bool:
    """True if `text` still carries legacy-font glyphs (so decoding is needed).

    Checked token-by-token, skipping the same English-classified tokens
    decode_legacy_hindi itself skips -- see _ENCODED_SIGNATURE for why.
    """
    if not text:
        return False
    return any(
        not _is_protected_english_token(token) and _ENCODED_SIGNATURE.search(token)
        for token in re.split(r"(\s+)", text)
    )


def decode_legacy_hindi(text: str) -> str:
    """
    Convert one run of legacy CDAC-GIST/ISFOC "gibberish" into Unicode Hindi.

    Safe to call twice: the visual-to-logical matra reordering below is a
    one-way transform, not an involution, so re-running it on already-decoded
    text can corrupt it (e.g. a correct "...िण" reordered back into
    "...णि"). What makes repeat calls safe is looks_encoded refusing to fire
    on decoded output -- see _ENCODED_SIGNATURE -- so a second call is a
    no-op rather than a second transform. Also safe on mixed content: text
    with no legacy signature (already Unicode, or pure English) is returned
    unchanged, and Latin-letter words are preserved verbatim even inside
    otherwise-Hindi passages.
    """
    if not looks_encoded(text):
        return text

    # -- Pre-processing --------------------------------------------------
    # Kill copy-paste damage seen in some sources: "\\\n... " line-continuation
    # joins and literal "­" escapes that arrive as text rather than bytes.
    text = re.sub(r"\\+\s*\.{3,}\s*", "", text)
    text = text.replace("\\u00ad", "\xad").replace("u00ad", "")
    text = text.replace("\\\n", "").replace("\\", "").replace("\n", "")
    # The letter ष is encoded with a soft-hyphen (U+00AD) plus its connector; it
    # MUST become ष here, before any cleanup would otherwise drop the invisible
    # soft-hyphen and make ष vanish (e.g. "सुषमा" → "सुामा").
    text = (text.replace("\xadÉ", "ष").replace("­É", "ष")
                .replace("\xad", "ष").replace("­", "ष"))

    # -- Substitution, protecting Latin words ----------------------------
    out = []
    for token in re.split(r"(\s+)", text):
        if _is_protected_english_token(token):
            out.append(token.replace("*", "।"))
            continue
        for key in _SORTED_KEYS:
            token = token.replace(key, ISFOC_MAP[key])
        out.append(token)
    text = "".join(out)

    # -- Fallback single-glyph cleanups ----------------------------------
    for a, b in (("Ö", "ु"), ("Ú", "ू"), ("ाे", "ो"), ("ाै", "ौ")):
        text = text.replace(a, b)

    # -- Structural fixes (order matters) --------------------------------
    # Merge an orphaned halant sitting in front of a matra (a half-form + bar
    # that should have combined): "ज्ो" → "जो".
    text = re.sub(r"्([ािीुूेैोौंःँ])", r"\1", text)
    # Shift the short-i matra "ि" to after its consonant (visual → logical),
    # carrying an anusvara typed with it ("िंस" -> "सिं") along for the ride.
    text = re.sub(r"(ि)(ं?)([क-हड़ढ़](?:्[क-हड़ढ़])*)", r"\3\1\2", text)
    # Shift reph left onto the consonant it belongs to, then realise it as र्.
    text = re.sub(
        r"([क-हड़ढ़](?:्[क-हड़ढ़])?)([ािीुूेैोौंःँ]*)" + _REPH,
        _REPH + r"\1\2",
        text,
    )
    return text.replace(_REPH, "र्")
