"""Tests for scripts/apply_turn_text_repairs.py: the tracked list of repaired old-font Hindi turns.

tests/data/turn_text_repairs_cases.json holds two real term-13 turns: the garbled text that the
parser writes, and the repaired text from the list. One turn has an LLM repair, one has a
dictionary repair.
"""
import json
import re
from pathlib import Path

import pytest

from scripts.apply_turn_text_repairs import (
    FIELDS,
    TSV,
    decide,
    decode_text,
    encode_text,
    read_rows,
    text_hash,
)

CASES = json.loads((Path(__file__).parent / "data" / "turn_text_repairs_cases.json").read_text(encoding="utf-8"))


def _row(case):
    return {
        "key": tuple(case["key"]),
        "garbled_sha256": text_hash(case["garbled"]),
        "method": case["method"],
        "text": case["repaired"],
    }


@pytest.mark.parametrize(
    "s",
    ["", "plain", "a\nb", "tab\there", "back\\slash", "literal \\n is not a new line", "end\\", "\r\n"],
)
def test_encode_then_decode_gives_the_same_text(s):
    encoded = encode_text(s)
    assert "\n" not in encoded and "\t" not in encoded and "\r" not in encoded
    assert decode_text(encoded) == s


def test_read_rows_reads_an_encoded_file(tmp_path):
    path = tmp_path / "repairs.tsv"
    case = CASES[0]
    line = [*map(str, case["key"]), text_hash(case["garbled"]), case["method"], encode_text(case["repaired"])]
    path.write_text("\t".join(FIELDS) + "\n" + "\t".join(line) + "\n", encoding="utf-8")
    [row] = read_rows(path)
    assert row == _row(case)


def test_read_rows_refuses_an_unknown_method(tmp_path):
    path = tmp_path / "repairs.tsv"
    path.write_text("\t".join(FIELDS) + "\n13\t1\t1\t1\tabc\trepair-guess\tx\n", encoding="utf-8")
    with pytest.raises(SystemExit):
        read_rows(path)


@pytest.mark.parametrize("case", CASES, ids=[c["method"] for c in CASES])
def test_garbled_parser_text_gets_the_repair(case):
    assert decide(case["garbled"], _row(case)) == "apply"


@pytest.mark.parametrize("case", CASES, ids=[c["method"] for c in CASES])
def test_a_second_run_finds_the_turn_done(case):
    assert decide(case["repaired"], _row(case)) == "done"


@pytest.mark.parametrize("case", CASES, ids=[c["method"] for c in CASES])
def test_changed_parser_text_is_skipped(case):
    # A parser change that moves one character must not receive the old repair.
    assert decide(case["garbled"] + " ", _row(case)) == "mismatch"


def test_a_missing_turn_is_reported():
    assert decide(None, _row(CASES[0])) == "missing"


def test_the_tracked_list_is_well_formed():
    rows = read_rows(TSV)
    assert len(rows) == 1413
    assert len({r["key"] for r in rows}) == len(rows)
    assert all(re.fullmatch(r"[0-9a-f]{64}", r["garbled_sha256"]) for r in rows)
    assert all(r["text"].strip() for r in rows)
    by_key = {r["key"]: r for r in rows}
    for case in CASES:
        assert by_key[tuple(case["key"])] == _row(case)
