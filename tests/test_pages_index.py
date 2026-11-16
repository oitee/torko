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


def test_party_weights_real(page_conn):
    d = parties.parties_page(page_conn, {})
    w = d["weights"]
    assert [s["code"] for s in w["series"]] == [r["code"] for r in d["parties"][: parties.WEIGHT_PARTIES]]
    # A weight is the speeches for each member of the party, against the same for the House, in that term.
    house = {t["term"]: t for t in w["terms"]}
    for s in w["series"]:
        for p in s["points"]:
            if p["weight"] is None:
                assert p["members"] < parties.WEIGHT_MIN_MEMBERS
                continue
            h = house[p["term"]]
            assert abs(p["weight"] - (p["speeches"] / p["members"]) / (h["speeches"] / h["members"])) < 0.001
    assert "weights_rule" in d


def test_party_terms_real(page_conn):
    d = parties.parties_page(page_conn, {})
    assert [t["term"] for t in d["terms"]] == [t["term"] for t in d["weights"]["terms"]]
    for t in d["terms"]:
        rows = t["parties"]
        # The stated order: members of the term, most first.
        assert [r["members"] for r in rows] == sorted((r["members"] for r in rows), reverse=True)
        # The members and the speeches of the parties add up to the totals of the term.
        assert sum(r["members"] for r in rows) == t["members"] and sum(r["speeches"] for r in rows) == t["speeches"]
        # A by-election adds a member, so a term has 543 members or a few more. It never has far more.
        assert 543 <= t["members"] < 620
        assert all(len(r["typical"]) <= parties.CARD_SUBJECTS for r in rows)
        grid = t["grid"]
        assert [r["code"] for r in grid["rows"]] == [r["code"] for r in rows[: parties.GRID_PARTIES]]
        assert len(grid["areas"]) == parties.GRID_DOMAINS and parties.PROCEDURE not in [a["name"] for a in grid["areas"]]
        for r in grid["rows"]:
            for area, c in zip(grid["areas"], r["cells"]):
                assert (c["lift"] is None) == (c["n"] < parties.GRID_MIN_SPEECHES)
                if c["lift"] is not None:
                    assert abs(c["lift"] - (c["n"] / r["tagged"]) / (area["speeches"] / t["tagged"])) < 0.006


def test_area_cell():
    # 30 of 100 speeches of the party against 150 of 1,000 of the House: the party gives the area twice the share.
    assert parties.area_cell(30, 100, 150, 1000) == {"n": 30, "lift": 2.0}
    assert parties.area_cell(19, 100, 150, 1000) == {"n": 19, "lift": None}


def test_speech_tags_cte_puts_the_condition_on_the_stored_rows():
    from pages.common import SPEECH_TAGS_CTE, speech_tags_cte
    assert "WHERE" not in SPEECH_TAGS_CTE
    assert "FROM speech_tags_mv si WHERE si.speech_id = :s\n" in speech_tags_cte("si.speech_id = :s")
