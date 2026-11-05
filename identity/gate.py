"""Decide if an answer may name a person. The gate never changes an answer."""
from __future__ import annotations

from typing import Literal

from identity.names import similarity
from identity.types import FIXED_ANSWERS, Answer, ParsedLabel

DEFAULT_LIMIT = 0.8
Status = Literal["accepted", "no_person", "review"]


def judge(answer: Answer, parsed: ParsedLabel, chosen_name: str, limit: float = DEFAULT_LIMIT,
          min_name: float = 0.45) -> Status:
    if answer.key in FIXED_ANSWERS:
        return "no_person" if answer.probability is None or answer.probability >= limit else "review"
    if answer.probability is not None and answer.probability < limit:
        return "review"
    if parsed.kind == "name" and similarity(parsed.name, chosen_name) < min_name:
        return "review"
    return "accepted"
