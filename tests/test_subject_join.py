from scripts.subject_join import join_units, unit_line, weighted_pr


def test_unit_line_shows_at_most_twelve_names():
    names = [(f"n{i}", 20 - i) for i in range(14)]
    line = unit_line(names)
    assert line.startswith("n0 (20); n1 (19)")
    assert line.endswith("(+2 more names)")
    assert "n12" not in line


def test_join_units_joins_the_nearest_pairs_first_and_respects_the_size_limit():
    subjects = join_units(3, [(0, 1, 0.05), (1, 2, 0.06)], sizes=[10, 10, 25], max_joined=30)
    assert sorted(sorted(s) for s in subjects) == [[0, 1], [2]]


def test_join_units_chains_when_the_size_allows():
    subjects = join_units(3, [(0, 1, 0.05), (1, 2, 0.06)], sizes=[2, 2, 2], max_joined=40)
    assert [sorted(s) for s in subjects] == [[0, 1, 2]]


def test_weighted_pr_uses_the_band_weights():
    gold = [("P1", 0.05, True, 1.0), ("P2", 0.15, False, 10.0), ("P3", 0.15, True, 10.0)]
    r = weighted_pr(gold, lambda pid, d: d < 0.10)
    assert r == {"precision": 1.0, "recall": round(1 / 11, 3)}
    r = weighted_pr(gold, lambda pid, d: True)
    assert r["precision"] == round(11 / 21, 3)


def test_joins_find_units_by_their_name_ids_and_skip_lost_units():
    from scripts.subject_join import joins_to_pairs, unit_key
    units = [[5, 3], [9], [7, 8]]
    assert unit_key(units[0]) == "3 5"
    rows = [{"name_ids_a": "3 5", "name_ids_b": "9", "centre_distance": "0.1"},
            {"name_ids_a": "7 8", "name_ids_b": "1 2", "centre_distance": "0.2"}]
    pairs, unmatched = joins_to_pairs(units, rows)
    assert pairs == [(0, 1, 0.1)] and unmatched == 1


def test_a_cannot_link_stops_a_chain_join():
    pairs = [(0, 1, 0.05), (1, 2, 0.06)]
    subjects = join_units(3, pairs, sizes=[2, 2, 2], cannot={frozenset((0, 2))})
    assert sorted(sorted(s) for s in subjects) == [[0, 1], [2]]


def test_a_cannot_link_between_other_subjects_does_not_matter():
    subjects = join_units(4, [(0, 1, 0.05)], sizes=[1, 1, 1, 1], cannot={frozenset((2, 3))})
    assert sorted(sorted(s) for s in subjects) == [[0, 1], [2], [3]]

