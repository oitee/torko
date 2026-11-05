from identity.final import choose, person_key
from identity.gate import judge
from identity.labels import read_label
from identity.names import similarity
from identity.pacing import Pace
from identity.plan import plan_all, plan_label
from identity.resolver import options_hash, resolve
from identity.retrieve import build_options, rule_answer
from identity.store import person_detail
from identity.types import Answer, Entry, LabelRow, ParsedLabel


def _member(number, name, seat):
    return Entry("person", number, name, f"seat {seat}", seat)


def test_minister_label_gives_the_name_in_brackets():
    assert read_label("THE MINISTER OF FINANCE (SHRI ARUN JAITLEY)") == ParsedLabel("name", "SHRI ARUN JAITLEY")


def test_a_bracket_inside_a_name_stays():
    assert read_label("THE MINISTER OF ROAD TRANSPORT (MAJ. GEN. (RETD.) B.C. KHANDURI)").name == "MAJ. GEN. (RETD.) B.C. KHANDURI"


def test_a_name_before_the_office_is_read():
    label = "SHRI PRAMOD MAHAJAN (THE MINISTER OF PARLIAMENTARY AFFAIRS)"
    assert read_label(label).name == "SHRI PRAMOD MAHAJAN"
    assert read_label("श्रीमती सुषमा स्वराज (विदेश मंत्री)").name == "श्रीमती सुषमा स्वराज"


def test_square_brackets_are_read():
    assert read_label("THE MINISTER OF HOUSING [SHRI M. VENKAIAH NAIDU] (a)").kind == "name"


def test_a_rank_is_not_a_seat():
    parsed = read_label("LT. GEN. (RETD.) TEJ PAL SINGH RAWAT (GARHWAL)")
    assert parsed.seat == "GARHWAL"
    assert read_label("MAJ. GEN. (RETD.) B.C. KHANDURI").seat == ""


def test_offices_and_titles_are_not_people():
    assert read_label("SECRETARY-GENERAL").kind == "office"
    assert read_label("महासचिव").kind == "office"
    assert read_label("THE MINISTER OF FINANCE").kind == "title_only"


def test_similarity_orders_real_spellings_first():
    assert similarity("DR. M. THAMBIDURAI", "M. Thambi Durai") > similarity("DR. M. THAMBIDURAI", "M. Thambi Singh")
    assert similarity("SHRI LALU PRASAD", "Lalu Prasad, Shri") > similarity("SHRI LALU PRASAD", "Panna Lal")
    assert similarity("श्रीमती रुबाब सईदा", "Rubab Sayda") > similarity("श्रीमती रुबाब सईदा", "Satabdi Roy")


def test_two_members_of_one_seat_need_the_model():
    parsed = ParsedLabel("name", "SHRI RAM KUMAR", "Karur")
    one = [_member(1, "Ram Kumar", "Karur")]
    assert rule_answer(parsed, one).key == "P1"
    assert rule_answer(parsed, one + [_member(2, "Ram Kumar Das", "Karur")]) is None


def test_a_seat_with_another_name_needs_the_model():
    assert rule_answer(ParsedLabel("name", "SHRI RAM KUMAR", "Karur"), [_member(1, "Other Person", "Karur")]) is None


def test_options_keep_the_seat_and_the_outside_names_inside_the_limit():
    seated = [_member(i, f"Member Number{i}", f"Seat{i}") for i in range(600)]
    seated.append(_member(999, "Rubab Sayda", "Bahraich"))
    outside = [Entry("rajya_sabha", 27, "Jaitley, Shri Arun", "RS")]
    options = build_options(ParsedLabel("name", "SHRI ARUN JAITLEY", "Bahraich"), seated, outside)
    keys = {e.key for e in options}
    assert len(options) <= 252
    assert {"P999", "RS27"} <= keys


def test_resolve_can_only_return_an_offered_key():
    row = LabelRow(14, "SHRI X", 10)
    options = [_member(1, "Shri X", "Karur")]
    seen = {}

    def decide(state, questions):
        seen.update(questions["speaker"]["criteria"])
        return {"answers": {"speaker": {"probabilities": {"P1": 0.8, "NONE": 0.1, "OFFICE": 0.05, "NOT_A_PERSON": 0.05}}}}

    answer = resolve(row, options, decide)
    assert set(seen) == {"P1", "NONE", "OFFICE", "NOT_A_PERSON"}
    assert (answer.key, answer.probability) == ("P1", 0.8)


def test_gate_sends_a_low_probability_to_review():
    parsed = ParsedLabel("name", "SHRI ARUN JAITLEY")
    assert judge(Answer("RS27", 0.5, "m"), parsed, "Jaitley, Shri Arun") == "review"
    assert judge(Answer("RS27", 0.9, "m"), parsed, "Jaitley, Shri Arun") == "accepted"


def test_gate_sends_a_name_that_does_not_fit_to_review():
    assert judge(Answer("P1563", 0.95, "m"), ParsedLabel("name", "श्रीमती रुबाब सईदा"), "Satabdi Roy") == "review"


def test_gate_reports_no_person():
    assert judge(Answer("NONE", 0.9, "m"), ParsedLabel("name", "SHRI X"), "") == "no_person"
    assert judge(Answer("OFFICE", None, "rule"), ParsedLabel("office"), "") == "no_person"


def test_a_changed_list_changes_the_hash():
    a, b = _member(1, "A", "S"), _member(2, "B", "T")
    assert options_hash([a, b]) == options_hash([b, a])
    assert options_hash([a]) != options_hash([a, b])


def test_pace_spaces_the_calls():
    now, naps = [0.0], []

    def sleep(seconds):
        naps.append(seconds)

    pace = Pace(10, clock=lambda: now[0], sleep=sleep)
    pace.wait()
    pace.wait()
    pace.wait()
    assert naps == [0.1, 0.2]


def test_a_linked_person_says_that_the_person_also_sat_in_the_rajya_sabha():
    detail = person_detail([18], {"latest_term": "2022-2024", "term_count": "3"})
    assert "Lok Sabha member in terms [18]" in detail
    assert "Rajya Sabha" in detail
    assert "Rajya Sabha" not in person_detail([18], None)


def test_a_changed_option_text_changes_the_hash():
    a = Entry("person", 559, "Piyush Goyal", "Lok Sabha member in terms [18].")
    b = Entry("person", 559, "Piyush Goyal", "Lok Sabha member in terms [18]. Also a Rajya Sabha member.")
    assert options_hash([a]) != options_hash([b])


def test_resolve_reports_the_input_tokens():
    def decide(state, questions):
        return {"answers": {"speaker": {"probabilities": {"NONE": 1.0}}}, "usage": {"input_tokens": 11074}}

    assert resolve(LabelRow(14, "SHRI X", 10), [], decide).tokens == 11074


def test_all_cores_give_the_same_plans_as_one_core():
    seated = {14: [_member(i, f"Member Number{i}", f"Seat{i}") for i in range(40)] + [_member(99, "Rubab Sayda", "Bahraich")]}
    outside = [Entry("rajya_sabha", 27, "Jaitley, Shri Arun", "RS")]
    rows = [LabelRow(14, "SHRI ARUN JAITLEY", 1), LabelRow(14, "RUBAB SAYDA (BAHRAICH)", 1), LabelRow(14, "SECRETARY-GENERAL", 1)]
    one = [plan_label(r, seated, outside, (10, 5)) for r in rows]
    assert plan_all(rows, seated, outside, (10, 5), processes=2) == one
    assert [p.answer.key if p.answer else None for p in one] == [None, "P99", "OFFICE"]


def test_a_person_wins_then_the_rule_then_the_model_then_the_fallback():
    answers = {"person": ("P59", None), "rule": ("P1", None), "decision-model": ("P598", 0.92), "old": ("P2", None)}
    assert choose(answers, "old") == ("P59", "person")
    del answers["person"]
    assert choose(answers, "old") == ("P1", "rule")
    del answers["rule"]
    assert choose(answers, "old") == ("P598", "decision-model")


def test_a_low_probability_or_none_falls_to_the_fallback():
    assert choose({"decision-model": ("P1", 0.79), "old": ("P2", None)}, "old") == ("P2", "old")
    assert choose({"decision-model": ("NONE", 0.9), "old": ("P2", None)}, "old") == ("P2", "old")
    assert choose({"decision-model": ("P1", 0.79)}) is None


def test_an_answer_becomes_a_person_id():
    assert person_key("P59", {}, {}) == 59
    assert person_key("RS27", {"RS27": 3000}, {}) == 3000
    assert person_key("NEW:jagdish-sharma", {}, {"NEW:jagdish-sharma": 3001}) == 3001
    assert person_key("OFFICE", {}, {}) is None
