"""Stage 3 of the tag pipeline: ask an LLM for the summary, the topics, and the other entities of each speech.
The script stores the answers in the tables speech_extractions and speech_items.

Scope: --year or --term. Sample mode (default) takes --debates random debates and at most --per-debate speeches
from each, and writes a review file. --all takes every speech of the scope.
A speech that has an extraction is skipped. --redo-stale extracts again the speeches that an older prompt
version made. --force extracts every selected speech again.
The prompts are in tags/extraction_v1/prompts/. --prompt v<N> picks a version. The default is the highest.

It needs GEMINI_API_KEY. Run from the repo root:

    set -a && source .env && set +a
    python3 scripts/extract_entities.py --year 2019
    python3 scripts/extract_entities.py --term 18 --all --dry-run
    python3 scripts/extract_entities.py --term 18 --all --workers 8
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import requests
from sqlalchemy import text

from db import get_engine
from tag_embed import api_key

FOLDER = Path(__file__).resolve().parent.parent / "tags" / "extraction_v1"
PROMPTS = FOLDER / "prompts"
DEFAULT_MODEL = "gemini-3.5-flash-lite"
MAX_TOPICS = 8
MAX_OTHERS = 8
OTHER_TYPES = ("law", "scheme", "institution", "place", "person", "group", "role")
LANGUAGES = ("en", "hi", "mixed")
EXCERPT_CHARS = 400
MAX_MENTION_WORDS = 8


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


def prompt_versions(folder: Path) -> dict[str, Path]:
    found = {}
    for path in folder.glob("extract_v*.md"):
        m = re.fullmatch(r"extract_(v\d+)\.md", path.name)
        if m:
            found[m.group(1)] = path
    return dict(sorted(found.items(), key=lambda kv: int(kv[0][1:])))


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


def mention_key(value: str) -> str:
    return re.sub(r"[\s​‌‍⁠﻿]+", "", value).casefold()


def mention_found(mention: str, speech_text: str) -> bool:
    key = mention_key(mention)
    return bool(key) and key in mention_key(speech_text)


def add_mention_checks(clean: dict, speech_text: str, warnings: list[str]) -> None:
    for e in clean["topics"] + clean["other_entities"]:
        e["mention_found"] = mention_found(e["mention"], speech_text)
        if len(e["mention"].split()) > MAX_MENTION_WORDS:
            warnings.append(f"mention of {e['name']!r} has {len(e['mention'].split())} words, the limit is {MAX_MENTION_WORDS}")


class ApiError(Exception):
    pass


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
            raise ApiError(f"HTTP {resp.status_code}: {resp.text[:300]}")
        data = resp.json()
        parts = data["candidates"][0].get("content", {}).get("parts", [])
        raw = "".join(p.get("text", "") for p in parts if not p.get("thought"))
        usage = data.get("usageMetadata", {})
        tokens = {"input": usage.get("promptTokenCount"), "output": usage.get("candidatesTokenCount"),
                  "thinking": usage.get("thoughtsTokenCount")}
        return json.loads(raw), tokens
    raise ApiError(f"still rate-limited after {retries} attempts")


def scope_filter(year: int | None, term: int | None) -> tuple[str, dict]:
    if term is not None:
        return "d.loksabha = :term", {"term": term}
    return "d.debate_date >= make_date(:y, 1, 1) AND d.debate_date < make_date(:y + 1, 1, 1)", {"y": year}


def select_speech_ids(conn, where: str, params: dict, args) -> tuple[list[int], int]:
    rows = conn.execute(text(f"""
        SELECT s.id, s.debate_id FROM speeches s JOIN debates d ON d.id = s.debate_id
        WHERE s.person_id IS NOT NULL AND s.word_count BETWEEN :lo AND :hi AND {where}
        ORDER BY d.debate_date, s.debate_id, s.seq_start
    """), {"lo": args.min_words, "hi": args.max_words, **params}).all()
    by_debate: dict[int, list[int]] = {}
    for sid, did in rows:
        by_debate.setdefault(did, []).append(sid)
    if args.all:
        return [sid for sid, _ in rows], len(by_debate)
    rng = random.Random(args.seed)
    debates = pick(sorted(by_debate), args.debates, rng)
    return [sid for did in debates for sid in pick(by_debate[did], args.per_debate, rng)], len(by_debate)


def fetch_speeches(conn, ids: list[int]) -> list[dict]:
    return [dict(r._mapping) for r in conn.execute(text("""
        SELECT s.id AS speech_id, s.debate_id, s.word_count, p.name AS member, d.title, d.debate_type,
               d.debate_date, d.loksabha, d.session, d.source_url,
               string_agg(t.text, E'\n\n' ORDER BY t.seq) AS text
        FROM speeches s
        JOIN persons p ON p.id = s.person_id
        JOIN debates d ON d.id = s.debate_id
        JOIN turns t ON t.speech_id = s.id
        WHERE s.id = ANY(:ids)
        GROUP BY s.id, p.name, d.id
        ORDER BY d.debate_date, s.debate_id, s.seq_start
    """), {"ids": ids})]


def plan(ids: list[int], existing: dict[int, str], version: str, redo_stale: bool,
         force: bool = False, stubs: frozenset[int] = frozenset()) -> tuple[list[int], list[int], list[int]]:
    """Returns (to extract, done, stale). A row of the model rule-stub counts as done, and only force extracts it again."""
    done = [i for i in ids if existing.get(i) == version or (i in existing and i in stubs)]
    stale = [i for i in ids if i in existing and existing[i] != version and i not in stubs]
    todo = [i for i in ids if i not in existing] + (stale if redo_stale or force else []) + (done if force else [])
    return todo, done, stale


def estimate(words: int, n: int) -> dict:
    return {"input": int(words * 1.5 + n * 1000), "output": n * 470}


def model_id(conn, name: str) -> int:
    """Adds the model name to the table models if it is new."""
    conn.execute(text("INSERT INTO models (name) VALUES (:n) ON CONFLICT (name) DO NOTHING"), {"n": name})
    return conn.execute(text("SELECT id FROM models WHERE name = :n"), {"n": name}).scalar()


def store(conn, s: dict, model: str, version: str, clean: dict, warnings: list[str], answer: dict, tokens: dict) -> None:
    ext_id = conn.execute(text("""
        INSERT INTO speech_extractions (speech_id, model_id, prompt_version, language, summary, warnings, raw, tokens)
        VALUES (:sid, :m, :ver, :lang, :summary, :warnings, CAST(:raw AS jsonb), CAST(:tokens AS jsonb))
        RETURNING id
    """), {"sid": s["speech_id"], "m": model_id(conn, model), "ver": version, "lang": clean["language"],
           "summary": clean["summary"], "warnings": warnings, "raw": json.dumps(answer, ensure_ascii=False),
           "tokens": json.dumps(tokens)}).scalar()
    rows = [{"ext": ext_id, "sid": s["speech_id"], "list": lst, "pos": pos, "name": e["name"], "type": e["type"],
             "sal": e["salience"] if isinstance(e["salience"], int) else None, "mention": e["mention"],
             "found": e["mention_found"]}
            for lst, items in (("topic", clean["topics"]), ("other", clean["other_entities"]))
            for pos, e in enumerate(items, 1)]
    if rows:
        conn.execute(text("""
            INSERT INTO speech_items (extraction_id, speech_id, list, position, name, type, model_salience, mention, mention_found)
            VALUES (:ext, :sid, :list, :pos, :name, :type, :sal, :mention, :found)
        """), rows)


def load_records(conn, ids: list[int]) -> list[dict]:
    speeches = {s["speech_id"]: s for s in fetch_speeches(conn, ids)}
    exts = conn.execute(text("""
        SELECT e.id, e.speech_id, m.name AS model, e.prompt_version, e.language, e.summary, e.warnings
        FROM speech_extractions e JOIN models m ON m.id = e.model_id
        WHERE e.speech_id = ANY(:ids)
    """), {"ids": ids}).all()
    items = conn.execute(text("""
        SELECT extraction_id, list, name, type, model_salience, mention, mention_found FROM speech_items
        WHERE extraction_id = ANY(:e) AND source = 'llm' ORDER BY extraction_id, list, position
    """), {"e": [x.id for x in exts]}).all()
    records = []
    for x in exts:
        s = speeches[x.speech_id]
        mine = [i for i in items if i.extraction_id == x.id]
        def as_dicts(lst):
            return [{"name": i.name, "type": i.type, "salience": i.model_salience, "mention": i.mention,
                     "mention_found": i.mention_found} for i in mine if i.list == lst]
        records.append({**{k: s[k] for k in ("speech_id", "debate_id", "member", "title", "loksabha", "session",
                                             "word_count", "source_url")},
                        "debate_date": s["debate_date"].isoformat(),
                        "excerpt": " ".join(s["text"].split())[:EXCERPT_CHARS],
                        "model": x.model, "prompt_version": x.prompt_version,
                        "language": x.language, "summary": x.summary, "warnings": list(x.warnings),
                        "topics": as_dicts("topic"), "other_entities": as_dicts("other")})
    order = {sid: n for n, sid in enumerate(ids)}
    return sorted(records, key=lambda r: order[r["speech_id"]])


def cell(value: str) -> str:
    return value.replace("|", "/").replace("\n", " ")


def review_markdown(records: list[dict], header: dict) -> str:
    out = [f"# Entity extraction review: {header['scope']}", "",
           f"Model `{header['model']}`, prompt `{header['prompt']}` (version `{header['prompt_version']}`), written on {header['run_date']}. "
           f"{len(records)} speeches from {header['debates_sampled']} random debates "
           f"(of {header['debates_in_scope']} debates in {header['scope']} with a speech in range), "
           f"{header['per_debate']} speeches per debate at most, {header['min_words']} to {header['max_words']} words, seed {header['seed']}.",
           "", "For each speech, write `ok`, or what is wrong, after `review:`. "
           "A mention marked *(not in text)* was not found in the speech text.", ""]
    for i, r in enumerate(records, 1):
        title = " ".join((r["title"] or "(no title)").split())
        out += [f"## {i}. {r['member']}: {title}", "",
                f"{r['debate_date']}, LS{r['loksabha']} session {r['session']}, {r['word_count']} words, "
                f"language `{r['language']}`, model `{r['model']}`, prompt `{r['prompt_version']}`. [Source]({r['source_url']}). Speech id {r['speech_id']}.", "",
                f"> {r['excerpt']}", "", f"**Summary.** {r['summary']}", ""]
        for label, items in (("Topics", r["topics"]), ("Other entities", r["other_entities"])):
            out += [f"**{label}.**", "", "| Salience | Type | Name | Mention |", "|---|---|---|---|"]
            out += [f"| {e['salience']} | {e['type']} | {cell(e['name'])} | {cell(e['mention'])}"
                    f"{'' if e.get('mention_found', True) else ' *(not in text)*'} |" for e in items]
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


def extract_one(s: dict, model: str, system: str, key: str) -> tuple[dict, dict, list[str], dict]:
    answer, tokens = generate(model, system, user_text(s), key)
    clean, warnings = check_answer(answer)
    add_mention_checks(clean, s["text"], warnings)
    return answer, clean, warnings, tokens


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    scope = ap.add_mutually_exclusive_group(required=True)
    scope.add_argument("--year", type=int)
    scope.add_argument("--term", type=int, help="Lok Sabha term, for example 17")
    ap.add_argument("--all", action="store_true", help="every qualifying speech, not a sample")
    ap.add_argument("--debates", type=int, default=10, help="sample mode: random debates (default 10)")
    ap.add_argument("--per-debate", type=int, default=3, help="sample mode: speeches per debate at most (default 3)")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--min-words", type=int, default=99)
    ap.add_argument("--max-words", type=int, default=5000)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--prompt", help="prompt version, for example v1 (default: the highest version in prompts/)")
    ap.add_argument("--workers", type=int, default=4, help="API calls at the same time (default 4)")
    ap.add_argument("--redo-stale", action="store_true", help="extract again the speeches done with an older prompt version")
    ap.add_argument("--force", action="store_true",
                    help="extract again every selected speech, also the speeches done with this prompt version")
    ap.add_argument("--dry-run", action="store_true", help="print the counts and a token estimate, call no model")
    args = ap.parse_args()

    versions = prompt_versions(PROMPTS)
    version = args.prompt or next(reversed(versions))
    if version not in versions:
        ap.error(f"no prompt file for {version}. Known versions: {', '.join(versions)}")
    prompt_file = versions[version]
    system = prompt_file.read_text(encoding="utf-8")
    label = f"LS{args.term}" if args.term is not None else str(args.year)
    where, params = scope_filter(args.year, args.term)
    engine = get_engine()
    with engine.connect() as conn:
        ids, debates_in_scope = select_speech_ids(conn, where, params, args)
        rows = conn.execute(text("""
            SELECT e.speech_id, e.prompt_version, m.name = 'rule-stub' AS is_stub
            FROM speech_extractions e JOIN models m ON m.id = e.model_id
            WHERE e.speech_id = ANY(:ids)"""), {"ids": ids}).all()
        existing = {r.speech_id: r.prompt_version for r in rows}
        stubs = frozenset(r.speech_id for r in rows if r.is_stub)
        todo, done, stale = plan(ids, existing, version, args.redo_stale, args.force, stubs)
        words = conn.execute(text("SELECT coalesce(sum(word_count), 0) FROM speeches WHERE id = ANY(:ids)"),
                             {"ids": todo}).scalar()
        over = conn.execute(text(f"""
            SELECT count(*) FROM speeches s JOIN debates d ON d.id = s.debate_id
            WHERE s.person_id IS NOT NULL AND s.word_count > :hi AND {where}"""), {"hi": args.max_words, **params}).scalar()
    est = estimate(words, len(todo))
    print(f"{label}: {len(ids)} speeches selected ({'all' if args.all else 'sample'}), {debates_in_scope} debates in scope. "
          f"Already done with this prompt: {len(done)}{', redo (--force)' if args.force else ''}. "
          f"Stale (other prompt): {len(stale)}{', redo' if args.redo_stale or args.force else ', skipped'}. To extract: {len(todo)} ({words} words). "
          f"Over {args.max_words} words, not selected: {over}.", flush=True)
    print(f"Prompt {version} ({prompt_file.name}). Estimate: about {est['input']:,} input tokens and "
          f"{est['output']:,} output tokens with {args.model}.", flush=True)
    if args.dry_run:
        return

    if todo:
        key = api_key()
        totals = {"input": 0, "output": 0, "thinking": 0}
        stored = failed = 0
        for start in range(0, len(todo), 200):
            with engine.connect() as conn:
                batch = fetch_speeches(conn, todo[start:start + 200])
            with ThreadPoolExecutor(max_workers=args.workers) as pool:
                futures = {pool.submit(extract_one, s, args.model, system, key): s for s in batch}
                for fut in as_completed(futures):
                    s = futures[fut]
                    try:
                        answer, clean, warnings, tokens = fut.result()
                    except (ApiError, json.JSONDecodeError, KeyError, IndexError) as exc:
                        failed += 1
                        print(f"  speech {s['speech_id']}: failed, no row written ({exc!r:.200})", flush=True)
                        continue
                    with engine.begin() as conn:
                        if s["speech_id"] in existing:
                            conn.execute(text("DELETE FROM speech_extractions WHERE speech_id = :sid"),
                                         {"sid": s["speech_id"]})
                        store(conn, s, args.model, version, clean, warnings, answer, tokens)
                    stored += 1
                    for k in totals:
                        totals[k] += tokens.get(k) or 0
                    if stored % 25 == 0 or stored + failed == len(todo):
                        print(f"  {stored + failed}/{len(todo)} done, {failed} failed", flush=True)
        print(f"stored {stored}, failed {failed}. Tokens: input {totals['input']}, output {totals['output']}, "
              f"thinking {totals['thinking']}", flush=True)

    if not args.all and not todo:
        print("nothing new was extracted, so no review file was written", flush=True)
    elif not args.all:
        out_dir = FOLDER / "results"
        out_dir.mkdir(parents=True, exist_ok=True)
        with engine.connect() as conn:
            records = load_records(conn, ids)
        header = {"scope": label, "model": args.model, "prompt": str(prompt_file.relative_to(FOLDER.parent.parent)),
                  "prompt_version": version, "run_date": date.today().isoformat(),
                  "debates_sampled": len({r["debate_id"] for r in records}),
                  "debates_in_scope": debates_in_scope, "per_debate": args.per_debate,
                  "min_words": args.min_words, "max_words": args.max_words, "seed": args.seed}
        stem = free_stem(out_dir, f"{label}_seed{args.seed}_{args.model}_{date.today().isoformat()}")
        (out_dir / f"{stem}.md").write_text(review_markdown(records, header) + "\n", encoding="utf-8")
        print(f"review file: {out_dir / stem}.md ({len(records)} of {len(ids)} speeches have an extraction)", flush=True)


if __name__ == "__main__":
    main()
