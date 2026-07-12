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
    and must be shifted to its logical position after it;
  * "reph" (र्) is typed after its consonant and must be moved before it;
  * Latin words are left untouched so interleaved English survives verbatim.
"""
import re

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
    "JÉ": "ख", "J": "ख्",
    "MÉ": "ग", "M": "ग्",
    "PÉ": "घ", "P": "घ्",
    "b": "ड", "½": "ड़",
    "SÉ": "च", "S": "च्",
    "EU": "छ",
    "VÉ": "ज", "V": "ज्",
    "ZÉ": "झ", "Z": "झ्",
    "g½": "ढ़", "gÉ": "ढ", "g": "ढ",
    "]": "ट",
    "~": "ठ",
    "hÉ": "ण", "h": "ण्",
    "iÉ": "त", "i": "त्",
    "lÉ": "थ", "l": "थ्",
    "n": "द",
    "vÉ": "ध", "v": "ध्",
    "xÉ": "न", "x": "न्",
    "{É": "प", "{": "प्",
    "{ÉE": "फ", "{ÉD": "फ्",
    "¤É": "ब", "¤": "ब्",
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
    "<Ç": "ई", "<": "इ", ">": "ई", "=": "उ",
    "Aä": "ऐ", "A": "ए",
    "+ÉÉä": "ओ", "+ÉÉè": "औ", "+ÉÉ": "आ", "+É": "अ",

    # Matras (vowel signs)
    "ÉÉä": "ो", "Éä": "ो", "ÉÉè": "ौ", "Éè": "ौ",
    "ÉÓ": "ीं", "ÉÒ": "ी", "ÉÊ": "ि", "ÉÚ": "ू", "ÉÖ": "ु",
    "ä": "े", "è": "ै", "É": "ा",

    # Modifiers
    "Æ": "ं", "Ó": "ं", "&": "ः", "Þ": "ृ", "ß": "ृ",
    "å": "ें", "é": "ैं", "ÉÆ": "ां", "Éå": "ों", "Éé": "ौं",
    "°ô": "रु", "°": "रू", "ç": "्", "Ì": "र्ि",

    # Reph is parked on a private-use marker so the later regex can shift it
    # left safely without colliding with a real "र्"; then it becomes "र्".
    "Ç": "",
    "Â": "",       # invisible filler glyph
    "*": "।",
}

_SORTED_KEYS = sorted(ISFOC_MAP, key=len, reverse=True)
_REPH = ""

# Signature of the legacy encoding: Latin-1 supplement letters/symbols the font
# uses as glyph indices. Real Unicode Devanagari (U+0900+) and plain ASCII
# English never contain these, so this cheaply tells encoded text apart from
# text that is already clean.
_ENCODED_SIGNATURE = re.compile(r"[¡-ÿ]")


def looks_encoded(text: str) -> bool:
    """True if `text` still carries legacy-font glyphs (so decoding is needed)."""
    return bool(text) and bool(_ENCODED_SIGNATURE.search(text))


def decode_legacy_hindi(text: str) -> str:
    """
    Convert one run of legacy CDAC-GIST/ISFOC "gibberish" into Unicode Hindi.

    Idempotent and safe on mixed content: text with no legacy signature (already
    Unicode, or pure English) is returned unchanged, and Latin-letter words are
    preserved verbatim even inside otherwise-Hindi passages.
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
        letters = [c for c in token if c.isalpha()]
        # An English word may be wrapped in non-ASCII punctuation (e.g. the
        # ellipsis in "…(Interruptions)"); judge by its LETTERS only so the
        # word is left intact rather than decoded into "…(Iदterruptत्oदs)".
        if letters and all(ord(c) < 128 for c in letters):
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
    # Shift the short-i matra "ि" to after its consonant (visual → logical).
    text = re.sub(r"(ि)([क-हड़ढ़](?:्[क-हड़ढ़])*)", r"\2\1", text)
    # Shift reph left onto the consonant it belongs to, then realise it as र्.
    text = re.sub(
        r"([क-हड़ढ़](?:्[क-हड़ढ़])?)([ािीुूेैोौंःँ]*)" + _REPH,
        _REPH + r"\1\2",
        text,
    )
    return text.replace(_REPH, "र्")
