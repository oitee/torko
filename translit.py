"""
Rule-based Devanagari -> Latin transliteration, offline and dependency-free.

Used to compare an Indic speaker label with a romanised roster name. The output
is not meant to be pretty romanisation -- it feeds `fold()`, which squashes both
sides into a spelling-insensitive key so "सिंह" and "Singh" land close enough to
compare.
"""
from __future__ import annotations

import re
import unicodedata

# Consonants carry an inherent 'a' unless a virama or matra follows.
_CONSONANTS = {
    "क": "k", "ख": "kh", "ग": "g", "घ": "gh", "ङ": "ng",
    "च": "ch", "छ": "chh", "ज": "j", "झ": "jh", "ञ": "ny",
    "ट": "t", "ठ": "th", "ड": "d", "ढ": "dh", "ण": "n",
    "त": "t", "थ": "th", "द": "d", "ध": "dh", "न": "n",
    "प": "p", "फ": "ph", "ब": "b", "भ": "bh", "म": "m",
    "य": "y", "र": "r", "ल": "l", "व": "v", "ळ": "l",
    "श": "sh", "ष": "sh", "स": "s", "ह": "h",
    "क़": "q", "ख़": "kh", "ग़": "g", "ज़": "z", "ड़": "r",
    "ढ़": "rh", "फ़": "f", "य़": "y",
}

_VOWELS = {
    "अ": "a", "आ": "aa", "इ": "i", "ई": "ee", "उ": "u", "ऊ": "oo",
    "ऋ": "ri", "ए": "e", "ऐ": "ai", "ओ": "o", "औ": "au",
    "ऑ": "o", "ऍ": "e", "ऎ": "e", "ऒ": "o",
}

_MATRAS = {
    "ा": "aa", "ि": "i", "ी": "ee", "ु": "u", "ू": "oo",
    "ृ": "ri", "े": "e", "ै": "ai", "ो": "o", "ौ": "au",
    "ॉ": "o", "ॅ": "e", "ॆ": "e", "ॊ": "o",
}

_VIRAMA = "्"
_NUKTA = "़"
_SIGNS = {"ं": "n", "ँ": "n", "ः": "h", "ऽ": ""}
_DIGITS = {chr(0x0966 + i): str(i) for i in range(10)}

_DEVANAGARI_RE = re.compile(r"[ऀ-ॿ]")


def has_devanagari(text: str) -> bool:
    return bool(text) and bool(_DEVANAGARI_RE.search(text))


def to_latin(text: str) -> str:
    """Transliterate any Devanagari in `text`; other scripts pass through."""
    if not has_devanagari(text):
        return text

    text = unicodedata.normalize("NFC", text).replace(_NUKTA, "")
    out: list[str] = []
    i = 0
    while i < len(text):
        ch = text[i]
        if ch in _CONSONANTS:
            out.append(_CONSONANTS[ch])
            nxt = text[i + 1] if i + 1 < len(text) else ""
            if nxt == _VIRAMA:          # conjunct: no vowel at all
                i += 2
                continue
            if nxt in _MATRAS:          # explicit vowel replaces the inherent 'a'
                out.append(_MATRAS[nxt])
                i += 2
                continue
            out.append("a")             # inherent vowel
            i += 1
            continue
        out.append(_VOWELS.get(ch) or _SIGNS.get(ch) or _DIGITS.get(ch) or ch)
        i += 1
    return "".join(out)


# Latin consonants (no vowels, no w/z/x — fold() has already swapped w->v and
# z->j by the time these are used). _CLUSTER_A_RE finds an optional inherent "a"
# a roman spelling writes between a consonant and a consonant cluster (two
# consonants, or a consonant+h digraph).
_CONSONANTS_LATIN = "bcdfghjklmnpqrstvy"
_CLUSTER_A_RE = re.compile(
    r"(?<=[" + _CONSONANTS_LATIN + r"])a(?=(?:[bcdfgjkptv]h|[" + _CONSONANTS_LATIN + r"]{2}))"
)


def fold(token: str) -> str:
    """Squash a Latin token into a spelling-insensitive key.

    Collapses the long/short vowel pairs transliteration produces, the v/w and
    z/j swaps common in romanised Indian names, and the trailing inherent 'a'
    that English spellings drop ("yaadava" -> "yadav", "Yadav" -> "yadav").
    Collapses the anusvara-nasal "ngh" and roman "nh" spellings so "Singh" and
    "सिंह" produce the same key. Drops the optional inherent 'a' a roman
    spelling writes inside a consonant cluster ("Meenakashi" vs "मीनाक्षी").
    """
    t = re.sub(r"[^a-z]", "", token.lower())
    for a, b in (("aa", "a"), ("ee", "i"), ("ii", "i"), ("oo", "u"), ("uu", "u")):
        t = t.replace(a, b)
    t = t.replace("w", "v").replace("z", "j")
    t = t.replace("ngh", "nh")
    prev = None
    while prev != t:            # one removal can expose the next cluster
        prev = t
        t = _CLUSTER_A_RE.sub("", t)
    t = re.sub(r"(.)\1+", r"\1", t)     # doubled letters carry no signal here
    if len(t) > 2 and t.endswith("a"):
        t = t[:-1]
    return t
