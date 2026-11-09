"""The places index: every state with the Lok Sabha seats of the record, as JSON.

Route: /places. A seat is a constituency name in the speakers table, without a bracket suffix such as (SC).
A seat has the state of its latest record. A seat has a place page when a place tag has the same slug.
speeches counts the speeches that carry the place tag, each speech once. A seat with no place tag has no count.
Every query is read-only. The result is kept for one hour.
"""
import re

from sqlalchemy import text

from pages.common import cached, slug
from pages.place import corpus_tag_counts

FEATURED = 5   # the seats with the most speeches, for the examples on the Your MP page
STATE_ORDER = "by name, A to Z"
SEAT_ORDER = "by name, A to Z, inside the state"
FEATURED_RULE = f"the {FEATURED} seats with the most speeches that carry the place tag, most first"


def load_places(conn):
    per, _ = corpus_tag_counts(conn)
    tags = {slug(r["tag"]): (r["id"], r["tag"]) for r in conn.execute(text(
        "SELECT id, tag FROM tags WHERE type = 'place' AND status <> 'merged' ORDER BY id DESC")).mappings()}
    seat_rows = conn.execute(text("""
        SELECT DISTINCT ON (name) regexp_replace(sp.constituency, '\\s*\\(.*\\)$', '') AS name, st.name AS state
        FROM speakers sp LEFT JOIN states st ON st.id = sp.state_id
        WHERE sp.constituency IS NOT NULL
        ORDER BY name, sp.lok_sabha_term DESC, sp.effective_from DESC""")).mappings().all()
    states = {}
    for r in seat_rows:
        name = re.sub(r"\s+", " ", r["name"]).strip()
        state = r["state"] or "No state"
        key = slug(name)
        tid = tags.get(key, (None, None))[0]
        seat = {"name": name, "slug": key, "page": tid is not None, "speeches": per.get(tid, 0) if tid else None}
        states.setdefault(state, []).append(seat)
    out = []
    for state in sorted(states):
        seats = sorted(states[state], key=lambda s: s["name"].lower())
        sk = slug(state)
        out.append({"name": state, "slug": sk, "page": sk in tags,
                    "speeches": per.get(tags[sk][0], 0) if sk in tags else None, "seats": seats})
    every = [dict(s, state=st["name"]) for st in out for s in st["seats"] if s["page"]]
    featured = sorted(every, key=lambda s: (-(s["speeches"] or 0), s["name"]))[:FEATURED]
    return out, featured


def places_page(conn, args=None):
    states, featured = cached("places_index", lambda: load_places(conn))
    return {
        "state_count": len(states), "seat_count": sum(len(s["seats"]) for s in states),
        "states": states, "featured": featured,
        "order": {"states": STATE_ORDER, "seats": SEAT_ORDER, "featured": FEATURED_RULE},
        "counts_note": (
            "speeches counts the speeches that carry the place tag, each speech once. A speech that only names the place "
            "in its text, and has no tag for it, is not counted. page is true when the place has its own page. "
            "A seat keeps the state of its latest record."),
    }


ROUTES = [("/places", places_page)]
