"""Build the review file for the gate of the summary tags.

The file lists 30 speeches with the summary, the extracted entities, and the 20 tags nearest to the summary vector.
Run from the repo root. The summaries need vectors first:

    python3 scripts/summary_tags_review.py --print-extraction-ids
    python3 scripts/embed_summaries.py --extraction-ids <the ids>
    python3 scripts/summary_tags_review.py
"""
from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from db import get_engine
from scripts.embed_summaries import STUB_MODEL, nearest_tags

SAMPLE_MODEL = "gemini-3.5-flash-lite"
RANDOM_TERMS = (16, 17, 18)
RANDOM_COUNT = 15
SEED = 20261007
TOP_N = 20
OUT = Path(__file__).resolve().parent.parent / "tags" / "summary_tags" / "results" / "review_v1.md"

INSTRUCTIONS = """\
# Review of the summary tags (version 1)

This file has 30 speeches. Each speech has a summary and a list of 20 tags. The tags are the nearest to the summary in meaning. A computer found them.

Your task: mark each tag. Change `[ ]` to `[x]` when the tag is relevant. A tag is relevant when the member's point involves the subject of the tag. Leave `[ ]` when the tag is not relevant.

Rules from the project:
- A passing reference gives no tag. Examples: a precedent, a comparison, a courtesy, a side list.
- The member's own constituency, named only to say who speaks, gives no tag.
- Judge each tag by its name and its description.

Check the summary against the source link when you are not sure. The list is in order: rank 1 is the nearest tag. Distance 0 means the same direction. A larger distance means less similar.

After you finish, the gate measures the share of your relevant tags that are in the top N, for each N from 5 to 20. You choose N.
"""


def pick_random(candidates: list[int], exclude: set[int], count: int, seed: int) -> list[int]:
    pool = sorted(i for i in candidates if i not in exclude)
    if len(pool) < count:
        raise ValueError(f"only {len(pool)} candidates for {count} picks")
    return sorted(random.Random(seed).sample(pool, count))


def select_extraction_ids(conn) -> list[int]:
    sample = [r[0] for r in conn.execute(text(
        "SELECT e.id FROM speech_extractions e JOIN models m ON m.id = e.model_id "
        "WHERE m.name = :m ORDER BY e.id"), {"m": SAMPLE_MODEL})]
    pool = [r[0] for r in conn.execute(text("""
        SELECT e.id FROM speech_extractions e
        JOIN models m ON m.id = e.model_id
        JOIN speeches s ON s.id = e.speech_id
        JOIN debates d ON d.id = s.debate_id
        WHERE m.name <> :stub AND d.loksabha = ANY(:terms) AND length(e.summary) > 0
    """), {"stub": STUB_MODEL, "terms": list(RANDOM_TERMS)})]
    return sample + pick_random(pool, set(sample), RANDOM_COUNT, SEED)


def load_speeches(conn, extraction_ids: list[int]) -> list[dict]:
    rows = conn.execute(text("""
        SELECT e.id AS extraction_id, e.speech_id, e.summary, m.name AS model,
               p.name AS member, d.debate_date, d.title, d.source_url, d.loksabha, s.word_count
        FROM speech_extractions e
        JOIN models m ON m.id = e.model_id
        JOIN speeches s ON s.id = e.speech_id
        JOIN debates d ON d.id = s.debate_id
        LEFT JOIN persons p ON p.id = s.person_id
        WHERE e.id = ANY(:ids)
    """), {"ids": extraction_ids})
    by_id = {r.extraction_id: dict(r._mapping) for r in rows}
    out = []
    for i in extraction_ids:
        d = by_id[i]
        d["items"] = [dict(r._mapping) for r in conn.execute(text(
            "SELECT list, position, name, type FROM speech_items WHERE extraction_id = :e AND source = 'llm' ORDER BY list, position"),
            {"e": i})]
        out.append(d)
    return out


def render_speech(n: int, sp: dict, tags: list[dict]) -> str:
    topics = [i for i in sp["items"] if i["list"] == "topic"]
    others = [i for i in sp["items"] if i["list"] == "other"]
    lines = [
        f"## {n}. Speech {sp['speech_id']}: {sp['member'] or 'unattributed'}",
        "",
        f"- Date: {sp['debate_date']} (Lok Sabha {sp['loksabha']}), {sp['word_count']} words",
        f"- Debate: {' '.join((sp['title'] or '').split())}",
        f"- Source: {sp['source_url']}",
        f"- Extraction model: {sp['model']}",
        "",
        f"**Summary.** {sp['summary'].strip()}",
        "",
        "**LLM topics:** " + ("; ".join(f"{i['name']} ({i['type']})" for i in topics) or "none"),
        "",
        "**LLM other entities:** " + ("; ".join(f"{i['name']} ({i['type']})" for i in others) or "none"),
        "",
        "| Mark | Rank | Distance | Tag | Description |",
        "|---|---|---|---|---|",
    ]
    for t in tags:
        desc = (t["description"] or "").replace("|", "/").replace("\n", " ")
        lines.append(f"| [ ] | {t['rank']} | {t['distance']:.3f} | {t['tag'].replace('|', '/')} | {desc} |")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--print-extraction-ids", action="store_true", help="print the 30 extraction ids and stop")
    args = ap.parse_args()

    engine = get_engine()
    with engine.connect() as conn:
        ids = select_extraction_ids(conn)
        if args.print_extraction_ids:
            print(",".join(map(str, ids)))
            return
        speeches = load_speeches(conn, ids)
        near = nearest_tags(conn, [s["speech_id"] for s in speeches], TOP_N)
    missing = [s["speech_id"] for s in speeches if not near[s["speech_id"]]]
    if missing:
        raise SystemExit(f"no summary vector for speeches {missing}. Run scripts/embed_summaries.py first.")
    parts = [INSTRUCTIONS]
    for n, sp in enumerate(speeches, 1):
        parts.append(render_speech(n, sp, near[sp["speech_id"]]))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(parts), encoding="utf-8")
    print(f"wrote {OUT} ({len(speeches)} speeches)")


if __name__ == "__main__":
    main()
