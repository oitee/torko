"""The bill page: what one bill does, where the members stood on it, by party, the reasons for and against, and
sample speeches.

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
REASON_SIDES = ["for", "against"]
TOP_REASONS = 5
MIN_REASON_MEMBERS = 2
OTHERS_ROW_MIN_SHARED = 4  # A side needs this many reasons of 2 or more members before its one-member points go to one row.
SMALL_BILL_MEMBERS = 5  # The chart of the bills list uses the same limit.

MEMBER_RULE = (
    "Each member counts one time. A member with a for speech and an against speech is mixed. "
    "Otherwise, a member with a for or an against speech has that stance, also when another speech is mixed. "
    "A member with only mixed and unclear speeches is mixed. A member with only unclear speeches is unclear. A speech with no identified member is not in these counts."
)
PARTY_RULE = (
    "Each member counts one time, in the party of the member on the date of the first speech on the bill. "
    f"The {TOP_PARTIES} parties with the most members who spoke have their own row. "
    "The other parties, and the members with no known party, are in Others."
)
SAMPLE_RULE = (
    f"Up to {SAMPLES_PER_STANCE} speeches for each stance, one for each member, by the members whose stance on the bill "
    "is the same as the stance of the speech. A for or against speech must make no point on the other side. "
    "The speeches with the most points on their side come first, then the longest. "
    "Mixed speeches have no points, so the longest come first."
)


SMALL_BILL_RULE = (
    f"Fewer than {SMALL_BILL_MEMBERS} members spoke on this bill, so the page shows no charts. "
    "It shows every speech with a stance on the bill, in the order of the debate."
)


def member_stance(stances):
    """The stance of one member from the stances of all the speeches of the member on the bill.

    A clear speech (for or against) wins over a mixed speech. A for speech and an against speech give mixed.
    """
    found = set(stances)
    clear = found & {"for", "against"}
    if len(clear) == 2:
        return "mixed"
    if clear:
        return clear.pop()
    return "mixed" if "mixed" in found else "unclear"


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


def sample_ids(rows, members, per_stance=SAMPLES_PER_STANCE):
    """[(stance, speech id)]: for each stance in SAMPLE_STANCES, the clearest speeches, by the rule in SAMPLE_RULE.

    Each row is one speech: speech_id, stance, person_id, words, and own, the count of its points on the side of
    its stance, and other, the count of its points on the other side. members is the result of members_of().
    """
    out = []
    for stance in SAMPLE_STANCES:
        pick = [r for r in rows if r["stance"] == stance and r["person_id"] is not None
                and members[r["person_id"]]["stance"] == stance
                and r["other"] == 0]
        pick.sort(key=lambda r: (-r["own"], -(r["words"] or 0), r["speech_id"]))
        seen = set()
        for r in pick:
            if r["person_id"] not in seen and len(seen) < per_stance:
                seen.add(r["person_id"])
                out.append((stance, r["speech_id"]))
    return out


REASON_RULE = (
    "A model read each speech and wrote down each point that the speech made for or against the bill, with a quote "
    "of the words of the member. A second model call put the points of one side into reasons, each with a short label. "
    "When a side had 5 reasons or more, a third call joined the reasons that gave the same reason in other words. "
    "The reasons are in order of the number of identified members who gave the reason, then the number of points. "
    "Each member shows one time in a reason, with the first quote. "
    "A reason that only one member gave is a point of that member, not a reason of the House. "
    f"When a side has {OTHERS_ROW_MIN_SHARED} or more reasons that 2 or more members gave, such points are in one last row of that side. "
    "Otherwise, the side shows each such point as a reason of its own, after the other reasons."
)


def reason_rows(rows):
    """Turn the points of one bill into the reasons of each side, in the order of REASON_RULE.

    Each row is one point: group (bill_arguments.id), side, label, person_id, member, party, speech_id, quote.
    The rows come in the order of the debate, so the first quote of a member is the first row of the member.
    """
    groups = {}
    for row in rows:
        group = groups.setdefault(row["group"], {"side": row["side"], "label": row["label"], "points": 0, "who": {}, "anon": []})
        group["points"] += 1
        quote = {"member_id": row["person_id"], "member": row["member"], "party": row["party"],
                 "speech_id": row["speech_id"], "quote": row["quote"]}
        if row["person_id"] is None:
            group["anon"].append(quote)
        else:
            group["who"].setdefault(row["person_id"], quote)
    out = {side: [] for side in REASON_SIDES}
    for gid, group in groups.items():
        if group["side"] in out:
            out[group["side"]].append({"id": gid, "label": group["label"], "members": len(group["who"]), "points": group["points"],
                                   "quotes": list(group["who"].values()) + group["anon"]})
    for side in out:
        out[side].sort(key=lambda group: (-group["members"], -group["points"], group["label"]))
    return out


def split_one_member(reasons):
    """Moves the reasons of one member to a last row of their side, by the rule in REASON_RULE.

    Returns (reasons, others), each {side: [reason]}. A side with fewer than OTHERS_ROW_MIN_SHARED reasons of
    MIN_REASON_MEMBERS members keeps all its reasons, and its others list is empty. A reason that only unidentified
    members gave counts as one member.
    """
    kept, others = {}, {}
    for side, rows in reasons.items():
        shared = [r for r in rows if r["members"] >= MIN_REASON_MEMBERS]
        if len(shared) >= OTHERS_ROW_MIN_SHARED:
            kept[side], others[side] = shared, [r for r in rows if r["members"] < MIN_REASON_MEMBERS]
        else:
            kept[side], others[side] = rows, []
    return kept, others


def canonical_id(conn, bill_id):
    """The id of the kept bill, or None. A bill that the merge step folded into another bill gives the id of that bill.

    The merge step points each folded bill straight at its kept bill, so one step is enough.
    """
    return conn.execute(text("""
        SELECT k.id FROM bills b JOIN bills k ON k.id = COALESCE(b.merged_into, b.id)
        WHERE b.id = :b AND k.merged_into IS NULL"""), {"b": bill_id}).scalar()


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
        SELECT ss.speech_id, ss.stance, s.person_id, s.word_count AS words, pa.party, d.debate_date,
               COALESCE(pt.n_for, 0) AS n_for, COALESCE(pt.n_against, 0) AS n_against
        FROM speech_stances ss JOIN speeches s ON s.id = ss.speech_id JOIN debates d ON d.id = s.debate_id
        LEFT JOIN (SELECT speech_id, count(*) FILTER (WHERE side = 'for') AS n_for,
                          count(*) FILTER (WHERE side = 'against') AS n_against
                   FROM speech_arguments WHERE bill_id = :b AND quote_found GROUP BY speech_id) pt
          ON pt.speech_id = ss.speech_id
        {PARTY_AT_DATE}
        WHERE ss.bill_id = :b ORDER BY d.debate_date, s.seq_start"""), {"b": kept}).mappings().all()
    rows = [dict(row, own=row["n_against"] if row["stance"] == "against" else row["n_for"],
                 other=row["n_for"] if row["stance"] == "against" else row["n_against"]) for row in rows]

    members = members_of(rows)
    small = len(members) < SMALL_BILL_MEMBERS
    samples = [(row["stance"], row["speech_id"]) for row in rows] if small else sample_ids(rows, members)
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

    points = conn.execute(text(f"""
        SELECT ba.id AS "group", ba.side, ba.label, s.person_id, pe.name AS member, pa.party, a.speech_id, a.quote
        FROM bill_arguments ba
        JOIN speech_arguments a ON a.bill_argument_id = ba.id
        JOIN speeches s ON s.id = a.speech_id JOIN debates d ON d.id = s.debate_id
        LEFT JOIN persons pe ON pe.id = s.person_id
        {PARTY_AT_DATE}
        WHERE ba.bill_id = :b ORDER BY d.debate_date, s.seq_start, a.position"""), {"b": kept}).mappings().all()

    dates = sorted({debate["debate_date"] for debate in debates if debate["debate_date"]})
    colours = party_colours(conn)
    parties = party_rows(members)
    for party in parties:
        party["colour"] = colours.get(party["party"])
    reasons, reason_others = split_one_member(reason_rows(points))
    return {
        "id": kept, "asked_id": bill_id, "name": bill["name"], "year": bill["year"], "summary": bill["summary"],
        "summary_note": "Summary generated solely from the text of the debates. No external source used",
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
        "sample_rule": SMALL_BILL_RULE if small else SAMPLE_RULE,
        "small": small,
        "reasons": reasons,
        "reason_others": reason_others,
        "reason_rule": REASON_RULE,
        "top_reasons": TOP_REASONS,
        "together": [{"id": joint["id"], "name": joint["name"], "year": joint["year"]} for joint in together],
        "same_name": [{"id": other["id"], "name": other["name"], "year": other["year"], "term": key_term(other["bill_key"]),
                       "side": other["side"]} for other in same_name],
        "same_name_note": "A different bill with the same name in the Lok Sabha term before or after this one.",
        "counts_note": "speeches counts the speeches with a stance on this bill. speech_counts splits them by stance. "
                       "members and member_counts count identified members. A stance is what a member said, not a vote.",
    }


ROUTES = [("/bill/<int:bill_id>", bill_page)]
