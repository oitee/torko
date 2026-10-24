"""Tests of the trends page: pure helpers (offline) and the route on the real database."""
import datetime

from pages.trends import ROUTES, MIN_TAGGED, core_range, rate_per_1000, shape, trends_page
from tests.pages_db import page_conn  # noqa: F401

D = datetime.date


def test_core_range_drops_a_stray_day():
    days = [(D(2020, 1, 1), 10), (D(2020, 1, 2), 10), (D(2020, 6, 1), 1)]
    first, last, stray = core_range(days)
    assert first.startswith("2020-01") and stray == 1


def test_core_range_empty():
    assert core_range([]) == (None, None, 0)


def test_rate_per_1000():
    assert rate_per_1000(5, 1000) == 5.0
    assert rate_per_1000(5, 0) is None


def test_shape_ignores_thin_sessions_and_ties_go_early():
    rows = [{"n": 1, "tagged": 1000}, {"n": 5, "tagged": 10}, {"n": 4, "tagged": 1000}, {"n": 4, "tagged": 1000}]
    peak, strength = shape(rows)
    assert peak == 2          # the thin session 1 is not used, the tie goes to the earlier session
    assert strength == round(4 / (9 / 3), 1)
    assert shape([{"n": 1, "tagged": MIN_TAGGED - 1}]) == (None, 0)
    assert shape([{"n": 0, "tagged": 1000}]) == (None, 0)


def test_route_rule():
    assert ROUTES == [("/trends/<slug>", trends_page)]


def test_jal_jeevan_mission(page_conn):
    d = trends_page(page_conn, "jal-jeevan-mission", {})
    assert d["name"] == "Jal Jeevan Mission"
    assert sum(s["n"] for s in d["sessions"]) == d["total"] > 100
    for s in d["sessions"]:
        assert s["tagged"] <= s["speeches"] and s["thin"] == (s["tagged"] < d["min_tagged"])
    assert d["peak"] is not None and d["strength"] > 1
    keys = [(s["term"], s["session"]) for s in d["sessions"]]
    assert keys == sorted(keys)


def test_unknown_gives_none(page_conn):
    assert trends_page(page_conn, "no-such-tag-xyz", {}) is None
