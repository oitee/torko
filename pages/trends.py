"""The data of the trends page: how often one tag was raised in each session, and how well the pipeline covered each session.

A reader must see where the data is thin. So every session row carries its coverage:
speeches (all speeches of the session), tagged (speeches with at least one kept item of any tag), and the share of tagged over speeches.
The rate of a session is the speeches that carry the tag per 1,000 tagged speeches of that session.
A session with fewer than MIN_TAGGED tagged speeches is marked thin. Its rate is given but it is not used for the peak.
"""
from statistics import median

from sqlalchemy import text

from pages.common import slug as to_slug
from pages.common import SPEECH_TAGS_CTE, cached, resolve_tag, year_tagged
from pages.place import speech_ids_for_tag

MIN_TAGGED = 300
MIN_LIFT = 5                # the share of a year must be at least this many times the typical share of the subject
MIN_SUBJECT_SPEECHES = 150  # a subject with fewer speeches over all years does not qualify
MIN_YEAR_SPEECHES = 20      # a subject with fewer speeches in the year does not qualify in that year
SUBJECTS_PER_YEAR = 3
LEFT_OUT_TYPES = {"role"}   # a role such as Prime Minister is a person who is named, not a subject of the year
RACE_WINDOW = 12            # months in each frame of the race
RACE_TOP = 10               # subjects shown in each frame of the race

OVERVIEW_NOTE = (
    "tagged counts the speeches of the year with at least one kept item of any tag. share is the percent of those speeches that carry "
    "the subject. typical is the median of the yearly shares of the subject. Each speech counts once for each subject, so two subjects "
    "can share speeches. A year counts by the date of the debate."
)

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

    The source files some debates under the wrong session number. Their dates are right, so they fall far from the session.
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


def yearly_subjects(rows, tagged):
    """Return one row for each year, with the subjects that stood out most in that year.

    rows holds (tag, type, year, n). tagged is {year: tagged speeches}. Each subject has a typical share: the median of its
    shares over all years. A subject qualifies in a year when its share is at least MIN_LIFT times typical, so a subject of
    every year cannot win. The order is by the distance above typical, largest first, and a tie goes by name.
    """
    by_tag = {}
    for tag, kind, year, n in rows:
        if kind not in LEFT_OUT_TYPES and year in tagged:
            by_tag.setdefault((tag, kind), {})[year] = n
    found = {y: [] for y in tagged}
    for (tag, kind), counts in by_tag.items():
        if sum(counts.values()) < MIN_SUBJECT_SPEECHES:
            continue
        shares = {y: 100 * counts.get(y, 0) / t for y, t in tagged.items() if t}
        typical = median(shares.values())
        for y, share in shares.items():
            if counts.get(y, 0) >= MIN_YEAR_SPEECHES and share >= MIN_LIFT * typical:
                found[y].append({"name": tag, "slug": to_slug(tag), "type": kind, "n": counts[y], "share": round(share, 1),
                                 "typical": round(typical, 2), "above": share - typical})
    out = []
    for y in sorted(tagged):
        top = sorted(found[y], key=lambda r: (-r["above"], r["name"]))[:SUBJECTS_PER_YEAR]
        out.append({"year": y, "tagged": tagged[y], "subjects": [{k: v for k, v in r.items() if k != "above"} for r in top]})
    return out


def trends_overview(conn, args):
    def load():
        rows = conn.execute(text(f"""
            WITH {SPEECH_TAGS_CTE}
            SELECT t.tag, t.type, extract(year FROM d.debate_date)::int, count(DISTINCT st.speech_id)
            FROM speech_tags st JOIN tags t ON t.id = st.tag_id JOIN speeches s ON s.id = st.speech_id
            JOIN debates d ON d.id = s.debate_id WHERE d.debate_date IS NOT NULL GROUP BY 1, 2, 3""")).all()
        return yearly_subjects(rows, year_tagged(conn))
    years = cached("trends_overview", load)
    return {"years": years, "last_date": str(conn.execute(text("SELECT max(debate_date) FROM debates")).scalar()),
            "rules": {"min_lift": MIN_LIFT, "min_subject_speeches": MIN_SUBJECT_SPEECHES, "min_year_speeches": MIN_YEAR_SPEECHES,
                      "subjects_per_year": SUBJECTS_PER_YEAR},
            "counts_note": OVERVIEW_NOTE}


RACE_NOTE = (
    "Each frame is a window of RACE_WINDOW calendar months that ends in the month of the frame. tagged is the denominator: "
    "the speeches of the window with at least one kept item of any tag. subjects[].n counts the speeches of the window that "
    "carry the subject, each speech once, by the date of the debate. share is 100 * n / tagged. typical is the median share "
    "of the subject over all frames. above is share minus typical, in percentage points. A subject qualifies in a frame when it "
    "has at least min_window_speeches speeches in the window and min_subject_speeches over all years. The top of each frame is "
    "the qualifying subjects with the largest above, and a tie goes by name. subjects lists every subject that is in the top of at "
    "least one frame, so a reader can rank each frame from this answer alone."
)


def month_index(year, month):
    return year * 12 + month - 1


def month_label(index):
    return f"{index // 12}-{index % 12 + 1:02d}"


def race_frames(rows, tagged, window=RACE_WINDOW, top=RACE_TOP):
    """Return the frames of the race: for each month, the subjects furthest above their typical share in the window that ends there.

    rows holds (tag, type, month index, n). tagged is {month index: tagged speeches}. A frame needs a full window, so the first
    frame is window - 1 months after the first month with tagged speeches. Months with no sitting count as zero.
    """
    if not tagged:
        return {"months": [], "tagged": [], "subjects": []}
    first, last = min(tagged), max(tagged)
    frames = list(range(first + window - 1, last + 1))

    def windowed(counts):
        out, run = [], sum(counts.get(m, 0) for m in range(first, first + window - 1))
        for f in frames:
            run += counts.get(f, 0)
            out.append(run)
            run -= counts.get(f - window + 1, 0)
        return out

    total = windowed(tagged)
    by_tag = {}
    for tag, kind, m, n in rows:
        if kind not in LEFT_OUT_TYPES:
            by_tag.setdefault((tag, kind), {})[m] = n
    cand = []
    for (tag, kind), counts in by_tag.items():
        if sum(counts.values()) < MIN_SUBJECT_SPEECHES:
            continue
        n = windowed(counts)
        shares = [100 * a / t if t else 0 for a, t in zip(n, total)]
        cand.append({"name": tag, "kind": kind, "n": n, "shares": shares, "typical": median(shares)})
    keep = set()
    for i in range(len(frames)):
        ok = [c for c in cand if c["n"][i] >= MIN_YEAR_SPEECHES]
        ok.sort(key=lambda c: (-(c["shares"][i] - c["typical"]), c["name"]))
        keep.update(c["name"] for c in ok[:top])
    subjects = [{"name": c["name"], "slug": to_slug(c["name"]), "type": c["kind"], "typical": round(c["typical"], 3), "n": c["n"]}
                for c in sorted(cand, key=lambda c: c["name"]) if c["name"] in keep]
    return {"months": [month_label(f) for f in frames], "tagged": total, "subjects": subjects}


def trends_race(conn, args):
    def load():
        rows = conn.execute(text(f"""
            WITH {SPEECH_TAGS_CTE}
            SELECT t.tag, t.type, (extract(year FROM d.debate_date) * 12 + extract(month FROM d.debate_date) - 1)::int,
                   count(DISTINCT st.speech_id)
            FROM speech_tags st JOIN tags t ON t.id = st.tag_id JOIN speeches s ON s.id = st.speech_id
            JOIN debates d ON d.id = s.debate_id WHERE d.debate_date IS NOT NULL GROUP BY 1, 2, 3""")).all()
        tagged = {int(m): n for m, n in conn.execute(text("""
            SELECT (extract(year FROM d.debate_date) * 12 + extract(month FROM d.debate_date) - 1)::int, count(*)
            FROM debates d JOIN speeches s ON s.debate_id = d.id
            WHERE d.debate_date IS NOT NULL AND EXISTS (SELECT 1 FROM speech_items si WHERE si.speech_id = s.id AND si.kept)
            GROUP BY 1"""))}
        return race_frames(rows, tagged)
    out = cached("trends_race", load)
    return {**out, "rules": {"window_months": RACE_WINDOW, "top": RACE_TOP, "min_subject_speeches": MIN_SUBJECT_SPEECHES,
                             "min_window_speeches": MIN_YEAR_SPEECHES},
            "counts_note": RACE_NOTE.replace("RACE_WINDOW", str(RACE_WINDOW))}


ROUTES = [("/trends", trends_overview), ("/trends/race", trends_race), ("/trends/<slug>", trends_page)]
