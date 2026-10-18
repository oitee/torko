from scripts.load_subjects import subject_rows


def test_subject_rows_sort_the_name_ids_and_resolve_the_parent_tag():
    final = [{"subject_id": "S1", "label": "Wage arrears", "label_source": "llm", "parent_tag": "Arrears",
              "n_names": "2", "n_speeches": "7", "n_debates": "7"}]
    rows, problems = subject_rows(final, {"S1": ["12", "3"]}, {"Arrears": 40})
    assert problems == []
    assert rows[0]["key"] == "3 12" and rows[0]["parent"] == 40 and rows[0]["names"] == [3, 12]


def test_an_unknown_parent_tag_is_a_problem_and_loads_as_no_parent():
    final = [{"subject_id": "S1", "label": "X", "label_source": "auto", "parent_tag": "Gone",
              "n_names": "1", "n_speeches": "1", "n_debates": "1"}]
    rows, problems = subject_rows(final, {"S1": ["5"]}, {})
    assert rows[0]["parent"] is None and len(problems) == 1
