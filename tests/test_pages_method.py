from pages import method
from tests.pages_db import page_conn  # noqa: F401


def test_routes():
    assert method.ROUTES == [("/method", method.method_page)]


def test_unread_text_is_fixed_text_with_a_source():
    u = method.UNREAD_TEXT
    assert u["text"] == "about 13.6%" and u["first_term"] == {"term": 13, "text": "32.5%"}
    assert "No query computes it" in u["source"]


def test_method_page_on_database(page_conn):  # noqa: F811
    from sqlalchemy import text
    out = method.method_page(page_conn, {})
    t, s = out["turns"], out["speeches"]
    assert t["member"] + t["chair_or_crowd"] + t["no_name"] == t["total"]
    assert t["total"] == page_conn.execute(text("SELECT count(*) FROM turns")).scalar()
    assert s["total"] == page_conn.execute(text("SELECT count(*) FROM speeches")).scalar()
    assert s["with_tldr"] <= s["eligible"] <= s["with_member"] <= s["total"]
    assert s["with_tag"] <= s["eligible"]
    labels = out["example"]["labels"]
    assert 0 < len(labels) <= method.EXAMPLE_LABELS
    assert [r["n"] for r in labels] == sorted((r["n"] for r in labels), reverse=True)
