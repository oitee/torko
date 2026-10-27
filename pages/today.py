"""The data of the page "On this day": what the Lok Sabha discussed on one calendar day in earlier years.

Date rule. Parliament does not sit on most calendar days. For each year, take the sitting day nearest to the month and day,
at most WINDOW days either side. A year with no sitting day in that window has no item. A tie goes to the earlier day.
A day of the year that does not exist (29 February in a year with no leap day) counts as 28 February.

Quote rule (a heuristic for a lay reader). The quote is one sentence from the turn of a member, never the chair, with these checks:
  1. The turn text is cleaned: HTML tags, editor markers like [r11], the leading "(Seat):" label and stage notes like
     (Interruptions) are removed. Torko never changes a word of the sentence.
  2. The sentence has 12 to 40 words, starts with a capital, ends with a full stop, and is English (at least 95% of letters are Latin).
  3. It does not open with a word that points back to an earlier sentence (This, He, However, And, ...).
  4. It has no pronoun that needs an earlier sentence (they, he, these, ...), no address to the chair (Sir, Madam, hon., Speaker),
     no reference that needs the paper in hand (Clause, Annexure, Question No., "the said"), no phrase that points back
     ("in the same manner"), and no brackets, digits or quotation marks.
  Hindi rule. When the day has no good English sentence, a Devanagari sentence may be the quote. It has 10 to 40 words, ends with
  a danda, a full stop or a question mark, and at least 95% of its letters are Devanagari. It has no digit, bracket or quotation mark,
  does not open with a word that points back, and has no pronoun or address that needs the context. A Latin "l" after a Devanagari
  letter is a broken danda in the source text. Torko reads it as a sentence end.
  5. Score: +1 for each long word that also appears in the debate title (at most 2), +2 for length from 15 to 28 words.
     The highest score wins. One quote per year.
"""
import datetime
import re

from sqlalchemy import text

from pages.common import PARTY_AT_DATE, cached, slug, speech_tags_cte, tidy_title, tidy_type
from pages.quotes import clean, good, good_hi, score, sentences

# The tags of the speeches in :ids only.
LOCAL_TAGS_CTE = speech_tags_cte("si.speech_id = ANY(:ids)")

WINDOW = 45
TOP_DEBATES = 3
TOP_SUBJECTS = 3
COUNTS_NOTE = (
    "items[].debates[].tagged_speeches counts the speeches of that debate that carry at least one kept tag, each speech once. "
    "It is not the count of all speeches of the debate. "
    "items[].debates is the main debates of the day: at most 3, ordered by tagged_speeches (most first), then by words (most first). "
    "subjects are the 3 tags most often carried by the speeches of the debate (place and role tags are left out), ties by name."
)


def nearest_day(days, year):
    target = datetime.date(year, *MONTH_DAY)
    cand = [(abs((d - target).days), d) for d in days if abs((d - target).days) <= WINDOW]
    return min(cand)[1] if cand else None


def parse_month_day(value):
    """Parse 'MM-DD' into (month, day). Return None when the text is not a real calendar day (29 February is real)."""
    m = re.fullmatch(r"(\d{1,2})-(\d{1,2})", (value or "").strip())
    if not m:
        return None
    month, day = int(m.group(1)), int(m.group(2))
    try:
        datetime.date(2000, month, day)  # 2000 is a leap year
    except ValueError:
        return None
    return month, day


def target_date(year, month_day):
    try:
        return datetime.date(year, *month_day)
    except ValueError:
        return datetime.date(year, 2, 28)


def nearest_day(days, year, month_day, window=WINDOW):
    """The sitting day of the year nearest to the month and day, at most window days away. A tie goes to the earlier day."""
    target = target_date(year, month_day)
    cand = [(abs((d - target).days), d) for d in days if abs((d - target).days) <= window]
    return min(cand)[1] if cand else None


def debates_for(conn, days):
    """The main debates of each chosen day. Returns {day: [debate, ...]}."""
    days = list(days)
    if not days:
        return {}
    ids = [r[0] for r in conn.execute(text(
        "SELECT s.id FROM speeches s JOIN debates d ON d.id = s.debate_id WHERE d.debate_date = ANY(:days)"), {"days": days})]
    rows = conn.execute(text(f"""
        WITH {LOCAL_TAGS_CTE}
        SELECT d.debate_date AS day, d.id, d.title, d.debate_type, d.source_url, t.tag, t.type, count(*) AS n
        FROM debates d JOIN speeches s ON s.debate_id = d.id
        LEFT JOIN speech_tags st ON st.speech_id = s.id LEFT JOIN tags t ON t.id = st.tag_id
        WHERE d.debate_date = ANY(:days) GROUP BY 1, 2, 3, 4, 5, 6, 7"""), {"days": days, "ids": ids}).mappings().all()
    words = dict(conn.execute(text(
        "SELECT debate_id, sum(word_count) FROM turns WHERE debate_id IN (SELECT id FROM debates WHERE debate_date = ANY(:days)) GROUP BY 1"),
        {"days": days}).all())
    tagged = dict(conn.execute(text(f"""
        WITH {LOCAL_TAGS_CTE}
        SELECT s.debate_id, count(DISTINCT s.id) FROM speeches s JOIN speech_tags st ON st.speech_id = s.id
        JOIN debates d ON d.id = s.debate_id WHERE d.debate_date = ANY(:days) GROUP BY 1"""), {"days": days, "ids": ids}).all())
    by = {}
    for r in rows:
        d = by.setdefault(r["id"], {"day": r["day"], "id": r["id"], "title": r["title"], "type": r["debate_type"],
                                    "url": r["source_url"], "subj": []})
        if r["tag"] and r["type"] not in ("role", "place"):
            d["subj"].append((r["n"], r["tag"]))
    out = {}
    for d in by.values():
        d["subj"].sort(key=lambda x: (-x[0], x[1]))
        out.setdefault(d["day"], []).append((-tagged.get(d["id"], 0), -(words.get(d["id"]) or 0), d["id"], d))
    res = {}
    for day, lst in out.items():
        lst.sort(key=lambda x: x[:3])
        res[day] = [{"id": d["id"], "title": tidy_title(re.sub(r"\s+", " ", d["title"] or "").strip()),
                     "type": tidy_type((d["type"] or "").strip()), "source_url": d["url"], "tagged_speeches": -k0,
                     "words": -k1,
                     "subjects": [{"name": t, "slug": slug(t)} for _, t in d["subj"][:TOP_SUBJECTS]]}
                    for k0, k1, _, d in lst[:TOP_DEBATES]]
    return res


def best_quote(conn, day):
    """Return (sentence, turn row, language) for the best quote of the day, or None."""
    turns = conn.execute(text(f"""
        SELECT t.id, t.text, t.speaker_label, pe.id AS mid, pe.name, d.id AS debate_id, d.title, d.source_url,
               pa.party, pa.seat, pa.state
        FROM turns t JOIN debates d ON d.id = t.debate_id JOIN speeches s ON s.id = t.speech_id
        JOIN persons pe ON pe.id = t.person_id
        {PARTY_AT_DATE.replace('s.person_id', 't.person_id')}
        WHERE d.debate_date = :d AND t.role_kind IS NULL AND t.person_id IS NOT NULL AND t.word_count >= 30
          AND coalesce(t.speaker_label, '') !~* '(अध्यक्ष|सभापति|speaker|chair|presiding)'
        ORDER BY t.id"""), {"d": day}).mappings().all()
    best = best_hi = None
    for t in turns:
        title_words = {w.lower() for w in re.findall(r"[A-Za-z]{5,}", t["title"] or "")}
        for s in sentences(clean(t["text"])):
            if good(s):
                key = (score(s, title_words), -abs(len(s.split()) - 24))
                if best is None or key > best[0]:
                    best = (key, s, t)
    if best:
        return best[1], best[2], "en"
    # The Hindi pass runs only when the day has no good English sentence.
    for t in turns:
        for s in sentences(clean(t["text"])):
            if not good(s) and good_hi(s):
                key = (0, -abs(len(s.split()) - 18))
                if best_hi is None or key > best_hi[0]:
                    best_hi = (key, s, t)
    if best_hi:
        return best_hi[1], best_hi[2], "hi"
    return None


def today_page(conn, args):
    raw = args.get("date")
    if raw:
        month_day = parse_month_day(raw)
        if month_day is None:
            return None
    else:
        now = datetime.date.today()
        month_day = (now.month, now.day)
    days = cached("sitting_days", lambda: sorted(r[0] for r in conn.execute(text(
        "SELECT DISTINCT debate_date FROM debates WHERE debate_date IS NOT NULL"))))
    years = sorted({d.year for d in days})
    chosen = {}
    for y in reversed(years):
        d = nearest_day(days, y, month_day)
        if d:
            chosen[y] = d
    all_debates = debates_for(conn, chosen.values())
    items = []
    for y, day in chosen.items():
        it = {"year": y, "date": day.isoformat(), "days_from": (day - target_date(y, month_day)).days,
              "debates": all_debates.get(day, []), "member": None, "member_id": None, "party": None, "seat": None, "state": None,
              "debate": None, "quote": None, "lang": None, "source_url": None}
        found = cached(("quote", day), lambda: best_quote(conn, day))
        if found:
            s, t, lang = found
            it.update(member=t["name"], member_id=t["mid"], party=t["party"], seat=t["seat"], state=t["state"],
                      debate=tidy_title(re.sub(r"\s+", " ", t["title"] or "").strip()), quote=s, lang=lang,
                      source_url=t["source_url"])
        items.append(it)
    return {"month": month_day[0], "day": month_day[1], "window": WINDOW, "counts_note": COUNTS_NOTE,
            "order_notes": {"items": "by year, latest first; one item per year with a sitting day inside the window",
                            "quote": "see the module docstring: one sentence per year, chosen by a stated score"},
            "items": items}


ROUTES = [("/today", today_page)]
