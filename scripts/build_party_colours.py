"""Write data/party_history/party_colours.tsv: one colour for each party code, from the Wikipedia member lists.

Each saved list (raw/wiki_ls<N>.html) has a legend for each state: a colour box, then a link to the party article.
The article is matched to a party code through the names that the party history build already uses.
A code with more than one colour takes the colour of the latest term. A legend row that is not a party
(an alliance, "Others", "Casual vacancy") has no code, so it is left out. A party with no legend gets no row.
"""
from __future__ import annotations

import csv
import html
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "party_history"
RAW = DATA / "raw"
OUT = DATA / "party_colours.tsv"

LEGEND = re.compile(r'class="legend-color"[^>]*background-color:\s*(#[0-9A-Fa-f]{6})[^>]*>.*?'
                    r'<a href="/wiki/([^"#]+)"', re.S)


def legend_colours(page: str, redirects: dict[str, str]) -> list[tuple[str, str]]:
    """Return (article title, colour) for each legend entry of one member list page. Colours are upper case."""
    out = []
    for colour, href in LEGEND.findall(page):
        title = unquote(html.unescape(href)).replace("_", " ")
        out.append((redirects.get(title, title), colour.upper()))
    return out


def article_codes() -> dict[str, str]:
    """Return the party code of each party article or full name that the party history data knows."""
    counts: dict[str, Counter] = defaultdict(Counter)
    with open(DATA / "results" / "speaker_terms.tsv", encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            if r["wiki_party"] and r["party"]:
                counts[r["wiki_party"]][r["party"]] += 1
    with open(DATA / "party_codes.tsv", encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            if r["code"].strip():
                counts[r["wiki_party"].strip()][r["code"].strip()] += 1
    for path in RAW.glob("sansad_ls*.json"):
        for m in json.loads(path.read_text(encoding="utf-8")):
            name, code = (m.get("partyFname") or "").strip(), (m.get("partySname") or "").strip()
            if name and code and code != "Not Available":
                counts[re.sub(r"\s+", " ", name)][code] += 1
    return {name: c.most_common(1)[0][0] for name, c in counts.items()}


def pick_colours(found: list[tuple[int, str, str]], codes: dict[str, str]) -> dict[str, tuple[str, str, int]]:
    """Return code -> (colour, article, term), from (term, article, colour) rows. The latest term wins."""
    out: dict[str, tuple[str, str, int]] = {}
    for term, article, colour in sorted(found):
        code = codes.get(article)
        if code:
            out[code] = (colour, article, term)
    return out


def main() -> None:
    redirects = json.loads((RAW / "wiki_redirects.json").read_text(encoding="utf-8"))
    found = []
    for path in sorted(RAW.glob("wiki_ls*.html")):
        term = int(re.search(r"ls(\d+)", path.name).group(1))
        found += [(term, a, c) for a, c in legend_colours(path.read_text(encoding="utf-8"), redirects)]
    colours = pick_colours(found, article_codes())
    with open(OUT, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["code", "colour", "wiki_article", "term"])
        for code in sorted(colours):
            w.writerow([code, *colours[code]])
    print(f"legend entries: {len(found)}, party colours: {len(colours)}", flush=True)


if __name__ == "__main__":
    sys.exit(main())
