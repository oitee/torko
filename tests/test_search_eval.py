"""The rules of the search test set: the score, the combined marks, and the reading of the questions."""
import search_eval


def test_recall_counts_known_speeches_in_the_first_ten_only():
    assert search_eval.recall_at_10([1, 2, 3], {1, 3, 9, 8}) == 0.5
    assert search_eval.recall_at_10(list(range(20, 40)) + [1], {1}) == 0


def test_recall_limit_is_ten_when_more_speeches_are_known():
    assert search_eval.recall_at_10(list(range(10)), set(range(50))) == 1


def test_a_question_with_no_known_speech_has_no_score():
    assert search_eval.recall_at_10([1], set()) is None


def test_a_speech_is_known_only_when_both_reviewers_say_yes():
    a = {("Q1", 1): "yes", ("Q1", 2): "yes", ("Q1", 3): "no"}
    b = {("Q1", 1): "yes", ("Q1", 2): "no", ("Q1", 3): "no"}
    assert search_eval.combine_marks(a, b) == [("Q1", 1)]


def test_the_question_file_keeps_the_quote_marks_of_a_phrase():
    questions = {q["id"]: q for q in search_eval.read_questions()}
    assert len(questions) == 30
    assert search_eval.phrase_of(questions["Q23"]["query"]) == "triple talaq"
    assert search_eval.phrase_of(questions["Q01"]["query"]) is None
