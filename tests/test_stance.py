import pytest

import stance as st


def pair(**kw):
    base = {"title": "Waqf (Amendment) Bill, 2024", "debate_date": "2024-08-08", "bill": "Waqf (Amendment) Bill, 2024",
            "bill_summary": "The Bill amends the Waqf Act.", "other_bills": [], "member": "A Member"}
    return base | kw


def test_state_names_the_bill_and_the_speech():
    s = st.state(pair(), "I oppose this Bill.")
    assert "Bill asked about: Waqf (Amendment) Bill, 2024" in s
    assert "What the bill does: The Bill amends the Waqf Act." in s
    assert "Other bills of this debate: none" in s
    assert s.endswith("Speech:\nI oppose this Bill.")


def test_state_with_no_summary_uses_the_name_only():
    assert "(no summary: only the name of the bill is known)" in st.state(pair(bill_summary=None), "x")


def test_state_lists_the_other_bills_of_a_clubbed_debate():
    s = st.state(pair(other_bills=["Union Territories Laws (Amendment) Bill, 2024"]), "x")
    assert "Other bills of this debate: Union Territories Laws (Amendment) Bill, 2024" in s


def test_state_marks_a_summary_in_place_of_the_speech():
    assert "Summary of the speech (the speech is too long to show):\nshort" in st.state(pair(), "short", "summary")


def test_questions_name_the_bill_and_ask_three_things():
    qs = st.questions("Waqf (Amendment) Bill, 2024")
    assert set(qs) == {"stance", "reasons", "on_bill"}
    assert "«Waqf (Amendment) Bill, 2024»" in qs["stance"]["instructions"]
    assert list(qs["stance"]["criteria"]) == st.STANCES


def test_parse_reads_the_three_answers():
    got = st.parse({"stance": {"probabilities": {"for": 0.8, "against": 0.1, "mixed": 0.05, "unclear": 0.05}},
                    "reasons": {"probabilities": {"0": 0.1, "1": 0.2, "2": 0.3, "3": 0.4}},
                    "on_bill": {"probabilities": {"most": 1.0}}})
    assert got["stance_p"]["for"] == 0.8
    assert got["reasons_p"] == [0.1, 0.2, 0.3, 0.4]
    assert got["on_bill_p"] == [0, 0, 0, 1.0, 0]


@pytest.mark.parametrize("probs,expected", [
    ({"for": 0.8, "against": 0.1, "mixed": 0.05, "unclear": 0.05}, "for"),
    ({"for": 0.5, "against": 0.4, "mixed": 0.05, "unclear": 0.05}, "unclear"),
    ({"for": 0.1, "against": 0.1, "mixed": 0.7, "unclear": 0.1}, "mixed"),
])
def test_pick_stance_needs_the_limit(probs, expected):
    assert st.pick_stance(probs, 0.6) == expected


@pytest.mark.parametrize("stances,expected", [
    (["for", "against"], "mixed"),
    (["for", "mixed"], "for"),
    (["against", "mixed"], "against"),
    (["unclear", "against"], "against"),
    (["unclear", "unclear"], "unclear"),
    (["mixed"], "mixed"),
    (["for", "against", "mixed"], "mixed"),
])
def test_join_stances_of_one_member(stances, expected):
    assert st.join_stances(stances) == expected
