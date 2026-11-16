from text_match import norm


def test_norm_makes_typographic_marks_plain_and_folds_case():
    assert norm("The  ‘Anti–Maritime’\nPiracy​") == "the 'anti-maritime' piracy"


def test_norm_of_none_is_empty():
    assert norm(None) == ""
