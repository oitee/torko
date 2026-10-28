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
    return server.app.test_client()


@pytest.mark.parametrize("path", ["/tag/arrears", "/member/1052", "/speech/178379", "/debate/683", "/place/latur",
                                  "/search", "/search?q=arrears"])
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


def test_an_unknown_api_address_keeps_a_plain_404(client):
    resp = client.get("/api/no-such-route")
    assert resp.status_code == 404
    assert INDEX not in resp.get_data(as_text=True)


def test_the_old_dashboard_stays(client):
    assert client.get("/dashboard.html").status_code == 200


def test_a_site_that_is_not_built_says_so(tmp_path, monkeypatch):
    monkeypatch.setattr(server, "WEB_DIST", tmp_path / "missing")
    resp = server.app.test_client().get("/tag/arrears")
    assert resp.status_code == 404
    assert "npm run build" in resp.get_data(as_text=True)
