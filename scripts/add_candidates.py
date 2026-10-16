"""Add stage 4 candidates to speech_items: dictionary entities and summary tags.

Sources:
  dictionary   Entity names from the dictionary that the speech text contains, at most --k for each speech.
  summary_tag  The --n tags nearest to the summary vector of the speech.

A speech that has rows of a source gets no new rows of it. --force deletes the rows and adds them again.

Usage (from the repo root):
    python3 scripts/add_candidates.py --speech-ids 260741,340402 --dry-run
    python3 scripts/add_candidates.py --term 18
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from db import get_engine
from entity_lookup import DEFAULT_K, EntityDictionary
from scripts.embed_summaries import nearest_tags
from scripts.extract_entities import fetch_speeches, scope_filter

DEFAULT_N = 12
GENERAL_TAGS_FILE = Path(__file__).resolve().parent.parent / "tags" / "summary_tags" / "data" / "general_tags.tsv"
SOURCES = ("dictionary", "summary_tag")
STUB_MODEL = "rule-stub"


def next_position(items: list[dict], list_name: str) -> int:
    return max((i["position"] for i in items if i["list"] == list_name), default=0) + 1


# A topic or group mention is often a phrase about a subject, not a name, so it never hides a dictionary match.
LONGER_NAME_TYPES_EXCLUDED = ("topic", "group")


def named_mentions(items: list[dict]) -> list[str]:
    return [i["mention"] for i in items
            if i["type"] not in LONGER_NAME_TYPES_EXCLUDED and i.get("mention_found") and i.get("mention")]


def dictionary_rows(items: list[dict], speech_text: str, dictionary: EntityDictionary, k: int) -> list[dict]:
    start = next_position(items, "other")
    found = dictionary.find(speech_text)
    out = []
    added = dictionary.lookup(speech_text, {i["name"] for i in items}, k, named_mentions(items))
    for rank, (name, type_, mention) in enumerate(added, 1):
        matches = found[name.casefold()][2]
        out.append({"list": "other", "position": start + rank - 1, "name": name, "type": type_,
                    "mention": mention, "mention_found": True, "tag_id": None,
                    "evidence": {"matches": matches, "rank": rank}})
    return out


def load_general_tags(path: Path = GENERAL_TAGS_FILE) -> frozenset[str]:
    with path.open(encoding="utf-8") as f:
        return frozenset(r["tag"].strip() for r in csv.DictReader(f, delimiter="\t") if r["tag"].strip())


def without_general(near: list[dict], general: frozenset[str], n: int) -> list[dict]:
    return [t for t in near if t["tag"] not in general][:n]


def summary_tag_rows(items: list[dict], near: list[dict]) -> list[dict]:
    start = next_position(items, "topic")
    return [{"list": "topic", "position": start + n, "name": t["tag"], "type": t["type"], "mention": "",
             "mention_found": False, "tag_id": t["tag_id"],
             "evidence": {"distance": round(float(t["distance"]), 4), "rank": t["rank"]}}
            for n, t in enumerate(near)]


def select_speeches(conn, where: str | None, params: dict) -> dict[int, int]:
    """Maps each speech id to its extraction id."""
    scope = f"AND {where}" if where else ""
    rows = conn.execute(text(f"""
        SELECT x.speech_id, x.id FROM speech_extractions x
        JOIN models m ON m.id = x.model_id
        JOIN speeches s ON s.id = x.speech_id JOIN debates d ON d.id = s.debate_id
        WHERE m.name <> :stub {scope}
        ORDER BY d.debate_date, x.speech_id
    """), {"stub": STUB_MODEL, **params}).all()
    return dict(rows)


def items_by_speech(conn, speech_ids: list[int]) -> dict[int, list[dict]]:
    out: dict[int, list[dict]] = {i: [] for i in speech_ids}
    for r in conn.execute(text("""
        SELECT speech_id, source, list, position, name, type, mention, mention_found
        FROM speech_items WHERE speech_id = ANY(:ids)
    """), {"ids": speech_ids}):
        out[r.speech_id].append(dict(r._mapping))
    return out


def insert(conn, speech_id: int, extraction_id: int, source: str, rows: list[dict]) -> None:
    for r in rows:
        conn.execute(text("""
            INSERT INTO speech_items (extraction_id, speech_id, list, position, name, type, mention, mention_found,
                                      source, tag_id, evidence)
            VALUES (:x, :s, :list, :position, :name, :type, :mention, :mention_found, :source, :tag_id,
                    CAST(:evidence AS jsonb))
        """), {**r, "x": extraction_id, "s": speech_id, "source": source,
               "evidence": json.dumps(r["evidence"], ensure_ascii=False)})


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    scope = ap.add_mutually_exclusive_group(required=True)
    scope.add_argument("--year", type=int)
    scope.add_argument("--term", type=int, help="Lok Sabha term, for example 18")
    scope.add_argument("--speech-ids", help="comma-separated speech ids")
    ap.add_argument("--sources", default=",".join(SOURCES), help=f"comma-separated, from {SOURCES}")
    ap.add_argument("--k", type=int, default=DEFAULT_K, help="the most dictionary entities added per speech")
    ap.add_argument("--n", type=int, default=DEFAULT_N, help="the number of summary tags per speech")
    ap.add_argument("--force", action="store_true", help="delete and add again the rows of the selected sources")
    ap.add_argument("--dry-run", action="store_true", help="count, write nothing")
    args = ap.parse_args()

    sources = [s for s in args.sources.split(",") if s]
    if not set(sources) <= set(SOURCES):
        raise SystemExit(f"unknown source in {sources}")
    if args.speech_ids:
        where, params = "s.id = ANY(:ids)", {"ids": [int(x) for x in args.speech_ids.split(",")]}
    else:
        where, params = scope_filter(args.year, args.term)

    engine = get_engine()
    dictionary = EntityDictionary.load() if "dictionary" in sources else None
    general = load_general_tags()
    with engine.connect() as conn:
        known = {r[0] for r in conn.execute(text("SELECT tag FROM tags WHERE tag = ANY(:t)"), {"t": list(general)})}
    if general - known:
        raise SystemExit(f"general tags not in the tag list: {sorted(general - known)}")
    with engine.connect() as conn:
        extraction_of = select_speeches(conn, where, params)
    ids = list(extraction_of)
    print(f"{len(ids)} speeches with an extraction that is not a stub. Sources: {', '.join(sources)}.", flush=True)

    added = {s: 0 for s in sources}
    skipped = {s: 0 for s in sources}
    no_vector = 0
    for start in range(0, len(ids), 200):
        batch = ids[start:start + 200]
        with engine.begin() as conn:
            if args.force and not args.dry_run:
                conn.execute(text("DELETE FROM speech_items WHERE speech_id = ANY(:ids) AND source = ANY(:src)"),
                             {"ids": batch, "src": sources})
            items = items_by_speech(conn, batch)
            texts = {s["speech_id"]: s["text"] for s in fetch_speeches(conn, batch)} if dictionary else {}
            near = {}
            if "summary_tag" in sources:
                found = nearest_tags(conn, batch, args.n + len(general))
                near = {sid: without_general(tags, general, args.n) for sid, tags in found.items()}
            for sid in batch:
                mine = items[sid]
                llm = [i for i in mine if i["source"] == "llm"]
                has = {i["source"] for i in mine}
                for source in sources:
                    if source in has and not args.force:
                        skipped[source] += 1
                        continue
                    if source == "dictionary":
                        rows = dictionary_rows(llm, texts.get(sid) or "", dictionary, args.k)
                    else:
                        if not near.get(sid):
                            no_vector += 1
                        rows = summary_tag_rows(llm, near.get(sid, []))
                    added[source] += len(rows)
                    if not args.dry_run:
                        insert(conn, sid, extraction_of[sid], source, rows)
        print(f"  {min(start + 200, len(ids))}/{len(ids)} speeches", flush=True)
    verb = "would add" if args.dry_run else "added"
    for s in sources:
        print(f"{s}: {verb} {added[s]} rows. Speeches skipped because they have rows of this source: {skipped[s]}.")
    if "summary_tag" in sources:
        print(f"speeches without a summary vector: {no_vector}")


if __name__ == "__main__":
    main()
