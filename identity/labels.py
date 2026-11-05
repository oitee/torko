"""Read the name and the seat in a printed speaker label. No model and no database."""
from __future__ import annotations

import re

from debate_fetch import _name_parts, is_crowd_label, is_presiding_label
from identity.types import ParsedLabel

MINISTER_RE = re.compile(r"minister|मंत्री|मन्त्री", re.IGNORECASE)
OFFICE_RE = re.compile(r"secretary[\s-]*general|secreatry|महासचिव|महा\s*सचिव|\bpresident\b|राष्ट्रपति", re.IGNORECASE)
MAX_NAME_WORDS = 7
RANK_ONLY = re.compile(r"^(retd\.?|सेवानिवृत्त)$", re.IGNORECASE)


def _groups(text: str) -> list[tuple[int, int]]:
    """The top-level bracket groups. A group can hold another group: (MAJ. GEN. (RETD.) B.C. KHANDURI)."""
    found, depth, start = [], 0, 0
    for i, ch in enumerate(text):
        if ch == "(":
            if depth == 0:
                start = i
            depth += 1
        elif ch == ")" and depth:
            depth -= 1
            if depth == 0:
                found.append((start, i))
    return found


def read_label(label: str | None) -> ParsedLabel:
    text = " ".join((label or "").replace("*", " ").replace("[", "(").replace("]", ")").split()).strip(" :")
    if not text:
        return ParsedLabel("not_a_name")
    minister = bool(MINISTER_RE.search(text))
    if not minister and (is_presiding_label(text) or is_crowd_label(text) or OFFICE_RE.search(text)):
        return ParsedLabel("office")
    groups = _groups(text)
    if minister:
        for start, end in reversed(groups):
            inside = text[start + 1:end].strip()
            if inside and not MINISTER_RE.search(inside):
                return ParsedLabel("name", inside)
        # The name comes before the office: SHRI PRAMOD MAHAJAN (THE MINISTER OF ...).
        before = text[:groups[0][0]].strip() if groups else ""
        if before and not MINISTER_RE.search(before):
            return ParsedLabel("name", before)
        return ParsedLabel("title_only")
    outside, seat, last = [], "", 0
    for start, end in groups:
        outside.append(text[last:start])
        inside = text[start + 1:end].strip()
        if inside and not RANK_ONLY.match(inside):
            seat = inside
        last = end + 1
    outside.append(text[last:])
    name = " ".join(" ".join(outside).split()).strip(" :")
    if not _name_parts(name)[0] or len(name.split()) > MAX_NAME_WORDS:
        return ParsedLabel("not_a_name")
    return ParsedLabel("name", name, seat)
