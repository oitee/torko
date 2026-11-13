"""site_exists.exists picks the check from the key name of the address, and from the rule for a slug."""
import site_exists


def test_an_address_with_no_key_always_exists():
    assert site_exists.exists(None, "/search", {}) is True


def test_a_missing_member_does_not_exist(monkeypatch):
    seen = {}

    def row(conn, sql, key):
        seen["sql"], seen["key"] = sql, key
        return False

    monkeypatch.setitem(site_exists.CHECKS, "member_id", lambda conn, k: row(conn, "SELECT 1 FROM persons WHERE id = :k", k))
    assert site_exists.exists(None, "/member/<int:member_id>", {"member_id": 99999999}) is False
    assert seen["key"] == 99999999 and "persons" in seen["sql"]


def test_a_place_slug_asks_for_a_place_tag_and_a_tag_slug_for_any_tag(monkeypatch):
    calls = []
    monkeypatch.setattr(site_exists, "resolve_tag", lambda conn, key, kind=None: calls.append((key, kind)) or {"id": 1})
    assert site_exists.exists(None, "/place/<slug>", {"slug": "latur"}) is True
    assert site_exists.exists(None, "/tag/<slug>", {"slug": "arrears"}) is True
    assert calls == [("latur", "place"), ("arrears", None)]


def test_an_unknown_tag_does_not_exist(monkeypatch):
    monkeypatch.setattr(site_exists, "resolve_tag", lambda conn, key, kind=None: None)
    assert site_exists.exists(None, "/tag/<slug>", {"slug": "no-such-tag"}) is False
