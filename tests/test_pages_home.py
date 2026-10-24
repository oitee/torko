from pages import home
from tests.pages_db import page_conn  # noqa: F401


def test_shape_typical_keeps_old_keys_and_adds_named_counts():
    rows = [{"tag": "Jal Jeevan Mission", "type": "scheme", "n_ses": 20, "n_term": 40, "lift": 3.14159}]
    out = home.shape_typical(rows)
    assert out == [{"name": "Jal Jeevan Mission", "slug": "jal-jeevan-mission", "type": "scheme", "n": 20,
                    "speeches_in_session": 20, "n_term": 40, "speeches_in_term": 40, "lift": 3.1}]


def test_routes():
    assert home.ROUTES == [("/home", home.home_page)]


def test_home_page_on_database(page_conn):  # noqa: F811
    out = home.home_page(page_conn, {})
    assert out["typical"] and out["chamber"] and out["counts_note"]
    lifts = [t["lift"] for t in out["typical"]]
    assert lifts == sorted(lifts, reverse=True)
    assert all(t["speeches_in_session"] >= home.MIN_SPEECHES for t in out["typical"])
    assert set(out["lit"]) <= {t["slug"] for t in out["typical"]}
