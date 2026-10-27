"""The party page: the data of one party, as JSON.

Route: /party/<code>. The code is parties.code and the match ignores case. An unknown code gives None.
The party of a speech is the party of the member at the date of the debate.
A tagged speech is a speech with at least one kept tag. A speaker with no known member is left out.
Every query is read-only.
"""
from collections import Counter, defaultdict

from sqlalchemy import text

from pages.common import PARTY_AT_DATE, SPEECH_TAGS_CTE, cached, slug, speech_tags_cte

TERMS = {13: "1999–2004", 14: "2004–2009", 15: "2009–2014", 16: "2014–2019", 17: "2019–2024", 18: "2024–"}
SUBJECT_KINDS = {"topic", "scheme", "law", "institution", "group", "person"}

MIN_PARTY_TAGGED = 30   # a party-term with fewer tagged speeches shows no typical subjects
MIN_N_TERM = 6          # least tagged speeches of the party on a subject, in one term
MIN_N_ALL = 15          # the same, over all terms (subjects and places)
MIN_N_PLACE = 10        # the same for places
GENERAL_SHARE = 0.03    # a subject on more than 3% of all tagged speeches of the term is general
TOP = 8
PROCEDURE = "Parliament and Procedure"


def corpus(conn):
    """Return (tags, by_term_all, all_n, hidden) for all parties. The result is kept for one hour.

    tags: tag id to tag row. by_term_all: term to Counter of tag id to tagged speeches of all parties.
    all_n: term to the number of tagged speeches of all parties. hidden: the ids of tags that no party page shows
    as a subject, which are the tags that name a party, and the procedure tags.
    """
    def load():
        tags = {r["id"]: dict(r) for r in conn.execute(text("SELECT id, tag, type, domain FROM tags")).mappings()}
        by_term_all = defaultdict(Counter)
        for term, tid, n in conn.execute(text(f"""
                WITH {SPEECH_TAGS_CTE}
                SELECT d.loksabha, st.tag_id, count(*) FROM speech_tags st
                JOIN speeches s ON s.id = st.speech_id JOIN debates d ON d.id = s.debate_id
                WHERE s.person_id IS NOT NULL GROUP BY 1, 2""")).all():
            by_term_all[term][tid] = n
        all_n = {term: n for term, n in conn.execute(text(f"""
            WITH {SPEECH_TAGS_CTE}
            SELECT d.loksabha, count(DISTINCT st.speech_id) FROM speech_tags st
            JOIN speeches s ON s.id = st.speech_id JOIN debates d ON d.id = s.debate_id
            WHERE s.person_id IS NOT NULL GROUP BY 1""")).all()}
        pnames = {n for (n,) in conn.execute(text("SELECT name FROM parties")).all()}
        codes = {c for (c,) in conn.execute(text("SELECT code FROM parties")).all()}
        hidden = {tid for tid, t in tags.items() if t["tag"] in pnames or t["tag"] in codes or t["domain"] == PROCEDURE}
        return tags, by_term_all, all_n, hidden
    return cached("party_corpus", load)


def find_party(conn, code):
    """Return the party row for a code, ignoring case, or None."""
    if not code:
        return None
    return conn.execute(text("SELECT id, code, name, colour FROM parties WHERE upper(code) = upper(:c) ORDER BY id LIMIT 1"),
                        {"c": str(code)}).mappings().first()


# The speeches of a party: the speeches of members who ever had the party, where the party at the date
# of the debate is the party. A speaker with no known member is left out.
PARTY_SPEECHES_CTE = f"""
party_speeches AS MATERIALIZED (
    SELECT s.id, s.person_id, d.loksabha AS term
    FROM speeches s JOIN debates d ON d.id = s.debate_id {PARTY_AT_DATE}
    WHERE s.person_id IN (SELECT person_id FROM speakers WHERE party_id = :pid) AND pa.party = :code
)"""


def _party_cte():
    return PARTY_SPEECHES_CTE + ", " + speech_tags_cte("si.speech_id IN (SELECT id FROM party_speeches)")


def party_counts(conn, party):
    """Return the party's counts per term, and its members with three or more speeches on a tag.

    The result is (p_cnt, p_sp, p_people, speakers, member_tag). Each of the first four is a dict keyed by term:
    p_cnt holds a Counter of tag id to tagged speeches of the party, p_sp the number of tagged speeches,
    p_people the number of members with a tagged speech, and speakers the number of members with any speech.
    member_tag maps a tag id to a list of (person id, tagged speeches with the tag, terms), most speeches first.
    """
    conn.execute(text("SET LOCAL jit = off"))
    rows = conn.execute(text(f"""
        WITH {_party_cte()},
        pr AS MATERIALIZED (
            SELECT ps.id AS sp, ps.person_id AS pid, ps.term, st.tag_id
            FROM speech_tags st JOIN party_speeches ps ON ps.id = st.speech_id)
        SELECT 'tag' AS k, term, tag_id, count(*) AS n, NULL::int AS pid, NULL::int[] AS terms FROM pr GROUP BY term, tag_id
        UNION ALL SELECT 'sp', term, NULL, count(DISTINCT sp), NULL, NULL FROM pr GROUP BY term
        UNION ALL SELECT 'people', term, NULL, count(DISTINCT pid), NULL, NULL FROM pr GROUP BY term
        UNION ALL SELECT 'speaking', term, NULL, count(DISTINCT person_id), NULL, NULL FROM party_speeches GROUP BY term
        UNION ALL SELECT 'member', NULL, tag_id, count(*), pid, array_agg(DISTINCT term) FROM pr
                  GROUP BY tag_id, pid HAVING count(*) >= 3"""),
        {"pid": party["id"], "code": party["code"]}).all()
    p_cnt, p_sp, p_people, speakers = defaultdict(Counter), {}, {}, {}
    member_tag = defaultdict(list)
    for k, term, tid, n, pid, terms in rows:
        if k == "tag":
            p_cnt[term][tid] = n
        elif k == "member":
            member_tag[tid].append((pid, n, sorted(terms)))
        else:
            {"sp": p_sp, "people": p_people, "speaking": speakers}[k][term] = n
    for v in member_tag.values():
        v.sort(key=lambda x: (-x[1], x[0]))
    return p_cnt, p_sp, p_people, speakers, member_tag


def lift_rows(party_cnt, party_n, all_cnt, all_n, tags, min_n, kinds, skip=frozenset()):
    """Return the tags of one party, ordered by lift (high first), then by count (high first), then by name.

    lift = (n / party_n) / (all / all_n). n counts the party's tagged speeches with the tag.
    party_n counts the party's tagged speeches. all and all_n are the same counts over all parties.
    """
    out = []
    for tid, n in party_cnt.items():
        t = tags[tid]
        if n < min_n or tid in skip or t["type"] not in kinds:
            continue
        share, base = n / party_n, all_cnt[tid] / all_n
        out.append({"tag": t["tag"], "slug": slug(t["tag"]), "type": t["type"], "n": n,
                    "share": round(share, 4), "base": round(base, 4), "lift": round(share / base, 2)})
    out.sort(key=lambda r: (-r["lift"], -r["n"], r["tag"]))
    return out


def general_tags(counter, total, share=GENERAL_SHARE):
    return {tid for tid, n in counter.items() if n / total > share}


def party_page(conn, code, args=None):
    party = find_party(conn, code)
    if party is None:
        return None
    code = party["code"]
    tags, by_term_all, all_n, hidden = corpus(conn)
    p_cnt, p_sp, p_people, speakers, member_tag = party_counts(conn, party)

    terms = []
    for term in sorted(TERMS):
        pn = p_sp.get(term, 0)
        row = {"term": term, "years": TERMS[term], "members_speaking": speakers.get(term, 0),
               "members_tagged": p_people.get(term, 0), "tagged": pn, "all_tagged": all_n.get(term, 0),
               "share_of_tagged": round(pn / all_n[term], 4) if all_n.get(term) else None, "typical": []}
        if pn >= MIN_PARTY_TAGGED:
            general = general_tags(by_term_all[term], all_n[term])
            row["typical"] = lift_rows(p_cnt[term], pn, by_term_all[term], all_n[term], tags,
                                       MIN_N_TERM, SUBJECT_KINDS, general | hidden)[:TOP]
        terms.append(row)

    tot_all, tot_party = Counter(), Counter()
    for term in all_n:
        tot_all.update(by_term_all[term])
        tot_party.update(p_cnt[term])
    n_all = sum(all_n.values())
    n_party = sum(p_sp.get(t, 0) for t in all_n)
    typ_all, places = [], []
    if n_party:
        typ_all = lift_rows(tot_party, n_party, tot_all, n_all, tags, MIN_N_ALL, SUBJECT_KINDS,
                            general_tags(tot_all, n_all) | hidden)[:TOP]
        places = lift_rows(tot_party, n_party, tot_all, n_all, tags, MIN_N_PLACE, {"place"})[:TOP]

    # The members of the party who spoke most on its top 3 subjects of all terms.
    name_to_id = {v["tag"]: k for k, v in tags.items()}
    top_ids = [name_to_id[r["tag"]] for r in typ_all[:3]]
    top3 = []
    for r, tid in zip(typ_all[:3], top_ids):
        best = member_tag.get(tid, [])[:5]
        people = {x["id"]: x for x in conn.execute(text(
            "SELECT id, name FROM persons WHERE id = ANY(:i)"), {"i": [b[0] for b in best]}).mappings()}
        top3.append({"tag": r["tag"], "slug": r["slug"], "members": [
            {"id": pid, "name": people[pid]["name"], "n": n, "terms": terms}
            for pid, n, terms in best if n >= 3]})

    return {
        "code": code, "name": party["name"], "colour": party["colour"], "total_tagged": n_party, "all_tagged": n_all,
        "terms": terms, "typical_all": typ_all, "places": places, "top3": top3,
        "rules": {"min_party_tagged": MIN_PARTY_TAGGED, "min_n_term": MIN_N_TERM, "min_n_all": MIN_N_ALL,
                  "min_n_place": MIN_N_PLACE, "general_share": GENERAL_SHARE, "top": TOP},
        "counts_note": (
            "total_tagged counts the tagged speeches of the party over all terms, and all_tagged counts the tagged "
            "speeches of all parties over all terms. In terms[], tagged counts the party's tagged speeches in the term, "
            "all_tagged counts the tagged speeches of all parties in the term, and share_of_tagged is tagged divided by "
            "all_tagged. members_speaking counts the members who spoke for the party in the term, tagged or not. "
            "members_tagged counts the members with at least one tagged speech. In typical, typical_all and places, "
            "n counts the party's tagged speeches with the tag, share is n divided by the party's tagged speeches "
            "(of the term, or of all terms), base is the same share over all parties, and lift is share divided by base. "
            "In top3, n counts the member's tagged speeches with the tag, all in the party's time. "
            "The party of a speech is the party of the member at the date of the debate."),
    }


ROUTES = [("/party/<code>", party_page)]
