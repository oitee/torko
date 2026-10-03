"""
Take random debates from one year and ask Gemini Flash for the summary, the topics, and the other entities of each speech.

This is step 3 of the tag plan (README "Next steps"). The output is for a
human review. Nothing goes into the database.

Which speeches: speeches with a known member and between --min-words and
--max-words words, from --debates random debates of --year, at most
--per-debate random speeches from each debate. The same --seed gives the same
sample. The text of a speech is the member's own turns, in order. A speech
never holds another member's words (checked 2026-10-03: 0 of 198,507 turns).

The prompt is tags/extraction_v1/prompts/extract_v1.md. Each output record
names the model, the prompt file, the md5 of the prompt text, and the date.
The answer has two lists: at most 8 topics and at most 8 other entities.

Output, in tags/extraction_v1/results/:
  <year>_seed<seed>_<model>_<date>.jsonl   one record per speech, with the raw model answer
  <year>_seed<seed>_<model>_<date>.md      a review file: summary, topics, and other entities per speech

Needs GEMINI_API_KEY. Run from the repo root:

    set -a && source .env && set +a
    python3 scripts/extract_entities.py --year 2019
    python3 scripts/extract_entities.py --year 2005 --debates 20 --per-debate 2 --seed 7
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
import time
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import requests
from sqlalchemy import text

from db import get_engine
from tag_embed import api_key

FOLDER = Path(__file__).resolve().parent.parent / "tags" / "extraction_v1"
PROMPT_FILE = FOLDER / "prompts" / "extract_v1.md"
DEFAULT_MODEL = "gemini-3.8-flash"
MAX_TOPICS = 8
MAX_OTHERS = 8
OTHER_TYPES = ("law", "scheme", "institution", "place", "person", "group", "role")
LANGUAGES = ("en", "hi", "mixed")
EXCERPT_CHARS = 400


def item_schema(types: tuple[str, ...] | None) -> dict:
    props = {"name": {"type": "string"},
             "salience": {"type": "integer", "minimum": 1, "maximum": 5},
             "mention": {"type": "string"}}
    if types:
        props["type"] = {"type": "string", "enum": list(types)}
    return {"type": "object", "properties": props, "required": list(props)}


SCHEMA = {
    "type": "object",
    "properties": {
        "language": {"type": "string", "enum": list(LANGUAGES)},
        "summary": {"type": "string"},
        "topics": {"type": "array", "maxItems": MAX_TOPICS, "items": item_schema(None)},
        "other_entities": {"type": "array", "maxItems": MAX_OTHERS, "items": item_schema(OTHER_TYPES)},
    },
    "required": ["language", "summary", "topics", "other_entities"],
}


def pick(items: list, n: int, rng: random.Random) -> list:
    if len(items) <= n:
        return list(items)
    chosen = set(rng.sample(range(len(items)), n))
    return [x for i, x in enumerate(items) if i in chosen]


def user_text(s: dict) -> str:
    return (f"Member: {s['member']}\nDebate: {s['title'] or '(no title)'}\nDate: {s['debate_date']}\n\n"
            f"Speech:\n{s['text']}")


def check_list(items: list, limit: int, types: tuple[str, ...] | None, seen: set[str],
               label: str, warnings: list[str]) -> list[dict]:
    out = []
    for e in items:
        name = (e.get("name") or "").strip()
        key = name.casefold()
        if not key:
            warnings.append(f"{label}: item with no name dropped")
            continue
        if key in seen:
            warnings.append(f"{label}: double item dropped: {name!r}")
            continue
        type_ = "topic" if types is None else e.get("type")
        if types is not None and type_ not in types:
            warnings.append(f"{label}: unknown type {type_!r} for {name!r}")
        if not isinstance(e.get("salience"), int) or not 1 <= e["salience"] <= 5:
            warnings.append(f"{label}: salience out of range for {name!r}: {e.get('salience')!r}")
        seen.add(key)
        out.append({"name": name, "type": type_, "salience": e.get("salience"), "mention": e.get("mention", "")})
    if len(out) > limit:
        warnings.append(f"{label}: {len(out)} items, kept the first {limit}")
        out = out[:limit]
    return out


def check_answer(answer: dict) -> tuple[dict, list[str]]:
    warnings: list[str] = []
    seen: set[str] = set()
    topics = check_list(answer.get("topics", []), MAX_TOPICS, None, seen, "topics", warnings)
    others = check_list(answer.get("other_entities", []), MAX_OTHERS, OTHER_TYPES, seen, "other", warnings)
    if not topics and others:
        warnings.append("no topic, but other entities")
    fives = sum(1 for e in topics + others if e["salience"] == 5)
    if fives > 2:
        warnings.append(f"{fives} items at salience 5, the limit is 2")
    if answer.get("language") not in LANGUAGES:
        warnings.append(f"unknown language {answer.get('language')!r}")
    summary = (answer.get("summary") or "").strip()
    if not summary:
        warnings.append("empty summary")
    elif len(summary.split()) > 30:
        warnings.append(f"summary has {len(summary.split())} words, the limit is 30")
    return {"language": answer.get("language"), "summary": summary, "topics": topics, "other_entities": others}, warnings


def generate(model: str, system: str, body_text: str, key: str, retries: int = 8) -> tuple[dict, dict]:
    """Returns the parsed answer and the token counts."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    body = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": body_text}]}],
        "generationConfig": {"responseMimeType": "application/json", "responseJsonSchema": SCHEMA},
    }
    for attempt in range(retries):
        resp = requests.post(url, json=body, headers={"x-goog-api-key": key}, timeout=300)
        if resp.status_code == 429 or resp.status_code >= 500:
            wait = min(60, 5 * 2 ** attempt)
            print(f"  HTTP {resp.status_code}, wait {wait}s", flush=True)
            time.sleep(wait)
            continue
        if resp.status_code != 200:
            raise SystemExit(f"Gemini API error {resp.status_code}: {resp.text[:500]}")
        data = resp.json()
        parts = data["candidates"][0].get("content", {}).get("parts", [])
        raw = "".join(p.get("text", "") for p in parts if not p.get("thought"))
        usage = data.get("usageMetadata", {})
        tokens = {"input": usage.get("promptTokenCount"), "output": usage.get("candidatesTokenCount"),
                  "thinking": usage.get("thoughtsTokenCount")}
        return json.loads(raw), tokens
    raise SystemExit(f"Gemini API still fails after {retries} attempts")


def sample_speeches(conn, year: int, n_debates: int, per_debate: int, min_words: int, max_words: int,
                    seed: int) -> tuple[list[dict], int]:
    rng = random.Random(seed)
    rows = conn.execute(text("""
        SELECT s.id, s.debate_id FROM speeches s JOIN debates d ON d.id = s.debate_id
        WHERE s.person_id IS NOT NULL AND s.word_count BETWEEN :lo AND :hi
          AND d.debate_date >= make_date(:y, 1, 1) AND d.debate_date < make_date(:y + 1, 1, 1)
        ORDER BY s.debate_id, s.seq_start
    """), {"lo": min_words, "hi": max_words, "y": year}).all()
    by_debate: dict[int, list[int]] = {}
    for sid, did in rows:
        by_debate.setdefault(did, []).append(sid)
    debates = pick(sorted(by_debate), n_debates, rng)
    ids = [sid for did in debates for sid in pick(by_debate[did], per_debate, rng)]
    speeches = [dict(r._mapping) for r in conn.execute(text("""
        SELECT s.id AS speech_id, s.debate_id, s.word_count, p.name AS member, d.title, d.debate_type,
               d.debate_date, d.loksabha, d.session, d.source_url,
               string_agg(t.text, E'\\n\\n' ORDER BY t.seq) AS text
        FROM speeches s
        JOIN persons p ON p.id = s.person_id
        JOIN debates d ON d.id = s.debate_id
        JOIN turns t ON t.speech_id = s.id
        WHERE s.id = ANY(:ids)
        GROUP BY s.id, p.name, d.id
        ORDER BY d.debate_date, s.debate_id, s.seq_start
    """), {"ids": ids})]
    return speeches, len(by_debate)


def cell(value: str) -> str:
    return value.replace("|", "/").replace("\n", " ")


def review_markdown(records: list[dict], header: dict) -> str:
    out = [f"# Entity extraction review: {header['year']}", "",
           f"Model `{header['model']}`, prompt `{header['prompt']}` (md5 `{header['prompt_md5'][:8]}`), run on {header['run_date']}. "
           f"{len(records)} speeches from {header['debates_sampled']} random debates "
           f"(of {header['debates_in_year']} debates in {header['year']} with a speech in range), "
           f"{header['per_debate']} speeches per debate at most, {header['min_words']} to {header['max_words']} words, seed {header['seed']}.",
           "", "For each speech, write `ok`, or what is wrong, after `review:`.", ""]
    for i, r in enumerate(records, 1):
        title = " ".join((r["title"] or "(no title)").split())
        out += [f"## {i}. {r['member']}: {title}", "",
                f"{r['debate_date']}, LS{r['loksabha']} session {r['session']}, {r['word_count']} words, "
                f"language `{r['language']}`. [Source]({r['source_url']}). Speech id {r['speech_id']}.", "",
                f"> {r['excerpt']}", "", f"**Summary.** {r['summary']}", ""]
        for label, items in (("Topics", r["topics"]), ("Other entities", r["other_entities"])):
            out += [f"**{label}.**", "", "| Salience | Type | Name | Mention |", "|---|---|---|---|"]
            out += [f"| {e['salience']} | {e['type']} | {cell(e['name'])} | {cell(e['mention'])} |" for e in items]
            if not items:
                out.append("| - | - | (none) | - |")
            out.append("")
        if r["warnings"]:
            out += ["", "Warnings: " + "; ".join(r["warnings"])]
        out += ["", "review: ", ""]
    return "\n".join(out)


def free_stem(folder: Path, stem: str) -> str:
    candidate, n = stem, 1
    while any(folder.glob(f"{candidate}.*")):
        n += 1
        candidate = f"{stem}_{n}"
    return candidate


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--debates", type=int, default=10, help="random debates to take (default 10)")
    ap.add_argument("--per-debate", type=int, default=3, help="speeches per debate at most (default 3)")
    ap.add_argument("--min-words", type=int, default=100)
    ap.add_argument("--max-words", type=int, default=5000)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    args = ap.parse_args()

    key = api_key()
    system = PROMPT_FILE.read_text(encoding="utf-8")
    prompt_md5 = hashlib.md5(system.encode("utf-8")).hexdigest()
    with get_engine().connect() as conn:
        speeches, debates_in_year = sample_speeches(conn, args.year, args.debates, args.per_debate,
                                                    args.min_words, args.max_words, args.seed)
    if not speeches:
        raise SystemExit(f"no speeches in range for {args.year}")
    n_debates = len({s["debate_id"] for s in speeches})
    print(f"{len(speeches)} speeches from {n_debates} debates "
          f"({debates_in_year} debates in {args.year} have a speech in range)", flush=True)

    run_date = date.today().isoformat()
    prompt_rel = str(PROMPT_FILE.relative_to(FOLDER.parent.parent))
    records, totals = [], {"input": 0, "output": 0, "thinking": 0}
    for i, s in enumerate(speeches, 1):
        try:
            answer, tokens = generate(args.model, system, user_text(s), key)
            clean, warnings = check_answer(answer)
        except (json.JSONDecodeError, KeyError, IndexError) as exc:
            answer, tokens = None, {}
            clean, warnings = ({"language": None, "summary": "", "topics": [], "other_entities": []},
                               [f"bad answer: {exc!r}"])
        for k in totals:
            totals[k] += tokens.get(k) or 0
        records.append({**{k: s[k] for k in ("speech_id", "debate_id", "member", "title", "debate_type",
                                             "loksabha", "session", "word_count", "source_url")},
                        "debate_date": s["debate_date"].isoformat(),
                        "excerpt": " ".join(s["text"].split())[:EXCERPT_CHARS],
                        **clean, "warnings": warnings, "raw": answer, "tokens": tokens,
                        "model": args.model, "prompt": prompt_rel, "prompt_md5": prompt_md5, "run_date": run_date})
        print(f"  {i}/{len(speeches)} speech {s['speech_id']}: {len(clean['topics'])} topics, "
              f"{len(clean['other_entities'])} other"
              + (f", {len(warnings)} warnings" if warnings else ""), flush=True)

    out_dir = FOLDER / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = free_stem(out_dir, f"{args.year}_seed{args.seed}_{args.model}_{run_date}")
    with (out_dir / f"{stem}.jsonl").open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    header = {"year": args.year, "model": args.model, "prompt": prompt_rel, "prompt_md5": prompt_md5, "run_date": run_date,
              "debates_sampled": n_debates, "debates_in_year": debates_in_year, "per_debate": args.per_debate,
              "min_words": args.min_words, "max_words": args.max_words, "seed": args.seed}
    (out_dir / f"{stem}.md").write_text(review_markdown(records, header) + "\n", encoding="utf-8")
    print(f"tokens: input {totals['input']}, output {totals['output']}, thinking {totals['thinking']}")
    print(f"written: {out_dir / stem}.jsonl and .md")


if __name__ == "__main__":
    main()
