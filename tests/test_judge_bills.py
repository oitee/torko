import pytest

from scripts.judge_bills import KEEP_P, ROLES, keep, question_key, questions_for, role_p


def test_one_choice_question_for_each_name():
    qs = questions_for([{"id": 7, "printed": "Designs Bill, 2000"}, {"id": 9, "printed": "Designs Act, 1911"}])
    assert list(qs) == ["role_7", "role_9"]
    assert qs["role_7"]["type"] == "choice" and set(qs["role_7"]["criteria"]) == set(ROLES)
    assert "«Designs Bill, 2000»" in qs["role_7"]["instructions"]


def test_probabilities_follow_the_order_moved_mentioned_unsure():
    answer = {"probabilities": {"unsure": 0.1, "moved": 0.8, "mentioned": 0.1}}
    assert role_p(answer) == [0.8, 0.1, 0.1]


def test_an_option_that_the_answer_leaves_out_gets_zero():
    assert role_p({"probabilities": {"moved": 1.0}}) == [1.0, 0.0, 0.0]


@pytest.mark.parametrize("checks, p, kept", [
    ([], [KEEP_P, 0.2, 0.1], True),
    ([], [0.69, 0.3, 0.01], False),
    (["year"], [0.99, 0.0, 0.01], False),
    ([], None, False),
])
def test_keep_needs_the_checks_and_moved_at_the_limit(checks, p, kept):
    assert keep(checks, p) is kept


def test_question_key_matches_the_row_id():
    assert question_key(42) == "role_42"


class FakeResult:
    def __init__(self, value):
        self.value = value

    def scalar(self):
        return self.value


class FakeConn:
    """Answers the one read of store: the raw answer of the extraction."""

    def __init__(self):
        self.updates = []

    def execute(self, statement, params=None):
        sql = str(statement)
        if sql.strip().startswith("UPDATE"):
            self.updates.append(params)
            return FakeResult(None)
        assert "SELECT bill_id" not in sql  # the bill row comes with the name, not from one more query
        return FakeResult("raw answer")


def test_a_kept_name_with_no_bill_row_gets_a_bill_of_the_debate_term(monkeypatch):
    import scripts.judge_bills as jb
    calls = []
    monkeypatch.setattr(jb.be, "check_answer", lambda raw, body: ([{"printed": "Citizenship (Amendment) Bill, 2019",
                                                                     "bill_key": "citizenship-amendment-2019"}], []))
    monkeypatch.setattr(jb.be, "bill_id", lambda conn, bill, loksabha: calls.append(loksabha) or 4145)
    conn = FakeConn()
    names = [{"id": 1, "printed": "Citizenship (Amendment) Bill, 2019", "bill_id": None}]
    answers = {question_key(1): {"probabilities": {"moved": 0.95, "mentioned": 0.03, "unsure": 0.02}}}
    kept, warnings = jb.store(conn, {"loksabha": 17, "input": "text"}, names, answers, KEEP_P)
    assert (kept, warnings, calls) == (1, [], [17])
    assert conn.updates[0]["bid"] == 4145
