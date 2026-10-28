"""Debate titles as plain text: the source keeps HTML in about 8% of them."""
from pages.common import tidy_title


def test_superscripts_join_their_number():
    assert tidy_title("Presentation of the 59<sup>th</sup>, 60<sup>th</sup> and 61<sup>st</sup> Reports") == \
        "Presentation of the 59th, 60th and 61st Reports"


def test_other_tags_go_away_and_codes_become_letters():
    t = 'Lok Sabhas.<span style="mso-spacerun: yes"> </span>She also made reference &amp; <B>more</B>'
    assert tidy_title(t) == "Lok Sabhas. She also made reference & more"


def test_a_line_break_becomes_a_space():
    assert tidy_title("Bill<br>2024<BR/>passed") == "Bill 2024 passed"


def test_a_less_than_sign_in_words_stays():
    assert tidy_title("Growth < 5 per cent") == "Growth < 5 per cent"


def test_an_upper_case_title_keeps_its_first_letter_only():
    assert tidy_title("PAPERS  LAID") == "Papers laid"
