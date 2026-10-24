from pages.speech import clean_layout, group_reasons, speech_page, split_title
from tests.pages_db import page_conn  # noqa: F401


def test_clean_layout_removes_marks_only():
    assert clean_layout("a [r11] b (l1/1150 c") == "a b c"


def test_split_title_laid():
    assert split_title("Report  - Laid ") == ("Report", True)
    assert split_title("Report") == ("Report", False)


def test_group_reasons_attaches_items():
    tags = [{"name": "A", "source": "llm"}, {"name": "B", "source": "summary_tag"}]
    items = [{"tag": "A", "source": "llm", "mention": "x"}]
    out = group_reasons(tags, items)
    assert out[0]["why"] == [{"source": "llm", "mention": "x"}]
    assert out[1]["why"] == [] and out[1]["source_note"]


def test_speech_route(page_conn):
    r = speech_page(page_conn, 176660, {})
    assert r["id"] == 176660 and r["turn_list"]
    llm = [t for t in r["tags"] if t["source"] == "llm"]
    assert llm and all(t["why"] for t in r["tags"])
    assert any(w["mention"] for t in llm for w in t["why"])


def test_speech_unknown(page_conn):
    assert speech_page(page_conn, -5, {}) is None
