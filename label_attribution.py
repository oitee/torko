"""Attribute a turn to a person by the name in the turn's OWN label.

This is the fix for the ministerial turns (internal_docs 033): the source hands
ministers a synthetic role-slot mpCode (>= 10000) that it reuses across
different humans -- 10008 is Ravi Shankar Prasad in one turn and Anbumani
Ramadoss in another. The code therefore cannot name the speaker. But each turn's
printed *label* does ("THE MINISTER OF ... (SHRI RAVI SHANKAR PRASAD)"), so we
attribute per turn off the label, matched against the roster, and drop rather
than guess when the label is ambiguous, presiding, crowd, or nameless.

Pure -- no database, no network. Depends only on callables passed in (the real
_folded_key / is_presiding_label / is_crowd_label from debate_fetch), so the
never-guess behaviour is unit-tested offline (tests/test_minister_attribution.py).
"""
from __future__ import annotations

from collections import defaultdict
from typing import Callable


def build_unique_index(
    name_by_pid: dict[int, str],
    folded_key: Callable[[str], str],
) -> dict[str, int]:
    """Folded roster-name key -> person id, with colliding keys DROPPED.

    Two people whose names fold to the same key (the Chandra Shekhar ceiling)
    leave no entry at all -- the same never-guess drop the matcher's
    `_folded_lookup` makes, so a label matching that key resolves to nobody
    rather than to an arbitrary one of them. An empty fold key (a nameless
    label) is never indexed.
    """
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
    """The person a turn's own label names, or None when we must not guess.

    None (never guessed) when the label is empty/None, a presiding office, a
    crowd, has no usable name token (empty fold key), or folds to a key that is
    not a *unique* roster person -- i.e. absent, or dropped for collision by
    `build_unique_index`. A ministerial title collapses to its parenthesised
    name inside `folded_key` (via _normalize_name), so the office words never
    reach the match.
    """
    if not label or is_presiding(label) or is_crowd(label):
        return None
    key = folded_key(label)
    if not key:
        return None
    return unique_person_by_key.get(key)
