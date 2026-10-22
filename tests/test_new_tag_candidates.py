from scripts.new_tag_candidates import is_candidate


def test_a_candidate_has_no_tag_and_enough_speeches_and_debates():
    row = {"parent_tag": "", "n_speeches": "12", "n_debates": "3"}
    assert is_candidate(row, 10, 3)
    assert not is_candidate(dict(row, parent_tag="Arrears"), 10, 3)
    assert not is_candidate(dict(row, n_debates="2"), 10, 3)


def test_the_parent_comes_from_the_database_by_subject_key():
    from scripts.new_tag_candidates import with_db_parents
    rows = [{"name_ids": "12 3", "parent_tag": "Arrears", "n_speeches": "20", "n_debates": "5"},
            {"name_ids": "7", "parent_tag": "", "n_speeches": "20", "n_debates": "5"},
            {"name_ids": "9", "parent_tag": "", "n_speeches": "20", "n_debates": "5"}]
    out, missing = with_db_parents(rows, {"3 12": None, "7": "Railway Budget"})
    assert [r["parent_tag"] for r in out] == ["", "Railway Budget", ""]
    assert missing == 1
