"""The hand-checked content of the home page: /api/home/featured.

The home page is the one exception to the rule that a stated rule picks every default. A person chooses its sample member,
quote, trend and search ideas in data/home/featured.json. The file holds only references into the database. This route checks
each reference and takes every name, date and count live from the database. An item that fails a check is left out, and
the answer says why in omitted.
"""
import json
import pathlib
import re

from sqlalchemy import text

from pages.common import resolve_tag, slug, tidy_title
from pages.member import seat_tags
from pages.speech import speech_page
from pages.trends import trends_page

FEATURED_FILE = pathlib.Path(__file__).resolve().parent.parent / "data" / "home" / "featured.json"

COUNTS_NOTE = (
    "member.speeches counts all speeches of the member. member.terms lists the Lok Sabha numbers of those speeches. "
    "member.seat and member.state are the seat of the newest term in which the member has a seat. "
    "quote.tags are the tags of the quoted speech, in the order of the Speech page. "
    "quote.tags[].subjects lists the specific subjects under the tag in that speech, each one time. "
    "trend.years counts the speeches with the tag in each calendar year, and tagged counts all speeches with a kept tag in that year."
)


def squash(s):
    """Lower case, with every run of white space as one space. The source text has irregular spaces and line breaks."""
    return re.sub(r"\s+", " ", s or "").strip().lower()


def contains(texts, part):
    """True when part occurs word for word in one of texts, after squash()."""
    p = squash(part)
    return bool(p) and any(p in squash(t) for t in texts)


def load_featured(path=None):
    return json.loads(pathlib.Path(path or FEATURED_FILE).read_text())


def speech_row(conn, speech_id):
    return conn.execute(text("""
        SELECT s.id, s.person_id, s.debate_id, s.seq_start, s.seq_end, pe.name AS member,
               d.debate_date, d.title, d.loksabha, d.source_url
        FROM speeches s JOIN debates d ON d.id = s.debate_id LEFT JOIN persons pe ON pe.id = s.person_id
        WHERE s.id = :i"""), {"i": speech_id}).mappings().first()


def own_turns(conn, s):
    """The labels and texts of the turns of the speech that belong to its member. An interruption by another member is not part of it."""
    return conn.execute(text("""
        SELECT speaker_label, text FROM turns
        WHERE debate_id = :d AND seq BETWEEN :a AND :b AND person_id = :p ORDER BY seq"""),
        {"d": s["debate_id"], "a": s["seq_start"], "b": s["seq_end"], "p": s["person_id"]}).all()


def latest_seat(rows):
    """rows: (term, seat, state). Return (seat, state) of the newest term that has a seat, or (None, None)."""
    with_seat = [r for r in rows if r[1]]
    if not with_seat:
        return None, None
    term, seat, state = max(with_seat, key=lambda r: r[0])
    return seat, state


def quote_tags(tags, domains):
    """The chips of the quote: each tag of the Speech page with its domain and its specific subjects.

    tags: the tags list of the Speech page. domains: {tag name: domain or None}.
    """
    out = []
    for t in tags:
        subjects = []
        for w in t.get("why", []):
            if w.get("subject") and w["subject"] not in subjects:
                subjects.append(w["subject"])
        out.append({"name": t["name"], "slug": t["slug"], "type": t["type"], "domain": domains.get(t["name"]),
                    "subjects": subjects})
    return out


def featured_member(conn, item):
    s = speech_row(conn, item["speech_id"])
    if s is None or s["person_id"] != item["member_id"]:
        return None, "member: the speech does not exist or does not belong to the member"
    labels = [r[0] for r in own_turns(conn, s)]
    if not contains(labels, item["printed"]):
        return None, "member: the printed name does not occur in the speech"
    n, terms = conn.execute(text("""
        SELECT count(*), array_agg(DISTINCT d.loksabha ORDER BY d.loksabha)
        FROM speeches s JOIN debates d ON d.id = s.debate_id WHERE s.person_id = :p"""), {"p": s["person_id"]}).one()
    rows = conn.execute(text("""
        SELECT sp.lok_sabha_term, sp.constituency, st.name FROM speakers sp LEFT JOIN states st ON st.id = sp.state_id
        WHERE sp.person_id = :p"""), {"p": s["person_id"]}).all()
    seat, state = latest_seat(rows)
    seat_id = seat_tags(conn, {(seat, state)}).get((seat, state)) if seat else None
    seat_slug = slug(conn.execute(text("SELECT tag FROM tags WHERE id = :i"), {"i": seat_id}).scalar()) if seat_id else None
    return {"member_id": s["person_id"], "name": s["member"], "printed": item["printed"], "speech_id": s["id"],
            "speeches": n, "terms": list(terms or []), "seat": seat, "state": state, "seat_slug": seat_slug}, None


def featured_quote(conn, item):
    s = speech_row(conn, item["speech_id"])
    if s is None or s["person_id"] is None:
        return None, "quote: the speech does not exist or has no member"
    if not contains([r[1] for r in own_turns(conn, s)], item["text"]):
        return None, "quote: the text does not occur word for word in the member's own turns"
    tags = (speech_page(conn, s["id"]) or {}).get("tags", [])
    domains = dict(conn.execute(text("SELECT tag, domain FROM tags WHERE tag = ANY(:n)"),
                                {"n": [t["name"] for t in tags]}).all()) if tags else {}
    return {"speech_id": s["id"], "text": item["text"], "member": s["member"], "member_id": s["person_id"],
            "date": s["debate_date"].isoformat() if s["debate_date"] else None, "debate": tidy_title(s["title"]),
            "term": s["loksabha"], "source_url": s["source_url"], "tags": quote_tags(tags, domains)}, None


def featured_trend(conn, item):
    t = trends_page(conn, item["tag"], {})
    if t is None:
        return None, "trend: the tag does not exist"
    return {"name": t["name"], "slug": t["slug"], "total": t["total"], "years": t["years"]}, None


def featured_ideas(conn, keys):
    out, omitted = [], []
    for key in keys:
        t = resolve_tag(conn, key)
        if t is None:
            omitted.append(f"search_ideas: no tag {key}")
            continue
        out.append({"name": t["tag"], "slug": slug(t["tag"]), "type": t["type"]})
    return out, omitted


def home_featured(conn, args=None, path=None):
    f = load_featured(path)
    out, omitted = {"counts_note": COUNTS_NOTE}, []
    for key, fn in (("member", featured_member), ("quote", featured_quote), ("trend", featured_trend)):
        if key not in f:
            out[key] = None
            continue
        value, problem = fn(conn, f[key])
        out[key] = value
        if problem:
            omitted.append(problem)
    ideas, problems = featured_ideas(conn, f.get("search_ideas", []))
    out["search_ideas"] = ideas
    out["omitted"] = omitted + problems
    return out


ROUTES = [("/home/featured", home_featured)]
