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
    text = text.replace("\\\n", "").replace("\\", "").replace("\n", "")
    # ष is encoded as a soft hyphen (U+00AD). Convert it before any cleanup drops it.
    text = (text.replace("\xadÉ", "ष").replace("­É", "ष")
                .replace("\xad", "ष").replace("­", "ष"))

    out = []
    for token in re.split(r"(\s+)", text):
        if _is_protected_english_token(token):
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
