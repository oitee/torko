from __future__ import annotations

import json
import sys
from pathlib import Path

import requests

ROOT_FOR_IMPORT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_FOR_IMPORT))

from party_history import parse_wiki_members, party_titles  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "party_history" / "raw"
TERMS = (13, 14, 15, 16, 17, 18)

MEMBER_API = "https://sansad.in/api_ls/member"
WIKI_API = "https://en.wikipedia.org/w/api.php"
USER_AGENT = "torko-research/0.1 (https://github.com/oitee/torko)"

# The fields kept from each sansad.in row. Addresses, phones, and emails are not kept.
SANSAD_FIELDS = (
    "mpsno", "initial", "firstName", "lastName", "mpFirstLastName", "gender",
    "stateName", "constName", "partySname", "partyFname", "lastLoksabha", "lsExpr",
)


def ordinal(n: int) -> str:
    return f"{n}th"  # 13th to 18th all take "th"


def fetch_sansad(term: int) -> list[dict]:
    resp = requests.get(MEMBER_API, params={"size": 2000, "page": 1, "loksabha": term}, timeout=60)
    resp.raise_for_status()
    body = resp.json()
    rows = body.get("membersDtoList", [])
    total = body["metaDatasDto"]["totalElements"]
    if len(rows) != total:
        raise SystemExit(f"term {term}: got {len(rows)} rows, API says {total}")
    return [{k: r.get(k) for k in SANSAD_FIELDS} for r in rows]


def fetch_wiki(term: int) -> tuple[int, str]:
    page = f"List of members of the {ordinal(term)} Lok Sabha"
    resp = requests.get(
        WIKI_API,
        params={"action": "parse", "page": page, "prop": "text|revid",
                "format": "json", "redirects": 1},
        headers={"User-Agent": USER_AGENT},
        timeout=60,
    )
    resp.raise_for_status()
    parsed = resp.json()["parse"]
    return parsed["revid"], parsed["text"]["*"]


def resolve_redirects(titles: list[str]) -> dict[str, str]:
    """A title that is not a redirect maps to itself."""
    out: dict[str, str] = {}
    for i in range(0, len(titles), 50):
        batch = titles[i:i + 50]
        resp = requests.get(
            WIKI_API,
            params={"action": "query", "titles": "|".join(batch), "redirects": 1, "format": "json"},
            headers={"User-Agent": USER_AGENT},
            timeout=60,
        )
        resp.raise_for_status()
        q = resp.json()["query"]
        norm = {n["from"]: n["to"] for n in q.get("normalized", [])}
        red = {r["from"]: r["to"] for r in q.get("redirects", [])}
        for t in batch:
            n = norm.get(t, t)
            out[t] = red.get(n, n)
    return out


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    for term in TERMS:
        rows = fetch_sansad(term)
        rows.sort(key=lambda r: r["mpsno"])
        (RAW / f"sansad_ls{term}.json").write_text(
            json.dumps(rows, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        revid, text = fetch_wiki(term)
        (RAW / f"wiki_ls{term}.html").write_text(
            f"<!-- revid {revid} -->\n{text}", encoding="utf-8")
        print(f"LS{term}: sansad {len(rows)} members, wikipedia revision {revid}", flush=True)

    titles = sorted({r.title for term in TERMS
                     for r in parse_wiki_members((RAW / f"wiki_ls{term}.html").read_text(encoding="utf-8"), term)
                     if r.title})
    titles = sorted(set(titles) | {t for term in TERMS
                                   for t in party_titles((RAW / f"wiki_ls{term}.html").read_text(encoding="utf-8"))})
    redirects = resolve_redirects(titles)
    (RAW / "wiki_redirects.json").write_text(
        json.dumps(redirects, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"redirects: {len(titles)} titles, {sum(1 for k, v in redirects.items() if k != v)} redirect", flush=True)


if __name__ == "__main__":
    sys.exit(main())
