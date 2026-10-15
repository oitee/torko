from __future__ import annotations

import csv
import json
import math
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from translit import fold

DEFAULT_CSV = Path(__file__).resolve().parent / "tags" / "entity_dictionary" / "results" / "entity_dictionary.csv"
META_NAME = "entity_dictionary_meta.json"
FALLBACK_SOURCE_SPEECHES = 50_000  # Used when the meta file is missing.
DEFAULT_K = 8
SEPARATOR = " | "
INDEX_LEN = 4  # Every mention key has 4 or more characters.
_COUNTED = re.compile(r"^(.*) \((\d+)\)$")
_IGNORED = set("​‌‍⁠﻿")


@dataclass(frozen=True)
class Entity:
    name: str
    type: str
    speeches: int
    mentions: tuple  # (mention text, uses) pairs


def _ignored(ch: str) -> bool:
    return ch.isspace() or ch in _IGNORED


def normalise(value: str) -> str:
    # Must match mention_key in scripts/extract_entities.py.
    return "".join(c.casefold() for c in value if not _ignored(c))


def normalise_with_positions(text: str) -> tuple[str, list[int]]:
    """Also return, for each normalised character, its index in `text`."""
    out, pos = [], []
    for i, ch in enumerate(text):
        if _ignored(ch):
            continue
        for c in ch.casefold():
            out.append(c)
            pos.append(i)
    return "".join(out), pos


def is_boundary(ch: str | None) -> bool:
    # A letter, digit, or combining mark is not a boundary. This matters for Devanagari vowel signs.
    if ch is None or ch.isspace():
        return True
    return unicodedata.category(ch)[0] in ("P", "S", "Z") and ch != "_"


def _edge_char(text: str, index: int, step: int) -> str | None:
    while 0 <= index < len(text):
        if text[index] not in _IGNORED:
            return text[index]
        index += step
    return None


def spelling_key(name: str) -> str:
    # Digit runs stay exact, so "Article 21" and "Article 12" never merge.
    parts, run, kind = [], "", None
    for ch in name.casefold():
        if ch.isdigit():
            k = "D"
        elif ch.isalpha() or unicodedata.category(ch)[0] == "M":
            k = "L"
        else:
            k = None
        if k is None:
            if kind == "D":  # A separator ends a digit run but not a letter run.
                parts.append((kind, run))
                run, kind = "", None
            continue
        if kind and k != kind:
            parts.append((kind, run))
            run = ""
        kind, run = k, run + ch
    if run:
        parts.append((kind, run))
    return "|".join("#" + r if k == "D" else re.sub(r"[a-z]+", lambda m: fold(m.group()), r) for k, r in parts)


def office_word_tokens(mention: str) -> list[str]:
    words, cur = [], ""
    for ch in mention:
        if is_boundary(ch):
            if cur:
                words.append(normalise(cur))
            cur = ""
        else:
            cur += ch
    if cur:
        words.append(normalise(cur))
    return words


def parse_counted(cell: str) -> list[tuple[str, int]]:
    pairs = []
    for part in cell.split(SEPARATOR):
        m = _COUNTED.match(part.strip())
        if m:
            pairs.append((m.group(1), int(m.group(2))))
    return pairs


class EntityDictionary:
    def __init__(self, entities: list[Entity], source_speeches: int = FALLBACK_SOURCE_SPEECHES):
        self.entities = entities
        self.source_speeches = source_speeches
        self.by_name = {e.name.casefold(): e for e in entities}
        self.by_spelling = {spelling_key(e.name): e for e in entities}
        self._index = {}  # first INDEX_LEN characters of a key -> list of (key, mention text, uses, entity)
        for e in entities:
            for text, uses in e.mentions:
                key = normalise(text)
                if len(key) >= INDEX_LEN:
                    self._index.setdefault(key[:INDEX_LEN], []).append((key, text, uses, e))

    @classmethod
    def from_rows(cls, rows: list[dict], source_speeches: int = FALLBACK_SOURCE_SPEECHES) -> "EntityDictionary":
        entities = []
        for r in rows:
            mentions = tuple(parse_counted(r["mentions"]))
            if mentions:
                entities.append(Entity(r["name"], r["type"], int(r["speeches"]), mentions))
        return cls(entities, source_speeches)

    @classmethod
    def load(cls, path: Path = DEFAULT_CSV) -> "EntityDictionary":
        total = FALLBACK_SOURCE_SPEECHES
        meta = Path(path).with_name(META_NAME)
        if meta.exists():
            total = json.loads(meta.read_text(encoding="utf-8"))["source_speeches"]
        with open(path, newline="", encoding="utf-8-sig") as f:
            return cls.from_rows(list(csv.DictReader(f)), total)

    def score(self, entity: Entity, occurrences: int) -> float:
        return occurrences * math.log(self.source_speeches / max(entity.speeches, 1))

    def find(self, text: str) -> dict[str, tuple[Entity, str, int]]:
        """Map the lower-case entity name to (entity, mention with most matches, total matches of all its mentions)."""
        norm, pos = normalise_with_positions(text)
        grams = {norm[i:i + INDEX_LEN] for i in range(len(norm) - INDEX_LEN + 1)}
        best: dict[str, tuple[Entity, str, int, int]] = {}  # name -> entity, mention, mention matches, total matches
        for gram in grams & self._index.keys():
            for key, mention, uses, entity in self._index[gram]:
                n = len(self._match_spans(norm, pos, text, key))
                if not n:
                    continue
                name = entity.name.casefold()
                old = best.get(name)
                total = n + (old[3] if old else 0)
                if old and (old[2], self._uses(old[0], old[1])) >= (n, uses):
                    best[name] = (old[0], old[1], old[2], total)
                else:
                    best[name] = (entity, mention, n, total)
        return {name: (e, m, total) for name, (e, m, _, total) in best.items()}

    @staticmethod
    def _uses(entity: Entity, mention: str) -> int:
        return dict(entity.mentions).get(mention, 0)

    @staticmethod
    def _match_spans(norm: str, pos: list[int], text: str, key: str) -> list[tuple[int, int]]:
        spans, start = [], norm.find(key)
        while start != -1:
            first, last = pos[start], pos[start + len(key) - 1]
            if is_boundary(_edge_char(text, first - 1, -1)) and is_boundary(_edge_char(text, last + 1, 1)):
                spans.append((first, last))
            start = norm.find(key, start + len(key))
        return spans

    def spans_of(self, text: str, mentions) -> list[tuple[int, int]]:
        norm, pos = normalise_with_positions(text)
        out = []
        for m in mentions:
            key = normalise(m)
            if key:
                out += self._match_spans(norm, pos, text, key)
        return out

    def inside_longer(self, text: str, hits: dict, longer_mentions=()) -> set[str]:
        """Names of the hits whose every match lies inside a longer match of another hit or of `longer_mentions`."""
        own = {name: self.spans_of(text, [m for m, _ in e.mentions]) for name, (e, _, _) in hits.items()}
        others = self.spans_of(text, longer_mentions)
        out = set()
        for name, spans in own.items():
            longer = others + [sp for n, s in own.items() if n != name for sp in s]
            if spans and all(any(a <= x and y <= b and b - a > y - x for a, b in longer) for x, y in spans):
                out.add(name)
        return out

    def lookup(self, text: str, already_has: set[str] | frozenset[str] = frozenset(), k: int = DEFAULT_K,
               longer_mentions=()) -> list[tuple[str, str, str]]:
        """Return at most `k` (name, type, matched mention), best score first.
        Skipping happens before the cap, so a skipped entity frees its place."""
        has = {spelling_key(n) for n in already_has}
        found = self.find(text)
        inside = self.inside_longer(text, found, longer_mentions)
        hits = [h for name, h in found.items() if spelling_key(h[0].name) not in has and name not in inside]
        hits.sort(key=lambda h: (-self.score(h[0], h[2]), h[0].name.casefold()))
        return [(e.name, e.type, mention) for e, mention, _ in hits[:k]]
