"""Stage 4 of the tag pipeline: ask the decision model which items of each speech are real subjects of the speech.
The script stores the answers and the keep decision on each item in speech_items.

Scope: --year, --term or --speech-ids. Sample mode (no --all) writes a review file with an empty `review` column.
An item is kept when its probability reaches the limit of its source: --keep-llm for the llm items and
--keep-other for the dictionary and summary tag items.
An item that the current model and question version judged is skipped. --force judges it again.
--rethreshold computes `kept` again from the stored probabilities and calls no model.
--score FILE compares the marks of a review file with the decisions of the model.
A run stops after --max-failures failed calls in a row, or when the input tokens reach --max-tokens.

  Topics and summary tags:
    subject (noul): "X (a <type>) is a main or supporting subject of this
            speech, not only a passing mention." No tag description.
  Named types (place, person, institution, law, scheme, group, role):
    use     (choice): absent / aside (an example, a precedent, a comparison,
            a courtesy, a side list) / point (part of the member's point) /
            other_meaning (the words mean something else than this name). The
            question shows the words of the speech, because the name can be a
            full name that the speech does not say.

An item is kept when P(true) or P(point) reaches the limit of its source. The
two kinds of source have opposite risks. An llm item is the extraction's own
choice, so the bad error is to drop a correct item: --keep-llm is low (0.4).
A dictionary entity or a summary tag is an addition, so the bad error is to
keep a wrong item: --keep-other is high (0.8). Every item keeps its
probabilities, so --rethreshold computes `kept` again and calls no model.

Rows judged with question version q4 keep their q4 probabilities (level,
role, refers). keep() reads both versions, and --questions q4 selects the q4
rows for --rethreshold and --score. A q4 named item also needs
P(refers) >= --keep-refers. Only q5 can judge new rows.

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
`review` column. You write keep or drop in that column, and --score FILE
compares your marks with the model's decisions. --score also reads the old
column name `owner`.

Needs TYPESAFE_API_KEY. Run from the repo root:

    set -a && source .env && set +a
    python3 scripts/judge_items.py --year 2019 --max-words 5000 --dry-run
    python3 scripts/judge_items.py --year 2019 --max-words 5000
    python3 scripts/judge_items.py --rethreshold --term 18 --questions q4
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
                            noul_probability, noul_q, sum_is_off)
from scripts.extract_entities import cell, fetch_speeches, free_stem, scope_filter

FOLDER = Path(__file__).resolve().parent.parent / "tags" / "judging"
QUESTIONS_VERSION = "q5"
USES = {
    "absent": "Not mentioned, or only the speaker or the Chair.",
    "aside": "Only an example, precedent, comparison, courtesy, or side list item.",
    "point": "Part of the member's point: asked for, argued about, or says where or to whom it applies.",
    "other_meaning": "The words mean something else than this name.",
}

# The q4 answer order of judge_role_p, needed to read the rows that q4 judged.
ROLES = ("absent", "aside", "point")


@dataclass(frozen=True)
class Thresholds:
    llm: float = 0.4
    other: float = 0.8
    refers: float = 0.6


def judged_by(model: str, questions: str = QUESTIONS_VERSION) -> str:
    return f"{model} {questions}"


def is_level(item: dict) -> bool:
    return item["type"] == "topic" or item.get("source") == "summary_tag"


def questions_for(items: list[dict]) -> dict[str, dict]:
    out = {}
    for it in items:
        i, name, type_ = it["id"], it["name"], it["type"]
        if is_level(it):
            out[f"level_{i}"] = noul_q(
                f"«{name}» (a {type_}) is a main or supporting subject of this speech, not only a passing mention.")
            continue
        out[f"use_{i}"] = choice_q(f"How does this speech use «{name}» (a {type_}, in the words «{it['mention']}»)?",
                                   USES)
    return out


def speech_state(s: dict) -> str:
    return (f"Member: {s['member']}\nDebate: {s['title'] or '(no title)'}\nDate: {s['debate_date']}\n\n"
            f"Speech:\n{s['text']}")


def summary_state(s: dict, summary: str, items: list[dict]) -> str:
    lines = [f"- {it['name']} ({it['type']}): " + (f"\"{it['mention']}\"" if it["mention"] else "(no quoted words)")
             for it in items]
    return (f"Member: {s['member']}\nDebate: {s['title'] or '(no title)'}\nDate: {s['debate_date']}\n\n"
            f"Summary of the speech: {summary}\n\nWords of the speech about each item:\n" + "\n".join(lines))


def p_keep(j: dict) -> float:
    if j.get("subject_p") is not None:
        return j["subject_p"]
    if j.get("use_p") is not None:
        return j["use_p"]["point"]
    if j.get("level_p") is not None:
        return j["level_p"][2] + j["level_p"][3]
    return j["role_p"]["point"]


def keep(j: dict, t: Thresholds = Thresholds()) -> bool:
    limit = t.llm if j["source"] == "llm" else t.other
    if p_keep(j) < limit:
        return False
    return j.get("role_p") is None or j["refers_p"] >= t.refers


def read_item(answers: dict, item: dict) -> tuple[dict, list[str], dict]:
    i, warnings, raw = item["id"], [], {}
    j = {"subject_p": None, "use_p": None, "source": item.get("source", "llm")}
    if is_level(item):
        raw["subject"] = answers[f"level_{i}"]
        j["subject_p"] = noul_probability(raw["subject"])
        if not 0 <= j["subject_p"] <= 1:
            warnings.append(f"subject probability out of range: {j['subject_p']}")
        return j, warnings, raw
    raw["use"] = answers[f"use_{i}"]
    j["use_p"] = choice_probabilities(raw["use"], list(USES))
    if sum_is_off(list(j["use_p"].values())):
        warnings.append(f"use probabilities sum to {sum(j['use_p'].values()):.3f}")
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
            UPDATE speech_items SET judge_subject_p = :sp, judge_use_p = :up,
                   judge_level_p = NULL, judge_role_p = NULL, judge_refers_p = NULL, judge_type_p = NULL,
                   judge_type = NULL, kept = :k, judge_state = :st,
                   judge_raw = CAST(:raw AS jsonb), judge_warnings = :w, judged_by = :by, judged_at = now()
            WHERE id = :id
        """), {"sp": j["subject_p"], "up": [j["use_p"][u] for u in USES] if j["use_p"] else None,
               "k": k, "st": state_kind, "raw": json.dumps(raw, ensure_ascii=False), "w": warnings,
               "by": version, "id": it["id"]})
    return kept_n


def judgement(row) -> dict:
    return {"subject_p": row.judge_subject_p,
            "use_p": dict(zip(USES, row.judge_use_p)) if row.judge_use_p else None,
            "level_p": row.judge_level_p,
            "role_p": dict(zip(ROLES, row.judge_role_p)) if row.judge_role_p else None,
            "refers_p": row.judge_refers_p, "source": row.source}


def select_items(conn, where: str | None, params: dict, version: str, force: bool) -> tuple[dict[int, list[dict]], int]:
    scope = f"AND {where}" if where else ""
    rows = conn.execute(text(f"""
        SELECT i.id, i.speech_id, i.list, i.position, i.name, i.type, i.mention, i.judged_by, i.source,
               g.description
        FROM speech_items i JOIN speeches s ON s.id = i.speech_id JOIN debates d ON d.id = s.debate_id
        LEFT JOIN tags g ON g.id = i.tag_id
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


JUDGED_COLUMNS = ("i.id, i.source, i.judge_subject_p, i.judge_use_p, i.judge_level_p, i.judge_role_p, "
                  "i.judge_refers_p, i.kept")


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
    """pairs holds (manual keep, model keep) for each item."""
    manual_keep = [m for o, m in pairs if o]
    manual_drop = [m for o, m in pairs if not o]
    return {"manual_keep": len(manual_keep), "model_keeps_of_those": sum(manual_keep),
            "manual_drop": len(manual_drop), "model_drops_of_those": sum(1 for m in manual_drop if not m)}


def read_marks(path: Path) -> dict[int, bool]:
    marks = {}
    with path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            mark = (row.get("review") or row.get("owner") or "").strip().lower()
            if mark in ("keep", "drop"):
                marks[int(row["item_id"])] = mark == "keep"
    return marks


def score_groups(rows) -> list[tuple[str, list]]:
    llm = [r for r in rows if r.source == "llm"]
    return [("llm topics", [r for r in llm if r.type == "topic"]),
            ("llm named", [r for r in llm if r.type != "topic"]),
            ("dictionary", [r for r in rows if r.source == "dictionary"]),
            ("recognised", [r for r in rows if r.source == "summary_tag"]),
            ("all", list(rows))]


def score(engine, path: Path, version: str, t: Thresholds) -> None:
    marks = read_marks(path)
    if not marks:
        raise SystemExit(f"no row in {path} has keep or drop in the review column")
    with engine.connect() as conn:
        rows = conn.execute(text(f"SELECT {JUDGED_COLUMNS}, i.type FROM speech_items i "
                                 "WHERE i.id = ANY(:ids) AND i.judged_by = :by"), {"ids": list(marks), "by": version}).all()
    print(f"{len(marks)} items marked by hand, {len(rows)} of them judged with {version}. {t}.")
    for label, sel in score_groups(rows):
        if not sel:
            continue
        r = gate_rates([(marks[x.id], keep(judgement(x), t)) for x in sel])
        print(f"  {label:12}: the model keeps {r['model_keeps_of_those']} of the {r['manual_keep']} items that the manual review "
              f"keeps, and drops {r['model_drops_of_those']} of the {r['manual_drop']} items that the manual review drops")


def write_review(engine, speech_ids: list[int], label: str, model: str, prefill: dict[int, bool] | None = None) -> Path:
    prefill = prefill or {}
    with engine.connect() as conn:
        speeches = {s["speech_id"]: s for s in fetch_speeches(conn, speech_ids)}
        summaries = dict(conn.execute(text(
            "SELECT speech_id, summary FROM speech_extractions WHERE speech_id = ANY(:ids)"), {"ids": speech_ids}).all())
        items = conn.execute(text("""
            SELECT i.id, i.speech_id, i.list, i.type, i.name, i.mention, i.mention_found, i.judge_subject_p,
                   i.judge_use_p, i.judge_level_p, i.judge_role_p, i.judge_refers_p, i.judge_type, i.kept,
                   i.judge_state, i.judge_warnings, i.source, i.evidence, g.description
            FROM speech_items i LEFT JOIN tags g ON g.id = i.tag_id
            WHERE i.speech_id = ANY(:ids) ORDER BY i.speech_id, i.list DESC, i.position
        """), {"ids": speech_ids}).all()
    out_dir = FOLDER / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = free_stem(out_dir, f"{label}_{model.replace('/', '_')}_{QUESTIONS_VERSION}_{date.today().isoformat()}")
    t = Thresholds()
    md = [f"# Relevance check review: {label}", "",
          f"Model `{model}`, questions `{QUESTIONS_VERSION}`, written on {date.today().isoformat()}. "
          f"{len(speech_ids)} speeches. For a topic or a recognised tag, `P(keep)` is P(a main or supporting subject). "
          f"For a named item, `P(keep)` is P(part of the member's point). An `llm` item is kept at {t.llm}, "
          f"a `dict` or `recognised` item at {t.other}. `P(refers)` and `Model type` exist only for rows that "
          f"question version q4 judged. "
          f"`Source`: `llm` = the extraction, `dict` = the entity dictionary found the words in the text, "
          f"`recognised` = a recognised tag, near the summary in meaning (its rank and distance in brackets). "
          f"Write keep or drop in the `review` column of `{stem}.tsv`. "
          f"{len(prefill)} items carry an earlier manual mark already.", ""]
    with (out_dir / f"{stem}.tsv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["item_id", "speech_id", "source", "list", "type", "model_type", "name", "mention", "p_keep",
                    "p_refers", "kept", "review"])
        for sid in speech_ids:
            s = speeches.get(sid)
            mine = [i for i in items if i.speech_id == sid]
            if not s or not mine:
                continue
            state = {i.judge_state for i in mine if i.judge_state}
            md += [f"## {s['member']}: {' '.join((s['title'] or '(no title)').split())}", "",
                   f"{s['debate_date']}, {s['word_count']} words, state `{'/'.join(sorted(state)) or '-'}`. "
                   f"Speech id {sid}.", "", f"**Summary.** {summaries.get(sid, '')}", "",
                   "| Kept | P(keep) | P(refers) | Source | Type | Model type | Name | Mention |",
                   "|---|---|---|---|---|---|---|---|"]
            for i in mine:
                j = judgement(i)
                judged = any(j[k] is not None for k in ("subject_p", "use_p", "level_p", "role_p"))
                pk = f"{p_keep(j):.2f}" if judged else "-"
                pr = f"{i.judge_refers_p:.2f}" if i.judge_refers_p is not None else "-"
                mt = i.judge_type if i.judge_type and i.judge_type != i.type else ""
                kept = {True: "yes", False: "no", None: "-"}[i.kept]
                src = {"llm": "llm", "dictionary": "dict", "summary_tag": "recognised"}[i.source]
                if i.source == "summary_tag":
                    src += f" ({i.evidence['rank']}, {i.evidence['distance']:.2f})"
                    mention = cell(i.description or "")
                    note = ""
                else:
                    mention = cell(i.mention)
                    note = "" if i.mention_found else " *(not in text)*"
                mark = {True: "keep", False: "drop"}.get(prefill.get(i.id), "")
                md.append(f"| {kept} | {pk} | {pr} | {src} | {i.type} | {mt} | {cell(i.name)} | {mention}{note} |")
                w.writerow([i.id, sid, i.source, i.list, i.type, mt, i.name,
                            i.description if i.source == "summary_tag" else i.mention, pk, pr, kept, mark])
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
    scope.add_argument("--speech-ids", help="comma-separated speech ids")
    ap.add_argument("--max-words", type=int, help="only speeches with at most this many words")
    ap.add_argument("--all", action="store_true", help="full mode: no review file")
    ap.add_argument("--model", default=MODEL)
    ap.add_argument("--state", choices=("auto", "speech", "summary"), default="auto",
                    help="what the model reads (default auto: the speech, or the summary when the speech is too long)")
    ap.add_argument("--keep-llm", type=float, default=Thresholds.llm, help="limit for llm items")
    ap.add_argument("--keep-other", type=float, default=Thresholds.other,
                    help="limit for dictionary entities and recognised tags")
    ap.add_argument("--keep-refers", type=float, default=Thresholds.refers, help="q4 named items only: P(refers)")
    ap.add_argument("--questions", default=QUESTIONS_VERSION,
                    help="the question version of the rows that --rethreshold and --score read (q4 or q5)")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--force", action="store_true", help="judge again the items done with this version")
    ap.add_argument("--dry-run", action="store_true", help="print the counts, call no model")
    ap.add_argument("--rethreshold", action="store_true", help="compute `kept` again from the stored probabilities")
    ap.add_argument("--score", type=Path, help="a review TSV with the review column filled in")
    ap.add_argument("--prefill", type=Path, help="sample mode: a review TSV whose marks fill the new review file")
    args = ap.parse_args()

    engine = get_engine()
    t = Thresholds(args.keep_llm, args.keep_other, args.keep_refers)
    version = judged_by(args.model, args.questions)
    if args.speech_ids:
        where, params = "s.id = ANY(:ids)", {"ids": [int(x) for x in args.speech_ids.split(",")]}
    else:
        where, params = (scope_filter(args.year, args.term) if args.year or args.term else (None, {}))
    if args.max_words:
        where = " AND ".join(x for x in (where, "s.word_count <= :max_words") if x)
        params = {**params, "max_words": args.max_words}
    if args.score:
        return score(engine, args.score, version, t)
    if args.rethreshold:
        return rethreshold(engine, where, params, version, t)

    if args.questions != QUESTIONS_VERSION:
        raise SystemExit(f"only question version {QUESTIONS_VERSION} can judge; --questions works with "
                         "--rethreshold and --score")
    label = (f"LS{args.term}" if args.term else str(args.year) if args.year else
             "sample" if args.speech_ids else "all")
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
        path = write_review(engine, ids, label, args.model, read_marks(args.prefill) if args.prefill else None)
        print(f"review files: {path}.md and {path}.tsv", flush=True)


if __name__ == "__main__":
    main()
