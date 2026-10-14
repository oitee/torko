import csv
import json
import re
from datetime import date
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data" / "party_history"

# The first day of each term and the last sitting in the debates.
TERMS = {13: (date(1999, 10, 20), date(2004, 2, 5)), 14: (date(2004, 6, 2), date(2009, 2, 26)),
         15: (date(2009, 6, 1), date(2014, 2, 21)), 16: (date(2014, 6, 4), date(2019, 2, 13)),
         17: (date(2019, 6, 17), date(2024, 2, 10)), 18: (date(2024, 6, 24), None)}
KINDS = {"election", "by-election", "split", "merger", "expulsion"}


def _events():
    with open(DATA / "party_events.tsv", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def _known_codes():
    codes = set()
    for term in TERMS:
        for m in json.loads((DATA / "raw" / f"sansad_ls{term}.json").read_text(encoding="utf-8")):
            codes.add((m.get("partySname") or "").strip())
    with open(DATA / "party_codes.tsv", encoding="utf-8", newline="") as f:
        codes |= {r["code"].strip() for r in csv.DictReader(f, delimiter="\t")}
    return codes - {"", "Not Available"}


def _members(term):
    return {m["mpsno"] for m in json.loads((DATA / "raw" / f"sansad_ls{term}.json").read_text(encoding="utf-8"))}


def test_events_file_is_not_empty_and_kinds_are_known():
    events = _events()
    assert len(events) > 0
    assert {e["kind"] for e in events} <= KINDS


def test_each_party_code_is_known():
    known = _known_codes()
    assert {e["party"] for e in _events()} <= known


def test_each_member_sat_in_the_term_of_the_event():
    for e in _events():
        assert int(e["mpsno"]) in _members(int(e["term"])), e


def test_an_election_row_has_no_date_and_a_dated_row_falls_inside_its_term():
    for e in _events():
        if e["kind"] == "election":
            assert e["effective_from"] == "", e
            continue
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", e["effective_from"]), e
        start, last = TERMS[int(e["term"])]
        d = date.fromisoformat(e["effective_from"])
        assert start < d and (last is None or d <= last), e


def test_no_two_rows_for_one_member_on_one_date():
    keys = [(e["term"], e["mpsno"], e["kind"] == "election", e["effective_from"]) for e in _events()]
    assert len(keys) == len(set(keys))
