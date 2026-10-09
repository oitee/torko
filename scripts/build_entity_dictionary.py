"""Build the entity dictionary from the stored extractions. This script calls no model and writes no database row.

Usage:
  python3 scripts/build_entity_dictionary.py [--out PATH]
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from db import get_engine
from entity_lookup import META_NAME, normalise, office_word_tokens, spelling_key
from scripts.extract_entities import mention_key

FOLDER = Path(__file__).resolve().parent.parent / "tags" / "entity_dictionary"
DEFAULT_OUT = FOLDER / "results" / "entity_dictionary.csv"
MIN_SPEECHES = 3
MIN_MENTION_USES = 2
MAX_SHORT_CHARS = 3
MIN_TOP_SHARE = 0.8
MAX_EXAMPLES = 5
SEPARATOR = " | "
EXCLUDE_FILE = FOLDER / "data" / "exclude.tsv"
# A mention of a person that contains one of these words names an office, not the person.
OFFICE_WORDS = ("प्रधानमंत्री", "पीएम", "prime minister", "pm", "मंत्री", "minister", "मुख्यमंत्री", "chief minister",
                "अध्यक्ष", "speaker", "राष्ट्रपति", "president", "सभापति", "chairman")
OFFICE_REASON = "person mention with an office word"
COLUMNS = ["name", "type", "other_types", "speeches", "avg_salience", "mentions", "n_mentions",
           "mentions_strong", "mentions_lite", "ambiguous_mentions", "name_variants", "example_ids"]

ITEMS_SQL = """
    SELECT i.speech_id, m.name AS model, i.name, i.type, i.model_salience AS salience, i.mention
    FROM speech_items i
    JOIN speech_extractions e ON e.id = i.extraction_id
    JOIN models m ON m.id = e.model_id
    WHERE i.list = 'other' AND i.mention_found
"""


def source_group(model: str) -> str | None:
    """Returns None for the rule stub model."""
    if model == "rule-stub":
        return None
    return "lite" if "lite" in model else "strong"


def most_common(counter: Counter) -> str:
    return sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]


def office_keys() -> set[str]:
    return {normalise(w) for w in OFFICE_WORDS if len(w.split()) == 1}


def office_phrases() -> set[tuple[str, ...]]:
    return {tuple(normalise(p) for p in w.split()) for w in OFFICE_WORDS if len(w.split()) > 1}


def has_office_word(mention: str) -> bool:
    words = office_word_tokens(mention)
    keys = office_keys()
    if any(w in keys for w in words):
        return True
    return any(tuple(words[i:i + len(p)]) == p for p in office_phrases() for i in range(len(words)))


def load_exclusions(path: Path = EXCLUDE_FILE) -> dict:
    out = {"name": {}, "mention": {}}
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            kind, value = r["kind"].strip(), r["value"].strip()
            if kind == "name":
                out["name"][spelling_key(value)] = r["reason"].strip()
            elif kind == "mention":
                out["mention"][mention_key(value)] = r["reason"].strip()
            else:
                raise ValueError(f"unknown kind {kind!r} in {path}")
    return out


def build(rows: list[dict], exclusions: dict | None = None) -> tuple[list[dict], dict]:
    exclusions = exclusions or {"name": {}, "mention": {}}
    summary = {"items_in": len(rows), "source_speeches": len({r["speech_id"] for r in rows}), "excluded": Counter(),
               "dropped_rule2": 0, "dropped_rule3": 0, "dropped_rule4": 0, "dropped_rule5": 0, "dropped_separator": 0}
    # Merge spelling variants. The most frequent spelling of a group is its name.
    forms = defaultdict(Counter)
    for r in rows:
        forms[spelling_key(r["name"])][" ".join(r["name"].split())] += 1
    canon = {k: most_common(c) for k, c in forms.items()}
    summary["spelling_groups_merged"] = sum(1 for c in forms.values() if len(c) > 1)
    # Exclusions.
    kept_rows = []
    for r in rows:
        gk = spelling_key(r["name"])
        mk = mention_key(r["mention"])
        reason = exclusions["name"].get(gk) or exclusions["mention"].get(mk)
        if not reason and r["type"] == "person" and has_office_word(r["mention"]):
            reason = OFFICE_REASON
        if reason:
            summary["excluded"][reason] += 1
        else:
            kept_rows.append(dict(r, group=gk))
    rows = kept_rows
    # Rule 2: names in 3 or more distinct speeches.
    speeches_of = defaultdict(set)
    for r in rows:
        speeches_of[r["group"]].add(r["speech_id"])
    kept_names = {k for k, s in speeches_of.items() if len(s) >= MIN_SPEECHES}
    items = []
    for r in rows:
        if r["group"] in kept_names and mention_key(r["mention"]):
            items.append(r)
        else:
            summary["dropped_rule2"] += 1
    # Group the uses of each mention.
    by_mention = defaultdict(list)
    for r in items:
        by_mention[mention_key(r["mention"])].append(r)
    entity_uses = defaultdict(list)  # group key -> kept uses (mention key, display, row)
    ambiguous_of = defaultdict(Counter)  # group key -> dropped ambiguous mention display -> uses
    for key, uses in by_mention.items():
        display = most_common(Counter(u["mention"].strip() for u in uses))
        if len(uses) < MIN_MENTION_USES:  # rule 3
            summary["dropped_rule3"] += len(uses)
        elif len(key) <= MAX_SHORT_CHARS:  # rule 4
            summary["dropped_rule4"] += len(uses)
        elif "|" in key:
            summary["dropped_separator"] += len(uses)
        else:
            names = Counter(u["group"] for u in uses)
            top, top_n = sorted(names.items(), key=lambda kv: (-kv[1], kv[0]))[0]
            if len(names) >= 2 and top_n / len(uses) < MIN_TOP_SHARE:  # rule 5
                summary["dropped_rule5"] += len(uses)
                for n, c in names.items():
                    ambiguous_of[n][display] += c
            else:  # rule 6: every use goes under the top name
                for u in uses:
                    entity_uses[top].append((key, display, u))
    entries = []
    mentions_kept = 0
    items_of = defaultdict(list)
    for r in items:
        items_of[r["group"]].append(r)
    for gk, uses in entity_uses.items():
        entries.append(_entry(gk, canon[gk], uses, speeches_of[gk], items_of[gk], ambiguous_of.get(gk, Counter())))
        mentions_kept += len(uses)
    entries.sort(key=lambda e: (-e["speeches"], e["name"].casefold()))
    summary.update(names_kept=len(entries), mention_uses_kept=mentions_kept, names_with_rule2=len(kept_names))
    return entries, summary


def _entry(nk: str, name: str, uses: list, speeches: set, own_items: list[dict], ambiguous: Counter) -> dict:
    types = Counter(r["type"] for r in own_items)
    top_type = most_common(types)
    salience = [r["salience"] for r in own_items if r["salience"] is not None]
    per_mention = defaultdict(lambda: {"total": 0, "strong": 0, "lite": 0, "forms": Counter()})
    for key, display, r in uses:
        m = per_mention[key]
        m["total"] += 1
        m["forms"][display] += 1
        group = source_group(r["model"])
        if group:
            m[group] += 1
    ordered = sorted(per_mention.values(), key=lambda m: (-m["total"], most_common(m["forms"])))
    variants = Counter()
    for _, _, r in uses:
        if r["group"] != nk:
            variants[" ".join(r["name"].split())] += 1
    case_variants = Counter(" ".join(r["name"].split()) for r in own_items)
    case_variants.pop(name, None)
    for form, c in case_variants.items():
        if form not in variants:
            variants[form] += c
    return {
        "name": name,
        "type": top_type,
        "other_types": [t for t, _ in sorted(types.items(), key=lambda kv: (-kv[1], kv[0])) if t != top_type],
        "speeches": len(speeches),
        "avg_salience": round(sum(salience) / len(salience), 1) if salience else "",
        "mentions": [(most_common(m["forms"]), m["total"], m["strong"], m["lite"]) for m in ordered],
        "ambiguous_mentions": [f"{d} ({c})" for d, c in sorted(ambiguous.items(), key=lambda kv: (-kv[1], kv[0]))],
        "name_variants": [f"{v} ({c})" for v, c in sorted(variants.items(), key=lambda kv: (-kv[1], kv[0]))],
        "example_ids": sorted(speeches)[:MAX_EXAMPLES],
    }


def csv_row(e: dict) -> dict:
    def join(parts):
        return SEPARATOR.join(parts)
    return {
        "name": e["name"], "type": e["type"], "other_types": join(e["other_types"]), "speeches": e["speeches"],
        "avg_salience": e["avg_salience"],
        "mentions": join(f"{m} ({t})" for m, t, s, l in e["mentions"]),
        "n_mentions": len(e["mentions"]),
        "mentions_strong": join(f"{m} ({s})" for m, t, s, l in e["mentions"] if s),
        "mentions_lite": join(f"{m} ({l})" for m, t, s, l in e["mentions"] if l),
        "ambiguous_mentions": join(e["ambiguous_mentions"]),
        "name_variants": join(e["name_variants"]),
        "example_ids": " ".join(str(i) for i in e["example_ids"]),
    }


def write_csv(entries: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        for e in entries:
            w.writerow(csv_row(e))


def read_items() -> list[dict]:
    with get_engine().connect() as conn:
        return [dict(r._mapping) for r in conn.execute(text(ITEMS_SQL))]


def print_summary(summary: dict) -> None:
    n = summary["items_in"]
    print(f"items read (list other, mention found): {n}")
    print(f"distinct speeches in the source: {summary['source_speeches']}")
    print(f"spelling groups with more than one spelling (merged): {summary['spelling_groups_merged']}")
    for reason, count in sorted(summary["excluded"].items()):
        print(f"mention uses dropped by exclusion, {reason}: {count}")
    print(f"names with 3 or more speeches (rule 2): {summary['names_with_rule2']}")
    for label, key in (("rule 2, name in fewer than 3 speeches", "dropped_rule2"),
                       ("rule 3, mention used fewer than 2 times", "dropped_rule3"),
                       ("rule 4, mention of 3 characters or fewer", "dropped_rule4"),
                       ("rule 5, ambiguous mention", "dropped_rule5"),
                       ("mention with the separator character", "dropped_separator")):
        print(f"mention uses dropped by {label}: {summary[key]}")
    print(f"mention uses kept: {summary['mention_uses_kept']} of {n} items read")
    print(f"names kept in the dictionary: {summary['names_kept']}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()
    entries, summary = build(read_items(), load_exclusions())
    write_csv(entries, args.out)
    args.out.with_name(META_NAME).write_text(json.dumps({"source_speeches": summary["source_speeches"]}) + "\n", encoding="utf-8")
    print_summary(summary)
    print(f"written: {args.out}")


if __name__ == "__main__":
    main()
