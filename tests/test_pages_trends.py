"""Tests of the trends page: pure helpers (offline) and the route on the real database."""
import datetime

from pages.trends import ROUTES, MIN_TAGGED, core_range, month_index, month_label, race_frames, trends_race, rate_per_1000, shape, trends_overview, trends_page, yearly_subjects
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
    assert ROUTES == [("/trends", trends_overview), ("/trends/race", trends_race), ("/trends/<slug>", trends_page)]


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


def test_years_add_up_to_the_sessions(page_conn):  # noqa: F811
    for slug in ("jal-jeevan-mission", "flood-relief"):
        d = trends_page(page_conn, slug, {})
        assert sum(y["n"] for y in d["years"]) == sum(s["n"] for s in d["sessions"]) == d["total"]
        assert [y["year"] for y in d["years"]] == sorted(y["year"] for y in d["years"])


def test_yearly_subjects_keeps_a_spike_and_drops_a_subject_of_every_year():
    tagged = {y: 1000 for y in range(2000, 2009)}
    rows = [("Spike", "topic", 2004, 200)] + [("Spike", "topic", y, 2) for y in tagged if y != 2004]
    rows += [("Every year", "topic", y, 100) for y in tagged] + [("Chief", "role", 2004, 500)]
    got = {r["year"]: r["subjects"] for r in yearly_subjects(rows, tagged)}
    assert [s["name"] for s in got[2004]] == ["Spike"]
    assert got[2004][0]["share"] == 20.0 and got[2004][0]["typical"] == 0.2
    assert got[2005] == []


def test_real_overview_names_known_events(page_conn):
    d = trends_overview(page_conn, {})
    names = {r["year"]: [s["name"] for s in r["subjects"]] for r in d["years"]}
    assert "Novel Coronavirus (COVID -19)" in names[2020]
    assert "Lokpal" in names[2011]
    assert all(len(v) <= 3 for v in names.values())


def test_month_index_and_label():
    assert month_label(month_index(2001, 1)) == "2001-01"
    assert month_label(month_index(2020, 12)) == "2020-12"


def _race_rows():
    # Twelve months. "Steady" has the same share in every month. "Spike" has its speeches only in the last three months.
    first = month_index(2000, 1)
    rows, tagged = [], {}
    for k in range(12):
        tagged[first + k] = 1000
        rows.append(("Steady", "topic", first + k, 100))
        rows.append(("Prime Minister", "role", first + k, 500))
        if k >= 9:
            rows.append(("Spike", "topic", first + k, 100))
    return rows, tagged, first


def test_race_frames_needs_a_full_window():
    rows, tagged, first = _race_rows()
    out = race_frames(rows, tagged, window=6)
    assert out["months"][0] == month_label(first + 5)  # the first window that has six months
    assert len(out["months"]) == 7
    assert out["tagged"] == [6000] * 7


def test_race_frames_windows_slide_and_count_empty_months_as_zero():
    first = month_index(2000, 1)
    tagged = {first: 100, first + 3: 100}  # months 2 and 3 have no sitting
    rows = [("A", "topic", first, 70), ("A", "topic", first + 3, 70)]
    out = race_frames(rows, tagged, window=2, top=1)
    assert out["tagged"] == [100, 0, 100]  # windows: months 1-2, 2-3, 3-4
    assert out["subjects"] == []  # the subject has fewer than 150 speeches over all years


def test_race_frames_ranks_by_distance_above_typical_and_leaves_out_roles():
    rows, tagged, _ = _race_rows()
    rows = [(t, k, m, n * 2) for t, k, m, n in rows]  # 200 per month, so each subject passes the 150 minimum
    out = race_frames(rows, tagged, window=3, top=1)
    names = [s["name"] for s in out["subjects"]]
    assert "Prime Minister" not in names   # a role is a person who is named, not a subject
    spike = next(s for s in out["subjects"] if s["name"] == "Spike")
    assert spike["n"][-1] == 600 and spike["n"][0] == 0
    # In the first frames neither subject is above typical, so the tie goes by name. Later Spike is above.
    assert names == ["Spike", "Steady"]


def test_race_frames_tie_goes_by_name():
    first = month_index(2000, 1)
    tagged = {first + k: 1000 for k in range(3)}
    rows = [(t, "topic", first + k, 100) for t in ("Beta", "Alpha") for k in range(3)]
    out = race_frames(rows, tagged, window=1, top=1)
    assert [s["name"] for s in out["subjects"]] == ["Alpha"]


def test_race_frames_skips_a_subject_with_few_speeches_in_the_window():
    first = month_index(2000, 1)
    tagged = {first + k: 1000 for k in range(10)}
    rows = [("Thin", "topic", first + k, 19) for k in range(10)] + [("Thick", "topic", first + k, 20) for k in range(10)]
    out = race_frames(rows, tagged, window=1, top=2)
    assert [s["name"] for s in out["subjects"]] == ["Thick"]


def test_race_on_the_real_database(page_conn):
    d = trends_race(page_conn, {})
    assert d["months"][0] >= "2000-01" and len(d["months"]) == len(d["tagged"])
    assert all(len(s["n"]) == len(d["months"]) for s in d["subjects"])
    assert any(s["name"] == "Novel Coronavirus (COVID -19)" for s in d["subjects"])
