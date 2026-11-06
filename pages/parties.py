"""The parties index: every party with at least one speech, as JSON.

Route: /parties. The party of a speech is the party of the member at the date of the debate.
A speech with no identified member, or with a member who has no known party at that date, belongs to no party.
Every query is read-only. The result is kept for one hour.
"""
from sqlalchemy import text

from pages.common import PARTY_AT_DATE, cached

ORDER_RULE = "by speeches, most first, then by party code"


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


def parties_page(conn, args=None):
    rows, total = cached("parties_index", lambda: load_parties(conn))
    return {
        "total": total, "count": len(rows), "order": ORDER_RULE, "parties": rows,
        "counts_note": (
            "speeches counts the speeches of the party, all of them, tagged or not. total counts all speeches "
            "with an identified member, so the speeches of all parties add up to less than total. "
            "members counts the members who spoke for the party. terms lists the Lok Sabha numbers with a speech of the party. "
            "The party of a speech is the party of the member at the date of the debate."),
    }


ROUTES = [("/parties", parties_page)]
