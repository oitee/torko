"""One comparison of two person names, for each use in label resolution."""
from __future__ import annotations

from difflib import SequenceMatcher
from functools import lru_cache

from debate_fetch import _name_parts as _parser_name_parts

WORD_FIT = 0.84
COMMON_WORDS = {"sinh", "singh", "kumar", "prasad", "devi", "lal", "ram", "yadav", "rao", "patel", "reddy"}


@lru_cache(maxsize=None)
def _name_parts(name: str) -> tuple[list[str], set[str]]:
    return _parser_name_parts(name)


def _ratio(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def _side(words: list[str], other_words: list[str], other_initials: set[str]) -> float:
    """The weighted share of `words` that the other name explains. A common word counts for less."""
    total = got = 0.0
    for word in words:
        weight = 0.25 if word in COMMON_WORDS else 1.0
        total += weight
        best = max((_ratio(word, o) for o in other_words), default=0.0)
        if best >= WORD_FIT:
            got += weight * best
        elif word[0] in other_initials:
            got += weight * 0.5
    return got / total if total else 0.0


def similarity(a: str, b: str) -> float:
    """How close two names are, from 0 to 1. The score only orders options. It decides nothing."""
    a_full, a_init = _name_parts(a or "")
    b_full, b_init = _name_parts(b or "")
    if not a_full or not b_full:
        return 0.0
    # Spaces move between spellings: Thambidurai is Thambi Durai.
    joined = max(_ratio("".join(sorted(a_full)), "".join(sorted(b_full))), _ratio("".join(a_full), "".join(b_full)))
    word_score = (_side(a_full, b_full, b_init) + _side(b_full, a_full, a_init)) / 2
    return max(word_score, joined)


def seat_similarity(a: str, b: str) -> float:
    a_full, _ = _name_parts(a or "")
    b_full, _ = _name_parts(b or "")
    if not a_full or not b_full:
        return 0.0
    return _ratio("".join(a_full), "".join(b_full))
