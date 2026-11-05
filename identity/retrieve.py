"""Choose the closed list of people for one label. No model and no database."""
from __future__ import annotations

from identity.names import seat_similarity, similarity
from identity.types import Entry, ParsedLabel

MAX_OPTIONS = 252  # The decision model takes 255 options, and three are fixed answers.
OUTSIDE_OPTIONS = 40
SEAT_FIT = 0.8


def seat_entries(parsed: ParsedLabel, seated: list[Entry]) -> list[Entry]:
    if not parsed.seat:
        return []
    return [e for e in seated if e.seat and seat_similarity(parsed.seat, e.seat) >= SEAT_FIT]


def build_options(parsed: ParsedLabel, seated: list[Entry], outside: list[Entry],
                  max_options: int = MAX_OPTIONS, outside_options: int = OUTSIDE_OPTIONS) -> list[Entry]:
    """Members of the seat first, then the closest other names. Keep the whole term when it fits."""
    by_seat = seat_entries(parsed, seated)
    chosen = {e.key: e for e in by_seat}
    near_outside = sorted(outside, key=lambda e: -similarity(parsed.name, e.name))[:outside_options]
    room = max_options - len(chosen) - len(near_outside)
    rest = [e for e in seated if e.key not in chosen]
    for entry in sorted(rest, key=lambda e: -similarity(parsed.name, e.name))[:max(room, 0)]:
        chosen[entry.key] = entry
    for entry in near_outside:
        chosen.setdefault(entry.key, entry)
    return list(chosen.values())


def rule_answer(parsed: ParsedLabel, seated: list[Entry], min_name: float = 0.8) -> Entry | None:
    """One member sits for the seat in the label, and the name fits: no model is needed."""
    if parsed.kind != "name" or not parsed.seat:
        return None
    by_seat = seat_entries(parsed, seated)
    fits = [e for e in by_seat if similarity(parsed.name, e.name) >= min_name]
    return fits[0] if len(fits) == 1 and len(by_seat) == 1 else None
