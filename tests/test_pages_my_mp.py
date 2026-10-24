from pages.my_mp import count_tags, group_members, my_mp_page, norm, rank_seats
from tests.pages_db import page_conn  # noqa: F401


def test_rank_seats_order():
    names = ["South Delhi", "Delhi", "Delhi Sadar", "Mumbai"]
    assert rank_seats(names, "delhi") == ["Delhi", "Delhi Sadar", "South Delhi"]
    assert rank_seats(names, "") == []
    assert norm(" Dr.  X-y ") == "dr x y"


def test_group_members_current_and_older():
    rows = [{"person_id": 1, "term": 17, "party": "A", "member": "M1"},
            {"person_id": 1, "term": 18, "party": "B", "member": "M1"},
            {"person_id": 2, "term": 15, "party": "C", "member": "M2"}]
    cur, old = group_members(rows, 18)
    assert [p["member"] for p in cur] == ["M1"] and cur[0]["terms"] == [17, 18] and cur[0]["party"] == "B"
    assert [p["member"] for p in old] == ["M2"]


def test_count_tags():
    out = count_tags({1: 9, 2: 9}, [{"speech_id": 1, "tag": "T", "type": "topic"},
                                    {"speech_id": 2, "tag": "T", "type": "topic"}])
    assert out == [{"person_id": 9, "tag": "T", "type": "topic", "n": 2}]


def test_my_mp_route(page_conn):
    r = my_mp_page(page_conn, {"q": "gorakh"})
    assert r["seat_count"] == 1 and r["seats"][0]["seat"] == "Gorakhpur"
    assert r["seats"][0]["current"][0]["member"]


def test_my_mp_unknown_and_empty(page_conn):
    assert my_mp_page(page_conn, {"q": "zzzzqq"})["seats"] == []
    assert my_mp_page(page_conn, {})["seats"] == []
