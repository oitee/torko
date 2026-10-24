from collections import Counter

import pages.party as p
from tests.pages_db import page_conn  # noqa: F401


def test_lift_rows_order_and_filters():
    tags = {1: {"tag": "A", "type": "topic"}, 2: {"tag": "B", "type": "topic"},
            3: {"tag": "C", "type": "place"}, 4: {"tag": "D", "type": "topic"}}
    party = Counter({1: 10, 2: 10, 3: 10, 4: 2})
    allc = Counter({1: 100, 2: 50, 3: 10, 4: 2})
    rows = p.lift_rows(party, 100, allc, 1000, tags, 6, {"topic"})
    assert [r["tag"] for r in rows] == ["B", "A"]
    assert rows[0]["lift"] == 2.0
    assert [r["tag"] for r in p.lift_rows(party, 100, allc, 1000, tags, 6, {"topic"}, skip={2})] == ["A"]


def test_general_tags():
    assert p.general_tags(Counter({1: 40, 2: 10}), 1000) == {1}


def test_party_page_real(page_conn):
    d = p.party_page(page_conn, "bjp", {})
    assert d["code"] == "BJP"
    assert d["total_tagged"] > 10000 and d["total_tagged"] <= d["all_tagged"]
    assert [t["term"] for t in d["terms"]] == [13, 14, 15, 16, 17, 18]
    assert all(t["tagged"] <= t["all_tagged"] for t in d["terms"])
    assert d["typical_all"] and d["top3"] and "counts_note" in d


def test_party_page_unknown(page_conn):
    assert p.party_page(page_conn, "NO-SUCH-PARTY", {}) is None
