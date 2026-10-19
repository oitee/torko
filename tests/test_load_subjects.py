from scripts.load_subjects import subject_rows


def test_subject_rows_sort_the_name_ids_into_the_key():
    final = [{"subject_id": "S1", "label": "Wage arrears", "label_source": "llm", "parent_tag": "Arrears",
              "n_names": "2", "n_speeches": "7", "n_debates": "7"}]
    rows = subject_rows(final, {"S1": ["12", "3"]})
    assert rows[0]["key"] == "3 12" and rows[0]["names"] == [3, 12]


def test_subject_rows_ignore_the_vote_parent_of_the_file():
    final = [{"subject_id": "S1", "label": "X", "label_source": "auto", "parent_tag": "Arrears",
              "n_names": "1", "n_speeches": "1", "n_debates": "1"}]
    assert "parent" not in subject_rows(final, {"S1": ["5"]})[0]
