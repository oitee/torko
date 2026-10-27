"""The "Your MP" page: seats that match a name, the current member of each seat, and the older members."""
import re

from sqlalchemy import text

from pages.common import SPEECH_TAGS_CTE, slug

MAX_SEATS = 12
MAX_TAGS = 5
# Tag types that do not describe a subject. The card hides them.
HIDDEN_TYPES = ("role", "person", "place")


def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def rank_seats(names, q):
    """Order the seat names that match q: exact first, then names that start with q, then the rest.

    Matching ignores case and punctuation. Names inside a group keep alphabetical order.
    """
    k = norm(q)
    if not k:
        return []
    exact = [n for n in names if norm(n) == k]
    starts = [n for n in names if norm(n) != k and norm(n).startswith(k)]
    inside = [n for n in names if not norm(n).startswith(k) and k in norm(n)]
    return (sorted(exact) + sorted(starts) + sorted(inside))[:MAX_SEATS]


def group_members(rows, latest_term):
    """Split member rows into the current members (latest term) and the older members.

    rows: dicts with person_id, term. One entry per person, with the list of terms of this seat.
    """
    people = {}
    for r in rows:
        p = people.setdefault(r["person_id"], {**{k: v for k, v in r.items() if k != "term"}, "terms": []})
        p["terms"].append(r["term"])
        if r["term"] == max(p["terms"]):
            p["party"] = r["party"]
    for p in people.values():
        p["terms"].sort()
    current = [p for p in people.values() if latest_term in p["terms"]]
    older = sorted((p for p in people.values() if latest_term not in p["terms"]),
                   key=lambda p: -max(p["terms"]))
    return current, older


def count_tags(owner, rows):
    """Count speeches per (member, tag). Order: member, then more speeches first, then tag name.

    owner: {speech id: person id}. rows: dicts with speech_id, tag, type. Each (speech, tag) is one row already.
    """
    n = {}
    for r in rows:
        key = (owner[r["speech_id"]], r["tag"], r["type"])
        n[key] = n.get(key, 0) + 1
    out = [{"person_id": k[0], "tag": k[1], "type": k[2], "n": v} for k, v in n.items()]
    return sorted(out, key=lambda x: (x["person_id"], -x["n"], x["tag"]))


def my_mp_page(conn, args):
    q = (args.get("q") or "").strip()
    if not q:
        return {"q": q, "latest_term": None, "seats": [], "seat_count": 0}
    latest = conn.execute(text("SELECT max(lok_sabha_term) FROM speakers")).scalar()
    names = [r[0] for r in conn.execute(text("""
        SELECT DISTINCT constituency FROM speakers
        WHERE constituency IS NOT NULL AND lower(constituency) LIKE '%' || lower(:q) || '%' ESCAPE '\\'"""),
        {"q": re.sub(r"([\\%_])", r"\\\1", q)}).all()]
    # A query with punctuation or spaces may not match by LIKE. Fall back to the normalised match.
    if not names and norm(q):
        allnames = [r[0] for r in conn.execute(text(
            "SELECT DISTINCT constituency FROM speakers WHERE constituency IS NOT NULL")).all()]
        names = [n for n in allnames if norm(q) in norm(n)]
    picked = rank_seats(names, q)
    if not picked:
        return {"q": q, "latest_term": latest, "seats": [], "seat_count": 0}

    rows = conn.execute(text("""
        SELECT DISTINCT ON (sp.constituency, sp.person_id, sp.lok_sabha_term)
               sp.constituency AS seat, st.name AS state, sp.person_id, sp.lok_sabha_term AS term, pe.name AS member,
               p.code AS party
        FROM speakers sp JOIN persons pe ON pe.id = sp.person_id LEFT JOIN parties p ON p.id = sp.party_id
        LEFT JOIN states st ON st.id = sp.state_id
        WHERE sp.constituency = ANY(:seats)
        ORDER BY sp.constituency, sp.person_id, sp.lok_sabha_term, sp.effective_from DESC"""),
        {"seats": picked}).mappings().all()

    seats = []
    cur_ids = set()
    for name in picked:
        current, older = group_members([dict(r) for r in rows if r["seat"] == name], latest)
        seats.append({"seat": name, "slug": slug(name), "current": current, "older": older})
        cur_ids |= {p["person_id"] for p in current}

    tags = {}
    if cur_ids:
        # The speech ids come first, so the tag query reads only the speeches of these members.
        sp = conn.execute(text("SELECT id, person_id FROM speeches WHERE person_id = ANY(:p)"),
                          {"p": list(cur_ids)}).all()
        owner = {sid: pid for sid, pid in sp}
        trows = conn.execute(text(f"""
            WITH {SPEECH_TAGS_CTE}
            SELECT st.speech_id, t.tag, t.type
            FROM speech_tags st JOIN tags t ON t.id = st.tag_id
            WHERE st.speech_id = ANY(:ids) AND t.type <> ALL(:hidden)"""),
            {"ids": list(owner), "hidden": list(HIDDEN_TYPES)}).mappings().all()
        trows = count_tags(owner, trows)
        for r in trows:
            lst = tags.setdefault(r["person_id"], [])
            if len(lst) < MAX_TAGS:
                lst.append({"name": r["tag"], "slug": slug(r["tag"]), "type": r["type"], "speeches": r["n"]})

    for s in seats:
        for p in s["current"]:
            p["top_tags"] = tags.get(p["person_id"], [])
        for p in s["current"] + s["older"]:
            p["id"] = p.pop("person_id")
            del p["seat"]
        s["same_name_note"] = ("More than one current member: two seats may share this name."
                               if len(s["current"]) > 1 else None)
    return {
        "q": q, "latest_term": latest, "seat_count": len(seats), "seats": seats,
        "top_tags_note": f"top_tags: the {MAX_TAGS} tags that most speeches of this member carry. speeches counts "
                         "the speeches of this member with the tag, in all terms. Role, person, and place tags are hidden.",
        "match_note": "q matches any part of the seat name, case-insensitive. Seat names have no state.",
    }


ROUTES = [("/my-mp", lambda conn, args: my_mp_page(conn, args))]
