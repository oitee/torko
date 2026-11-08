"""The sitemap of the public site: the page addresses that search engines may index, as XML.

The sitemap holds:
- the Home page and the Method page,
- each party that had at least one member in the Lok Sabha,
- each member with at least one speech,
- each place tag with at least MIN_PLACE_SPEECHES speeches,
- the TOP_TAGS tags with the most speeches. Place, role and person tags are not in this list.

A speech counts once for a tag. A merged tag counts as its kept tag.
Speech and debate pages are not in the sitemap, because a rebuild of the database gives them new ids.
The sitemap gives no lastmod date. A wrong date is worse than no date.
"""
import os
from urllib.parse import quote
from xml.sax.saxutils import escape

from sqlalchemy import text

from pages.common import SPEECH_TAGS_CTE, slug

MIN_PLACE_SPEECHES = 10
TOP_TAGS = 250
NOT_IN_TOP_TAGS = ("place", "role", "person")
DEFAULT_SITE_URL = "https://torko.in"


def site_url(env=None):
    """The public address of the site, from VITE_SITE_URL, with no "/" at the end."""
    env = os.environ if env is None else env
    return (env.get("VITE_SITE_URL") or DEFAULT_SITE_URL).rstrip("/")


def tag_paths(tags):
    """Return the tag paths and the place paths of the sitemap.

    tags: rows of (id, name, type, status, n), where n is the number of speeches of the tag.
    A slug can belong to more than one tag. The page shows the live tag with the lowest id,
    so a tag is in the sitemap only when its slug opens that tag.
    """
    live = sorted((t for t in tags if t[3] not in ("rejected", "merged")), key=lambda t: t[0])
    opens_tag, opens_place = {}, {}
    for t in live:
        opens_tag.setdefault(slug(t[1]), t[0])
        if t[2] == "place":
            opens_place.setdefault(slug(t[1]), t[0])

    by_count = sorted(live, key=lambda t: (-t[4], t[0]))
    top = [t for t in by_count if t[2] not in NOT_IN_TOP_TAGS and t[4] > 0 and opens_tag[slug(t[1])] == t[0]]
    places = [t for t in by_count if t[2] == "place" and t[4] >= MIN_PLACE_SPEECHES
              and opens_place[slug(t[1])] == t[0]]
    return ([f"/tag/{slug(t[1])}" for t in top[:TOP_TAGS]],
            sorted(f"/place/{slug(t[1])}" for t in places))


def page_paths(conn):
    """Return every path of the sitemap, in a fixed order: Home, Method, parties, members, places, tags."""
    parties = [r[0] for r in conn.execute(text(
        "SELECT code FROM parties WHERE id IN (SELECT party_id FROM speakers) ORDER BY code"))]
    members = [r[0] for r in conn.execute(text(
        "SELECT DISTINCT person_id FROM speeches WHERE person_id IS NOT NULL ORDER BY 1"))]
    tags = conn.execute(text(f"""
        WITH {SPEECH_TAGS_CTE}, n AS (SELECT tag_id, count(DISTINCT speech_id) AS n FROM speech_tags GROUP BY 1)
        SELECT t.id, t.tag, t.type, t.status, COALESCE(n.n, 0) FROM tags t LEFT JOIN n ON n.tag_id = t.id
    """)).all()
    top, places = tag_paths(tags)
    return (["/", "/method"]
            + [f"/party/{quote(code, safe='')}" for code in parties]
            + [f"/member/{pid}" for pid in members]
            + places + top)


def render(base, paths):
    """The sitemap XML for the given site address and paths."""
    rows = "".join(f"  <url><loc>{escape(base + p)}</loc></url>\n" for p in paths)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + rows + "</urlset>\n")
