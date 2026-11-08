"""The parties index: every party with at least one speech, as JSON.

Route: /parties. The party of a speech is the party of the member at the date of the debate.
A speech with no identified member, or with a member who has no known party at that date, belongs to no party.
Every query is read-only. The result is kept for one hour.
"""
from sqlalchemy import text

from pages.common import PARTY_AT_DATE, cached

ORDER_RULE = "by speeches, most first, then by party code"
WEIGHT_PARTIES = 6     # the chart of speaking weight shows the parties with the most speeches
WEIGHT_MIN_MEMBERS = 3 # a term with fewer members of the party who spoke has no point, because one member swings it


def load_parties(conn):
    """Return (rows, total) for all parties. total is the number of speeches with an identified member."""
    rows = conn.execute(text(f"""
        SELECT pa.party AS code, count(*) AS speeches, count(DISTINCT s.person_id) AS members,
               array_agg(DISTINCT d.loksabha ORDER BY d.loksabha) AS terms,
               min(d.debate_date) AS first, max(d.debate_date) AS last
        FROM speeches s JOIN debates d ON d.id = s.debate_id {PARTY_AT_DATE}
        WHERE s.person_id IS NOT NULL AND pa.party IS NOT NULL GROUP BY 1""")).mappings().all()
    names = {r["code"]: (r["name"], r["colour"]) for r in conn.execute(text(
        "SELECT DISTINCT ON (code) code, name, colour FROM parties ORDER BY code, id")).mappings()}
    total = conn.execute(text("SELECT count(*) FROM speeches WHERE person_id IS NOT NULL")).scalar()
    out = [{"code": r["code"], "name": names.get(r["code"], (r["code"], None))[0],
            "colour": names.get(r["code"], (None, None))[1], "speeches": r["speeches"], "members": r["members"],
            "terms": list(r["terms"]), "first": str(r["first"]) if r["first"] else None,
            "last": str(r["last"]) if r["last"] else None} for r in rows]
    out.sort(key=lambda r: (-r["speeches"], r["code"]))
    return out, total


def load_weights(conn, codes):
    """Speaking weight of each party in each term: speeches for each member who spoke, against the same for the House.

    weight = (speeches of the party / members of the party who spoke) / (speeches of the House / members of the House who spoke).
    The House counts the speeches of members with a known party. A weight of 2 means the members of the party spoke
    twice as often as the members of the House, on average.
    """
    rows = conn.execute(text(f"""
        SELECT pa.party AS code, d.loksabha AS term, count(*) AS speeches, count(DISTINCT s.person_id) AS members
        FROM speeches s JOIN debates d ON d.id = s.debate_id {PARTY_AT_DATE}
        WHERE s.person_id IS NOT NULL AND pa.party IS NOT NULL GROUP BY 1, 2""")).mappings().all()
    by_key = {(r["code"], r["term"]): r for r in rows}
    house = {}
    for r in rows:
        h = house.setdefault(r["term"], {"speeches": 0, "members": 0})
        h["speeches"] += r["speeches"]
        h["members"] += r["members"]
    terms = sorted(house)
    series = []
    for code in codes:
        points = []
        for t in terms:
            r = by_key.get((code, t))
            if r is None or r["members"] < WEIGHT_MIN_MEMBERS:
                points.append({"term": t, "speeches": r["speeches"] if r else 0, "members": r["members"] if r else 0, "weight": None})
                continue
            per_member = r["speeches"] / r["members"]
            per_house = house[t]["speeches"] / house[t]["members"]
            points.append({"term": t, "speeches": r["speeches"], "members": r["members"], "weight": round(per_member / per_house, 3)})
        series.append({"code": code, "points": points})
    return {"terms": [{"term": t, **house[t]} for t in terms], "series": series}


def parties_page(conn, args=None):
    rows, total = cached("parties_index", lambda: load_parties(conn))
    codes = [r["code"] for r in rows[:WEIGHT_PARTIES]]
    weights = cached("parties_weights", lambda: load_weights(conn, codes))
    return {
        "total": total, "count": len(rows), "order": ORDER_RULE, "parties": rows, "weights": weights,
        "weights_rule": (
            f"The {WEIGHT_PARTIES} parties with the most speeches. Weight = (speeches of the party / members of the party who spoke) "
            "/ (speeches of the House / members of the House who spoke), in each term. The House counts members with a known party. "
            f"A term with fewer than {WEIGHT_MIN_MEMBERS} members of the party who spoke has no point."),
        "counts_note": (
            "speeches counts the speeches of the party, all of them, tagged or not. total counts all speeches "
            "with an identified member, so the speeches of all parties add up to less than total. "
            "members counts the members who spoke for the party. terms lists the Lok Sabha numbers with a speech of the party. "
            "The party of a speech is the party of the member at the date of the debate."),
    }


ROUTES = [("/parties", parties_page)]
