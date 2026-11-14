import pytest

from scripts.merge_bills import blocked, groups, join_input, next_links, number_marks, pick_kept


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
    # A real case: the merge step joined the 14th and the 15th Lok Sabha bills of this name.
    ({**b("Indian Trusts (Amendment)"), "bill_key": "indiantrustsamendment-2009-ls14"},
     {**b("Indian Trusts (Amendment) Bill"), "bill_key": "indiantrustsamendmentbill-2009-ls15"}, "term"),
    ({**b("Indian Trusts (Amendment)"), "bill_key": "indiantrustsamendment-2009-ls15"},
     {**b("Indian Trusts (Amendment) Bill"), "bill_key": "indiantrustsamendmentbill-2009-ls15"}, None),
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


def row(i, key, kept=None, year=2019):
    return {"id": i, "kept_id": kept or i, "bill_key": key, "year": year}


def test_the_same_name_in_the_next_term_links_the_two_bills():
    # A real case: the Citizenship (Amendment) Bill of January 2019 and the new bill of December 2019.
    rows = [row(4145, "citizenshipamendmentbill-2019-ls17"), row(9001, "citizenshipamendmentbill-2019-ls16")]
    assert next_links(rows, []) == {9001: 4145}


def test_a_merge_answer_links_two_spellings_in_adjacent_terms():
    rows = [row(3279, "indiantrustsamendment-2009-ls14", year=2009),
            row(3305, "indiantrustsamendmentbill-2009-ls15", year=2009)]
    pairs = [("indiantrustsamendment-2009-ls14", "indiantrustsamendmentbill-2009-ls15")]
    assert next_links(rows, []) == {}
    assert next_links(rows, pairs) == {3279: 3305}


def test_a_merged_spelling_counts_for_its_kept_bill():
    rows = [row(1, "abill-2009-ls14", year=2009), row(2, "a-2009-ls14", kept=1, year=2009),
            row(3, "a-2009-ls15", year=2009)]
    assert next_links(rows, []) == {1: 3}


def test_no_link_across_a_gap_a_year_or_two_candidates():
    assert next_links([row(1, "x-2019-ls15"), row(2, "x-2019-ls17")], []) == {}
    assert next_links([row(1, "x-2019-ls16"), row(2, "x-2020-ls17", year=2020)], []) == {}
    rows = [row(1, "x-2019-ls16"), row(2, "x-2019-ls17"), row(3, "xbill-2019-ls17")]
    assert next_links(rows, [("x-2019-ls16", "xbill-2019-ls17")]) == {}
