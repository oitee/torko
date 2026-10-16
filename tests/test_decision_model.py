import pytest

from decision_model import (DecisionError, choice_probabilities, looks_too_long, noul_probability, score_probabilities,
                            score_q, sum_is_off)

LEVELS = ["0 not a subject", "1 passing", "2 supporting", "3 central"]
REAL_SCORE = {"type": "score", "score": 2.99, "confidence": 0.99,
              "legend": {"0": LEVELS[0], "1": LEVELS[1], "2": LEVELS[2], "3": LEVELS[3]},
              "probabilities": {"0": 0.0, "1": 0.0, "2": 0.01, "3": 0.99}}
REAL_NOUL = {"type": "noul", "noul": 0.99}
REAL_CHOICE = {"type": "choice", "choice": "Rural Employment Guarantee", "confidence": 1.0,
               "probabilities": {"NONE": 0.0, "Road Construction": 0.0, "Rural Employment Guarantee": 1.0}}


def test_score_probabilities_come_back_in_level_order():
    assert score_probabilities(REAL_SCORE, LEVELS) == [0.0, 0.0, 0.01, 0.99]


def test_score_probabilities_also_accept_the_level_text_as_key():
    answer = {"probabilities": {LEVELS[3]: 0.7, LEVELS[0]: 0.3}}
    assert score_probabilities(answer, LEVELS) == [0.3, 0.0, 0.0, 0.7]


def test_a_score_level_that_was_not_asked_is_an_error():
    with pytest.raises(DecisionError):
        score_probabilities({"probabilities": {"7": 1.0}}, LEVELS)


def test_noul_reads_the_documented_field():
    assert noul_probability(REAL_NOUL) == 0.99


def test_noul_with_no_probability_is_an_error():
    with pytest.raises(DecisionError):
        noul_probability({"type": "noul"})


def test_choice_gives_every_option_and_zero_for_a_missing_one():
    options = ["Rural Employment Guarantee", "Road Construction", "NONE", "Water"]
    probs = choice_probabilities(REAL_CHOICE, options)
    assert probs == {"Rural Employment Guarantee": 1.0, "Road Construction": 0.0, "NONE": 0.0, "Water": 0.0}


def test_a_choice_option_that_was_not_asked_is_an_error():
    with pytest.raises(DecisionError):
        choice_probabilities(REAL_CHOICE, ["Road Construction", "NONE"])


def test_an_answer_with_no_probabilities_is_an_error():
    with pytest.raises(DecisionError):
        choice_probabilities({"choice": "NONE"}, ["NONE"])


def test_a_score_question_needs_two_to_ten_levels():
    with pytest.raises(ValueError):
        score_q("?", ["only one"])
    with pytest.raises(ValueError):
        score_q("?", [str(i) for i in range(11)])


def test_rounding_to_two_decimals_is_not_a_broken_sum_but_a_real_gap_is():
    assert not sum_is_off([0.33, 0.33, 0.33])
    assert not sum_is_off([0.04] * 22 + [0.04])        # 0.92 over 23 rounded answers
    assert sum_is_off([0.5, 0.2])


def test_a_context_error_is_told_apart_from_other_errors():
    assert looks_too_long(400, '{"error": "input exceeds the maximum context length"}')
    assert looks_too_long(413, "")
    assert looks_too_long(400, '{"detail":{"error_type":"max_tokens_exceeded"}}')
    assert not looks_too_long(400, '{"error": "unknown question type"}')
    assert not looks_too_long(401, "context")
