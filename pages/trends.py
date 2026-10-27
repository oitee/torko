"""The data of the trends page: how often one tag was raised in each session, and how well the pipeline covered each session.

A reader must see where the data is thin. So every session row carries its coverage:
speeches (all speeches of the session), tagged (speeches with at least one kept item of any tag), and the share of tagged over speeches.
The rate of a session is the speeches that carry the tag per 1,000 tagged speeches of that session.
A session with fewer than MIN_TAGGED tagged speeches is marked thin. Its rate is given but it is not used for the peak.
"""
from sqlalchemy import text

from pages.common import slug as to_slug
from pages.common import cached, resolve_tag
from pages.place import speech_ids_for_tag

MIN_TAGGED = 300

COUNTS_NOTE = (
    "n counts the speeches of the session that carry a kept tag of this tag, each speech once. "
    "tagged is the denominator: the speeches of the session that have at least one kept item of any tag. "
    "speeches counts all speeches of the session, tagged or not. "
    "per1000 is n per 1,000 tagged speeches of the same session. "
    "strength is the peak per1000 divided by the per1000 over all non-thin sessions together. "
    "A thin session has fewer than min_tagged tagged speeches. It is left out of peak and strength. "
    "years has one row for each calendar year of the debate date. "
    "years.n counts the speeches of the year that carry the tag, each speech once, by the same rule as sessions.n. "
    "years.tagged counts the speeches of the year that have at least one kept item of any tag. "
    "A session that crosses New Year is split between two years, so a year is not a session."
)


def core_range(days):
    """The dates of the main sitting block of a session.

    Some debates carry a date far from their session (for example answers filed late).
    So the range is the biggest block of days with no gap above 35 days,
    with 2% of the debates trimmed from each end. Input: sorted (day, debates) pairs.
    Returns first, last, and the number of debates outside the block.
    """
    if not days:
        return None, None, 0
    blocks, cur = [], [days[0]]
    for prev, d in zip(days, days[1:]):
        if (d[0] - prev[0]).days > 35:
            blocks.append(cur)
            cur = []
        cur.append(d)
    blocks.append(cur)
    best = max(blocks, key=lambda b: sum(n for _, n in b))
    total = sum(n for _, n in best)
    lo = hi = None
    run = 0
    for day, n in best:
        run += n
        if lo is None and run >= 0.02 * total:
            lo = day
        if run <= 0.98 * total or hi is None:
            hi = day
    return str(lo), str(hi), sum(n for _, n in days) - total


def session_coverage(conn):
    """Per (term, session): first and last date of the main block, stray debates, all speeches, tagged speeches."""
    def load():
        days = {}
        for term, session, day, n in conn.execute(text(
                "SELECT loksabha, session, debate_date, count(*) FROM debates WHERE debate_date IS NOT NULL "
                "GROUP BY 1, 2, 3 ORDER BY 1, 2, 3")).all():
            days.setdefault((term, session), []).append((day, n))
        counts = {(r[0], r[1]): (r[2], r[3]) for r in conn.execute(text("""
            SELECT d.loksabha, d.session, count(*) AS speeches,
                   count(*) FILTER (WHERE EXISTS (SELECT 1 FROM speech_items si WHERE si.speech_id = s.id AND si.kept)) AS tagged
            FROM debates d JOIN speeches s ON s.debate_id = d.id GROUP BY 1, 2"""))}
        keys = sorted(set(days) | set(counts) | {(r[0], r[1]) for r in conn.execute(text("SELECT DISTINCT loksabha, session FROM debates"))})
        out = []
        for term, session in keys:
            first, last, stray = core_range(days.get((term, session), []))
            sp, tg = counts.get((term, session), (0, 0))
            out.append({"term": term, "session": session, "first": first, "last": last, "stray_debates": stray,
                        "speeches": sp, "tagged": tg})
        return out
    return cached("session_coverage", load)


def year_tagged(conn):
    """Per calendar year of the debate date: the speeches with at least one kept item of any tag."""
    return cached("year_tagged", lambda: {int(y): n for y, n in conn.execute(text("""
        SELECT extract(year FROM d.debate_date), count(*) FROM debates d JOIN speeches s ON s.debate_id = d.id
        WHERE d.debate_date IS NOT NULL AND EXISTS (SELECT 1 FROM speech_items si WHERE si.speech_id = s.id AND si.kept)
        GROUP BY 1"""))})


def rate_per_1000(n, tagged):
    return round(1000 * n / tagged, 2) if tagged else None


def shape(rows, min_tagged=MIN_TAGGED):
    """From rows with n and tagged, return (peak index or None, strength).

    Only non-thin sessions count. strength = the peak rate / the rate over all non-thin sessions.
    Ties for the peak go to the earlier session.
    """
    ok = [i for i, r in enumerate(rows) if r["tagged"] >= min_tagged]
    if not ok:
        return None, 0
    n_all = sum(rows[i]["n"] for i in ok)
    overall = 1000 * n_all / sum(rows[i]["tagged"] for i in ok)
    peak = max(ok, key=lambda i: (rows[i]["n"] / rows[i]["tagged"], -i))
    if not overall:
        return None, 0
    return peak, round(1000 * rows[peak]["n"] / rows[peak]["tagged"] / overall, 1)


def trends_page(conn, slug, args):
    t = resolve_tag(conn, slug)
    if t is None:
        return None
    ids = speech_ids_for_tag(conn, t["id"])
    per = {}
    months = {}
    per_year = {}
    for y, n in conn.execute(text("""
            SELECT extract(year FROM d.debate_date), count(*) FROM speeches s JOIN debates d ON d.id = s.debate_id
            WHERE s.id = ANY(:ids) AND d.debate_date IS NOT NULL GROUP BY 1"""), {"ids": ids}):
        per_year[int(y)] = n
    for r in conn.execute(text("""
            SELECT d.loksabha AS term, d.session, to_char(date_trunc('month', d.debate_date), 'YYYY-MM') AS m, count(*) AS n
            FROM speeches s JOIN debates d ON d.id = s.debate_id WHERE s.id = ANY(:ids) GROUP BY 1, 2, 3"""), {"ids": ids}).mappings():
        key = (r["term"], r["session"])
        per[key] = per.get(key, 0) + r["n"]
        if r["m"]:
            months.setdefault(key, []).append((-r["n"], r["m"]))
    sessions = []
    for c in session_coverage(conn):
        key = (c["term"], c["session"])
        n = per.get(key, 0)
        peak_month = min(months[key])[1] if key in months else None  # most speeches, earlier month on a tie
        sessions.append({**c, "n": n, "per1000": rate_per_1000(n, c["tagged"]),
                         "tagged_share": round(c["tagged"] / c["speeches"], 3) if c["speeches"] else None,
                         "thin": c["tagged"] < MIN_TAGGED, "peak_month": peak_month})
    tagged_by_year = year_tagged(conn)
    years = [{"year": y, "n": per_year.get(y, 0), "tagged": tagged_by_year.get(y, 0)}
             for y in sorted(set(tagged_by_year) | set(per_year))]
    peak, strength = shape(sessions)
    return {
        "name": t["tag"], "slug": to_slug(t["tag"]), "type": t["type"], "subtype": t["subtype"], "domain": t["domain"],
        "description": t["description"], "aliases": t["aliases"],
        "total": len(ids), "min_tagged": MIN_TAGGED, "strength": strength,
        "peak": {"term": sessions[peak]["term"], "session": sessions[peak]["session"]} if peak is not None else None,
        "counts_note": COUNTS_NOTE,
        "order_notes": {"sessions": "by Lok Sabha term, then session number; every session of the database is listed, also those with n = 0",
                        "years": "by calendar year, every year with a debate"},
        "sessions": sessions, "years": years,
    }


ROUTES = [("/trends/<slug>", trends_page)]
