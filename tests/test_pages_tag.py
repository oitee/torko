import datetime

from pages import tag
from tests.pages_db import page_conn  # noqa: F401

def test_shape_tag_keeps_keys_and_adds_named_counts():
    t = {"tag": "Onions", "type": "crop", "domain": "agri", "description": "d", "aliases": ["x"]}
    out = tag.shape_tag(
        t, {"llm": 3, "dictionary": 1},
        [{"term": 18, "session": 1, "n": 2, "first": datetime.date(2024, 6, 1)}],
        [{"party": "BJP", "n": 1, "party_total": 4}],
        [{"mid": 9, "name": "A", "n": 3, "last": datetime.date(2024, 7, 1), "party": "BJP", "seat": "X", "state": "Y"}],
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
