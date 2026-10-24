from pages.debate import debate_page, is_listed, kind_counts, official_list, tokens, turn_kind
from tests.pages_db import page_conn  # noqa: F401


def test_tokens_drop_titles():
    assert tokens("Shri A. K. Singh") == {"singh"}


def test_official_list_skips_bad_entries():
    assert official_list([{"mpCode": 5, "mpName": " A  B "}, "x"]) == [{"code": "5", "name": "A B"}]
    assert official_list(None) == []


def test_is_listed_by_code_and_name():
    off = [{"code": "7", "name": "Dr. Ravi Kumar"}]
    assert is_listed(7, "X", set(), off)
    assert is_listed(1, "Ravi Kumar", set(), off)
    assert not is_listed(1, "Sita Devi", set(), off)


def test_turn_kind_and_counts():
    assert turn_kind("A", None) == "member"
    assert turn_kind(None, "crowd") == "crowd"
    assert turn_kind(None, None) == "unattributed"
    assert kind_counts([{"kind": "member"}, {"kind": "member"}, {"kind": "crowd"}]) == {"member": 2, "crowd": 1}


def test_debate_route(page_conn):
    r = debate_page(page_conn, 62933, {})
    assert r["turn_count"] == len(r["turn_list"]) > 50
    assert sum(r["turn_kinds"].values()) == r["turn_count"]
    assert any(not t["attributed"] for t in r["turn_list"])
    assert r["people"] and r["tags"]


def test_debate_unknown(page_conn):
    assert debate_page(page_conn, -5, {}) is None
