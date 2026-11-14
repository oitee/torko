"""The bill page: what one bill does, where the members stood on it, by party, and sample speeches.

The stance of a speech comes from the table speech_stances: one row for each speech and each kept bill of its debate.
A stance is what a member said in a speech. It is not a vote.
"""
from sqlalchemy import text

from bill_extract import key_term
from pages.common import PARTY_AT_DATE, party_colours, speech_rows, tidy_title

STANCES = ["for", "against", "mixed", "unclear"]
SAMPLE_STANCES = ["for", "against", "mixed"]
TOP_PARTIES = 7
SAMPLES_PER_STANCE = 3
OTHERS = "Others"

MEMBER_RULE = (
    "Each member counts one time. A member with only one clear stance (for or against) in all speeches has that stance. "
    "A member with a mixed speech, or with both for and against speeches, is mixed. "
    "A member with only unclear speeches is unclear. A speech with no identified member is not in these counts."
)
PARTY_RULE = (
    "Each member counts one time, in the party of the member on the date of the first speech on the bill. "
    f"The {TOP_PARTIES} parties with the most members who spoke have their own row. "
    "The other parties, and the members with no known party, are in Others."
)
SAMPLE_RULE = (
    f"Up to {SAMPLES_PER_STANCE} speeches for each stance: the longest speech of that stance from each of the "
    f"{SAMPLES_PER_STANCE} parties with the most members of that stance. A party with no known code does not count."
)


def member_stance(stances):
    """The stance of one member from the stances of all the speeches of the member on the bill."""
    clear = {s for s in stances if s != "unclear"}
    if not clear:
        return "unclear"
    if "mixed" in clear or clear == {"for", "against"}:
        return "mixed"
    return clear.pop()


def stance_counts(values):
    out = {s: 0 for s in STANCES}
    for v in values:
        out[v] += 1
    return out


def members_of(rows):
    """One entry for each identified member: {person_id: {stance, party, first}}. rows are in date order."""
    members = {}
    for r in rows:
        if r["person_id"] is None:
            continue
        m = members.setdefault(r["person_id"], {"stances": [], "party": r["party"]})
        m["stances"].append(r["stance"])
    return {pid: {"stance": member_stance(m["stances"]), "party": m["party"]} for pid, m in members.items()}


def party_rows(members):
    """Rows of {party, members, counts}, in order of members who spoke. The last row is Others when it has members."""
    by_party = {}
    for m in members.values():
        by_party.setdefault(m["party"], []).append(m["stance"])
    named = sorted(((p, s) for p, s in by_party.items() if p), key=lambda x: (-len(x[1]), x[0]))
    out = [{"party": p, "members": len(s), "counts": stance_counts(s)} for p, s in named[:TOP_PARTIES]]
    rest = [st for _, s in named[TOP_PARTIES:] for st in s] + by_party.get(None, [])
    if rest:
        out.append({"party": OTHERS, "members": len(rest), "counts": stance_counts(rest), "no_party": len(by_party.get(None, []))})
    return out


def sample_ids(rows, per_stance=SAMPLES_PER_STANCE):
    """[(stance, speech id)]: for each stance in SAMPLE_STANCES, the longest speech of that stance from each of
    the parties with the most members of that stance, one speech for each party."""
    out = []
    for stance in SAMPLE_STANCES:
        pick = [r for r in rows if r["stance"] == stance and r["party"]]
        members = {}
        for r in pick:
            members.setdefault(r["party"], set()).add(r["person_id"])
        for party in sorted(members, key=lambda p: (-len(members[p]), p))[:per_stance]:
            best = max((r for r in pick if r["party"] == party), key=lambda r: (r["words"] or 0, -r["speech_id"]))
            out.append((stance, best["speech_id"]))
    return out


def canonical_id(conn, bill_id):
    """The id of the kept bill. A bill that the merge step folded into another bill gives the id of that bill."""
    seen = set()
    while bill_id not in seen:
        seen.add(bill_id)
        row = conn.execute(text("SELECT merged_into FROM bills WHERE id = :b"), {"b": bill_id}).first()
        if row is None:
            return None
        if row[0] is None:
            return bill_id
        bill_id = row[0]
    return None


def bill_page(conn, bill_id, args=None):
    kept = canonical_id(conn, bill_id)
    if kept is None:
        return None
    bill = conn.execute(text("SELECT id, name, year, summary FROM bills WHERE id = :b"), {"b": kept}).mappings().first()

    debates = conn.execute(text("""
        SELECT DISTINCT d.id, d.loksabha, d.session, d.dbslno, d.debate_date, d.title, d.source_url
        FROM debate_bills db JOIN bills x ON x.id = db.bill_id
        JOIN debates d ON (d.loksabha, d.session, d.dbslno) = (db.loksabha, db.session, db.dbslno)
        WHERE db.kept AND COALESCE(x.merged_into, x.id) = :b
        ORDER BY d.debate_date, d.dbslno"""), {"b": kept}).mappings().all()
    debate_ids = [debate["id"] for debate in debates]

    rows = conn.execute(text(f"""
        SELECT ss.speech_id, ss.stance, s.person_id, s.word_count AS words, pa.party, d.debate_date
        FROM speech_stances ss JOIN speeches s ON s.id = ss.speech_id JOIN debates d ON d.id = s.debate_id
        {PARTY_AT_DATE}
        WHERE ss.bill_id = :b ORDER BY d.debate_date, s.seq_start"""), {"b": kept}).mappings().all()
    rows = [dict(row) for row in rows]

    members = members_of(rows)
    samples = sample_ids(rows)
    sample_rows = {row["id"]: row for row in speech_rows(conn, [sid for _, sid in samples], with_tags=False)}

    together = conn.execute(text("""
        SELECT DISTINCT k.id, k.name, k.year
        FROM debate_bills db JOIN bills x ON x.id = db.bill_id
        JOIN bills k ON k.id = COALESCE(x.merged_into, x.id)
        JOIN debates d ON (d.loksabha, d.session, d.dbslno) = (db.loksabha, db.session, db.dbslno)
        WHERE db.kept AND d.id = ANY(:ids) AND k.id <> :b ORDER BY k.year, k.name"""),
        {"ids": debate_ids, "b": kept}).mappings().all() if debate_ids else []

    # A bill does not continue into a new Lok Sabha. A bill of the same name in the term before or after is
    # a different bill with its own page. bills.next_id links the two.
    same_name = conn.execute(text("""
        SELECT id, name, year, bill_key, 'next' AS side FROM bills WHERE id = (SELECT next_id FROM bills WHERE id = :b)
        UNION ALL
        SELECT id, name, year, bill_key, 'previous' FROM bills WHERE next_id = :b AND merged_into IS NULL
        ORDER BY bill_key"""), {"b": kept}).mappings().all()

    dates = sorted({debate["debate_date"] for debate in debates if debate["debate_date"]})
    colours = party_colours(conn)
    parties = party_rows(members)
    for party in parties:
        party["colour"] = colours.get(party["party"])
    return {
        "id": kept, "asked_id": bill_id, "name": bill["name"], "year": bill["year"], "summary": bill["summary"],
        "summary_note": "A model wrote this summary from the text of the debates on the bill. It uses no other source.",
        "terms": sorted({debate["loksabha"] for debate in debates}),
        "first_date": dates[0].isoformat() if dates else None,
        "last_date": dates[-1].isoformat() if dates else None,
        "days": len(dates),
        "debates": [{"id": debate["id"], "title": tidy_title(" ".join((debate["title"] or "").split())),
                     "date": debate["debate_date"].isoformat() if debate["debate_date"] else None,
                     "term": debate["loksabha"], "session": debate["session"], "source_url": debate["source_url"]} for debate in debates],
        "speeches": len(rows),
        "speech_counts": stance_counts(row["stance"] for row in rows),
        "members": len(members),
        "member_counts": stance_counts(member["stance"] for member in members.values()),
        "member_rule": MEMBER_RULE,
        "unidentified_speeches": sum(1 for row in rows if row["person_id"] is None),
        "parties": parties,
        "party_rule": PARTY_RULE,
        "samples": [{**sample_rows[sid], "stance": stance} for stance, sid in samples if sid in sample_rows],
        "sample_rule": SAMPLE_RULE,
        "together": [{"id": joint["id"], "name": joint["name"], "year": joint["year"]} for joint in together],
        "same_name": [{"id": other["id"], "name": other["name"], "year": other["year"], "term": key_term(other["bill_key"]),
                       "side": other["side"]} for other in same_name],
        "same_name_note": "A different bill with the same name in the Lok Sabha term before or after this one.",
        "counts_note": "speeches counts the speeches with a stance on this bill. speech_counts splits them by stance. "
                       "members and member_counts count identified members. A stance is what a member said, not a vote.",
    }


ROUTES = [("/bill/<int:bill_id>", bill_page)]
