"""The gate of the entity lookup. This script reads the database and calls no model.

Part (a): precision and recall proxies against the entities that the strong model extracted.
Part (b): the number of added entities per speech on a random sample of speeches of the lite models.

Usage:
  python3 scripts/entity_lookup_gate.py [--sample 2000] [--seed 1]
Output: tags/entity_dictionary/results/gate_report.md
"""
from __future__ import annotations

import argparse
import random
import statistics
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from db import get_engine
from entity_lookup import DEFAULT_K, EntityDictionary, spelling_key
from scripts.extract_entities import fetch_speeches

REPORT = Path(__file__).resolve().parent.parent / "tags" / "entity_dictionary" / "results" / "gate_report.md"
STRONG_MODEL = "gemini-3.8-flash"
UNCAPPED = 10_000
CHUNK = 400


def speech_names(conn, model_filter: str) -> dict[int, dict]:
    rows = conn.execute(text(f"""
        SELECT i.speech_id, i.list, i.name, i.mention_found
        FROM speech_items i
        JOIN speech_extractions e ON e.id = i.extraction_id
        JOIN models m ON m.id = e.model_id
        WHERE {model_filter}
    """))
    out = defaultdict(lambda: {"other_found": set(), "all": set()})
    for speech_id, lst, name, found in rows:
        out[speech_id]["all"].add(name)
        if lst == "other" and found:
            out[speech_id]["other_found"].add(spelling_key(name))
    return out


def speech_ids_of(conn, model_filter: str) -> list[int]:
    return [r[0] for r in conn.execute(text(f"""
        SELECT e.speech_id FROM speech_extractions e JOIN models m ON m.id = e.model_id WHERE {model_filter}
        ORDER BY e.speech_id"""))]


def texts_of(conn, ids: list[int]):
    for i in range(0, len(ids), CHUNK):
        for s in fetch_speeches(conn, ids[i:i + CHUNK]):
            yield s["speech_id"], s["text"]


def proxies(dictionary: EntityDictionary, conn, ids, names, k) -> dict:
    looked = hit = own_in_dict = own_found = 0
    speeches_with_own = 0
    for speech_id, body in texts_of(conn, ids):
        own = names[speech_id]["other_found"]
        got = {spelling_key(n) for n, _, _ in dictionary.lookup(body, frozenset(), k)}
        looked += len(got)
        hit += len(got & own)
        in_dict = {n for n in own if n in dictionary.by_spelling}
        own_in_dict += len(in_dict)
        own_found += len(got & in_dict)
        speeches_with_own += bool(in_dict)
    return {"k": k, "looked": looked, "hit": hit, "own_in_dict": own_in_dict, "own_found": own_found,
            "speeches_with_own": speeches_with_own}


def distribution(dictionary: EntityDictionary, conn, ids, names, k) -> list[int]:
    return [len(dictionary.lookup(body, frozenset(names[sid]["all"]), k)) for sid, body in texts_of(conn, ids)]


def pct(a: int, b: int) -> str:
    return f"{100 * a / b:.1f}%" if b else "n/a"


def describe(counts: list[int], k: int) -> list[str]:
    n = len(counts)
    s = sorted(counts)
    q = lambda p: s[min(n - 1, int(p * n))]
    return [f"| mean | {statistics.mean(counts):.2f} |", f"| median | {statistics.median(counts)} |",
            f"| 90th percentile | {q(0.9)} |", f"| 99th percentile | {q(0.99)} |", f"| maximum | {s[-1]} |",
            f"| speeches with 0 added | {sum(c == 0 for c in counts)} ({pct(sum(c == 0 for c in counts), n)}) |",
            ] + ([f"| speeches at the cap of {k} | {sum(c >= k for c in counts)} ({pct(sum(c >= k for c in counts), n)}) |"] if k < UNCAPPED else [])


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--sample", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=1)
    args = ap.parse_args()
    dictionary = EntityDictionary.load()
    lines = ["# Entity lookup gate report", "",
             f"The dictionary has {len(dictionary.entities)} entities. K is the cap of added entities per speech.", ""]
    with get_engine().connect() as conn:
        flt = f"m.name = '{STRONG_MODEL}'"
        ids = speech_ids_of(conn, flt)
        names = speech_names(conn, flt)
        lines += [f"## (a) Precision and recall proxies on {len(ids)} speeches that '{STRONG_MODEL}' extracted", "",
                  "The lookup ran with an empty \"already has\" set. The dictionary was built from the same speeches, so the proxies are optimistic.", "",
                  "| K | names looked up | of them also extracted by the model (precision proxy) | model names in the dictionary | of them found (recall proxy) | speeches with such a name |",
                  "|---|---|---|---|---|---|"]
        for k in (DEFAULT_K, UNCAPPED):
            p = proxies(dictionary, conn, ids, names, k)
            label = str(k) if k != UNCAPPED else "no cap"
            lines.append(f"| {label} | {p['looked']} | {p['hit']} ({pct(p['hit'], p['looked'])} of {p['looked']}) | {p['own_in_dict']} | "
                         f"{p['own_found']} ({pct(p['own_found'], p['own_in_dict'])} of {p['own_in_dict']}) | {p['speeches_with_own']} of {len(ids)} |")
        lite = "m.name LIKE '%flash-lite%'"
        lite_ids = speech_ids_of(conn, lite)
        sample = sorted(random.Random(args.seed).sample(lite_ids, min(args.sample, len(lite_ids))))
        lite_names = speech_names(conn, lite)
        lines += ["", f"## (b) Added entities per speech, {len(sample)} random speeches of {len(lite_ids)} that lite models extracted (seed {args.seed})", "",
                  "The \"already has\" set is every item name (topics and other entities) of the speech."]
        for k in (DEFAULT_K, UNCAPPED):
            counts = distribution(dictionary, conn, sample, lite_names, k)
            lines += ["", f"K = {k if k != UNCAPPED else 'no cap'}. Denominator: {len(counts)} speeches.", "", "| statistic | value |", "|---|---|"] + describe(counts, k)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
