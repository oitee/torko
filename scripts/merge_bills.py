"""Step 5 of the bill step: merge the spellings of one bill, then give each bill one summary.

The merge:
1. Exact: the same bill_key is the same bill. bill_extract.py already makes one bills row for each key.
2. Candidates: two bills of the same year whose names have a pg_trgm similarity of MIN_SIMILARITY or more.
3. Hard rules in code: a pair is never a candidate when the Lok Sabha terms differ, when the years differ, when the amendment numbers differ,
   when the digits in the two names differ ("No. 2" and "No. 3"), or when the ordinal words differ
   ("Second Amendment" and "Amendment").
4. The decision model reads both names, their debate titles, and their summaries, and answers: same bill,
   different bill, or unsure. A pair merges only when "same" has a probability of SAME_P or more.
5. The answers go to data/bill_merges.tsv. --apply reads that file and sets bills.merged_into, so a rebuild
   applies the merges again with no model call. The kept bill of a group is the bill with the most debates.

The summary of each kept bill (bills.summary), with --summaries:
- no summary in its debates: NULL.
- one distinct summary: a copy, with no model call (summary_model_id NULL).
- two or more: an LLM joins them (--join-sample N calls the Gemini API for at most 15 bills).
  The prompt is tags/bills/prompts/merge_summary_v1.md. It uses only the given summaries and adds nothing.

    set -a && source .env && set +a
    python3 scripts/merge_bills.py --candidates            # print the candidate counts, call no model
    python3 scripts/merge_bills.py --judge                 # decision model, writes data/bill_merges.tsv
    python3 scripts/merge_bills.py --apply                 # set bills.merged_into from the file
    python3 scripts/merge_bills.py --summaries             # copy the single summaries, list the rest
    python3 scripts/merge_bills.py --join-sample 12        # join the summaries of 12 bills with the Gemini API
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from bill_extract import base_key, key_term
from db import get_engine
from llm import model_id

ROOT = Path(__file__).resolve().parent.parent
MERGES = ROOT / "data" / "bill_merges.tsv"
PROMPTS = ROOT / "tags" / "bills" / "prompts"
MIN_SIMILARITY = 0.6
SAME_P = 0.7
QUESTIONS_VERSION = "m1"
SUMMARY_PROMPT_VERSION = "merge_summary_v1"
DEFAULT_MODEL = "gemini-3.8-flash"
MAX_JOIN_SAMPLE = 15

ORDINAL_WORDS = {
    "first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth", "ninth", "tenth", "eleventh",
    "twelfth", "thirteenth", "fourteenth", "fifteenth", "sixteenth", "seventeenth", "eighteenth", "nineteenth",
    "twentieth", "thirtieth", "fortieth", "fiftieth", "sixtieth", "seventieth", "eightieth", "ninetieth",
    "hundredth", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety", "hundred",
}
SAME = {
    "same": "Both names are spellings of one bill: the same bill of the same year.",
    "different": "The names are two different bills.",
    "unsure": "The text does not show if the two names are one bill.",
}


def number_marks(name: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """The digits and the ordinal words of a name, in order. Two names with different marks are different bills."""
    low = (name or "").lower()
    digits = tuple(re.findall(r"\d+", low))
    words = tuple(w for w in re.findall(r"[a-z]+", low.replace("-", " ")) if w in ORDINAL_WORDS)
    return digits, words


def blocked(a: dict, b: dict) -> str | None:
    """Why the pair can never merge, or None. a and b hold bill_key, name, year, and amendment_ordinal.

    A bill does not continue into a new Lok Sabha, so two keys of different terms are two bills.
    """
    if key_term(a.get("bill_key")) != key_term(b.get("bill_key")):
        return "term"
    if a["year"] != b["year"]:
        return "year"
    if (a.get("amendment_ordinal") or None) != (b.get("amendment_ordinal") or None):
        return "amendment number"
    if number_marks(a["name"])[0] != number_marks(b["name"])[0]:
        return "digits"
    if number_marks(a["name"])[1] != number_marks(b["name"])[1]:
        return "ordinal words"
    return None


def kept_bills(conn) -> dict[int, dict]:
    """Every bill that a kept debate_bills row uses, with its debate titles and summaries."""
    rows = conn.execute(text("""
        SELECT b.id, b.name, b.year, b.bill_key, b.amendment_ordinal,
               array_agg(DISTINCT regexp_replace(coalesce(g.title, ''), '\\s+', ' ', 'g')) AS titles,
               array_remove(array_agg(DISTINCT d.summary), NULL) AS summaries,
               count(DISTINCT d.id) AS n_debates
        FROM bills b
        JOIN debate_bills d ON d.bill_id = b.id AND d.kept
        JOIN debates g ON g.loksabha = d.loksabha AND g.session = d.session AND g.dbslno = d.dbslno
        GROUP BY b.id
    """)).mappings().all()
    return {r["id"]: dict(r) for r in rows}


def candidate_pairs(conn, bills: dict[int, dict]) -> tuple[list[tuple[int, int, float]], dict[str, int]]:
    rows = conn.execute(text("""
        SELECT x.id, y.id, similarity(lower(x.name), lower(y.name))
        FROM bills x JOIN bills y ON x.year = y.year AND x.id < y.id
        WHERE x.id = ANY(:ids) AND y.id = ANY(:ids) AND similarity(lower(x.name), lower(y.name)) >= :s
    """), {"ids": list(bills), "s": MIN_SIMILARITY}).all()
    pairs, why = [], {}
    for a, b, s in rows:
        reason = blocked(bills[a], bills[b])
        if reason:
            why[reason] = why.get(reason, 0) + 1
        else:
            pairs.append((a, b, float(s)))
    return pairs, why


def pair_state(a: dict, b: dict) -> str:
    def one(label: str, x: dict) -> str:
        titles = "\n".join(f"  - {t.strip()[:300]}" for t in x["titles"][:3])
        summary = x["summaries"][0] if x["summaries"] else "(no summary)"
        return f"{label}: {x['name']}, {x['year']}\nDebate titles:\n{titles}\nSummary: {summary}"
    return ("Two bill names from debates of the Lok Sabha, the lower house of the Parliament of India. "
            "Each name has a year, the titles of its debates, and a summary of what the bill does.\n\n"
            + one("Name A", a) + "\n\n" + one("Name B", b))


def read_merges(path: Path = MERGES) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def write_merges(rows: list[dict], path: Path = MERGES) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["key_a", "key_b", "name_a", "name_b", "similarity", "p_same", "p_different", "p_unsure", "decision",
              "judged_by"]
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter="\t", lineterminator="\n")
        w.writeheader()
        for r in sorted(rows, key=lambda r: (r["key_a"], r["key_b"])):
            w.writerow({k: r.get(k, "") for k in fields})


def groups(pairs: list[tuple[str, str]]) -> list[set[str]]:
    """Joins the merged pairs into groups. A chain a-b, b-c is one group."""
    parent: dict[str, str] = {}

    def find(x: str) -> str:
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in pairs:
        parent[find(a)] = find(b)
    out: dict[str, set[str]] = {}
    for x in list(parent):
        out.setdefault(find(x), set()).add(x)
    return [g for g in out.values() if len(g) > 1]


def pick_kept(group: set[str], debates: dict[str, int], ids: dict[str, int]) -> str:
    """The kept key of a group: the most debates, then the lowest bills.id."""
    return min(group, key=lambda k: (-debates.get(k, 0), ids.get(k, 10 ** 9)))


def apply_merges(conn) -> dict[str, int]:
    rows = [row for row in read_merges() if row["decision"] == "merge"]
    crossed = [row for row in rows if key_term(row["key_a"]) != key_term(row["key_b"])]
    rows = [row for row in rows if row not in crossed]
    info = conn.execute(text("""
        SELECT b.bill_key, b.id, count(d.id) FILTER (WHERE d.kept) AS n
        FROM bills b LEFT JOIN debate_bills d ON d.bill_id = b.id GROUP BY b.id
    """)).all()
    ids = {key: i for key, i, _ in info}
    debates = {key: n_debates for key, _, n_debates in info}
    conn.execute(text("UPDATE bills SET merged_into = NULL WHERE merged_into IS NOT NULL"))
    merged = missing = 0
    for group in groups([(row["key_a"], row["key_b"]) for row in rows]):
        if any(key not in ids for key in group):
            missing += 1
            continue
        target = pick_kept(group, debates, ids)
        for key in group - {target}:
            conn.execute(text("UPDATE bills SET merged_into = :t WHERE id = :id"), {"t": ids[target], "id": ids[key]})
            merged += 1
    linked = link_terms(conn)
    return {"merge_rows": len(rows), "skipped_merge_rows_of_two_terms": len(crossed),
            "bills_merged_into_another": merged, "groups_with_a_missing_key": missing,
            "bills_linked_to_the_next_term": linked}


def next_links(bills: list[dict], merge_pairs: list[tuple[str, str]]) -> dict[int, int]:
    """{earlier kept id: later kept id} for two bills of the same name in adjacent terms.

    bills holds one dict for each bills row: id, kept_id, bill_key, year. Two kept bills link when their terms
    are adjacent, their years are equal, and one of their rows has the same name key as a row of the other,
    or the merge file has a "merge" answer for a pair of their rows. A bill with two or more candidates in
    the next term gets no link, because the link would be a guess.
    """
    kept = {}
    for b in bills:
        key = kept.setdefault(b["kept_id"], {"term": None, "year": b["year"], "keys": set()})
        key["keys"].add(b["bill_key"])
        if b["id"] == b["kept_id"]:
            key["term"] = key_term(b["bill_key"])
    owner = {b["bill_key"]: b["kept_id"] for b in bills}
    same = set()
    for a, b in merge_pairs:
        if a in owner and b in owner:
            same.add((owner[a], owner[b]))
            same.add((owner[b], owner[a]))
    found: dict[int, set[int]] = {}
    for earlier_id, earlier in kept.items():
        for later_id, later in kept.items():
            if earlier["term"] is None or later["term"] != earlier["term"] + 1 or earlier["year"] != later["year"]:
                continue
            if {base_key(key) for key in earlier["keys"]} & {base_key(key) for key in later["keys"]} or (earlier_id, later_id) in same:
                found.setdefault(earlier_id, set()).add(later_id)
    return {earlier_id: next(iter(later_ids)) for earlier_id, later_ids in found.items() if len(later_ids) == 1}


def link_terms(conn) -> int:
    """Sets bills.next_id on each kept bill that next_links finds. It calls no model."""
    rows = conn.execute(text("""
        SELECT b.id, coalesce(b.merged_into, b.id) AS kept_id, b.bill_key, b.year
        FROM bills b WHERE EXISTS (SELECT 1 FROM debate_bills d WHERE d.bill_id = b.id AND d.kept)
    """)).mappings().all()
    pairs = [(r["key_a"], r["key_b"]) for r in read_merges() if r["decision"] == "merge"]
    links = next_links([dict(r) for r in rows], pairs)
    conn.execute(text("UPDATE bills SET next_id = NULL WHERE next_id IS NOT NULL"))
    for i, j in links.items():
        conn.execute(text("UPDATE bills SET next_id = :j WHERE id = :i"), {"i": i, "j": j})
    return len(links)


def judge(conn, workers: int) -> dict[str, int]:
    from decision_model import MODEL, DecisionError, api_key, choice_probabilities, choice_q, decide

    bills = kept_bills(conn)
    pairs, why = candidate_pairs(conn, bills)
    old = read_merges()
    done = {(row["key_a"], row["key_b"]) for row in old if row["judged_by"] == f"{MODEL} {QUESTIONS_VERSION}"}
    todo = [(id_a, id_b, similarity) for id_a, id_b, similarity in pairs if (bills[id_a]["bill_key"], bills[id_b]["bill_key"]) not in done]
    key = api_key()
    question = {"same": choice_q("Are Name A and Name B one bill?", SAME)}

    def ask(pair):
        id_a, id_b, similarity = pair
        return pair, decide(pair_state(bills[id_a], bills[id_b]), question, key)

    new, failed = [], 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for fut in as_completed([pool.submit(ask, probs) for probs in todo]):
            try:
                (id_a, id_b, similarity), data = fut.result()
            except DecisionError as exc:
                failed += 1
                print(f"  failed: {str(exc)[:200]}", flush=True)
                continue
            probs = choice_probabilities(data["answers"]["same"], list(SAME))
            new.append({"key_a": bills[id_a]["bill_key"], "key_b": bills[id_b]["bill_key"], "name_a": bills[id_a]["name"],
                        "name_b": bills[id_b]["name"], "similarity": f"{similarity:.2f}", "p_same": f"{probs['same']:.2f}",
                        "p_different": f"{probs['different']:.2f}", "p_unsure": f"{probs['unsure']:.2f}",
                        "decision": "merge" if probs["same"] >= SAME_P else "apart", "judged_by": f"{MODEL} {QUESTIONS_VERSION}"})
    keys = {(row["key_a"], row["key_b"]) for row in new}
    write_merges([row for row in old if (row["key_a"], row["key_b"]) not in keys] + new)
    return {"candidates": len(pairs), "asked": len(todo), "failed": failed,
            "merge": sum(row["decision"] == "merge" for row in new), **{f"blocked_by_{reason.replace(' ', '_')}": v for reason, v in why.items()}}


def bill_summaries(conn) -> dict[int, list[str]]:
    """The distinct summaries of each kept bill, with the summaries of the bills merged into it."""
    rows = conn.execute(text("""
        SELECT coalesce(b.merged_into, b.id) AS kept_id, d.summary
        FROM debate_bills d JOIN bills b ON b.id = d.bill_id
        WHERE d.kept AND d.summary IS NOT NULL
        ORDER BY d.loksabha, d.session, d.dbslno
    """)).all()
    out: dict[int, list[str]] = {}
    for kept_id, summary in rows:
        lst = out.setdefault(kept_id, [])
        if summary.strip() not in lst:
            lst.append(summary.strip())
    return out


def copy_single_summaries(conn) -> dict[str, int]:
    found = bill_summaries(conn)
    single = {i: s[0] for i, s in found.items() if len(s) == 1}
    conn.execute(text("UPDATE bills SET summary = NULL, summary_model_id = NULL "
                      "WHERE summary_model_id IS NULL"))
    for i, s in single.items():
        conn.execute(text("UPDATE bills SET summary = :s, summary_model_id = NULL WHERE id = :i"), {"s": s, "i": i})
    joined = conn.execute(text("SELECT count(*) FROM bills WHERE summary_model_id IS NOT NULL")).scalar()
    return {"bills_with_one_summary_copied": len(single),
            "bills_with_two_or_more_summaries": sum(len(s) > 1 for s in found.values()),
            "of_them_joined_by_a_model": joined}


def join_input(name: str, year: int, summaries: list[str]) -> str:
    lines = "\n".join(f"{i}. {s}" for i, s in enumerate(summaries, 1))
    return f"Bill: {name}, {year}\n\nSummaries from different debates on this bill:\n{lines}\n"


JOIN_SCHEMA = {"type": "object", "properties": {"summary": {"type": "string"}}, "required": ["summary"]}


def join_sample(conn, n: int, model: str) -> list[dict]:
    from scripts.extract_entities import generate
    from tag_embed import api_key

    found = {i: s for i, s in bill_summaries(conn).items() if len(s) > 1}
    todo = conn.execute(text("SELECT id, name, year FROM bills WHERE id = ANY(:ids) AND summary_model_id IS NULL "
                             "ORDER BY md5(id::text) LIMIT :n"), {"ids": list(found), "n": n}).all()
    system = (PROMPTS / f"{SUMMARY_PROMPT_VERSION}.md").read_text(encoding="utf-8")
    key = api_key()
    out = []
    for bid, name, year in todo:
        answer, _ = generate(model, system, join_input(name, year, found[bid]), key, schema=JOIN_SCHEMA)
        summary = (answer.get("summary") or "").strip() or None
        conn.execute(text("UPDATE bills SET summary = :s, summary_model_id = :m WHERE id = :i"),
                     {"s": summary, "m": model_id(conn, model), "i": bid})
        out.append({"bill": f"{name}, {year}", "inputs": found[bid], "joined": summary})
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--candidates", action="store_true")
    mode.add_argument("--judge", action="store_true")
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--summaries", action="store_true")
    mode.add_argument("--join-sample", type=int)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    args = ap.parse_args()
    if args.join_sample is not None and not 1 <= args.join_sample <= MAX_JOIN_SAMPLE:
        ap.error(f"--join-sample must be 1 to {MAX_JOIN_SAMPLE}")
    engine = get_engine()
    if args.candidates:
        with engine.connect() as conn:
            bills = kept_bills(conn)
            pairs, why = candidate_pairs(conn, bills)
        print(f"{len(bills)} kept bills. {len(pairs)} candidate pairs. Blocked: {why}")
        for id_a, id_b, similarity in sorted(pairs, key=lambda p: p[2])[:40]:
            print(f"  {similarity:.2f}  {bills[id_a]['name']}  |  {bills[id_b]['name']}  ({bills[id_a]['year']})")
        return
    with engine.begin() as conn:
        if args.judge:
            result = judge(conn, args.workers)
        elif args.apply:
            result = apply_merges(conn)
        elif args.summaries:
            result = copy_single_summaries(conn)
        else:
            result = {"joined": join_sample(conn, args.join_sample, args.model)}
            for joined_row in result["joined"]:
                print(json.dumps(joined_row, ensure_ascii=False, indent=1))
            result = {"joined": len(result["joined"])}
    print(", ".join(f"{name.replace('_', ' ')}: {v}" for name, v in result.items()))


if __name__ == "__main__":
    main()
