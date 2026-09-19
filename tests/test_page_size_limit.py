"""The debate list must not return more rows than MAX_PAGE_SIZE in one request."""
import pytest

import server


@pytest.fixture
def captured(monkeypatch):
    calls = {}

    def fake_list_debates(**kwargs):
        calls.update(kwargs)
        return {"total": 0, "results": []}

    monkeypatch.setattr(server.dashboard_db, "list_debates", fake_list_debates)
    return calls


@pytest.mark.parametrize(
    "requested, expected",
    [("1000000", server.MAX_PAGE_SIZE), ("10", 10), ("0", 1), ("-5", 1), (None, 20)],
)
def test_page_size_is_clamped(captured, requested, expected):
    url = "/api/dashboard/debates" + (f"?pageSize={requested}" if requested else "")
    resp = server.app.test_client().get(url)
    assert resp.status_code == 200
    assert captured["page_size"] == expected
    assert resp.get_json()["pageSize"] == expected
