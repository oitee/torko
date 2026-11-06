from collections import Counter

import pages.party as p
from tests.pages_db import page_conn  # noqa: F401


def test_rank_rows_order_and_filters():
    tags = {1: {"tag": "A", "type": "topic"}, 2: {"tag": "B", "type": "topic"},
            3: {"tag": "C", "type": "place"}, 4: {"tag": "D", "type": "topic"}, 5: {"tag": "E", "type": "topic"}}
    # E has the highest lift (10) but few speeches. B has a lower lift (2.5) on many more speeches, so more extra speeches.
    party = Counter({1: 10, 2: 50, 3: 10, 4: 2, 5: 8})
    allc = Counter({1: 100, 2: 200, 3: 10, 4: 2, 5: 8})
    rows = p.rank_rows(party, 100, allc, 1000, tags, 6, {"topic"})
    assert [r["tag"] for r in rows] == ["B", "E"]  # A has extra 0, so it is left out
    assert rows[0]["extra"] == 30.0 and rows[0]["lift"] == 2.5
    assert rows[1]["lift"] == 10.0
    assert [r["tag"] for r in p.rank_rows(party, 100, allc, 1000, tags, 6, {"topic"}, skip={2})] == ["E"]


def test_rank_rows_needs_enough_members():
    tags = {1: {"tag": "A", "type": "topic"}, 2: {"tag": "B", "type": "topic"}}
    party, allc = Counter({1: 20, 2: 20}), Counter({1: 20, 2: 20})
    rows = p.rank_rows(party, 100, allc, 1000, tags, 6, {"topic"}, members={1: 1, 2: 4}, min_members=3)
    assert [(r["tag"], r["members"]) for r in rows] == [("B", 4)]


def test_general_tags():
    assert p.general_tags(Counter({1: 40, 2: 10}), 1000) == {1}


def test_party_page_real(page_conn):
    d = p.party_page(page_conn, "bjp", {})
    assert d["code"] == "BJP"
    assert d["total_tagged"] > 10000 and d["total_tagged"] <= d["all_tagged"]
    assert [t["term"] for t in d["terms"]] == [13, 14, 15, 16, 17, 18]
    assert all(t["tagged"] <= t["all_tagged"] for t in d["terms"])
    assert d["typical_all"] and d["top3"] and "counts_note" in d
    # Each typical subject has enough members and more speeches than the House rate predicts.
    assert all(r["members"] >= p.MIN_MEMBERS and r["extra"] > 0 for r in d["typical_all"])
    assert [r["extra"] for r in d["typical_all"]] == sorted((r["extra"] for r in d["typical_all"]), reverse=True)


def test_party_page_unknown(page_conn):
    assert p.party_page(page_conn, "NO-SUCH-PARTY", {}) is None


def test_party_page_recent_speeches(page_conn):
    d = p.party_page(page_conn, "bjp", {})
    assert 0 < len(d["recent"]) <= p.RECENT
    assert [r["date"] for r in d["recent"]] == sorted((r["date"] for r in d["recent"]), reverse=True)
    assert all(r["party"] == "BJP" for r in d["recent"])
