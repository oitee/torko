from flask import Blueprint

import pages_api


def test_register_skips_missing_modules_and_adds_routes(monkeypatch):
    import types, sys
    mod = types.ModuleType("pages.fake_page")
    mod.ROUTES = [("/fake/<key>", lambda conn, key, args: {"key": key})]
    monkeypatch.setitem(sys.modules, "pages.fake_page", mod)
    bp = Blueprint("t", __name__)
    assert pages_api.register(bp, ["fake_page", "no_such_page"]) == ["fake_page"]


def test_page_routes_sit_directly_under_api():
    import server
    rules = {r.rule for r in server.app.url_map.iter_rules()}
    assert "/api/member/<int:member_id>" in rules and "/api/tags" in rules
    assert not any(r.startswith("/api/pages") for r in rules)
