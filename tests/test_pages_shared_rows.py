import datetime

from pages.common import KIND_LABELS, KINDS, clean_layout, speech_kind, speech_rows
from pages.sessions import name_sessions
from tests.pages_db import page_conn  # noqa: F401


def test_speech_kind_reads_the_type_in_any_case_and_spacing():
    assert speech_kind("Matters under rule-377") == "rule_377"
    assert speech_kind("SPECIAL  MENTION (ZERO HOUR)") == "zero_hour"
    assert speech_kind("Papers laid on the table") == "other"
    assert speech_kind(None) == "other"


def test_each_type_has_one_kind_and_each_kind_a_label():
    types = [t for _, ts in KINDS.values() for t in ts]
    assert len(types) == len(set(types))
    assert set(KINDS) | {"other"} == set(KIND_LABELS)


def test_clean_layout_removes_only_the_marks():
    assert clean_layout("We [r11] need (l1/1150 water.") == "We need water."


def d(s):
    return datetime.date.fromisoformat(s)


def test_a_session_from_late_january_is_budget():
    out = name_sessions({(17, 5): [(d("2021-01-29"), 3), (d("2021-02-01"), 5), (d("2021-03-25"), 4)]})
    assert out[(17, 5)]["label"] == "Budget 2021"


def test_a_second_session_with_one_name_is_special():
    out = name_sessions({(17, 12): [(d("2023-07-20"), 50)], (17, 13): [(d("2023-09-18"), 5)]})
    assert out[(17, 12)]["label"] == "Monsoon 2023"
    assert out[(17, 13)]["label"] == "Special session, September 2023"


def test_speech_rows_give_kind_position_and_printed(page_conn):
    row = speech_rows(page_conn, [176709])[0]
    assert row["kind"] == "bill" and row["kind_label"] == "Bill" and row["short"] is False
    assert 1 <= row["position"] <= row["of"]
    sid = page_conn.execute(__import__("sqlalchemy").text(
        "SELECT id FROM speeches WHERE person_id IS NULL ORDER BY id LIMIT 1")).scalar()
    assert speech_rows(page_conn, [sid])[0]["printed"]
