import argument_group as ag


def test_close_points_sit_next_to_each_other():
    v = {1: [1.0, 0.0], 2: [0.0, 1.0], 3: [0.99, 0.14], 4: [0.1, 0.995]}
    order = ag.order_points([1, 2, 3, 4], v)
    assert sorted(order) == [1, 2, 3, 4]
    pos = {i: n for n, i in enumerate(order)}
    assert abs(pos[1] - pos[3]) == 1 and abs(pos[2] - pos[4]) == 1


def test_a_short_list_keeps_the_id_order():
    assert ag.order_points([5, 2], {}) == [2, 5]


def test_a_good_answer_passes():
    groups, problems = ag.check_answer({"groups": [{"label": "Makes religion a test for citizenship", "points": [1, 3]},
                                                   {"label": "Breaks the Assam Accord", "points": [2]}]}, 3)
    assert problems == []
    assert [g["points"] for g in groups] == [[1, 3], [2]]


def test_a_missing_point_a_double_point_and_a_point_outside_are_refused():
    _, p = ag.check_answer({"groups": [{"label": "A", "points": [1, 2]}, {"label": "B", "points": [2, 9]}]}, 3)
    text = " | ".join(p)
    assert "point 2 is in group 1 and in group 2" in text
    assert "point 9 is not in the list" in text
    assert "1 points are in no group: [3]" in text


def test_a_group_with_no_label_or_a_long_label_is_refused():
    long_label = " ".join(["word"] * (ag.MAX_LABEL_WORDS + 1))
    _, p = ag.check_answer({"groups": [{"label": " ", "points": [1]}, {"label": long_label, "points": [2]}]}, 2)
    assert "group 1 has no label" in p and "group 2: the label is too long" in p


def test_an_answer_with_no_groups_is_refused():
    assert ag.check_answer({}, 2)[1] == ["groups is not a list with groups"]


def test_the_input_numbers_the_points_from_one():
    body = ag.build_input("Citizenship (Amendment) Bill", 2019, "against", ["Religion as a test", "Faith-based citizenship"])
    assert "Bill: Citizenship (Amendment) Bill, 2019" in body
    assert "\n1. Religion as a test\n2. Faith-based citizenship\n" in body
    assert "against the bill" in body
