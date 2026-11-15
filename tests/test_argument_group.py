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


# The join call: the groups of one answer, with the point ids 11 to 16 in the order of the list.
GROUPS = [{"label": "Delays women's reservation by linking it to delimitation", "points": [1, 2, 3]},
          {"label": "Reduces the seats of southern states", "points": [4]},
          {"label": "Holds women's reservation hostage to delimitation", "points": [5, 6]}]
ORDER = [16, 12, 14, 11, 15, 13]
POINTS = {11: "South loses seats", 12: "Linked to delimitation", 13: "Hostage to the census",
          14: "No date for the quota", 15: "Hostage to delimitation", 16: "Delimitation first"}


def test_the_merge_input_puts_the_largest_group_first_and_shows_its_points_by_id():
    body, merge_order = ag.build_merge_input("Constitution Bill", 2026, "against", GROUPS, ORDER, POINTS)
    assert merge_order == [0, 2, 1]
    assert body.splitlines()[:4] == ["Bill: Constitution Bill, 2026", "Side: the points that members made against the bill.",
                                     "Groups (3):", ""]
    assert "1. Delays women's reservation by linking it to delimitation (3 points)\n   - Linked to delimitation\n" \
           "   - No date for the quota\n   - Delimitation first" in body
    assert body.endswith("3. Reduces the seats of southern states (1 points)\n   - South loses seats")


def test_the_merge_input_shows_at_most_four_points_of_a_group():
    big = [{"label": "A", "points": [1, 2, 3, 4, 5, 6]}]
    body, _ = ag.build_merge_input("B", 2020, "for", big, ORDER, POINTS)
    assert body.count("   - ") == ag.MERGE_POINTS_SHOWN


def test_a_good_join_answer_and_an_empty_one_pass():
    joins, problems = ag.check_joins({"joins": [{"groups": [1, 2], "label": "Delays women's reservation"}]}, 3)
    assert problems == [] and joins == [{"label": "Delays women's reservation", "groups": [1, 2]}]
    assert ag.check_joins({"joins": []}, 3) == ([], [])


def test_a_broken_join_answer_is_refused():
    _, p = ag.check_joins({"joins": [{"groups": [1, 2], "label": "A"}, {"groups": [2, 9], "label": ""},
                                     {"groups": [3], "label": "C"}]}, 3)
    text = " | ".join(p)
    assert "group 2 is in join 1 and in join 2" in text
    assert "join 2: group 9 is not in the list" in text
    assert "join 2: has no label" in text
    assert "join 3 has fewer than 2 groups" in text
    assert ag.check_joins({}, 3)[1] == ["joins is not a list"]


def test_a_join_makes_one_group_with_its_label_and_the_order_follows_size():
    _, merge_order = ag.build_merge_input("B", 2026, "against", GROUPS, ORDER, POINTS)
    final = ag.apply_joins(GROUPS, merge_order, [{"label": "Delays women's reservation by linking it to delimitation",
                                                  "groups": [1, 2]}])
    assert final == [{"label": "Delays women's reservation by linking it to delimitation", "points": [1, 2, 3, 5, 6]},
                     {"label": "Reduces the seats of southern states", "points": [4]}]


def test_no_join_keeps_the_groups():
    _, merge_order = ag.build_merge_input("B", 2026, "against", GROUPS, ORDER, POINTS)
    assert ag.apply_joins(GROUPS, merge_order, []) == [GROUPS[0], GROUPS[2], GROUPS[1]]


def test_the_latest_prompts_of_each_kind():
    assert ag.latest_prompt_version("group").startswith("group_v")
    assert ag.latest_prompt_version("merge").startswith("merge_v")
