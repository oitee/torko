"""Tests of the place page: pure helpers (offline) and the route on the real database."""
import time

from pages.place import ROUTES, place_page, same_seat
from tests.pages_db import page_conn  # noqa: F401


def test_same_seat_ignores_bracket_suffix_and_case():
    assert same_seat("Gorakhpur", "Gorakhpur")
    assert same_seat("GORAKHPUR (SC)", "Gorakhpur")
    assert not same_seat("Gorakhpur Rural", "Gorakhpur")
    assert not same_seat(None, "Gorakhpur")


def test_route_rule():
    assert ROUTES == [("/place/<slug>", place_page)]


def test_state_place(page_conn):
    t = time.time()
    d = place_page(page_conn, "kerala", {})
    assert d["name"] == "Kerala" and d["subtype"] == "state"
    assert d["total"] > 1000 and d["holders"] == []
    assert d["sessions"] and sum(s["n"] for s in d["sessions"]) == d["total"]
    assert all(p["per100"] <= 100 for p in d["parties"])
    assert [m["n"] for m in d["members"]] == sorted((m["n"] for m in d["members"]), reverse=True)
    assert len(d["recent"]) == 8 and "counts_note" in d
    assert time.time() - t < 30


def test_district_place_has_holders(page_conn):
    d = place_page(page_conn, "gorakhpur", {})
    assert d["holders"] and all(h["seat"] for h in d["holders"])
    assert {h["state"] for h in d["holders"]} == {"Uttar Pradesh"}
    lifts = [a["lift"] for a in d["associated"]]
    assert lifts == sorted(lifts, reverse=True)


def test_unknown_and_non_place_give_none(page_conn):
    assert place_page(page_conn, "no-such-place-xyz", {}) is None
    assert place_page(page_conn, "jal-jeevan-mission", {}) is None  # a scheme, not a place
