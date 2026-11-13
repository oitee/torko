"""Does the item of a page address exist? The server asks this before it sends the site.

An address such as /member/99999999 has the form of a page, but no member has that id.
The server then sends the site with status 404, so that search engines do not store an empty page.
Each check reads only the key of the item. It does not build the page data.
"""
from sqlalchemy import text

from pages.common import resolve_tag
from pages.party import find_party


def _row(conn, sql, key):
    return conn.execute(text(sql), {"k": key}).first() is not None


CHECKS = {
    "member_id": lambda conn, k: _row(conn, "SELECT 1 FROM persons WHERE id = :k", k),
    "speech_id": lambda conn, k: _row(conn, "SELECT 1 FROM speeches WHERE id = :k", k),
    "debate_id": lambda conn, k: _row(conn, "SELECT 1 FROM debates WHERE id = :k", k),
    "code": lambda conn, k: find_party(conn, k) is not None,
}


def exists(conn, rule, kw):
    """True when the item that the address names exists. An address with no key, such as /search, always exists."""
    if not kw:
        return True
    (name, key), = kw.items()
    if name == "slug":
        return resolve_tag(conn, key, "place" if rule.startswith("/place/") else None) is not None
    return CHECKS[name](conn, key)
