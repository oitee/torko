import argument_extract as ae

SPEECH = "Sir, I oppose this Bill. It takes away the power of the States over their own police."


def pair():
    return {"bill": "Police Bill, 2020", "bill_summary": None, "title": "Police Bill, 2020",
            "debate_date": "2020-01-01", "member": "A Member", "text": SPEECH}


def test_input_holds_the_bill_the_stance_and_the_speech():
    body = ae.input_text(pair(), "against")
    assert "Bill: Police Bill, 2020" in body
    assert "(no summary: only the name of the bill is known)" in body
    assert "Position of the speaker on the bill: against" in body
    assert body.endswith("Speech:\n" + SPEECH)


def test_check_keeps_a_good_point_and_finds_its_quote():
    points, warnings = ae.check_answer({"points": [
        {"side": "against", "point": "The Bill takes police powers from the States.",
         "quote": "it takes away the power of the States"}]}, SPEECH)
    assert warnings == []
    assert points[0]["quote_found"] is True


def test_check_marks_a_quote_that_is_not_in_the_speech():
    points, warnings = ae.check_answer({"points": [
        {"side": "against", "point": "The Bill is unconstitutional.", "quote": "this Bill is unconstitutional"}]}, SPEECH)
    assert points[0]["quote_found"] is False
    assert warnings == ["point 1: quote not in the speech"]


def test_check_drops_a_bad_side_and_an_empty_quote():
    points, warnings = ae.check_answer({"points": [
        {"side": "neutral", "point": "x", "quote": "I oppose"},
        {"side": "for", "point": "x", "quote": ""}]}, SPEECH)
    assert points == []
    assert len(warnings) == 2


def test_check_keeps_only_five_points():
    p = {"side": "against", "point": "x", "quote": "I oppose this Bill"}
    points, warnings = ae.check_answer({"points": [p] * 7}, SPEECH)
    assert len(points) == 5
    assert warnings[0] == "7 points, only the first 5 kept"


def test_an_empty_list_is_a_valid_answer():
    assert ae.check_answer({"points": []}, SPEECH) == ([], [])


def test_pair_id_and_prompt_version():
    assert ae.pair_id(12, 34) == "12-34"
    assert ae.latest_prompt_version() == "v3"
