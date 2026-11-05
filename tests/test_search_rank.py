"""The rules of best-match search: the phrase rule, the join of two lists, and the fall back to word results."""
from pages import search_rank as R
from tests.pages_db import page_conn  # noqa: F401


def test_only_a_search_text_wholly_in_quote_marks_is_a_phrase():
    assert R.phrase_of('"triple talaq"') == "triple talaq"
    assert R.phrase_of("“triple talaq”") == "triple talaq"
    assert R.phrase_of("triple talaq") is None
    assert R.phrase_of('the "triple" talaq') is None


def test_a_speech_in_both_lists_beats_a_speech_at_the_top_of_one_list():
    assert R.fuse([[1, 2, 3], [9, 2]]) == [2, 1, 9, 3]


def test_an_empty_list_keeps_the_order_of_the_other():
    assert R.fuse([[5, 4, 3], []]) == [5, 4, 3]


def test_a_search_text_has_one_form_for_the_stored_vector():
    assert R.normal_query("  Stray   CATTLE ") == "stray cattle"


class FakeResult:
    def scalar(self):
        return None


class FakeConn:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, *a, **k):
        return FakeResult()


class FakeStore:
    def connect(self):
        return FakeConn()


def test_a_failed_model_call_gives_no_vector_and_no_error(monkeypatch):
    def fail(_):
        raise TimeoutError("model is down")
    monkeypatch.setattr(R, "embed_query", fail)
    assert R.query_vector(FakeStore(), "farmers") is None


def test_word_results_stay_and_nginx_does_not_store_them_when_the_model_call_fails(page_conn, monkeypatch):
    import server
    monkeypatch.setattr(R, "embed_query", lambda _: (_ for _ in ()).throw(TimeoutError("down")))
    with server.app.test_client() as c:
        resp = c.get("/api/speeches?q=unusedsearchtextforthistest latur&per_page=1")
    assert resp.status_code == 200
    assert resp.get_json()["by_meaning"] is False
    assert resp.headers["Cache-Control"] == "no-store"
