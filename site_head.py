"""The title and the description of a page, written into the HTML before the server sends it.

Link previews and search engines do not run JavaScript. They read only the first HTML file.
Without this step, every page has the same title "Torko" and the same description.
Example: /speech/178379 gets the title "Mahua Moitra · 17 Dec 2025 · Torko" and its TLDR as the description.
"""
import html
import re

from sqlalchemy import text

DESCRIPTION_MAX = 300


def shorten(words, limit=DESCRIPTION_MAX):
    """Cut a text at the last whole word before the limit, and add an ellipsis character."""
    words = " ".join((words or "").split())
    if len(words) <= limit:
        return words
    return words[:limit].rsplit(" ", 1)[0].rstrip(",;:") + "…"


def plain(words):
    """Remove HTML tags and entities. Some debate titles hold tags, such as <sup>th</sup> or <span style=...>."""
    return html.unescape(re.sub(r"<[^>]*>", "", words or ""))


def speech_title(member, date):
    """The same title that the Speech page sets in the browser: member, date, Torko."""
    name = member or "Speech"
    when = f"{date.day} {date:%b %Y}" if date else ""
    return " · ".join(p for p in (name, when, "Torko") if p)


def speech_head(conn, speech_id):
    """The title and the description of a speech, or None when the speech does not exist.

    The description is the TLDR. A speech with no TLDR gets the title of its debate.
    """
    row = conn.execute(text("""
        SELECT pe.name AS member, d.debate_date, d.title, se.summary
        FROM speeches s JOIN debates d ON d.id = s.debate_id
        LEFT JOIN persons pe ON pe.id = s.person_id
        LEFT JOIN speech_extractions se ON se.speech_id = s.id
        WHERE s.id = :i"""), {"i": speech_id}).mappings().first()
    if row is None:
        return None
    description = row["summary"] or (f"A speech in the Lok Sabha debate: {plain(row['title'])}" if row["title"] else "")
    return {"title": speech_title(row["member"], row["debate_date"]), "description": shorten(description)}


def _set_meta(page, attr, key, value):
    """Replace the content of one meta tag. The tag must be in the page already."""
    pattern = re.compile(rf'(<meta {attr}="{re.escape(key)}" content=")[^"]*(")')
    return pattern.sub(lambda m: m.group(1) + html.escape(value, quote=True) + m.group(2), page, count=1)


def render(page, head):
    """Write the title and the description of head into the HTML page. Values are escaped for HTML."""
    title, description = head["title"], head["description"]
    page = re.sub(r"<title>[^<]*</title>", lambda m: f"<title>{html.escape(title)}</title>", page, count=1)
    page = _set_meta(page, "property", "og:title", title)
    if description:
        page = _set_meta(page, "name", "description", description)
        page = _set_meta(page, "property", "og:description", description)
    return page
