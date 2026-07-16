import re

# CDAC-GIST/ISFOC font table. Keys are applied longest-first, so clusters win over single glyphs.
ISFOC_MAP = {
    # Whole words that the generic rules mangle
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
    # Pre-base short-i with an anusvara. It shifts like "ÉÊ".
    "ÉË": "िं",
    "ä": "े", "è": "ै", "É": "ा",

    # Modifiers
    "Æ": "ं", "Ó": "ं", "&": "ः", "Þ": "ृ", "ß": "ृ",
    "å": "ें", "é": "ैं", "ÉÆ": "ां", "Éå": "ों", "Éé": "ौं",
    "°ô": "रु", "°": "रू", "ç": "्", "Ì": "र्ि",

    # Reph goes on a marker so the regex below can move it without matching a real "र्".
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

    # Remove line-continuation joins and literal "\\u00ad" escapes that arrive as text.
    text = re.sub(r"\\+\s*\.{3,}\s*", "", text)
    text = text.replace("\\u00ad", "\xad").replace("u00ad", "")
    text = text.replace("\\\n", "").replace("\\", "").replace("\n", "")
    # ष is encoded as a soft hyphen (U+00AD). Convert it before any cleanup drops it.
    text = (text.replace("\xadÉ", "ष").replace("­É", "ष")
                .replace("\xad", "ष").replace("­", "ष"))

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

    for a, b in (("Ö", "ु"), ("Ú", "ू"), ("ाे", "ो"), ("ाै", "ौ")):
        text = text.replace(a, b)

    # The order of these three fixes matters.
    # Merge a halant that stands before a matra: "ज्ो" -> "जो".
    text = re.sub(r"्([ािीुूेैोौंःँ])", r"\1", text)
    # Move the short-i matra after its consonant, with its anusvara.
    text = re.sub(r"(ि)(ं?)([क-हड़ढ़](?:्[क-हड़ढ़])*)", r"\3\1\2", text)
    # Move reph before its consonant. The final replace makes it र्.
    text = re.sub(
        r"([क-हड़ढ़](?:्[क-हड़ढ़])?)([ािीुूेैोौंःँ]*)" + _REPH,
        _REPH + r"\1\2",
        text,
    )
    return text.replace(_REPH, "र्")
