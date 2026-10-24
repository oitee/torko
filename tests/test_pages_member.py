import pages.member as m
from pages.common import speech_tags_cte
from tests.pages_db import page_conn  # noqa: F401


def test_split_name():
    assert m.split_name("Ravindra Shukla Alias Ravi Kishan") == ("Ravindra Shukla", "Ravi Kishan")
    assert m.split_name("N K Premachandran") == ("N K Premachandran", None)


def test_lift_is_share_over_share():
    assert m.lift(10, 100, 50, 1000) == 2.0


def test_pick_typical_rules():
    gtags = {
        1: {"tag": "Railways", "type": "topic", "n": 100},
        2: {"tag": "Kerala", "type": "place", "n": 80},
        3: {"tag": "Speaker", "type": "role", "n": 90},
        4: {"tag": "Rare", "type": "topic", "n": 5},
        5: {"tag": "Everything", "type": "topic", "n": 9000},
        6: {"tag": "Water", "type": "topic", "n": 100},
    }
    typical, places = m.pick_typical([(1, 5), (2, 7), (3, 9), (4, 9), (5, 9), (6, 2)], gtags, 10000, 50)
    assert [t["name"] for t in typical] == ["Railways"]
    assert [p["name"] for p in places] == ["Kerala"]
    assert typical[0]["lift"] == 10.0


def test_party_path_removes_repeats():
    terms = [{"parties": ["INC"]}, {"parties": ["INC", "BJD"]}, {"parties": ["BJD"]}]
    assert m.party_path(terms) == ["INC", "BJD"]


def test_restricted_cte_adds_condition():
    assert "AND si.speech_id = 1" in speech_tags_cte("si.speech_id = 1")


def test_member_page_real(page_conn):
    d = m.member_page(page_conn, "97", {})
    assert d["name"] == "Adhir Ranjan Chowdhury"
    assert d["speeches"] > 1000 and 0 < d["tagged_speeches"] <= d["speeches"]
    assert d["typical"] and all(t["n"] <= t["all"] for t in d["typical"])
    assert len(d["marks"]) <= d["speeches"]
    assert d["recent"] and "counts_note" in d


def test_member_page_unknown(page_conn):
    assert m.member_page(page_conn, "99999999", {}) is None
    assert m.member_page(page_conn, "abc", {}) is None
