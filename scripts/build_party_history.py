"""
Build the party and the constituency of each member in each Lok Sabha term (LS 13 to 18).
This script calls no network and writes nothing to the database.

Input (read only, made by scripts/fetch_party_sources.py):
  - data/party_history/raw/sansad_ls<N>.json   who sat in term N, with the sansad.in member code
  - data/party_history/raw/wiki_ls<N>.html     the Wikipedia list of members of term N
  - data/party_history/raw/wiki_redirects.json link title -> article title
  - data/party_history/party_codes.tsv         hand map: Wikipedia party name -> party code

Output (data/party_history/results/):
  - speaker_terms.tsv  one row for each (member, term) on the sansad.in lists. A row with
                       method 'none' has no Wikipedia match, so its party is not known.
  - rejects.tsv        the candidate pairs that the matcher refused, with the reason
  - report.md          counts for each term and each method

Rules (see party_history.py):
  - Names are compared only inside one term.
  - A pair is kept only when each side is the other's single best candidate.
  - In the member's last term, sansad.in knows the seat. A pair in another seat is never kept.
  - A Wikipedia article that matches two member codes keeps only seat-confirmed matches.
  - Two fill steps follow. A member with one article in other terms takes the free row with
    that article. In the last term, a member takes the only free row in the sansad.in seat.
  - The party is the first party on the row: the party at the general election or by-election.
  - The constituency is the Wikipedia spelling. It is for matching only. No business logic may
    use it, because spellings differ across sources and across delimitations.

Run from the repo root:

    python3 -I scripts/build_party_history.py
"""
from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import party_history as ph  # noqa: E402

DATA = ROOT / "data" / "party_history"
RAW = DATA / "raw"
RESULTS = DATA / "results"
TERMS = (13, 14, 15, 16, 17, 18)

COLUMNS = ["term", "mpsno", "sansad_name", "last_term", "method", "score", "wiki_name",
           "wiki_title", "state", "constituency", "wiki_party", "party", "other_parties"]


def _key(name: str) -> str:
    return re.sub(r"[^a-z]", "", name.lower())


def load_party_codes(members_by_term: dict[int, list[dict]]) -> dict[str, str | None]:
    codes: dict[str, str | None] = {}
    for members in members_by_term.values():
        for m in members:
            if m.get("partyFname") and m.get("partySname"):
                codes[_key(m["partyFname"])] = m["partySname"].strip()
    with open(DATA / "party_codes.tsv", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            codes[_key(row["wiki_party"])] = row["code"].strip() or None
    return codes


def build() -> tuple[list[dict], list[dict]]:
    redirects = json.loads((RAW / "wiki_redirects.json").read_text(encoding="utf-8"))
    members_by_term: dict[int, list[dict]] = {}
    rows_by_term: dict[int, list[ph.WikiRow]] = {}
    matches: list[ph.Match] = []
    rejects: list[dict] = []
    for term in TERMS:
        members_by_term[term] = json.loads((RAW / f"sansad_ls{term}.json").read_text(encoding="utf-8"))
        rows_by_term[term] = ph.parse_wiki_members(
            (RAW / f"wiki_ls{term}.html").read_text(encoding="utf-8"), term, redirects)
        got, refused = ph.match_term(members_by_term[term], rows_by_term[term], term)
        matches += got
        rejects += refused
    matches, dropped, bad = ph.check_articles(matches)
    rejects += dropped
    matches += ph.fill_by_article(matches, members_by_term, rows_by_term, bad)
    matches += ph.fill_by_seat(matches, members_by_term, rows_by_term)

    codes = load_party_codes(members_by_term)
    unknown = sorted({m.row.party for m in matches if _key(m.row.party) not in codes})
    if unknown:
        raise SystemExit("party names with no code, add them to party_codes.tsv: " + "; ".join(unknown))

    by_pair = {(m.row.term, m.mpsno): m for m in matches}
    if len(by_pair) != len(matches):
        raise SystemExit("a member has two matches in one term")
    out: list[dict] = []
    for term in TERMS:
        for mem in members_by_term[term]:
            m = by_pair.get((term, mem["mpsno"]))
            row = {"term": term, "mpsno": mem["mpsno"], "sansad_name": mem["mpFirstLastName"],
                   "last_term": mem["lastLoksabha"], "method": "none", "score": "",
                   "wiki_name": "", "wiki_title": "", "state": "", "constituency": "",
                   "wiki_party": "", "party": "", "other_parties": ""}
            if m is not None:
                party = codes[_key(m.row.party)]
                others = [codes.get(_key(p)) or p for p in m.row.parties[1:]]
                row.update(method=m.method, score=m.score, wiki_name=m.row.name,
                           wiki_title=m.row.title, state=m.row.state, constituency=m.row.seat,
                           wiki_party=m.row.party, party=party or "",
                           other_parties="; ".join(o for o in others if o and o != party))
            out.append(row)
    return out, rejects


def write(rows: list[dict], rejects: list[dict]) -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    with open(RESULTS / "speaker_terms.tsv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    with open(RESULTS / "rejects.tsv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["term", "mpsno", "reason", "detail"], delimiter="\t",
                           lineterminator="\n")
        w.writeheader()
        w.writerows(sorted(rejects, key=lambda r: (r["term"], r["mpsno"])))

    lines = ["# Party history build report", "",
             "Counted over: every (member, term) pair on the sansad.in member lists for LS 13 to 18.",
             "A match is a pair of a sansad.in member and a Wikipedia row. It is not a checked fact.", "",
             "| Term | Members | Matched | name+seat | name | article | seat | No match | Party not known |",
             "|---|---|---|---|---|---|---|---|---|"]
    for term in TERMS:
        t = [r for r in rows if r["term"] == term]
        c = Counter(r["method"] for r in t)
        matched = len(t) - c["none"]
        noparty = sum(1 for r in t if r["method"] != "none" and not r["party"])
        lines.append(f"| {term} | {len(t)} | {matched} | {c['name+seat']} | {c['name']} | "
                     f"{c['article']} | {c['seat']} | {c['none']} | {noparty} |")
    total = len(rows)
    matched = sum(1 for r in rows if r["method"] != "none")
    lines += ["", f"Total: {matched} of {total} pairs matched ({matched / total:.1%}).",
              f"Rows with a second party on Wikipedia (a change inside the term): "
              f"{sum(1 for r in rows if r['other_parties'])}.",
              f"Rejected candidate pairs: {len(rejects)} "
              f"({', '.join(f'{k}: {v}' for k, v in Counter(r['reason'] for r in rejects).most_common())}).", ""]
    (RESULTS / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


def main() -> None:
    rows, rejects = build()
    write(rows, rejects)


if __name__ == "__main__":
    sys.exit(main())
