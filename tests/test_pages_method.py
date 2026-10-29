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


def test_words_keeps_the_first_words_and_marks_a_cut():
    assert method.words("a b c d", 2) == "a b …"
    assert method.words("a b", 5) == "a b"
    assert method.words(None, 3) == ""


def test_the_old_font_example_decodes_to_readable_hindi():
    from legacy_hindi import decode_legacy_hindi
    out = decode_legacy_hindi(method.LEGACY_EXAMPLE["text"])
    assert out == "अध्यक्ष महोदय, गृह मंत्री जी ने कहा था कि झाबुआ के मामले में 3 तारीख को बयान देंगे।"
    assert "É" not in out


def test_examples_on_database(page_conn):  # noqa: F811
    ex = method.method_page(page_conn, {})["examples"]
    assert ex["legacy"]["text"] and ex["legacy"]["debate"] is not None
    if ex["speech"]:
        own = [t for t in ex["speech"]["turns"] if t["own"]]
        assert own and len(own) < len(ex["speech"]["turns"])
    if ex["subjects"]:
        assert any(i["kept"] for i in ex["subjects"]["items"])
    if ex["subject_group"]:
        assert len(ex["subject_group"]["names"]) >= 2
