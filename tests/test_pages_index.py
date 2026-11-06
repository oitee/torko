import pages.parties as parties
import pages.places as places
from tests.pages_db import page_conn  # noqa: F401


def test_parties_page_real(page_conn):
    d = parties.parties_page(page_conn, {})
    rows = d["parties"]
    assert d["count"] == len(rows) and rows
    # The stated order: speeches, most first, then the code.
    assert rows == sorted(rows, key=lambda r: (-r["speeches"], r["code"]))
    # Every speech of a party has an identified member, so the parties never add up to more than the total.
    assert sum(r["speeches"] for r in rows) <= d["total"]
    assert all(r["members"] >= 1 and r["terms"] == sorted(r["terms"]) for r in rows)
    assert "counts_note" in d


def test_places_page_real(page_conn):
    d = places.places_page(page_conn, {})
    states = d["states"]
    assert d["state_count"] == len(states)
    assert d["seat_count"] == sum(len(s["seats"]) for s in states)
    assert [s["name"] for s in states] == sorted(s["name"] for s in states)
    for s in states:
        assert [x["name"] for x in s["seats"]] == sorted(x["name"] for x in s["seats"])
    featured = d["featured"]
    assert len(featured) == 5 and all(f["page"] for f in featured)
    assert [f["speeches"] for f in featured] == sorted((f["speeches"] for f in featured), reverse=True)
