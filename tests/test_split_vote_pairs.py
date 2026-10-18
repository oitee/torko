from scripts.split_vote_pairs import collect, split_pair


def test_two_tags_that_share_the_vote_make_a_pair():
    assert split_pair({"MNREGA": 0.5, "NREGA": 0.4, "NONE": 0.05}) == (("MNREGA", 0.5), ("NREGA", 0.4))


def test_none_is_never_one_of_the_pair():
    assert split_pair({"NONE": 0.5, "Budget": 0.3, "Fund Allocation": 0.1}) is None


def test_a_weak_second_tag_makes_no_pair():
    assert split_pair({"Budget": 0.6, "Fund Allocation": 0.15}) is None


def test_a_low_total_makes_no_pair():
    assert split_pair({"Budget": 0.35, "Fund Allocation": 0.3}) is None


def test_the_pair_key_is_the_same_in_both_orders():
    rows = [("Rail budget", "topic", 4, {"Rail Budget": 0.5, "Railway Budget": 0.4}),
            ("Railway budget", "topic", 2, {"Railway Budget": 0.6, "Rail Budget": 0.3})]
    pairs = collect(rows)
    assert list(pairs) == [("Rail Budget", "Railway Budget")]
    assert pairs[("Rail Budget", "Railway Budget")]["p_a"] == [0.5, 0.3]
