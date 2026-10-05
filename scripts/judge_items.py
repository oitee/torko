"""Stage 4 of the tag pipeline: ask the decision model which items of each speech are real subjects of the speech.
The script stores the answers and the keep decision on each item in speech_items.

Stage 3 gives each speech at most 8 topics and 8 other entities (speech_items).
Some are only background, or are the speaker, the Chair, or procedure. All
items of one speech go in one call. Questions version q3:

  Topics:
    level   (score): how central the topic is to the speech, 0 to 3.
  Named types (place, person, institution, law, scheme, group, role):
    role    (choice): absent / aside (an example, a precedent, a comparison,
            a courtesy, a side list) / point (part of the member's point; once
            is enough). The question shows the words of the speech, because
            the name can be a full name that the speech does not say.
    refers  (noul): the words of the speech refer to the item's name, and the
            speech with common knowledge tells which one, without a guess.
            This catches a full name that the extraction model guessed.
    type    (choice): what kind of thing the item is. It never decides keep or
            drop. When the model picks a type with p >= TYPE_P, judge_type
            holds it, and later stages use it.

A topic is kept when P(level 2 or 3) >= --keep-level. A named item is kept
when P(point) >= --keep-point and P(refers) >= --keep-refers. Every item keeps
its probabilities, so --rethreshold computes `kept` again and calls no model.

State: the member, the debate title, the date, and the speech text. When the
speech does not fit in the model's context, the state is the stage 3 summary
plus the mention of each item ('summary' in judge_state). --state forces one.

Idempotent. An item that has judged_by equal to the current model and question
version is skipped. --force judges every selected item again. A new question
version judges every item again and replaces its stage 4 columns. Each speech
is written in its own transaction as soon as its answer arrives.

Which speeches: every speech with an extraction, or only those in one --year
or one --term. In sample mode (no --all) a review file is written in
tags/judging/results/: a Markdown file to read and a TSV file with an empty
`owner` column. The owner writes keep or drop in that column, and --score FILE
compares the owner's marks with the model's decisions.

Needs TYPESAFE_API_KEY. Run from the repo root:

    set -a && source .env && set +a
    python3 scripts/judge_items.py --year 2019 --max-words 5000 --dry-run
    python3 scripts/judge_items.py --year 2019 --max-words 5000
    python3 scripts/judge_items.py --rethreshold --keep-point 0.5
    python3 scripts/judge_items.py --score tags/judging/results/2019_....tsv
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from db import get_engine
from decision_model import (MODEL, DecisionError, StateTooLong, api_key, choice_probabilities, choice_q, decide,
                            noul_probability, noul_q, score_probabilities, score_q, sum_is_off)
from scripts.extract_entities import cell, fetch_speeches, free_stem, scope_filter

FOLDER = Path(__file__).resolve().parent.parent / "tags" / "judging"
QUESTIONS_VERSION = "q3"
TYPE_P = 0.7

LEVELS = [
    "0, not a subject: it is not in the speech, or it is only the speaker, the Chair, an addressee, or procedure.",
    "1, passing: it is named once, as background, as an example, or as the source of a statement.",
    "2, supporting: the speech discusses it in more than one sentence, or the member's request depends on it.",
    "3, central: the speech is mainly about it.",
]

ROLES = {
    "absent": "The speech does not mention it, or it is only the speaker or the Chair.",
    "aside": "The speech mentions it only as an example, a precedent, a comparison, a courtesy (thanks, praise, "
             "a greeting), or one item in a side list. The member's point does not depend on it.",
    "point": "The speech mentions it as part of the member's point. The member asks for something about it, "
             "argues about it, or uses it to say where or to whom the point applies. One mention is enough.",
}

TYPES = {
    "place": "A specific place: a country, state, district, city, village, river, port, or region.",
    "person": "One specific person.",
    "institution": "An organisation or a body: a ministry, court, commission, company, party, or department.",
    "law": "An Act, a bill, an ordinance, an article of the Constitution, or a code.",
    "scheme": "A government programme, mission, or scheme.",
    "group": "A class of people, for example farmers or Dalits.",
    "role": "An office that one person holds at a time, for example Prime Minister.",
    "topic": "A subject or an issue, not a named thing.",
    "other": "A named thing of none of these kinds, for example a treaty, a book, or an event.",
}


@dataclass(frozen=True)
class Thresholds:
    level: float = 0.6
    point: float = 0.6
    refers: float = 0.6


def judged_by(model: str) -> str:
    return f"{model} {QUESTIONS_VERSION}"


def questions_for(items: list[dict]) -> dict[str, dict]:
    """All questions of one speech. Topics: level_<id>. Named items: role_<id>, refers_<id>, type_<id>."""
    out = {}
    for it in items:
        i, name, type_ = it["id"], it["name"], it["type"]
        if type_ == "topic":
            out[f"level_{i}"] = score_q(f"How central is «{name}» (a topic) to this speech?", LEVELS)
            continue
        out[f"role_{i}"] = choice_q(
            f"How does this speech use «{name}» (a {type_}, in the words «{it['mention']}»)?", ROLES)
        out[f"refers_{i}"] = noul_q(
            f"In this speech, the words «{it['mention']}» refer to «{name}». The speech, with common knowledge, "
            f"is enough to tell that it is this one specific thing, without a guess.")
        out[f"type_{i}"] = choice_q(f"What kind of thing is «{name}», as this speech uses it?", TYPES)
    return out


def speech_state(s: dict) -> str:
    return (f"Member: {s['member']}\nDebate: {s['title'] or '(no title)'}\nDate: {s['debate_date']}\n\n"
            f"Speech:\n{s['text']}")


def summary_state(s: dict, summary: str, items: list[dict]) -> str:
    lines = [f"- {it['name']} ({it['type']}): \"{it['mention']}\"" for it in items]
    return (f"Member: {s['member']}\nDebate: {s['title'] or '(no title)'}\nDate: {s['debate_date']}\n\n"
            f"Summary of the speech: {summary}\n\nWords of the speech about each item:\n" + "\n".join(lines))


def keep(j: dict, t: Thresholds = Thresholds()) -> bool:
    """The stage 4 decision for one item, from its stored probabilities.
    A topic: central enough. A named item: part of the point, and the name is what the words refer to."""
    if j.get("level_p") is not None:
        return j["level_p"][2] + j["level_p"][3] >= t.level
    return j["role_p"]["point"] >= t.point and j["refers_p"] >= t.refers


def read_item(answers: dict, item: dict) -> tuple[dict, list[str], dict]:
    """Check and read the answers of one item. Returns the judgement, the warnings, and the raw answers."""
    i, warnings, raw = item["id"], [], {}
    j = {"level_p": None, "role_p": None, "refers_p": None, "type_p": None, "type": None}
    if item["type"] == "topic":
        raw["level"] = answers[f"level_{i}"]
        j["level_p"] = score_probabilities(raw["level"], LEVELS)
        if sum_is_off(j["level_p"]):
            warnings.append(f"level probabilities sum to {sum(j['level_p']):.3f}")
        return j, warnings, raw
    raw["role"], raw["refers"], raw["type"] = answers[f"role_{i}"], answers[f"refers_{i}"], answers[f"type_{i}"]
    j["role_p"] = choice_probabilities(raw["role"], list(ROLES))
    j["refers_p"] = noul_probability(raw["refers"])
    j["type_p"] = choice_probabilities(raw["type"], list(TYPES))
    for label, probs in (("role", j["role_p"]), ("type", j["type_p"])):
        if sum_is_off(list(probs.values())):
            warnings.append(f"{label} probabilities sum to {sum(probs.values()):.3f}")
    if not 0 <= j["refers_p"] <= 1:
        warnings.append(f"refers probability out of range: {j['refers_p']}")
    top = max(j["type_p"], key=j["type_p"].get)
    if j["type_p"][top] >= TYPE_P:
        j["type"] = top
    return j, warnings, raw


def judge_one(s: dict, summary: str, items: list[dict], mode: str, key: str, model: str) -> tuple[str, dict]:
    questions = questions_for(items)
    if mode in ("auto", "speech"):
        try:
            return "speech", decide(speech_state(s), questions, key, model)
        except StateTooLong:
            if mode == "speech":
                raise
    return "summary", decide(summary_state(s, summary, items), questions, key, model)


def store(conn, items: list[dict], state_kind: str, data: dict, version: str, t: Thresholds) -> int:
    kept_n = 0
    for it in items:
        j, warnings, raw = read_item(data["answers"], it)
        raw["model"] = data.get("model")
        k = keep(j, t)
        kept_n += k
        conn.execute(text("""
            UPDATE speech_items SET judge_level_p = :lp, judge_role_p = :rp, judge_refers_p = :fp,
                   judge_type_p = CAST(:tp AS jsonb), judge_type = :jt, kept = :k, judge_state = :st,
                   judge_raw = CAST(:raw AS jsonb), judge_warnings = :w, judged_by = :by, judged_at = now()
            WHERE id = :id
        """), {"lp": j["level_p"], "rp": [j["role_p"][r] for r in ROLES] if j["role_p"] else None,
               "fp": j["refers_p"], "tp": json.dumps(j["type_p"]) if j["type_p"] else None, "jt": j["type"],
               "k": k, "st": state_kind, "raw": json.dumps(raw, ensure_ascii=False), "w": warnings,
               "by": version, "id": it["id"]})
    return kept_n


def judgement(row) -> dict:
    """The judgement of one stored row, in the shape that keep() reads."""
    return {"level_p": row.judge_level_p,
            "role_p": dict(zip(ROLES, row.judge_role_p)) if row.judge_role_p else None,
            "refers_p": row.judge_refers_p}


def select_items(conn, where: str | None, params: dict, version: str, force: bool) -> tuple[dict[int, list[dict]], int]:
    scope = f"AND {where}" if where else ""
    rows = conn.execute(text(f"""
        SELECT i.id, i.speech_id, i.list, i.position, i.name, i.type, i.mention, i.judged_by
        FROM speech_items i JOIN speeches s ON s.id = i.speech_id JOIN debates d ON d.id = s.debate_id
        WHERE TRUE {scope}
        ORDER BY d.debate_date, i.speech_id, i.list DESC, i.position
    """), params).all()
    todo: dict[int, list[dict]] = {}
    done = 0
    for r in rows:
        if r.judged_by == version and not force:
            done += 1
            continue
        todo.setdefault(r.speech_id, []).append(dict(r._mapping))
    return todo, done


JUDGED_COLUMNS = "i.id, i.judge_level_p, i.judge_role_p, i.judge_refers_p, i.kept"


def rethreshold(engine, where: str | None, params: dict, version: str, t: Thresholds) -> None:
    scope = f"AND {where}" if where else ""
    with engine.begin() as conn:
        rows = conn.execute(text(f"""
            SELECT {JUDGED_COLUMNS}
            FROM speech_items i JOIN speeches s ON s.id = i.speech_id JOIN debates d ON d.id = s.debate_id
            WHERE i.judged_by = :by {scope}
        """), {**params, "by": version}).all()
        changed = [{"id": r.id, "k": keep(judgement(r), t)} for r in rows]
        changed = [c for c, r in zip(changed, rows) if c["k"] != r.kept]
        if changed:
            conn.execute(text("UPDATE speech_items SET kept = :k WHERE id = :id"), changed)
    print(f"{len(rows)} items judged with {version} read, {len(changed)} changed `kept` ({t}). "
          f"No model was called.", flush=True)


def gate_rates(pairs: list[tuple[bool, bool]]) -> dict:
    """pairs = (owner keeps, model keeps). The two stage 4 gate numbers, with their counts."""
    owner_keep = [m for o, m in pairs if o]
    owner_drop = [m for o, m in pairs if not o]
    return {"owner_keep": len(owner_keep), "model_keeps_of_those": sum(owner_keep),
            "owner_drop": len(owner_drop), "model_drops_of_those": sum(1 for m in owner_drop if not m)}


def score(engine, path: Path, version: str, t: Thresholds) -> None:
    """Compare the owner's keep or drop marks with the model's decisions, for topics and named items apart."""
    marks = {}
    with path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            mark = (row.get("owner") or "").strip().lower()
            if mark in ("keep", "drop"):
                marks[int(row["item_id"])] = mark == "keep"
    if not marks:
        raise SystemExit(f"no row in {path} has keep or drop in the owner column")
    with engine.connect() as conn:
        rows = conn.execute(text(f"SELECT {JUDGED_COLUMNS}, i.type FROM speech_items i "
                                 "WHERE i.id = ANY(:ids) AND i.judged_by = :by"), {"ids": list(marks), "by": version}).all()
    print(f"{len(marks)} items marked by the owner, {len(rows)} of them judged with {version}. {t}.")
    for label, sel in (("topics", [r for r in rows if r.type == "topic"]),
                       ("named items", [r for r in rows if r.type != "topic"]), ("all", rows)):
        r = gate_rates([(marks[x.id], keep(judgement(x), t)) for x in sel])
        print(f"  {label:11}: the model keeps {r['model_keeps_of_those']} of the {r['owner_keep']} items that the owner "
              f"keeps, and drops {r['model_drops_of_those']} of the {r['owner_drop']} items that the owner drops")


def write_review(engine, speech_ids: list[int], label: str, model: str) -> Path:
    with engine.connect() as conn:
        speeches = {s["speech_id"]: s for s in fetch_speeches(conn, speech_ids)}
        summaries = dict(conn.execute(text(
            "SELECT speech_id, summary FROM speech_extractions WHERE speech_id = ANY(:ids)"), {"ids": speech_ids}).all())
        items = conn.execute(text("""
            SELECT id, speech_id, list, type, name, mention, mention_found, judge_level_p, judge_role_p,
                   judge_refers_p, judge_type, kept, judge_state, judge_warnings
            FROM speech_items WHERE speech_id = ANY(:ids) ORDER BY speech_id, list DESC, position
        """), {"ids": speech_ids}).all()
    out_dir = FOLDER / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = free_stem(out_dir, f"{label}_{model.replace('/', '_')}_{QUESTIONS_VERSION}_{date.today().isoformat()}")
    t = Thresholds()
    md = [f"# Relevance check review: {label}", "",
          f"Model `{model}`, questions `{QUESTIONS_VERSION}`, written on {date.today().isoformat()}. "
          f"{len(speech_ids)} speeches. For a topic, `P(keep)` is P(central or supporting), kept at {t.level}. "
          f"For a named item, `P(keep)` is P(part of the member's point), kept at {t.point} together with "
          f"`P(refers)` at {t.refers}. `Model type` shows the model's type only when it differs from the extraction type. "
          f"Write keep or drop in the `owner` column of `{stem}.tsv`.", ""]
    with (out_dir / f"{stem}.tsv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["item_id", "speech_id", "list", "type", "model_type", "name", "mention", "p_keep", "p_refers",
                    "kept", "owner"])
        for sid in speech_ids:
            s = speeches.get(sid)
            mine = [i for i in items if i.speech_id == sid]
            if not s or not mine:
                continue
            state = {i.judge_state for i in mine if i.judge_state}
            md += [f"## {s['member']}: {' '.join((s['title'] or '(no title)').split())}", "",
                   f"{s['debate_date']}, {s['word_count']} words, state `{'/'.join(sorted(state)) or '-'}`. "
                   f"Speech id {sid}.", "", f"**Summary.** {summaries.get(sid, '')}", "",
                   "| Kept | P(keep) | P(refers) | Type | Model type | Name | Mention |",
                   "|---|---|---|---|---|---|---|"]
            for i in mine:
                if i.judge_level_p:
                    pk = f"{i.judge_level_p[2] + i.judge_level_p[3]:.2f}"
                elif i.judge_role_p:
                    pk = f"{i.judge_role_p[list(ROLES).index('point')]:.2f}"
                else:
                    pk = "-"
                pr = f"{i.judge_refers_p:.2f}" if i.judge_refers_p is not None else "-"
                mt = i.judge_type if i.judge_type and i.judge_type != i.type else ("?" if i.type != "topic" and not i.judge_type else "")
                kept = {True: "yes", False: "no", None: "-"}[i.kept]
                note = "" if i.mention_found else " *(not in text)*"
                md.append(f"| {kept} | {pk} | {pr} | {i.type} | {mt} | {cell(i.name)} | {cell(i.mention)}{note} |")
                w.writerow([i.id, sid, i.list, i.type, mt, i.name, i.mention, pk, pr, kept, ""])
            warns = [x for i in mine for x in i.judge_warnings]
            if warns:
                md += ["", "Warnings: " + "; ".join(warns)]
            md.append("")
    (out_dir / f"{stem}.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    return out_dir / stem


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    scope = ap.add_mutually_exclusive_group()
    scope.add_argument("--year", type=int)
    scope.add_argument("--term", type=int, help="Lok Sabha term, for example 17")
    ap.add_argument("--max-words", type=int, help="only speeches with at most this many words")
    ap.add_argument("--all", action="store_true", help="full mode: no review file")
    ap.add_argument("--model", default=MODEL)
    ap.add_argument("--state", choices=("auto", "speech", "summary"), default="auto",
                    help="what the model reads (default auto: the speech, or the summary when the speech is too long)")
    ap.add_argument("--keep-level", type=float, default=Thresholds.level, help="topics: P(level 2 or 3)")
    ap.add_argument("--keep-point", type=float, default=Thresholds.point, help="named items: P(point)")
    ap.add_argument("--keep-refers", type=float, default=Thresholds.refers, help="named items: P(refers)")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--force", action="store_true", help="judge again the items done with this version")
    ap.add_argument("--dry-run", action="store_true", help="print the counts, call no model")
    ap.add_argument("--rethreshold", action="store_true", help="compute `kept` again from the stored probabilities")
    ap.add_argument("--score", type=Path, help="a review TSV with the owner column filled in")
    args = ap.parse_args()

    engine = get_engine()
    t = Thresholds(args.keep_level, args.keep_point, args.keep_refers)
    version = judged_by(args.model)
    where, params = (scope_filter(args.year, args.term) if args.year or args.term else (None, {}))
    if args.max_words:
        where = " AND ".join(x for x in (where, "s.word_count <= :max_words") if x)
        params = {**params, "max_words": args.max_words}
    if args.score:
        return score(engine, args.score, version, t)
    if args.rethreshold:
        return rethreshold(engine, where, params, version, t)

    label = f"LS{args.term}" if args.term else str(args.year) if args.year else "all"
    with engine.connect() as conn:
        todo, done = select_items(conn, where, params, version, args.force)
    n_items = sum(len(v) for v in todo.values())
    print(f"{label}: {len(todo)} speeches with {n_items} items to judge. Already judged with {version}: {done}.",
          flush=True)
    if args.dry_run or not todo:
        return

    key = api_key()
    ids = list(todo)
    stored = failed = kept_total = 0
    states = {"speech": 0, "summary": 0}
    tokens = 0
    for start in range(0, len(ids), 100):
        batch_ids = ids[start:start + 100]
        with engine.connect() as conn:
            speeches = {s["speech_id"]: s for s in fetch_speeches(conn, batch_ids)}
            summaries = dict(conn.execute(text(
                "SELECT speech_id, summary FROM speech_extractions WHERE speech_id = ANY(:ids)"),
                {"ids": batch_ids}).all())
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = {pool.submit(judge_one, speeches[sid], summaries[sid], todo[sid], args.state, key, args.model): sid
                       for sid in batch_ids}
            for fut in as_completed(futures):
                sid = futures[fut]
                try:
                    state_kind, data = fut.result()
                    with engine.begin() as conn:
                        kept_total += store(conn, todo[sid], state_kind, data, version, t)
                except DecisionError as exc:
                    failed += 1
                    print(f"  speech {sid}: failed, nothing written ({exc!s:.200})", flush=True)
                    continue
                stored += 1
                states[state_kind] += 1
                tokens += (data.get("usage") or {}).get("input_tokens") or 0
                print(f"  speech {sid}: {len(todo[sid])} items, state {state_kind} "
                      f"({stored + failed}/{len(ids)})", flush=True)
    print(f"judged {stored} speeches, failed {failed}. Kept {kept_total} of the items in the judged speeches. "
          f"State: speech {states['speech']}, summary {states['summary']}. Input tokens {tokens:,}.", flush=True)
    if not args.all:
        path = write_review(engine, ids, label, args.model)
        print(f"review files: {path}.md and {path}.tsv", flush=True)


if __name__ == "__main__":
    main()
