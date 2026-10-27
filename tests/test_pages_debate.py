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


def test_role_in_debate():
    from pages.debate import role_in_debate
    assert role_in_debate(5, 5, None) == "speech"
    assert role_in_debate(None, 5, "presiding") == "interruption"
    assert role_in_debate(None, None, "presiding") == "chair"
    assert role_in_debate(None, None, "crowd") == "between"
    assert role_in_debate(None, None, None) == "between"


def _check(conn, debate_id):
    r = debate_page(conn, debate_id, {})
    places = [t["role_in_debate"] for t in r["turn_list"]]
    assert set(places) <= {"speech", "interruption", "chair", "between"}
    assert places.count("interruption") == sum(s["interruptions"] for s in r["speeches"])
    assert all("inside_speech" in t for t in r["turn_list"] if t["role_in_debate"] == "interruption")
    assert len(r["speeches"]) and all("summary" in s and "tags" in s for s in r["speeches"])
    no_member = sum(1 for s in r["speeches"] if s["member_id"] is None)
    assert sum(p["speeches"] for p in r["people"]) + no_member == len(r["speeches"])
    assert not {s["member_id"] for s in r["silent"]} & {p["id"] for p in r["people"]}
    assert r["id"] not in [x["id"] for x in r["same_day"]]
    return r


def test_debate_new_fields_recent(page_conn):
    r = _check(page_conn, 62933)
    assert len(r["speeches"]) == 29


def test_debate_new_fields_old(page_conn):
    _check(page_conn, 2666)
