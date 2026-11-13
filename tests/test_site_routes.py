"""Flask sends the one HTML file of the public site for every page address (web/dist/index.html)."""
import pytest

import server

INDEX = "<!doctype html><div id=root></div>"


@pytest.fixture
def client(tmp_path, monkeypatch):
    (tmp_path / "assets").mkdir()
    (tmp_path / "index.html").write_text(INDEX)
    (tmp_path / "assets" / "index-abc123.js").write_text("console.log(1)")
    monkeypatch.setattr(server, "WEB_DIST", tmp_path)
    monkeypatch.setattr(server.site_exists, "exists", lambda conn, rule, kw: "99999999" not in str(kw.values()))
    monkeypatch.setattr(server.pages_api, "get_engine", lambda: FakeEngine())
    monkeypatch.setattr(server.site_head, "speech_head",
                        lambda conn, i: None if i == 99999999 else {"title": "A · 1 Jan 2020 · Torko", "description": "D"})
    return server.app.test_client()


class FakeEngine:
    def connect(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


@pytest.mark.parametrize("path", ["/", "/tag/arrears", "/member/1052", "/debate/683", "/place/latur",
                                  "/search", "/search?q=arrears", "/method", "/party/BJP", "/parties", "/places", "/trends",
                                  "/my-mp", "/my-mp?q=latur"])
def test_each_page_address_gets_the_site(client, path):
    resp = client.get(path)
    assert resp.status_code == 200
    assert resp.get_data(as_text=True) == INDEX


def test_built_assets_are_sent_and_kept_for_a_year(client):
    resp = client.get("/assets/index-abc123.js")
    assert resp.status_code == 200
    assert resp.get_data(as_text=True) == "console.log(1)"
    assert "max-age=31536000" in resp.headers["Cache-Control"]


@pytest.mark.parametrize("path", ["/no/such/page", "/member/abc", "/dev/components"])
def test_an_address_with_no_page_gets_the_site_with_status_404(client, path):
    resp = client.get(path)
    assert resp.status_code == 404
    assert resp.get_data(as_text=True) == INDEX


@pytest.mark.parametrize("path", ["/member/99999999", "/speech/99999999", "/debate/99999999", "/tag/99999999",
                                  "/place/99999999", "/party/99999999"])
def test_a_page_address_for_an_item_that_does_not_exist_gets_status_404(client, path):
    resp = client.get(path)
    assert resp.status_code == 404
    assert resp.get_data(as_text=True) == INDEX


def test_an_unknown_api_address_keeps_a_plain_404(client):
    resp = client.get("/api/no-such-route")
    assert resp.status_code == 404
    assert INDEX not in resp.get_data(as_text=True)


def test_the_old_dashboard_stays(client):
    assert client.get("/dashboard.html").status_code == 200


def test_the_old_start_page_stays_at_its_file_name(client):
    resp = client.get("/index.html")
    assert resp.status_code == 200
    assert resp.get_data(as_text=True) != INDEX


def test_a_site_that_is_not_built_says_so(tmp_path, monkeypatch):
    monkeypatch.setattr(server, "WEB_DIST", tmp_path / "missing")
    resp = server.app.test_client().get("/tag/arrears")
    assert resp.status_code == 404
    assert "npm run build" in resp.get_data(as_text=True)


def test_a_speech_page_gets_its_own_title_and_description(tmp_path, monkeypatch):
    page = '<title>Torko</title><meta name="description" content="x" /><meta property="og:title" content="x" />' \
           '<meta property="og:description" content="x" /><div id=root></div>'
    (tmp_path / "index.html").write_text(page)
    monkeypatch.setattr(server, "WEB_DIST", tmp_path)
    monkeypatch.setattr(server.pages_api, "get_engine", lambda: FakeEngine())
    monkeypatch.setattr(server.site_head, "speech_head", lambda conn, i: {"title": "A · 1 Jan 2020 · Torko", "description": "D"})
    resp = server.app.test_client().get("/speech/178379")
    body = resp.get_data(as_text=True)
    assert resp.status_code == 200
    assert "<title>A · 1 Jan 2020 · Torko</title>" in body
    assert 'name="description" content="D"' in body and 'property="og:description" content="D"' in body
