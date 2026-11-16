"""The plain form of a text, so that a quote or a name can be found in a longer text with an `in` test."""
import re
import unicodedata

_INVISIBLE = re.compile(r"[​‌‍⁠﻿]")
_FOLD = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"',
                       "–": "-", "—": "-", "‑": "-", " ": " "})


def norm(value: str | None) -> str:
    """Lower case, one space for each run of white space, typographic quotes and dashes made plain."""
    value = unicodedata.normalize("NFC", value or "")
    value = _INVISIBLE.sub("", value).translate(_FOLD)
    return " ".join(value.split()).casefold()
