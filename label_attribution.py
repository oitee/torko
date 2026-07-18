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
