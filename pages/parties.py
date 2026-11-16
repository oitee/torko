"""The parties index: every party with at least one speech, as JSON.

Route: /parties. The party of a speech is the party of the member at the date of the debate.
A speech with no identified member, or with a member who has no known party at that date, belongs to no party.
Every query is read-only. The result is kept for one hour.
"""
from collections import Counter, defaultdict

from sqlalchemy import text

from pages.common import PARTY_AT_DATE, SPEECH_TAGS_CTE, cached
from pages.party import (MIN_MEMBERS, MIN_N_TERM, MIN_PARTY_TAGGED, PROCEDURE, SUBJECT_KINDS, TERMS, corpus,
                         general_tags, rank_rows)

ORDER_RULE = "by speeches, most first, then by party code"
WEIGHT_PARTIES = 6     # the chart of speaking weight shows the parties with the most speeches
WEIGHT_MIN_MEMBERS = 3 # a term with fewer members of the party who spoke has no point, because one member swings it
CARD_SUBJECTS = 3      # the subjects shown for each party of a term
GRID_PARTIES = 8       # the grid of a term shows the parties with the most members in the term
GRID_DOMAINS = 8       # and the subject areas with the most tagged speeches in the term
GRID_MIN_SPEECHES = 20 # a cell with fewer tagged speeches of the party has no value
# A row of speakers with one of these sources is a person with no Lok Sabha seat in the term.
NO_SEAT_SOURCES = ("not-a-member", "last-term-fallback", "added-person")


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
    speeches = defaultdict(dict)
    for r in rows:
        speeches[r["term"]][r["code"]] = r["speeches"]
    return {"terms": [{"term": t, **house[t]} for t in terms], "series": series, "speeches": speeches}


def load_term_members(conn):
    """Return {term: {party code: members}}: the members with a Lok Sabha seat in the term, by party.

    The party is the party of the member at the start of the term. A member who came in at a by-election counts too,
    so a term can have more members than the 543 seats of the House. A person with no seat in the term is left out.
    """
    out = defaultdict(dict)
    for term, code, n in conn.execute(text("""
            SELECT sp.lok_sabha_term, pa.code, count(DISTINCT sp.person_id)
            FROM speakers sp JOIN lok_sabhas ls ON ls.number = sp.lok_sabha_term JOIN parties pa ON pa.id = sp.party_id
            WHERE sp.effective_from = ls.start_date AND sp.source <> ALL(:no_seat) GROUP BY 1, 2"""),
            {"no_seat": list(NO_SEAT_SOURCES)}).all():
        out[term][code] = n
    return out


def load_term_tags(conn):
    """Return the tagged-speech counts of each party in each term, for the subjects and the subject areas.

    The result is (tag_n, tag_members, tagged, area_n, house_area, house_tagged).
    tag_n: (party, term) to Counter of tag id to tagged speeches. tag_members: the same, to members who spoke on the tag.
    tagged: (party, term) to the tagged speeches of the party. area_n: (party, term) to Counter of subject area to
    speeches with one or more tags of the area. house_area and house_tagged: the same two counts over all parties of a term.
    """
    conn.execute(text("SET LOCAL jit = off"))
    rows = conn.execute(text(f"""
        WITH {SPEECH_TAGS_CTE},
        pr AS MATERIALIZED (
            SELECT s.id AS sp, s.person_id AS pid, d.loksabha AS term, pa.party, st.tag_id, t.domain
            FROM speech_tags st JOIN speeches s ON s.id = st.speech_id JOIN debates d ON d.id = s.debate_id
            JOIN tags t ON t.id = st.tag_id {PARTY_AT_DATE}
            WHERE s.person_id IS NOT NULL AND pa.party IS NOT NULL),
        -- pr has one row for each (speech, tag), so a speech with 3 tags is there 3 times.
        -- The two lists below remove the copies once, so the speech counts need no count(DISTINCT) of their own.
        per_speech AS MATERIALIZED (SELECT DISTINCT sp, term, party FROM pr),
        per_area AS MATERIALIZED (SELECT DISTINCT sp, term, party, domain FROM pr WHERE domain IS NOT NULL)
        SELECT 'tag' AS k, party, term, tag_id, NULL AS area, count(*) AS n, count(DISTINCT pid) AS m FROM pr GROUP BY 2, 3, 4
        UNION ALL SELECT 'tagged', party, term, NULL, NULL, count(*), NULL FROM per_speech GROUP BY 2, 3
        UNION ALL SELECT 'area', party, term, NULL, domain, count(*), NULL FROM per_area GROUP BY 2, 3, 5
        UNION ALL SELECT 'house_area', NULL, term, NULL, domain, count(*), NULL FROM per_area GROUP BY 3, 5
        UNION ALL SELECT 'house_tagged', NULL, term, NULL, NULL, count(*), NULL FROM per_speech GROUP BY 3""")).all()
    tag_n, tag_members, area_n, house_area = defaultdict(Counter), defaultdict(Counter), defaultdict(Counter), defaultdict(Counter)
    tagged, house_tagged = {}, {}
    for k, party, term, tid, area, n, m in rows:
        if k == "tag":
            tag_n[(party, term)][tid] = n
            tag_members[(party, term)][tid] = m
        elif k == "tagged":
            tagged[(party, term)] = n
        elif k == "area":
            area_n[(party, term)][area] = n
        elif k == "house_area":
            house_area[term][area] = n
        else:
            house_tagged[term] = n
    return tag_n, tag_members, tagged, area_n, house_area, house_tagged


def area_cell(n, party_tagged, house_n, house_tagged):
    """One cell of the grid. lift = (n / party_tagged) / (house_n / house_tagged). A cell with too few speeches has no lift."""
    if n < GRID_MIN_SPEECHES or not party_tagged or not house_n:
        return {"n": n, "lift": None}
    return {"n": n, "lift": round((n / party_tagged) / (house_n / house_tagged), 2)}


def load_terms(conn, weights):
    """Return one row for each term: the members and the speeches of each party, its subjects, and the grid of subject areas."""
    members = load_term_members(conn)
    tag_n, tag_members, tagged, area_n, house_area, house_tagged = load_term_tags(conn)
    tags, by_term_all, all_n, hidden = corpus(conn)
    out = []
    for h in weights["terms"]:
        term = h["term"]
        seats = members.get(term, {})
        total_members = sum(seats.values())
        general = general_tags(by_term_all[term], all_n[term]) if all_n.get(term) else set()
        rows = []
        for code in sorted(set(seats) | set(weights["speeches"].get(term, {}))):
            speeches = weights["speeches"].get(term, {}).get(code, 0)
            pn = tagged.get((code, term), 0)
            typical = []
            if pn >= MIN_PARTY_TAGGED:
                typical = rank_rows(tag_n[(code, term)], pn, by_term_all[term], all_n[term], tags, MIN_N_TERM,
                                    SUBJECT_KINDS, general | hidden, tag_members[(code, term)], MIN_MEMBERS)[:CARD_SUBJECTS]
            rows.append({
                "code": code, "members": seats.get(code, 0), "speeches": speeches, "tagged": pn,
                "member_share": round(seats.get(code, 0) / total_members, 4) if total_members else None,
                "speech_share": round(speeches / h["speeches"], 4) if h["speeches"] else None,
                "typical": [{"tag": r["tag"], "slug": r["slug"], "n": r["n"], "lift": r["lift"]} for r in typical]})
        rows.sort(key=lambda r: (-r["members"], -r["speeches"], r["code"]))
        areas = sorted((a for a in house_area[term] if a != PROCEDURE), key=lambda a: (-house_area[term][a], a))[:GRID_DOMAINS]
        grid_rows = [{"code": r["code"], "tagged": r["tagged"], "cells": [
            area_cell(area_n[(r["code"], term)][a], r["tagged"], house_area[term][a], house_tagged[term]) for a in areas]}
            for r in rows[:GRID_PARTIES]]
        out.append({"term": term, "years": TERMS.get(term, ""), "members": total_members, "speeches": h["speeches"],
                    "tagged": house_tagged.get(term, 0), "parties": rows,
                    "grid": {"areas": [{"name": a, "speeches": house_area[term][a]} for a in areas], "rows": grid_rows}})
    return out


def parties_page(conn, args=None):
    rows, total = cached("parties_index", lambda: load_parties(conn))
    codes = [r["code"] for r in rows[:WEIGHT_PARTIES]]
    weights = cached("parties_weights", lambda: load_weights(conn, codes))
    terms = cached("parties_terms", lambda: load_terms(conn, weights))
    return {
        "total": total, "count": len(rows), "order": ORDER_RULE, "parties": rows,
        "weights": {"terms": weights["terms"], "series": weights["series"]}, "terms": terms,
        "terms_rule": (
            "terms[] has one row for each Lok Sabha. members counts the members with a seat in the term, by the party at "
            "the start of the term. A by-election adds a member, so the members of a term can be more than 543. "
            "speeches counts the speeches of members with a known party. member_share and speech_share are shares of these two. "
            f"typical lists up to {CARD_SUBJECTS} subjects that the party raises more than the House in the term, by the "
            "rule of the party page. grid has the "
            f"{GRID_PARTIES} parties with the most members in the term and the {GRID_DOMAINS} subject areas with the most "
            "tagged speeches. A cell counts the tagged speeches of the party with one or more tags of the area. "
            "lift = (cell / tagged speeches of the party) / (the same for all parties). "
            f"A cell with fewer than {GRID_MIN_SPEECHES} speeches has no lift."),
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
