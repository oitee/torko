import pytest

from scripts.merge_bills import blocked, groups, join_input, number_marks, pick_kept


def b(name, year=2009, ordinal=None):
    return {"name": name, "year": year, "amendment_ordinal": ordinal}


@pytest.mark.parametrize("x, y, reason", [
    (b("Appropriation (No. 2) Bill"), b("Appropriation (No. 3) Bill"), "digits"),
    (b("Central Goods and Services Tax (Second Amendment) Bill"), b("Central Goods and Services Tax (Amendment) Bill"),
     "ordinal words"),
    (b("Constitution (One Hundred and Twenty-Eighth Amendment) Bill", 2023, "one hundred and twenty-eighth"),
     b("Constitution (One Hundred and Thirty-First Amendment) Bill", 2023, "one hundred and thirty-first"),
     "amendment number"),
    (b("Constitution (One Hundred and Twenty-Eighth Amendment) Bill", 2023, "one hundred and twenty-eighth"),
     b("Constitution (One Hundred and Thirty-First Amendment) Bill", 2026, "one hundred and thirty-first"), "year"),
    (b("Finance (No. 2) Bill"), b("Finance Bill (No. 2)"), None),
    (b("Streeet Vendors (Protection of Livelihood) Bill"), b("Street Vendors (Protection of Livelihood) Bill"), None),
])
def test_hard_rules(x, y, reason):
    assert blocked(x, y) == reason


def test_number_marks_reads_digits_and_ordinal_words():
    assert number_marks("Constitution (Ninety-Sixth Amendment) Bill") == ((), ("ninety", "sixth"))
    assert number_marks("Appropriation (Railways) No. 6 Bill") == (("6",), ())


def test_a_chain_of_pairs_is_one_group():
    assert sorted(map(sorted, groups([("a", "b"), ("b", "c"), ("x", "y")]))) == [["a", "b", "c"], ["x", "y"]]


def test_the_kept_bill_has_the_most_debates_then_the_lowest_id():
    assert pick_kept({"a", "b", "c"}, {"a": 1, "b": 3, "c": 3}, {"a": 1, "b": 9, "c": 5}) == "c"


def test_join_input_numbers_each_summary():
    text = join_input("Wakf (Amendment) Bill", 2010, ["One.", "Two."])
    assert "Wakf (Amendment) Bill, 2010" in text and "1. One." in text and "2. Two." in text
