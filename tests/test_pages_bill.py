import pytest

from pages.bill import OTHERS, TOP_PARTIES, bill_page, reason_rows, member_stance, members_of, party_rows, sample_ids
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


def test_sample_is_longest_speech_of_leading_party():
    rows = [row(1, 1, "A", "for", 900), row(2, 2, "B", "for", 50), row(3, 3, "B", "for", 60),
            row(4, 4, "C", "against", 10), row(5, None, None, "against", 5000)]
    assert sample_ids(rows, per_stance=1) == [("for", 3), ("against", 4)]
    assert sample_ids(rows) == [("for", 3), ("for", 1), ("against", 4)]


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
    assert sum(g["points"] for side in b["reasons"].values() for g in side) == n
    for side in b["reasons"].values():
        keys = [(-g["members"], -g["points"]) for g in side]
        assert keys == sorted(keys)
