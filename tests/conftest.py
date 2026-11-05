import pytest
from bs4 import BeautifulSoup


def first_block(html: str, tag: str = "p"):
    return BeautifulSoup(html, "lxml").find(tag)


@pytest.fixture(autouse=True)
def no_model_call_for_a_search(monkeypatch):
    """The tests make no network call. A search with no stored vector falls back to word results."""
    from pages import search_rank

    def refuse(_):
        raise ConnectionError("no network in tests")
    monkeypatch.setattr(search_rank, "embed_query", refuse)
