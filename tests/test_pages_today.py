"""Tests of the "On this day" page: the date parsing and the choice of the day (offline), and the route on the real database."""
import datetime

from pages.today import ROUTES, good, good_hi, nearest_day, parse_month_day, target_date, today_page
from tests.pages_db import page_conn  # noqa: F401

D = datetime.date


def test_parse_month_day():
    assert parse_month_day("10-23") == (10, 23)
    assert parse_month_day("2-9") == (2, 9)
    assert parse_month_day("02-29") == (2, 29)
    for bad in ["13-01", "02-30", "abc", "", None, "10/23", "2020-10-23"]:
        assert parse_month_day(bad) is None


def test_target_date_leap_day_falls_back():
    assert target_date(2023, (2, 29)) == D(2023, 2, 28)
    assert target_date(2024, (2, 29)) == D(2024, 2, 29)


def test_nearest_day_window_and_tie():
    days = [D(2020, 10, 20), D(2020, 10, 26), D(2020, 3, 1)]
    assert nearest_day(days, 2020, (10, 23)) == D(2020, 10, 20)   # a tie goes to the earlier day
    assert nearest_day(days, 2020, (7, 1)) is None                # nothing within 45 days
    assert nearest_day(days, 2019, (10, 23)) is None


def test_quote_rules():
    assert good("The Government must build new irrigation canals across every drought district of the country this year.")
    assert not good("Sir, the Government must build new irrigation canals across every drought district of the country.")
    assert not good("Too short a sentence.")
    assert not good_hi("यह एक वाक्य है जो पीछे की ओर इशारा करता है और बहुत लंबा है इसलिए नहीं चलेगा।")


def test_route_rule():
    assert ROUTES == [("/today", today_page)]


def test_today_on_a_date(page_conn):
    d = today_page(page_conn, {"date": "12-01"})
    assert (d["month"], d["day"]) == (12, 1) and d["items"]
    years = [i["year"] for i in d["items"]]
    assert years == sorted(years, reverse=True)
    for i in d["items"]:
        assert abs(i["days_from"]) <= d["window"] and len(i["debates"]) <= 3
        if i["quote"]:
            assert i["lang"] in ("en", "hi") and i["member"]


def test_today_default_and_bad_date(page_conn):
    assert today_page(page_conn, {})["items"]
    assert today_page(page_conn, {"date": "99-99"}) is None
