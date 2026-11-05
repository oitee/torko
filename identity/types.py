"""The records of label resolution. A person is never identified by a parsed text id in the logic."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

LabelKind = Literal["name", "office", "title_only", "not_a_name"]
SourceKind = Literal["person", "rajya_sabha", "lok_sabha"]

NONE = "NONE"
OFFICE = "OFFICE"
NOT_A_PERSON = "NOT_A_PERSON"
FIXED_ANSWERS = {
    NONE: "no option is the person who spoke under this label",
    OFFICE: "the label names an office, not one person",
    NOT_A_PERSON: "the label is a heading, a vote count, or other text, not a speaker",
}


@dataclass(frozen=True)
class ParsedLabel:
    kind: LabelKind
    name: str = ""
    seat: str = ""


@dataclass(frozen=True)
class LabelRow:
    term: int
    label: str
    words: int
    code: str = ""
    first_date: str = ""
    last_date: str = ""
    title: str = ""
    excerpt: str = ""


@dataclass(frozen=True)
class Entry:
    """One person who can be an answer: a person in Torko, or a row of a sansad.in member list."""
    source: SourceKind
    number: int
    name: str
    detail: str
    seat: str = ""

    @property
    def key(self) -> str:
        prefix = {"person": "P", "rajya_sabha": "RS", "lok_sabha": "LS"}[self.source]
        return f"{prefix}{self.number}"

    @property
    def text(self) -> str:
        return f"{self.name}. {self.detail}"


@dataclass(frozen=True)
class Answer:
    """`key` is an Entry key or a fixed answer. `probability` is None for a rule."""
    key: str
    probability: float | None
    decided_by: str
    top: tuple[tuple[str, float], ...] = ()
    tokens: int = 0
