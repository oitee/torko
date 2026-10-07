from debate_fetch import is_crowd_label, is_presiding_label
from label_attribution import label_alias_person, normalize_label

ALIASES = {
    (17, "डॉ. सत्यपाल सिंह ( बागपत )"): 1754,
    (18, "SHRI P. P. CHAUDHARY (PALI)"): 297,
    (17, "HON. SPEAKER"): 1,          # a wrong row, on purpose
}


def _person(term, label):
    return label_alias_person(ALIASES, term, label, is_presiding_label, is_crowd_label)


def test_normalize_label_removes_outer_spaces_and_joins_inner_white_space():
    assert normalize_label("  डॉ. सत्यपाल  सिंह\n( बागपत ) ") == "डॉ. सत्यपाल सिंह ( बागपत )"
    assert normalize_label(None) == ""


def test_an_exact_label_in_its_own_term_gets_the_member():
    assert _person(17, "डॉ. सत्यपाल सिंह ( बागपत )") == 1754
    assert _person(17, " डॉ. सत्यपाल सिंह\t( बागपत )") == 1754


def test_the_same_label_in_another_term_gets_no_member():
    assert _person(16, "डॉ. सत्यपाल सिंह ( बागपत )") is None
    assert _person(17, "SHRI P. P. CHAUDHARY (PALI)") is None


def test_a_label_that_differs_by_one_character_gets_no_member():
    assert _person(18, "SHRI P.P. CHAUDHARY (PALI)") is None
    assert _person(18, "shri p. p. chaudhary (pali)") is None


def test_a_chair_label_never_gets_a_member_even_with_a_row():
    assert _person(17, "HON. SPEAKER") is None


def test_an_empty_label_gets_no_member():
    assert _person(17, "") is None
    assert _person(17, None) is None


def _row(**kw):
    row = {"loksabha": 17, "speaker_label": "डॉ. सत्यपाल सिंह ( बागपत )", "person_id": 1754,
           "member_name": "Satya Pal Singh", "basis": "name_and_constituency", "source": "test"}
    return dict(row, **kw)


def _check(rows):
    from scripts.load_label_aliases import check_rows
    check_rows(rows, {17, 18}, {1754: "Satya  Pal Singh", 297: "P P Chaudhary"})


def test_the_loader_accepts_a_good_row_and_ignores_extra_spaces_in_the_roster_name():
    _check([_row()])


def test_the_loader_stops_on_a_chair_label_a_wrong_name_or_a_double_pair():
    import pytest
    for rows in ([_row(speaker_label="HON. SPEAKER")],
                 [_row(member_name="P P Chaudhary")],
                 [_row(speaker_label=" डॉ. सत्यपाल सिंह ( बागपत )")],
                 [_row(), _row(person_id=297, member_name="P P Chaudhary")]):
        with pytest.raises(SystemExit):
            _check(rows)
