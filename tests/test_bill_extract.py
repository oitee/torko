import json
from pathlib import Path

import pytest

import bill_extract as be

DATA = Path(__file__).parent / "data" / "bills"


def frozen(name):
    return json.loads((DATA / f"{name}.json").read_text(encoding="utf-8"))


def turn(seq, words, speech_id=None, label="A"):
    return {"seq": seq, "label": label, "text": " ".join(f"w{seq}" for _ in range(words)), "speech_id": speech_id}


# ---------------------------------------------------------------- the input

@pytest.mark.parametrize("name", ["normal", "clubbed", "code"])
def test_input_of_frozen_debates_does_not_change(name):
    case = frozen(name)
    assert be.input_text(case["debate"]) == case["expected_input"]


def test_clubbed_debate_input_holds_all_three_bill_names():
    body = be.norm(frozen("clubbed")["expected_input"])
    for bill in ("constitution (one hundred and thirty-first amendment) bill, 2026",
                 "union territories laws (amendment) bill, 2026", "delimitation bill, 2026"):
        assert bill in body


def test_title_is_one_line():
    body = frozen("code")["expected_input"]
    first = body.splitlines()[0]
    assert first.startswith("Title: Combined discussion") and "Bankruptcy Code (Amendment) Bill, 2021" in first


def test_start_takes_five_speeches_when_they_hold_enough_words():
    turns = [turn(i, 300, speech_id=i) for i in range(8)]
    start, last = be.select_turns(turns)
    assert [t["seq"] for t in start] == [0, 1, 2, 3, 4]
    assert [t["seq"] for t in last] == [6, 7]


def test_start_takes_more_speeches_until_it_has_1200_words():
    turns = [turn(i, 100, speech_id=i) for i in range(20)]
    start, _ = be.select_turns(turns)
    assert sum(len(t["text"].split()) for t in start) == 1200
    assert len(start) == 12


def test_start_keeps_chair_turns_between_speeches():
    turns = [turn(0, 400, 1), turn(1, 5, None, "Chair"), turn(2, 400, 1), turn(3, 400, 2), turn(4, 400, 3),
             turn(5, 400, 4), turn(6, 400, 5), turn(7, 400, 6)]
    start, _ = be.select_turns(turns)
    assert [t["seq"] for t in start] == [0, 1, 2, 3, 4, 5, 6]


def test_start_stops_at_word_4000_and_marks_the_cut():
    turns = [turn(0, 50, 1), turn(1, 6000, 2), turn(2, 10, 3), turn(3, 10, 4)]
    start, last = be.select_turns(turns)
    assert sum(len(t["text"].split()) for t in start) == be.MAX_WORDS
    assert start[-1]["cut"] and start[-1]["seq"] == 1
    assert [t["seq"] for t in last] == [2, 3]
    assert "[the text is cut here]" in be.turn_text(start[-1])


def test_last_turns_are_not_repeated_when_the_start_holds_them():
    turns = [turn(i, 50, speech_id=i) for i in range(4)]
    start, last = be.select_turns(turns)
    assert len(start) == 4 and last == []


def test_debate_with_no_speech_takes_turns_up_to_1200_words():
    turns = [turn(i, 500, None, "Chair") for i in range(5)]
    start, _ = be.select_turns(turns)
    assert [t["seq"] for t in start] == [0, 1, 2]


# ---------------------------------------------------------------- the checks

BODY = ("Title: Discussion on the Anti-Maritime Piracy Bill, 2019\nType: GOVERNMENT BILLS\nDate: 2022-12-21\n\n"
        "Minister: I beg to move that the Anti-Maritime Piracy Bill, 2019, as reported by the Committee, "
        "be taken into consideration. The Merchant Shipping Act, 1958 does not cover piracy.\n"
        "Minister: I beg to move that the Constitution (One Hundred and Twenty-Eighth Amendment) Bill, 2023 "
        "be taken into consideration.\n")


def bill(**kw):
    b = {"printed": "Anti-Maritime Piracy Bill, 2019", "name": "Anti-Maritime Piracy Bill", "year": 2019,
         "amendment_ordinal": None, "quote": "I beg to move that the Anti-Maritime Piracy Bill, 2019, as reported",
         "role": "moved", "summary": "The Bill makes piracy at sea a crime."}
    b.update(kw)
    return b


def answer(*bills):
    return {"bills": list(bills), "outcome": "passed", "outcome_quote": None, "none_reason": None}


def test_a_correct_bill_is_kept_with_its_key_and_summary():
    bills, warnings = be.check_answer(answer(bill()), BODY)
    assert bills[0]["kept"] and bills[0]["checks_failed"] == []
    assert bills[0]["bill_key"] == "antimaritimepiracybill-2019"
    assert bills[0]["summary"] == "The Bill makes piracy at sea a crime."
    assert warnings == []


def test_a_name_that_is_not_in_the_text_is_dropped():
    bills, _ = be.check_answer(answer(bill(printed="Anti-Piracy Bill, 2019", quote="Anti-Piracy Bill, 2019")), BODY)
    assert not bills[0]["kept"] and not bills[0]["name_found"] and "name" in bills[0]["checks_failed"]


def test_a_year_from_the_debate_date_is_dropped():
    bills, _ = be.check_answer(answer(bill(year=2022)), BODY)
    assert not bills[0]["kept"] and bills[0]["checks_failed"] == ["year"]


def test_the_year_can_follow_the_printed_name():
    b = bill(printed="Anti-Maritime Piracy Bill", quote="the Anti-Maritime Piracy Bill, 2019, as reported")
    bills, _ = be.check_answer(answer(b), BODY)
    assert bills[0]["kept"]


def test_a_wrong_amendment_ordinal_is_dropped():
    b = bill(printed="Constitution (One Hundred and Twenty-Eighth Amendment) Bill, 2023",
             name="Constitution (One Hundred and Twenty-Eighth Amendment) Bill", year=2023,
             amendment_ordinal="one hundred and thirty-first",
             quote="the Constitution (One Hundred and Twenty-Eighth Amendment) Bill, 2023 be taken")
    bills, _ = be.check_answer(answer(b), BODY)
    assert bills[0]["checks_failed"] == ["ordinal"]
    good, _ = be.check_answer(answer({**b, "amendment_ordinal": "One Hundred and Twenty-Eighth"}), BODY)
    assert good[0]["kept"] and good[0]["amendment_ordinal"] == "one hundred and twenty-eighth"


def test_a_quote_that_does_not_hold_the_name_is_dropped():
    bills, _ = be.check_answer(answer(bill(quote="does not cover piracy")), BODY)
    assert bills[0]["checks_failed"] == ["quote"]


def test_a_mentioned_bill_loses_its_summary_and_is_not_kept():
    b = bill(printed="Merchant Shipping Act, 1958", name="Merchant Shipping Act", year=1958,
             quote="The Merchant Shipping Act, 1958 does not cover piracy", role="mentioned",
             summary="The Act rules shipping.")
    bills, warnings = be.check_answer(answer(b), BODY)
    assert bills[0]["summary"] is None and bills[0]["checks_failed"] == [] and not bills[0]["kept"]
    assert any("summary of the mentioned bill" in w for w in warnings)


def test_a_double_bill_is_dropped():
    bills, warnings = be.check_answer(answer(bill(), bill()), BODY)
    assert len(bills) == 1 and any("double bill" in w for w in warnings)


def test_an_empty_answer_warns_that_no_bill_is_kept():
    _, warnings = be.check_answer(answer(), BODY)
    assert warnings == ["no kept bill"]


def test_case_white_space_and_curly_quotes_do_not_stop_a_match():
    assert be.norm("The  ‘Anti–Maritime’\nPiracy") == be.norm("the 'anti-maritime' piracy")


# ---------------------------------------------------------------- the key

def test_a_different_year_or_amendment_number_gives_a_different_key():
    k128 = be.bill_key("Constitution (One Hundred and Twenty-Eighth Amendment) Bill", 2023)
    k131 = be.bill_key("Constitution (One Hundred and Thirty-First Amendment) Bill", 2026)
    k131_23 = be.bill_key("Constitution (One Hundred and Thirty-First Amendment) Bill", 2023)
    assert len({k128, k131, k131_23}) == 3


def test_key_drops_a_leading_the_and_punctuation():
    assert be.bill_key("The Delimitation Bill", 2026) == be.bill_key("Delimitation  Bill", 2026) == "delimitationbill-2026"


# ---------------------------------------------------------------- the amendment number

ORDER_BODY = ("Title: Constitution (Scheduled Castes) Order (Amendment) Bill, 2012\n"
              "Minister: I beg to move that the Constitution (Scheduled Castes) Order (Amendment) Bill, 2012 "
              "be taken into consideration.\n"
              "Minister: I beg to move that the Constitution (104 th Amendment ) Bill, 2005 be taken into consideration.\n")


def test_an_amendment_of_a_presidential_order_needs_no_amendment_number():
    # Real case: LS15-14-9972. The old rule dropped 63 such names because the name holds "Constitution".
    b = bill(printed="Constitution (Scheduled Castes) Order (Amendment) Bill, 2012",
             name="Constitution (Scheduled Castes) Order (Amendment) Bill", year=2012,
             quote="the Constitution (Scheduled Castes) Order (Amendment) Bill, 2012 be taken")
    bills, _ = be.check_answer(answer(b), ORDER_BODY)
    assert bills[0]["kept"] and bills[0]["amendment_ordinal"] is None


def test_an_amendment_number_in_digits_matches_the_words_of_the_answer():
    b = bill(printed="Constitution (104 th Amendment ) Bill, 2005", name="Constitution (104th Amendment) Bill",
             year=2005, amendment_ordinal="one hundred and fourth",
             quote="the Constitution (104 th Amendment ) Bill, 2005 be taken")
    bills, _ = be.check_answer(answer(b), ORDER_BODY)
    assert bills[0]["kept"]
    wrong, _ = be.check_answer(answer({**b, "amendment_ordinal": "one hundred and fifth"}), ORDER_BODY)
    assert wrong[0]["checks_failed"] == ["ordinal"]


@pytest.mark.parametrize("printed, number", [
    ("Constitution (One Hundred and Twenty-Third) Amendment Bill, 2017", 123),
    ("Constitution (One Hundredth Amendment) Act, 2015", 100),
    ("Constitution (Second Amendment) Bill", 2),
    ("The Constitution (One Hundred and Thirty-First Amendment) Bill, 2026", 131),
])
def test_the_amendment_number_is_read_from_the_printed_name(printed, number):
    assert be.ordinal_number(be.amendment_number_text(printed)) == number


@pytest.mark.parametrize("printed", [
    "Constitution (Scheduled Tribes) Order (Second Amendment) Bill, 2022",
    "Sixth Schedule to the Constitution (Amendment) Bill, 2003",
    "Constitution (Jammu and Kashmir) Scheduled Tribes Order (Amendment) Bill, 2023",
])
def test_a_name_with_no_amendment_number_gives_none(printed):
    assert be.amendment_number_text(printed) is None


def test_the_stored_key_ends_with_the_term():
    key = be.term_key(be.bill_key("Citizenship (Amendment) Bill", 2019), 16)
    assert key == "citizenshipamendmentbill-2019-ls16"
    assert be.key_term(key) == 16
    assert be.base_key(key) == "citizenshipamendmentbill-2019"
    assert be.key_term("citizenshipamendmentbill-2019") is None


class _Conn:
    """A fake connection that counts the INSERT statements."""
    def __init__(self, known):
        self.known, self.inserts = dict(known), 0

    def execute(self, stmt, params):
        sql = str(stmt)
        name = params["n"]

        class R:
            def __init__(self, v):
                self.v = v

            def scalar(self):
                return self.v
        if sql.startswith("INSERT"):
            self.inserts += 1
            self.known.setdefault(name, len(self.known) + 1)
            return R(None)
        return R(self.known.get(name))


def test_a_known_model_uses_no_sequence_number():
    # A real case: two dry runs of a loader with 19,279 pairs used up the SMALLINT sequence of models.
    conn = _Conn({"gemini-3.8-flash": 3})
    assert be.model_id(conn, "gemini-3.8-flash") == 3
    assert conn.inserts == 0
    assert be.model_id(conn, "new-model") == 2
    assert conn.inserts == 1
