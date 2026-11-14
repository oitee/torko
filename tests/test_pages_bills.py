from pages.bills import OPPOSED_MIN_MEMBERS, bill_rows, short_lists, term_labels
from tag_search import bill_matches


def test_bill_rows_count_each_member_once():
    rows = [(1, 10, 7, "for"), (1, 11, 7, "against"), (1, 12, 8, "unclear"), (1, 13, None, "against")]
    assert bill_rows(rows) == {1: {"speeches": 4, "members": 2,
                                   "counts": {"for": 0, "against": 0, "mixed": 1, "unclear": 1}}}


def bill(i, members, against=0, term=18, last="2026-01-01", year=2026):
    return {"id": i, "members": members, "term": term, "last_date": last, "year": year,
            "counts": {"for": members - against, "against": against, "mixed": 0, "unclear": 0}}


def test_most_opposed_needs_enough_members():
    small = bill(1, OPPOSED_MIN_MEMBERS - 1, against=OPPOSED_MIN_MEMBERS - 1)
    big = bill(2, OPPOSED_MIN_MEMBERS, against=5)
    assert short_lists([small, big])["most_opposed"] == [2]


def test_term_labels_pick_most_members_in_each_term():
    assert term_labels([bill(1, 30, term=17), bill(2, 40, term=17), bill(3, 3, term=18)]) == [2]


def test_bill_matches_put_exact_name_first():
    bills = [{"id": 1, "name": "Citizenship (Amendment) Bill", "year": 2019, "members": 71, "n_speeches": 148},
             {"id": 2, "name": "Citizenship (Amendment) Bill", "year": 2003, "members": 90, "n_speeches": 10},
             {"id": 3, "name": "Finance Bill", "year": 2019, "members": 30, "n_speeches": 40}]
    assert [r["id"] for r in bill_matches("citizenship amendment bill 2019", bills)] == [1]
    assert [r["id"] for r in bill_matches("citizenship amendment", bills)] == [2, 1]
    assert bill_matches("citizenship", bills)[0]["name"] == "Citizenship (Amendment) Bill, 2003"
