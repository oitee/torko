from __future__ import annotations

from collections import defaultdict
from typing import Callable


def build_unique_index(
    name_by_pid: dict[int, str],
    folded_key: Callable[[str], str],
) -> dict[str, int]:
    """Folded name key -> person id. A key shared by two people gets no entry."""
    key2pids: dict[str, set[int]] = defaultdict(set)
    for pid, name in name_by_pid.items():
        k = folded_key(name or "")
        if k:
            key2pids[k].add(pid)
    return {k: next(iter(v)) for k, v in key2pids.items() if len(v) == 1}


def resolve_label_to_person(
    label: str | None,
    unique_person_by_key: dict[str, int],
    folded_key: Callable[[str], str],
    is_presiding: Callable[[str], bool],
    is_crowd: Callable[[str], bool],
) -> int | None:
    """The person the label names, or None if it is empty, presiding, crowd or ambiguous."""
    if not label or is_presiding(label) or is_crowd(label):
        return None
    key = folded_key(label)
    if not key:
        return None
    return unique_person_by_key.get(key)


def normalize_label(label: str | None) -> str:
    """The form that the table label_aliases stores. A lookup must use it too."""
    return " ".join((label or "").split())


def label_alias_person(
    aliases: dict[tuple[int, str], int],
    loksabha: int,
    label: str | None,
    is_presiding: Callable[[str], bool],
    is_crowd: Callable[[str], bool],
) -> int | None:
    """`aliases` maps (term, normalised label) to a person id."""
    key = normalize_label(label)
    if not key or is_presiding(key) or is_crowd(key):
        return None
    return aliases.get((loksabha, key))
