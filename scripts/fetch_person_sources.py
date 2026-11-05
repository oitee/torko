#!/usr/bin/env python3
"""Save the Lok Sabha and Rajya Sabha member lists of sansad.in as two small tracked files.

The files keep only the fields that identify a person. They leave out addresses, telephone
numbers, and email addresses. The Rajya Sabha list gives only the latest term and party of a
member, so use it for identity, not for the party in a past term.

    python3 scripts/fetch_person_sources.py
"""
from __future__ import annotations

import csv
from pathlib import Path

import requests

OUT = Path(__file__).resolve().parent.parent / "data" / "person_sources"
LS_URL = "https://sansad.in/api_ls/member"
RS_URL = "https://sansad.in/api_rs/member/sitting-members"
LS_FIELDS = {"mpsno": "mpsno", "name": "mpFirstLastName", "last_term": "lastLoksabha", "terms": "lsExpr",
             "party": "partySname", "state": "stateName", "seat": "constName"}
RS_FIELDS = {"mpsno": "mpsno", "name": "name", "name_hindi": "hname", "latest_term": "term",
             "term_count": "termCount", "latest_party": "partyCode", "latest_state": "state", "status": "status"}


def trim(record: dict, fields: dict[str, str]) -> dict:
    return {out: " ".join(str(record.get(src) or "").split()) for out, src in fields.items()}


def write(path: Path, records: list[dict], fields: dict[str, str]) -> None:
    rows = sorted((trim(r, fields) for r in records), key=lambda r: int(r["mpsno"]))
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(fields), delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print(f"{path.name}: {len(rows)} rows", flush=True)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    ls = requests.get(LS_URL, params={"size": 6000, "page": 1}, timeout=120)
    ls.raise_for_status()
    write(OUT / "lok_sabha_members.tsv", ls.json()["membersDtoList"], LS_FIELDS)
    rs = requests.get(RS_URL, params={"size": 3000, "page": 1}, timeout=120)
    rs.raise_for_status()
    write(OUT / "rajya_sabha_members.tsv", rs.json()["records"], RS_FIELDS)


if __name__ == "__main__":
    main()
