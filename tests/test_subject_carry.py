from scripts.subject_carry import (CHANGED, FAR, GREW, KEPT, SAME, carry_subjects, classify_units, copy_keyed_rows,
                                   copy_pair_rows, growth_ok, unit_map)


def near(i, m):
    return 0.05


def far(i, m):
    return 0.2


def test_growth_limit_is_half_of_the_old_names():
    assert growth_ok(2, 1)
    assert not growth_ok(2, 2)
    assert growth_ok(10, 5)
    assert not growth_ok(10, 6)


def test_unchanged_unit_is_same():
    r = classify_units([[1, 2]], [[1, 2]], near)
    assert r[0]["status"] == SAME and r[0]["old"] == 0


def test_unit_that_gains_one_close_new_name_is_kept():
    r = classify_units([[1, 2]], [[1, 2, 9]], near)
    assert r[0]["status"] == KEPT and r[0]["added"] == [(9, 0.05)]


def test_unit_that_gains_a_far_name_goes_again():
    assert classify_units([[1, 2]], [[1, 2, 9]], far)[0]["status"] == FAR


def test_the_limit_compares_with_the_centre_distance():
    dist = {9: 0.05, 8: 0.15}
    r = classify_units([[1, 2, 3, 4]], [[1, 2, 3, 4, 8, 9]], lambda i, m: dist[m])
    assert r[0]["status"] == FAR


def test_unit_that_grows_by_more_than_half_goes_again():
    assert classify_units([[1, 2]], [[1, 2, 8, 9]], near)[0]["status"] == GREW


def test_merge_of_two_old_units_is_changed():
    assert classify_units([[1, 2], [3, 4]], [[1, 2, 3, 4]], near)[0]["status"] == CHANGED


def test_unit_that_takes_a_name_of_another_old_unit_is_changed():
    assert classify_units([[1, 2, 3], [4, 5]], [[1, 2, 3, 4]], near)[0]["status"] == CHANGED


def test_split_parts_of_an_old_unit_are_changed():
    r = classify_units([[1, 2, 3, 4]], [[1, 2], [3, 4, 9]], near)
    assert [x["status"] for x in r] == [CHANGED, CHANGED]


def test_new_unit_of_new_names_is_changed():
    assert classify_units([[1, 2]], [[8, 9]], near)[0]["status"] == CHANGED


def test_unit_map_holds_same_and_kept_only():
    old, new = [[1, 2], [3, 4], [5, 6]], [[1, 2], [3, 4, 9], [5, 6, 7]]
    res = classify_units(old, new, lambda i, m: 0.2 if m == 7 else 0.05)
    assert unit_map(old, new, res) == {"1 2": "1 2", "3 4": "3 4 9"}


def test_subject_of_kept_units_gets_the_new_key():
    old_units = [[1, 2], [3, 4]]
    umap = {"1 2": "1 2", "3 4": "3 4 9"}
    smap, why = carry_subjects({"1 2 3 4": [1, 2, 3, 4]}, old_units, umap)
    assert smap == {"1 2 3 4": "1 2 3 4 9"} and why["kept"] == 1


def test_subject_with_a_changed_unit_has_no_new_key():
    smap, why = carry_subjects({"1 2 3 4": [1, 2, 3, 4]}, [[1, 2], [3, 4]], {"1 2": "1 2"})
    assert smap == {} and why["a unit changed"] == 1


def test_subject_growth_limit_applies_to_the_whole_subject():
    umap = {"1 2": "1 2 8", "3 4": "3 4 9"}
    smap, why = carry_subjects({"1 2 3 4": [1, 2, 3, 4]}, [[1, 2], [3, 4]], umap, max_growth=0.25)
    assert smap == {} and why["grew too much"] == 1


def test_pair_rows_are_copied_under_new_keys_and_old_rows_stay():
    rows = [{"name_ids_a": "1 2", "name_ids_b": "3 4", "confidence": "high"},
            {"name_ids_a": "1 2", "name_ids_b": "5 6", "confidence": "low"}]
    out = copy_pair_rows(rows, {"1 2": "1 2", "3 4": "3 4 9"})
    assert out == [{"name_ids_a": "1 2", "name_ids_b": "3 4 9", "confidence": "high"}]


def test_pair_row_with_both_keys_unchanged_is_not_copied():
    assert copy_pair_rows([{"name_ids_a": "1 2", "name_ids_b": "3 4"}], {"1 2": "1 2", "3 4": "3 4"}) == []


def test_keyed_row_is_not_copied_over_an_existing_key():
    rows = [{"name_ids": "1 2", "label": "A"}, {"name_ids": "1 2 9", "label": "B"}]
    assert copy_keyed_rows(rows, {"1 2": "1 2 9"}) == []
    assert copy_keyed_rows(rows[:1], {"1 2": "1 2 9"}) == [{"name_ids": "1 2 9", "label": "A"}]
