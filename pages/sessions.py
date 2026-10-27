"""The name of each session, from the dates of its debates.

Rule. The first day of the main block of sitting days (core_range in pages/trends.py) decides the name:
January to May is Budget, June to September is Monsoon, October to December is Winter. The label is the name and the year.
When the rule gives one name twice in one year, the session with more debates keeps it. Each other one is
"Special session, <Month> <Year>".
"""
import datetime

from sqlalchemy import text

from pages.common import cached
from pages.trends import core_range


def season(month):
    return "Budget" if month <= 5 else "Monsoon" if month <= 9 else "Winter"


def name_sessions(days_by_session):
    """Return {(term, session): {label, first, last}} from {(term, session): sorted [(day, debates)]}."""
    rows = {}
    for key, days in days_by_session.items():
        first, last, _ = core_range(days)
        if first is None:
            continue
        start = datetime.date.fromisoformat(first)
        rows[key] = {"first": first, "last": last, "start": start, "debates": sum(n for _, n in days),
                     "label": f"{season(start.month)} {start.year}"}
    by_label = {}
    for key, r in rows.items():
        by_label.setdefault(r["label"], []).append(key)
    for keys in by_label.values():
        keys.sort(key=lambda k: (-rows[k]["debates"], rows[k]["start"]))
        for k in keys[1:]:
            rows[k]["label"] = f"Special session, {rows[k]['start']:%B %Y}"
    return {k: {"term": k[0], "session": k[1], "label": r["label"], "first": r["first"], "last": r["last"]}
            for k, r in rows.items()}


def session_labels(conn):
    """Return {(term, session): {term, session, label, first, last}} for every session with a dated debate. Cached."""
    def load():
        days = {}
        for term, session, day, n in conn.execute(text(
                "SELECT loksabha, session, debate_date, count(*) FROM debates WHERE debate_date IS NOT NULL "
                "GROUP BY 1, 2, 3 ORDER BY 1, 2, 3")).all():
            days.setdefault((term, session), []).append((day, n))
        return name_sessions(days)
    return cached("session_labels", load)
