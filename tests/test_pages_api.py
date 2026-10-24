from flask import Blueprint

import pages_api


def test_register_skips_missing_modules_and_adds_routes(monkeypatch):
    import types, sys
    mod = types.ModuleType("pages.fake_page")
    mod.ROUTES = [("/fake/<key>", lambda conn, key, args: {"key": key})]
    monkeypatch.setitem(sys.modules, "pages.fake_page", mod)
    bp = Blueprint("t", __name__)
    assert pages_api.register(bp, ["fake_page", "no_such_page"]) == ["fake_page"]
