from scripts.build_tag_related import rank_related
from tests.pages_db import page_conn  # noqa: F401
from pages import tag

TOTAL = 107949
# Real numbers from the build on the local database (Sugarcane case).
COUNTS = {1: 226, 2: 425, 3: 384, 4: 351, 5: 15225, 6: 168}
NAMES = {1: "Sugarcane", 2: "Sugar", 3: "Sugarcane Growers", 4: "Sugarcane Pricing", 5: "Farmers", 6: "Sugar Industry"}
PAIRS = [(1, 2, 198), (1, 3, 164), (1, 4, 101), (1, 5, 196), (1, 6, 62)]


def test_lift_is_shared_over_expected():
    rows = {r[1]: r for r in rank_related(PAIRS, COUNTS, TOTAL, NAMES)}
    assert round(rows[2][3], 2) == 0.89 and round(rows[2][4], 1) == 222.5
    assert round(rows[3][4], 1) == 204.0 and round(rows[4][4], 1) == 137.4


def test_big_tag_does_not_lead_by_shared_count():
    rows = [r for r in rank_related(PAIRS, COUNTS, TOTAL, NAMES) if r[0] == 1]
    rows.sort(key=lambda r: (-r[4], -r[2], NAMES[r[1]]))
    assert [r[1] for r in rows][-1] == 5
    assert [NAMES[r[1]] for r in rows][:2] == ["Sugar", "Sugarcane Growers"]


def test_minimum_shared_and_top_and_tie_order():
    pairs = [(1, 2, 7), (1, 3, 8), (1, 4, 8)]
    counts = {1: 100, 2: 10, 3: 10, 4: 10}
    names = {1: "A", 2: "B", 3: "Z", 4: "C"}
    rows = rank_related(pairs, counts, 1000, names)
    assert [r[1] for r in rows] == [3, 4]  # B has 7 shared and is out
    assert [r[1] for r in rank_related(pairs, counts, 1000, names, top=1)] == [4]  # tie: the name C is before Z


def test_sugarcane_related_on_database(page_conn):  # noqa: F811
    out = tag.tag_page(page_conn, "sugarcane", {})
    names = [r["name"] for r in out["related"]]
    assert "Sugarcane Growers" in names and "Sugarcane Pricing" in names
    first = out["related"][0]
    assert first["name"] == "Sugar" and first["speeches_shared"] == 198 and first["lift"] == 222.5
    lifts = [r["lift"] for r in out["related"]]
    assert lifts == sorted(lifts, reverse=True) and len(names) <= 14
    assert all(r["speeches_shared"] >= 8 for r in out["related"])
