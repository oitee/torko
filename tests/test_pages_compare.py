from collections import Counter

import pages.compare as c
from tests.pages_db import page_conn  # noqa: F401


def test_parse_terms():
    assert c.parse_terms("18, 17") == [17, 18]
    assert c.parse_terms("x") is None
    assert c.parse_terms("99") is None
    assert c.parse_terms("") is None


def test_compare_sides_classifies():
    tags = {i: {"tag": f"T{i}", "type": "topic"} for i in (1, 2, 3, 4)}
    ca = Counter({1: 10, 2: 10, 3: 1})
    cb = Counter({1: 9, 2: 1, 4: 12})
    out = c.compare_sides(tags, set(), Counter({1: 1, 2: 1, 3: 1, 4: 1}), 10000, ca, 100, cb, 100, 3)
    assert [r["tag"] for r in out["shared"]] == ["T1"]
    assert [r["tag"] for r in out["only_a"]] == ["T2"]
    assert [r["tag"] for r in out["only_b"]] == ["T4"]
    assert out["n_shared"] == 1


def test_compare_sides_hidden_and_zero_side():
    tags = {1: {"tag": "T1", "type": "topic"}}
    out = c.compare_sides(tags, {1}, Counter(), 0, Counter({1: 5}), 10, Counter(), 0, 3)
    assert out["shared"] == [] and out["only_a"] == []


def test_compare_members_real(page_conn):
    d = c.compare_page(page_conn, {"kind": "member", "a": "3754", "b": "4569"})
    assert d["a"]["name"] == "N K Premachandran" and d["terms"]
    assert d["a_tagged"] > 0 and d["b_tagged"] > 0
    assert d["a_tagged"] <= d["tagged_all"]


def test_compare_parties_real(page_conn):
    d = c.compare_page(page_conn, {"kind": "party", "a": "DMK", "b": "aiadmk", "terms": "15,17"})
    assert d["terms"] == [15, 17] and d["b"]["id"] == "AIADMK"
    assert d["parties"]


def test_compare_unknown_keys(page_conn):
    assert c.compare_page(page_conn, {"kind": "member", "a": "3754", "b": "999999999"}) is None
    assert c.compare_page(page_conn, {"kind": "party", "a": "DMK"}) is None
    assert c.compare_page(page_conn, {"kind": "team", "a": "1", "b": "2"}) is None
    assert c.compare_page(page_conn, {}) is None
