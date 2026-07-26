import re

# Private-use marker for reph (र्). It is moved before its consonant, then becomes र्.
_REPH = ""

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
    # क and फ are two halves, and a below-base matra sits between them.
    "BÉÖE": "कु", "BÉßE": "कृ", "{ÉÖE": "फु",
    "JÉ": "ख", "J": "ख्",
    "MÉ": "ग", "M": "ग्",
    "PÉ": "घ", "P": "घ्",
    "b": "ड", "½": "ड़",
    "SÉ": "च", "S": "च्",
    # "EU" is the closing half of क/फ plus छ. छ alone needs its own row.
    "EU": "छ", "U": "छ",
    "VÉ": "ज", "V": "ज्",
    "ZÉ": "झ", "Z": "झ्",
    "g½": "ढ़", "gÉ": "ढ", "g": "ढ",
    # A second ढ़ glyph.
    "fÃ": "ढ़",
    "]": "ट",
    "~": "ठ",
    "hÉ": "ण", "h": "ण्",
    "iÉ": "त", "i": "त्",
    "kÉ": "त्त",   # "MÉÖhÉ´ÉkÉÉ" -> गुणवत्ता
    "lÉ": "थ", "l": "थ्",
    "n": "द",
    # Each द-conjunct is one glyph. "u" carries its connector, but "tÉ" takes a separate "É".
    "u": "द्व", "tÉ": "द्य", "q": "द्द",
    # ह has a separate half-form glyph.
    "ÿ": "ह्",
    "vÉ": "ध", "v": "ध्",
    "xÉ": "न", "x": "न्",
    "{É": "प", "{": "प्",
    "{ÉE": "फ", "{ÉD": "फ्",
    "¤É": "ब", "¤": "ब्",
    # ब्र, भ्र and स्र are single glyphs. The bare half-form is needed because a following
    # "ÉÉä" consumes the "É" first, and the halant merge below rejoins the pieces.
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
    "µÉE": "क्र",
    "|ÉE": "फ्र",
    # Subscript र and य are typed after the consonant they join.
    "Å": "्र",
    "á": "्य",
    "<Ç": "ई", "<": "इ", ">ó": "ऊ", ">": "ई", "=": "उ",
    "Aä": "ऐ", "A": "ए",
    "+ÉÉä": "ओ", "+ÉÉè": "औ", "+ÉÉ": "आ", "+É": "अ",
    # "अ" plus a pre-base "ि" collides with "आ". Without these rows "+ÉÉ" eats the "É" that "ÉÊ" needs.
    "+ÉÉÊ": "अि",
    # Same collision for the other glyphs that open with "É".
    "+ÉÉì": "ऑ", "+ÉÉÎ": "अि", "+ÉÉË": "अिं",

    # Matras (vowel signs)
    "ÉÉä": "ो", "Éä": "ो", "ÉÉè": "ौ", "Éè": "ौ",
    "ÉÓ": "ीं", "ÉÒ": "ी", "ÉÊ": "ि", "ÉÚ": "ू", "ÉÖ": "ु",
    # Pre-base short-i with an anusvara. It shifts like "ÉÊ".
    "ÉË": "िं",
    # "ÉÎ" and "ÉÏ" are wide variants of "ÉÊ" and "ÉË", used before a conjunct.
    "ÉÎ": "ि", "ÉÏ": "िं",
    "Éì": "ॉ",
    "ä": "े", "è": "ै", "É": "ा",

    # Modifiers
    "Æ": "ं", "Ó": "ं", "&": "ः", "Þ": "ृ", "ß": "ृ",
    "Ä": "ँ",
    "å": "ें", "é": "ैं", "ÉÆ": "ां", "Éå": "ों", "Éé": "ौं",
    "°ô": "रु", "°": "रू", "âó": "रु", "ç": "्", "Ì": "र्ि",

    # Reph goes on a marker so the regex below can move it without matching a real "र्".
    "Ç": _REPH,
    # These matras carry the reph in the same glyph. The font builds ो as ा + े.
    "ÉÔ": _REPH + "ी",
    "Éæ": _REPH + "ो",
    "æ": _REPH + "े",
    "ÉÈ": _REPH + "ां",
    # "ÉÍ" is not mapped. Its reph belongs to the next consonant, and the shift regexes would misplace it.
    "Â": "",       # invisible filler glyph
    "*": "।",
}

_SORTED_KEYS = sorted(ISFOC_MAP, key=len, reverse=True)

# A glyph sequence that proves the text is still encoded. Only keys of two or more characters
# count, because single glyphs such as "½", "®", "°" and "*" occur in ordinary text.
# Decoder output must not match, so a second decode pass never runs.
_ENCODED_SIGNATURE = re.compile(
    "|".join(
        re.escape(k)
        for k in _SORTED_KEYS
        if len(k) >= 2 and any("¡" <= ch <= "ÿ" for ch in k)
    )
)


def _is_protected_english_token(token: str) -> bool:
    # Only letters count, so English inside non-ASCII punctuation is still English.
    letters = [c for c in token if c.isalpha()]
    return bool(letters) and all(ord(c) < 128 for c in letters)


def looks_encoded(text: str) -> bool:
    if not text:
        return False
    return any(
        not _is_protected_english_token(token) and _ENCODED_SIGNATURE.search(token)
        for token in re.split(r"(\s+)", text)
    )


def decode_legacy_hindi(text: str) -> str:
    """Safe to call twice. Text with no legacy signature, such as English, is returned unchanged."""
    if not looks_encoded(text):
        return text

    # Remove line-continuation joins and literal "\\u00ad" escapes that arrive as text.
    text = re.sub(r"\\+\s*\.{3,}\s*", "", text)
    text = text.replace("\\u00ad", "\xad").replace("u00ad", "")
    # Keep a bare "\n". It is a paragraph break, and removing it breaks the English-token test below.
    text = text.replace("\\\n", "").replace("\\", "")
    # ष is encoded as a soft hyphen (U+00AD). Convert it before any cleanup drops it.
    text = (text.replace("\xadÉ", "ष").replace("­É", "ष")
                .replace("\xad", "ष").replace("­", "ष"))

    out = []
    for token in re.split(r"(\s+)", text):
        if _is_protected_english_token(token):
            # An asterisk on an English token is not a danda.
            out.append(token)
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
