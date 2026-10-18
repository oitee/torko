from scripts.new_tag_candidates import is_candidate


def test_a_candidate_has_no_tag_and_enough_speeches_and_debates():
    row = {"parent_tag": "", "n_speeches": "12", "n_debates": "3"}
    assert is_candidate(row, 10, 3)
    assert not is_candidate(dict(row, parent_tag="Arrears"), 10, 3)
    assert not is_candidate(dict(row, n_debates="2"), 10, 3)
