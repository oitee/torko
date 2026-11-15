import pytest

from pages.bill import OTHERS, TOP_PARTIES, bill_page, reason_rows, split_one_member, member_stance, members_of, party_rows, sample_ids
from pages.speeches import conditions, parse_args
from tests.pages_db import page_conn  # noqa: F401


def row(sid, pid, party, stance, words=100):
    return {"speech_id": sid, "person_id": pid, "party": party, "stance": stance, "words": words}


@pytest.mark.parametrize("stances,expected", [
    (["for", "unclear"], "for"),
    (["against", "against"], "against"),
    (["for", "against"], "mixed"),
    (["for", "mixed"], "for"),
    (["against", "mixed"], "against"),
    (["for", "against", "mixed"], "mixed"),
    (["mixed", "unclear"], "mixed"),
    (["unclear", "unclear"], "unclear"),
])
def test_member_stance_rule(stances, expected):
    assert member_stance(stances) == expected


def test_members_count_once_and_skip_unidentified():
    m = members_of([row(1, 7, "BJP", "for"), row(2, 7, "BJP", "unclear"), row(3, None, None, "against")])
    assert m == {7: {"stance": "for", "party": "BJP"}}


def test_party_rows_put_small_parties_and_no_party_in_others():
    members = {i: {"stance": "for", "party": f"P{i}"} for i in range(TOP_PARTIES + 2)}
    members[100] = {"stance": "against", "party": None}
    rows = party_rows(members)
    assert len(rows) == TOP_PARTIES + 1
    assert rows[-1]["party"] == OTHERS
    assert rows[-1]["members"] == 3 and rows[-1]["no_party"] == 1
    assert rows[-1]["counts"] == {"for": 2, "against": 1, "mixed": 0, "unclear": 0}


def _speech(sid, person, stance, words, own=0, other=0):
    return {"speech_id": sid, "person_id": person, "party": "P", "stance": stance, "words": words,
            "own": own, "other": other}


def test_samples_are_the_clear_speeches_with_the_most_points():
    rows = [_speech(1, 1, "for", 900, own=1), _speech(2, 2, "for", 50, own=4), _speech(3, 3, "for", 5000, own=0, other=3),
            _speech(4, 4, "for", 70, own=4), _speech(5, 5, "for", 60, own=2, other=1), _speech(6, None, "for", 9000, own=9),
            _speech(7, 7, "for", 8000)]
    members = members_of(rows)
    # 3 has only points against; 5 has a point against; 6 has no identified member. A tie in points goes to length.
    assert sample_ids(rows, members) == [("for", 4), ("for", 2), ("for", 1)]
    # A speech with no point comes after the speeches with points.
    assert sample_ids(rows, members, per_stance=4)[-1] == ("for", 7)


def test_a_sample_member_must_have_the_stance_of_the_speech_and_shows_one_time():
    rows = [_speech(1, 1, "for", 100, own=3), _speech(2, 1, "against", 100, own=3),
            _speech(3, 2, "against", 100, own=2), _speech(4, 2, "against", 900, own=1),
            _speech(5, 3, "mixed", 300), _speech(6, 4, "mixed", 400), _speech(7, 4, "for", 10, own=1)]
    members = members_of(rows)
    # Member 1 is mixed (a for and an against speech), but has no mixed speech. Member 4 is for, not mixed.
    assert sample_ids(rows, members) == [("for", 7), ("against", 3), ("mixed", 5)]


def test_bill_filter_on_speech_list():
    f, bad = parse_args(None, {"bill": "4644"})
    assert bad is None and "bill" in conditions(f)


def test_bill_route_on_real_data(page_conn):
    assert bill_page(page_conn, 999999999) is None
    b = bill_page(page_conn, 4644)  # Delimitation Bill, 2026: three debates in April 2026
    if b is None:
        return
    assert b["name"] == "Delimitation Bill" and b["year"] == 2026
    assert sum(b["member_counts"].values()) == b["members"]
    assert sum(p["members"] for p in b["parties"]) == b["members"]
    assert sum(b["speech_counts"].values()) == b["speeches"]
    assert {s["stance"] for s in b["samples"]} <= {"for", "against", "mixed"}


def test_a_bill_of_the_same_name_in_another_term_is_a_different_bill(page_conn):
    # A real case: the 16th Lok Sabha debated a Citizenship (Amendment) Bill, 2019 in January 2019.
    # The 17th Lok Sabha debated a new bill of that name in December 2019. Each one has its own page.
    b = bill_page(page_conn, 4145)
    if b is None:
        return
    assert b["terms"] == [17]
    assert [(o["term"], o["side"]) for o in b["same_name"]] == [(16, "previous")]
    old = bill_page(page_conn, b["same_name"][0]["id"])
    assert old["terms"] == [16]
    assert [(o["id"], o["term"], o["side"]) for o in old["same_name"]] == [(4145, 17, "next")]


def point(group, side, pid, quote, label="L"):
    return {"group": group, "side": side, "label": label, "person_id": pid, "member": f"M{pid}", "party": "P",
            "speech_id": 10 + (pid or 0), "quote": quote}


def test_reasons_count_members_once_and_order_by_members_then_points():
    rows = [point(1, "for", 7, "first"), point(1, "for", 7, "second"), point(1, "for", 8, "x"),
            point(2, "for", 9, "y"), point(2, "for", None, "a"), point(2, "for", None, "b"),
            point(3, "against", 7, "z"), point(4, "unclear", 7, "dropped")]
    r = reason_rows(rows)
    assert [g["id"] for g in r["for"]] == [1, 2]
    one = r["for"][0]
    assert (one["members"], one["points"]) == (2, 3)
    assert [q["quote"] for q in one["quotes"]] == ["first", "x"]  # one quote for each member, the first one
    two = r["for"][1]
    assert (two["members"], two["points"], len(two["quotes"])) == (1, 3, 3)  # each unidentified point shows
    assert [g["id"] for g in r["against"]] == [3]


def test_reasons_on_real_data(page_conn):
    # The 17th Lok Sabha Citizenship (Amendment) Bill, 2019: every point of the bill is in one reason of its side.
    b = bill_page(page_conn, 4145)
    if b is None or not b["reasons"]["against"]:
        return
    n = page_conn.exec_driver_sql(
        "SELECT count(*) FROM speech_arguments WHERE bill_id = 4145 AND bill_argument_id IS NOT NULL").scalar()
    every = [g for part in ("reasons", "reason_others") for side in b[part].values() for g in side]
    assert sum(g["points"] for g in every) == n
    for side in b["reasons"].values():
        keys = [(-g["members"], -g["points"]) for g in side]
        assert keys == sorted(keys)
    for side, rows in b["reason_others"].items():
        assert all(g["members"] <= 1 for g in rows)
        assert not rows or (len(b["reasons"][side]) >= 4 and all(g["members"] >= 2 for g in b["reasons"][side]))


def _r(members, label="R"):
    return {"id": label, "label": label, "members": members, "points": max(members, 1), "quotes": []}


def test_reasons_of_one_member_go_to_the_last_row_when_a_side_has_4_shared_reasons():
    shared = [_r(5, "a"), _r(4, "b"), _r(3, "c"), _r(2, "d")]
    kept, others = split_one_member({"for": shared + [_r(1, "e"), _r(0, "f")], "against": [_r(3, "g")]})
    assert [g["label"] for g in kept["for"]] == ["a", "b", "c", "d"]
    assert [g["label"] for g in others["for"]] == ["e", "f"]
    assert [g["label"] for g in kept["against"]] == ["g"] and others["against"] == []


def test_a_side_where_every_reason_has_one_member_keeps_all_its_reasons():
    kept, others = split_one_member({"for": [_r(1, "a"), _r(1, "b"), _r(0, "c")], "against": []})
    assert [g["label"] for g in kept["for"]] == ["a", "b", "c"] and others["for"] == []
    assert kept["against"] == [] and others["against"] == []


def test_a_side_with_3_shared_reasons_shows_each_point_of_one_member_as_a_reason():
    # The Banning of Unregulated Deposit Schemes Bill, 2018 has 1 shared reason on each side.
    kept, others = split_one_member({"for": [_r(4, "a"), _r(3, "b"), _r(2, "c"), _r(1, "d")]})
    assert [g["label"] for g in kept["for"]] == ["a", "b", "c", "d"] and others["for"] == []
