import datetime

from pages import tag
from tests.pages_db import page_conn  # noqa: F401

def test_shape_tag_keeps_keys_and_adds_named_counts():
    t = {"tag": "Onions", "type": "crop", "domain": "agri", "description": "d", "aliases": ["x"]}
    out = tag.shape_tag(
        t, {"llm": 3, "dictionary": 1},
        [{"term": 18, "session": 1, "n": 2, "first": datetime.date(2024, 6, 1)}],
        [{"party": "BJP", "n": 1, "party_total": 4}],
        [{"mid": 9, "name": "A", "n": 3, "last": datetime.date(2024, 7, 1), "party": "BJP", "seat": "X", "state": "Y",
          "first": datetime.date(2024, 6, 1), "terms": [18]}],
        [{"id": 1, "label": "l", "n_speeches": 5, "n_debates": 2}],
        [{"tag": "Farmers", "type": "group", "n": 2}], [], [])
    assert out["total"] == 4 and out["slug"] == "onions" and out["counts_note"]
    assert out["sessions"][0]["speeches_tagged"] == 2 and out["sessions"][0]["year"] == 2024
    assert out["parties"][0]["per100"] == 25.0 and out["parties"][0]["party_speeches_with_tags"] == 4
    assert out["members"][0]["last"] == "2024-07-01"
    assert out["related"][0]["slug"] == "farmers"


def test_routes():
    assert ("/tag/<slug>", tag.tag_page) in tag.ROUTES
    assert ("/tags", tag.tags_list) in tag.ROUTES


def test_tag_page_on_database(page_conn):  # noqa: F811
    out = tag.tag_page(page_conn, "jal-jeevan-mission", {})
    assert out["name"] == "Jal Jeevan Mission" and out["total"] > 0
    assert out["recent"] and out["members"]
    assert tag.tag_page(page_conn, "no-such-tag-xyz", {}) is None


def test_tags_list_on_database(page_conn):  # noqa: F811
    out = tag.tags_list(page_conn, {})
    names = [t["name"] for t in out["tags"]]
    assert "Jal Jeevan Mission" in names
    assert names == sorted(names, key=str.lower)


def test_peak_year_tie_goes_to_earlier_year():
    assert tag.peak_year({2020: 5, 2018: 5, 2019: 3}) == 2018
    assert tag.peak_year({2021: 2, 2022: 7}) == 2022
    assert tag.peak_year({}) is None


def test_pick_quote_uses_good_sentence_only():
    texts = ["Thank you. This is short.",
             "Farmers in the country deserve a fair price for every single crop grown across the country every year."]
    assert tag.pick_quote(texts, "Farmers welfare") == texts[1]
    assert tag.pick_quote(["Hello."], "x") is None
    assert tag.pick_quote([], "x") is None


def test_shape_tag_header_members_and_peak():
    t = {"tag": "Onions", "type": "crop", "domain": "agri", "description": "d", "aliases": []}
    head = {"n_members": 7, "n_subjects": 9, "first": datetime.date(2004, 1, 2), "last": datetime.date(2024, 3, 4)}
    m = {"mid": 1, "name": "A", "n": 3, "first": datetime.date(2009, 1, 1), "last": datetime.date(2010, 1, 1),
         "party": "X", "seat": "S", "state": "T", "terms": [15, 14]}
    out = tag.shape_tag(t, {"llm": 1}, [], [], [m], [{"id": 4, "label": "l", "n_speeches": 1, "n_debates": 1}], [], [], [], head, {4: 2020})
    assert out["n_members"] == 7 and out["n_subjects"] == 9 and out["first"] == "2004-01-02" and out["last"] == "2024-03-04"
    assert out["members"][0]["first"] == "2009-01-01" and out["members"][0]["terms"] == [14, 15]
    assert out["subjects"][0]["peak"] == 2020
    assert "n_members" in out["counts_note"] and "no identified member" in out["counts_note"]


def test_tag_page_header_term_and_quote_on_database(page_conn):  # noqa: F811
    from sqlalchemy import text
    from pages.common import tag_speeches
    out = tag.tag_page(page_conn, "farmers", {})
    ids = [r[0] for r in tag_speeches(page_conn, 37)]
    direct = page_conn.execute(text("SELECT count(DISTINCT person_id) FROM speeches WHERE id = ANY(:s)"), {"s": ids}).scalar()
    assert out["n_members"] == direct and out["first"] <= out["last"]
    assert all(m["first"] <= m["last"] for m in out["members"])
    assert all("quote" in r and "subject" in r for r in out["recent"])
    one = tag.tag_page(page_conn, "farmers", {"term": "17"})
    term_total = sum(s["n"] for s in out["sessions"] if s["term"] == 17)
    assert sum(p["n"] for p in one["parties"]) <= term_total
    assert all(r["term"] == 17 for r in one["recent"])
