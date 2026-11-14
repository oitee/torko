"""The bills landing page: every kept bill with a stance count, three short lists, and the data of the chart.

A bill here is a kept bill (bills.merged_into IS NULL) with at least one speech in speech_stances.
The stance of a member on a bill uses the rule of the bill page: pages.bill.member_stance.
"""
from collections import defaultdict

from sqlalchemy import text

from pages.bill import STANCES, member_stance, stance_counts
from pages.common import cached, slug, speech_tags_cte

CHART_MIN_MEMBERS = 5
OPPOSED_MIN_MEMBERS = 10
SHORT_LIST = 5
TAGS_PER_BILL = 5
TAG_CHOICES = 40

RULES = {
    "latest": "By the last day of debate on the bill.",
    "most_members": "By the number of members who spoke on the bill, in all terms.",
    "most_opposed": f"By the share of members who spoke against the bill. Only bills with {OPPOSED_MIN_MEMBERS} or more members who spoke.",
    "chart": f"Each dot is one bill with {CHART_MIN_MEMBERS} or more members who spoke. "
             "The height is the share of these members who spoke against the bill. The size is the number of members. "
             "The label in each term names the bill with the most members who spoke.",
    "member": "Each member counts one time for each bill. A member with only one clear stance (for or against) has that stance. "
              "A member with a mixed speech, or with both for and against speeches, is mixed. "
              "A member with only unclear speeches is unclear. A speech with no identified member is not in the member counts.",
    "tags": f"The tags of a bill are the {TAGS_PER_BILL} tags with most speeches on the bill. "
            "Tags of places, persons, roles and parliamentary procedure are left out. "
            f"The filter offers the {TAG_CHOICES} tags that most bills have.",
}


def bill_rows(stance_rows):
    """Fold rows of (bill_id, speech_id, person_id, stance) into {bill_id: {speeches, members, counts}}."""
    speeches = defaultdict(set)
    by_member = defaultdict(lambda: defaultdict(list))
    for bill_id, speech_id, person_id, stance in stance_rows:
        speeches[bill_id].add(speech_id)
        if person_id is not None:
            by_member[bill_id][person_id].append(stance)
    out = {}
    for bill_id, ids in speeches.items():
        members = by_member.get(bill_id, {})
        out[bill_id] = {"speeches": len(ids), "members": len(members),
                        "counts": stance_counts(member_stance(s) for s in members.values())}
    return out


def against_share(b):
    return b["counts"]["against"] / b["members"] if b["members"] else 0.0


def short_lists(bills):
    latest = sorted(bills, key=lambda b: (b["last_date"] or "", b["members"]), reverse=True)
    most = sorted(bills, key=lambda b: (-b["members"], -(b["year"] or 0)))
    opposed = sorted((b for b in bills if b["members"] >= OPPOSED_MIN_MEMBERS),
                     key=lambda b: (-against_share(b), -b["members"]))
    return {"latest": [b["id"] for b in latest[:SHORT_LIST]],
            "most_members": [b["id"] for b in most[:SHORT_LIST]],
            "most_opposed": [b["id"] for b in opposed[:SHORT_LIST]]}


def term_labels(bills):
    """The id of the bill with the most members in each term, among the bills in the chart."""
    best = {}
    for b in bills:
        if b["members"] < CHART_MIN_MEMBERS or b["term"] is None:
            continue
        cur = best.get(b["term"])
        if cur is None or (b["members"], b["id"]) > (cur["members"], cur["id"]):
            best[b["term"]] = b
    return sorted(b["id"] for b in best.values())


def load(conn):
    meta = conn.execute(text("""
        SELECT b.id, b.name, b.year, b.amendment_ordinal IS NOT NULL AS amendment,
               min(d.loksabha) AS term, min(d.debate_date) AS first_date, max(d.debate_date) AS last_date
        FROM bills b
        JOIN bills x ON COALESCE(x.merged_into, x.id) = b.id
        JOIN debate_bills db ON db.bill_id = x.id AND db.kept
        JOIN debates d ON (d.loksabha, d.session, d.dbslno) = (db.loksabha, db.session, db.dbslno)
        WHERE b.merged_into IS NULL GROUP BY b.id""")).mappings().all()
    stats = bill_rows(conn.execute(text("""
        SELECT ss.bill_id, ss.speech_id, s.person_id, ss.stance
        FROM speech_stances ss JOIN speeches s ON s.id = ss.speech_id""")).all())
    tags = defaultdict(list)
    for bill_id, tag, n in conn.execute(text(f"""
        WITH {speech_tags_cte("si.speech_id IN (SELECT speech_id FROM speech_stances)")}, per AS (
            SELECT ss.bill_id, t.tag, count(DISTINCT ss.speech_id) n,
                   row_number() OVER (PARTITION BY ss.bill_id ORDER BY count(DISTINCT ss.speech_id) DESC, t.tag) rk
            FROM speech_stances ss JOIN speech_tags st ON st.speech_id = ss.speech_id JOIN tags t ON t.id = st.tag_id
            WHERE t.type NOT IN ('place', 'person', 'role') AND t.domain IS DISTINCT FROM 'Parliament and Procedure'
            GROUP BY ss.bill_id, t.tag)
        SELECT bill_id, tag, n FROM per WHERE rk <= :k ORDER BY bill_id, rk"""), {"k": TAGS_PER_BILL}):
        tags[bill_id].append(tag)

    names = {}
    count = defaultdict(int)
    for info in meta:
        if info["id"] not in stats:
            continue
        for tag_name in tags.get(info["id"], []):
            names[slug(tag_name)] = tag_name
            count[slug(tag_name)] += 1
    choices = sorted(count, key=lambda slug_key: (-count[slug_key], names[slug_key]))[:TAG_CHOICES]
    index = {slug_key: i for i, slug_key in enumerate(choices)}

    bills = []
    for info in meta:
        stat = stats.get(info["id"])
        if not stat:
            continue
        bills.append({"id": info["id"], "name": info["name"], "year": info["year"], "amendment": info["amendment"],
                      "term": info["term"],
                      "first_date": info["first_date"].isoformat() if info["first_date"] else None,
                      "last_date": info["last_date"].isoformat() if info["last_date"] else None,
                      **stat, "tags": [index[slug(tag_name)] for tag_name in tags.get(info["id"], []) if slug(tag_name) in index]})
    members_any = conn.execute(text("""SELECT count(DISTINCT s.person_id), count(DISTINCT ss.speech_id)
        FROM speech_stances ss JOIN speeches s ON s.id = ss.speech_id""")).first()
    bills.sort(key=lambda bill: (bill["last_date"] or "", bill["id"]), reverse=True)
    years = [bill["year"] for bill in bills if bill["year"]]
    return {
        "bills": bills,
        "lists": short_lists(bills),
        "labels": term_labels(bills),
        "tag_choices": [{"slug": slug_key, "name": names[slug_key], "bills": count[slug_key]} for slug_key in choices],
        "totals": {"bills": len(bills), "speeches": members_any[1], "members": members_any[0],
                   "terms": sorted({bill["term"] for bill in bills if bill["term"]}),
                   "first_year": min(years) if years else None, "last_year": max(years) if years else None},
        "chart_min_members": CHART_MIN_MEMBERS,
        "stances": STANCES,
        "rules": RULES,
        "tags_note": "tags of a bill are positions in tag_choices.",
        "counts_note": "members counts identified members who spoke on the bill. counts splits them by stance. "
                       "speeches counts the speeches with a stance on the bill. A stance is what a member said, not a vote.",
    }


def bills_page(conn, args=None):
    return cached("bills_page", lambda: load(conn))


ROUTES = [("/bills", bills_page)]
