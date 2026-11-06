"""The shared, paged list of speeches: /api/speeches.

One list serves the Member, Tag, Search and Place pages. All filters are optional and combine with AND.
A speech with no identified member is in the list, with its printed name. It has no tags and no summary,
so a tag, subject or place filter never finds it. A member or party filter leaves it out.

format=csv is internal. No page uses it. It is for reports made by hand, and the public API description leaves it out.
"""
import csv
import io
import re
from datetime import date

import dashboard_db

from flask import Response, after_this_request, has_request_context
from sqlalchemy import text

from pages.common import (KIND_LABELS, KINDS, PARTY_AT_DATE, cached, clean_layout, party_colours, resolve_tag, slug, speech_kind,
                          speech_rows, speech_tags_cte, tag_speeches)
from pages.sessions import session_labels
from pages.search_rank import fuse, nearest_speeches, phrase_of, query_vector, save_near, stored_near, word_speeches
from tag_search import STOP

MAX_PER_PAGE = 50
DEFAULT_PER_PAGE = 20
MAX_CSV_ROWS = 100000
EXCERPT_CHARS = 300
FACET_SUBJECTS = 20
LANG_LABELS = {"en": "English", "hi": "Hindi", "mixed": "Mixed"}

COUNTS_NOTE = (
    "total counts the speeches that match every filter, each speech once. "
    "A speech with no identified member is in total. It has no tags and no summary, so a tag, subject or place filter "
    "never finds it. Counts by member or party leave out the speeches with no identified member. "
    "A speech with a member but no known party at the date of the debate is also left out of the party counts. "
    "With two or more tags in tag, a speech matches when it carries all of them. With group=member and two or more tags, "
    "a member matches with at least one speech for each tag, in any speeches. total stays the count of speeches of the filter. "
    "With q, a speech matches when its own turns and the member name hold every word of q, "
    "or when its summary is near q in meaning. An interruption by another member does not count. "
    "q in quote marks matches only a turn that holds these exact words in this order. "
    "An exact repeat of an earlier speech by the same member is left out. "
    "Each facet count uses all the filters except the filter of that facet. "
    "party_not, state_not, seat_not and lang_not leave out a speech with no known value. "
    "tag_not and subject_not keep a speech with no tags."
)
FACET_NOTE = (
    "facets.term, session, subject, party and kind count speeches. Each one uses every filter except its own. "
    "facets.subject counts only when tag is given, for the 20 subjects of the tag with most matching speeches. "
    "facets.party leaves out the speeches with no identified member or no known party. "
    "facets=tag, tag_all, state, seat, lang, member, place or subject_all adds that count: a comma list, with or without 1. "
    "facets.tag gives the 30 tags with most speeches. facets.tag_all gives every tag with a matching speech. "
    "Its count keeps the ticked tags, because tags combine with AND. "
    "The matches by meaning are the nearest summaries under all the filters, so a facet count can be lower than the count after you choose it."
)

# The debate type of a speech in the form of the kind table: upper case, single spaces.
TYPE_SQL = "upper(regexp_replace(btrim(coalesce(d.debate_type, '')), '\\s+', ' ', 'g'))"
ALL_TYPES = [t for _, types in KINDS.values() for t in types]
SORTS = {
    "latest": "d.debate_date DESC NULLS LAST, s.id DESC",
    "oldest": "d.debate_date ASC NULLS LAST, s.id ASC",
    "longest": "s.word_count DESC NULLS LAST, s.id DESC",
}
GROUP_SORTS = {
    "most": "n DESC, words DESC, pe.name",
    "latest": "last DESC, pe.name",
    "oldest": "first ASC, pe.name",
    "longest": "words DESC, pe.name",
}
# Which filters a facet leaves out of its own count.
OWN_FILTERS = {"term": {"term", "term_not"}, "session": {"session", "session_not"}, "subject": {"subject", "subject_not"},
               "party": {"party", "party_not"}, "kind": {"kind", "kind_not"}, "state": {"state", "state_not"},
               "seat": {"seat", "seat_not"}, "lang": {"lang", "lang_not"},
               # Ticked tags combine with AND, so the count of a tag keeps them: it says what the next tick leaves.
               "tag": {"tag_any", "tag_not"}, "tag_all": {"tag_any", "tag_not"},
               "member": {"member", "member_not"}, "place": {"place", "place_not"}, "subject_all": {"subject", "subject_not"}}
# The filters that read the party, seat or state of the member at the date of the debate.
PARTY_FILTERS = {"party", "party_not", "state", "state_not", "seat", "seat_not"}
# The facets that a page asks for by name, because each one has a cost. facets=1 gives the other five.
NAMED_FACETS = {"tag", "tag_all", "state", "seat", "lang", "member", "place", "subject_all"}
FACET_TAGS = 30
ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")


def int_list(value):
    """Return the integers of a comma list. Words that are not integers are dropped."""
    return [int(x) for x in re.split(r"[,\s]+", value or "") if re.fullmatch(r"\d+", x)]


def str_list(value):
    return [x.strip() for x in (value or "").split(",") if x.strip()]


def int_arg(value, default, low, high):
    try:
        n = int(value)
    except (TypeError, ValueError):
        return default
    return max(low, min(high, n))


def session_pairs(value):
    """Return [(term, session)] from '17-15,18-1'. A part that has a wrong form is dropped."""
    out = []
    for part in str_list(value):
        m = re.fullmatch(r"(\d+)-(\d+)", part)
        if m:
            out.append((int(m.group(1)), int(m.group(2))))
    return out


def kind_types(kinds):
    """Return (types, want_other): the debate types of the kinds, and whether the kind 'other' is in the list."""
    types = [t for k in kinds if k in KINDS for t in KINDS[k][1]]
    return types, "other" in kinds


def iso_date(value):
    """Return the date text when it has the form YYYY-MM-DD and is a real date. Else None."""
    text_value = (value or "").strip()
    if not ISO_DATE.fullmatch(text_value):
        return None
    try:
        date.fromisoformat(text_value)
    except ValueError:
        return None
    return text_value


def like_pattern(value):
    """Return an ILIKE pattern that finds the text anywhere. A % or _ in the text is an ordinary letter."""
    return "%" + value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"


def slug_ids(conn, value, tag_type=None):
    """Return (names, speech ids of each slug), or None for an unknown slug. names is {slug: name}."""
    names, sets = {}, []
    for one in dict.fromkeys(str_list(value)):
        t = resolve_tag(conn, one, tag_type) if tag_type else resolve_tag(conn, one)
        if not t:
            return None
        names[one] = t["tag"]
        sets.append({sid for sid, _ in tag_speeches(conn, t["id"])})
    return names, sets


def parse_args(conn, args):
    """Return (filters, error). filters is a dict of the parsed arguments. error is 'tag' or 'place' for an unknown slug."""
    f = {
        "member": int_list(args.get("member")), "member_not": int_list(args.get("member_not")),
        "term": int_list(args.get("term")), "session": session_pairs(args.get("session")),
        "kind": str_list(args.get("kind")), "party": [p.upper() for p in str_list(args.get("party"))],
        "party_not": [p.upper() for p in str_list(args.get("party_not"))],
        "min_words": int_arg(args.get("min_words"), 0, 0, 10**7),
        "subject": int_list(args.get("subject")), "q": (args.get("q") or "").strip(),
        "term_not": int_list(args.get("term_not")), "session_not": session_pairs(args.get("session_not")),
        "kind_not": str_list(args.get("kind_not")), "subject_not": int_list(args.get("subject_not")),
        "state": str_list(args.get("state")), "state_not": str_list(args.get("state_not")),
        "seat": str_list(args.get("seat")), "seat_not": str_list(args.get("seat_not")),
        "lang": str_list(args.get("lang")), "lang_not": str_list(args.get("lang_not")),
        "max_words": int_arg(args.get("max_words"), 0, 0, 10**7),
        "date_from": iso_date(args.get("date_from")), "date_to": iso_date(args.get("date_to")),
        "title": (args.get("title") or "").strip(), "title_not": (args.get("title_not") or "").strip(),
        "tag_any_ids": None, "tag_not_ids": None, "place_not_ids": None, "slug_names": {},
        "phrase": phrase_of(args.get("q")),
        "tag_ids": None, "place_ids": None,
    }
    slugs = list(dict.fromkeys(str_list(args.get("tag"))))
    if slugs:
        sets = []
        for one in slugs:
            t = resolve_tag(conn, one)
            if not t:
                return f, "tag"
            sets.append({"name": t["tag"], "slug": slug(t["tag"]), "ids": [sid for sid, _ in tag_speeches(conn, t["id"])]})
        if len(sets) == 1:
            f["tag_id"] = t["id"]
        else:  # Two or more tags: a speech needs all of them. The Members view has its own rule, in speeches().
            f["tag_sets"] = sets
        f["tag_ids"] = sorted(set.intersection(*(set(x["ids"]) for x in sets)))
        f["slug_names"].update({x["slug"]: x["name"] for x in sets})
    # A comma list of places: a speech needs one of them. A list after any_of or none_of works the same way.
    for key, target, kind, bad in (("place", "place_ids", "place", "place"), ("place_not", "place_not_ids", "place", "place"),
                                   ("tag_any", "tag_any_ids", None, "tag"), ("tag_not", "tag_not_ids", None, "tag")):
        if args.get(key):
            got = slug_ids(conn, args[key], kind)
            if got is None:
                return f, bad
            f["slug_names"].update(got[0])
            f[target] = sorted(set().union(*got[1]))
    return f, None


def filter_names(conn, f):
    """Return the names of the values in the address, so that a page can show them: {member: {id: name}, subject: ..., slug: ...}."""
    out = {"slug": f.get("slug_names", {})}
    members = f["member"] + f["member_not"]
    subjects = f["subject"] + f["subject_not"]
    if members:
        out["member"] = {str(i): n for i, n in conn.execute(text("SELECT id, name FROM persons WHERE id = ANY(:ids)"), {"ids": members})}
    if subjects:
        out["subject"] = {str(i): n for i, n in conn.execute(text("SELECT id, label FROM subjects WHERE id = ANY(:ids)"), {"ids": subjects})}
    return out


def conditions(f):
    """Return {filter name: (sql, params)} for the filters that are set. The SQL uses the aliases s and d, and pa for the party."""
    c = {}
    if f["member"]:
        c["member"] = ("s.person_id = ANY(:member)", {"member": f["member"]})
    if f["member_not"]:
        c["member_not"] = ("s.person_id IS NOT NULL AND s.person_id <> ALL(:member_not)", {"member_not": f["member_not"]})
    if f["tag_ids"] is not None:
        c["tag"] = ("s.id = ANY(:tag_ids)", {"tag_ids": f["tag_ids"]})
    if f["place_ids"] is not None:
        c["place"] = ("s.id = ANY(:place_ids)", {"place_ids": f["place_ids"]})
    if f["subject"]:
        c["subject"] = ("""s.id IN (SELECT si.speech_id FROM speech_items si
            JOIN subject_names sn ON sn.entity_name_id = si.entity_name_id
            WHERE si.kept AND sn.subject_id = ANY(:subject))""", {"subject": f["subject"]})
    if f["term"]:
        c["term"] = ("d.loksabha = ANY(:term)", {"term": f["term"]})
    if f["session"]:
        parts, p = [], {}
        for i, (term, sess) in enumerate(f["session"]):
            parts.append(f"(d.loksabha = :st{i} AND d.session = :ss{i})")
            p[f"st{i}"], p[f"ss{i}"] = term, sess
        c["session"] = ("(" + " OR ".join(parts) + ")", p)
    if f["kind"]:
        types, other = kind_types(f["kind"])
        parts = []
        if types:
            parts.append(f"{TYPE_SQL} = ANY(:kind_types)")
        if other:
            parts.append(f"{TYPE_SQL} <> ALL(:all_types)")
        c["kind"] = ("(" + " OR ".join(parts or ["false"]) + ")", {"kind_types": types, "all_types": ALL_TYPES})
    if f["min_words"]:
        c["min_words"] = ("s.word_count >= :min_words", {"min_words": f["min_words"]})
    if f.get("phrase"):
        c["q"] = ("""s.id IN (SELECT t.speech_id FROM turns t JOIN speeches s2 ON s2.id = t.speech_id
            WHERE to_tsvector('simple', t.text) @@ phraseto_tsquery('simple', :q)
              AND t.person_id IS NOT DISTINCT FROM s2.person_id)""", {"q": f["phrase"]})
    elif f["q"]:
        c["q"] = ("""s.id IN (SELECT speech_id FROM speech_search
            WHERE words @@ plainto_tsquery('simple', :q) AND repeat_of IS NULL)""", {"q": f["q"]})
    if f.get("term_not"):
        c["term_not"] = ("d.loksabha IS NOT NULL AND d.loksabha <> ALL(:term_not)", {"term_not": f["term_not"]})
    if f.get("session_not"):
        parts, p = [], {}
        for i, (term, sess) in enumerate(f["session_not"]):
            parts.append(f"(d.loksabha = :nt{i} AND d.session = :ns{i})")
            p[f"nt{i}"], p[f"ns{i}"] = term, sess
        c["session_not"] = ("NOT (" + " OR ".join(parts) + ")", p)
    if f.get("kind_not"):
        types, other = kind_types(f["kind_not"])
        parts = []
        if types:
            parts.append(f"{TYPE_SQL} = ANY(:kind_not_types)")
        if other:
            parts.append(f"{TYPE_SQL} <> ALL(:all_types)")
        c["kind_not"] = ("NOT (" + " OR ".join(parts or ["false"]) + ")", {"kind_not_types": types, "all_types": ALL_TYPES})
    if f.get("tag_any_ids") is not None:
        c["tag_any"] = ("s.id = ANY(:tag_any_ids)", {"tag_any_ids": f["tag_any_ids"]})
    if f.get("tag_not_ids") is not None:  # A speech with no tags has none of the tags, so it stays.
        c["tag_not"] = ("NOT (s.id = ANY(:tag_not_ids))", {"tag_not_ids": f["tag_not_ids"]})
    if f.get("place_not_ids") is not None:
        c["place_not"] = ("NOT (s.id = ANY(:place_not_ids))", {"place_not_ids": f["place_not_ids"]})
    if f.get("subject_not"):
        c["subject_not"] = ("""s.id NOT IN (SELECT si.speech_id FROM speech_items si
            JOIN subject_names sn ON sn.entity_name_id = si.entity_name_id
            WHERE si.kept AND sn.subject_id = ANY(:subject_not))""", {"subject_not": f["subject_not"]})
    if f.get("max_words"):
        c["max_words"] = ("s.word_count <= :max_words", {"max_words": f["max_words"]})
    if f.get("date_from"):
        c["date_from"] = ("d.debate_date >= CAST(:date_from AS date)", {"date_from": f["date_from"]})
    if f.get("date_to"):
        c["date_to"] = ("d.debate_date <= CAST(:date_to AS date)", {"date_to": f["date_to"]})
    if f.get("title"):
        c["title"] = ("d.title ILIKE :title", {"title": like_pattern(f["title"])})
    if f.get("title_not"):
        c["title_not"] = ("coalesce(d.title, '') NOT ILIKE :title_not", {"title_not": like_pattern(f["title_not"])})
    if f.get("lang"):
        c["lang"] = ("s.id IN (SELECT speech_id FROM speech_extractions WHERE language = ANY(:lang))", {"lang": f["lang"]})
    if f.get("lang_not"):  # As with party_not: a speech with no known language is left out.
        c["lang_not"] = ("s.id IN (SELECT speech_id FROM speech_extractions WHERE language <> ALL(:lang_not))", {"lang_not": f["lang_not"]})
    for key, col in (("state", "pa.state"), ("seat", "pa.seat")):
        if f.get(key):
            c[key] = (f"{col} = ANY(:{key})", {key: f[key]})
        if f.get(f"{key}_not"):  # As with party_not: a speech with no known value is left out.
            c[f"{key}_not"] = (f"{col} IS NOT NULL AND {col} <> ALL(:{key}_not)", {f"{key}_not": f[f"{key}_not"]})
    if f["party"]:
        c["party"] = ("pa.party = ANY(:party)", {"party": f["party"]})
    if f["party_not"]:
        c["party_not"] = ("pa.party IS NOT NULL AND pa.party <> ALL(:party_not)", {"party_not": f["party_not"]})
    return c


def where(conds, skip=()):
    """Return (WHERE sql, params, needs_party) from the conditions, without the filters in skip."""
    use = {k: v for k, v in conds.items() if k not in skip}
    sql = " AND ".join(v[0] for v in use.values()) or "true"
    params = {}
    for v in use.values():
        params.update(v[1])
    return sql, params, any(k in use for k in PARTY_FILTERS)


def from_sql(needs_party):
    return "FROM speeches s JOIN debates d ON d.id = s.debate_id" + (f" {PARTY_AT_DATE}" if needs_party else "")


# Sentences end at . ! ? or the Hindi danda.
SENTENCE_END = re.compile(r"(?<=[.!?।])\s+")


def query_words(q):
    return [w for w in re.findall(r"\w+", (q or "").lower())]


def highlight_words(q):
    """The words of q to mark in an excerpt: small words such as "in" go, unless q holds nothing else."""
    words = query_words(q)
    return [w for w in words if w not in STOP] or words


def make_excerpt(raw, words, limit=EXCERPT_CHARS):
    """Return (excerpt, marks): the first sentence of the cleaned text that has a word, and [start, end] of each match in it.

    Words match whole words, with case ignored. A sentence longer than limit is cut around the first match.
    Return (None, []) when no word is found.
    """
    if not words:
        return None, []
    rx = re.compile(r"(?<!\w)(?:" + "|".join(re.escape(w) for w in sorted(set(words), key=len, reverse=True)) + r")(?!\w)", re.I)
    for sentence in SENTENCE_END.split(clean_layout(raw).strip()):
        m = rx.search(sentence)
        if not m:
            continue
        start = 0
        if len(sentence) > limit:
            start = max(0, m.start() - limit // 3)
            end = min(len(sentence), start + limit)
            piece = sentence[start:end]
        else:
            piece = sentence
        marks = [[x.start(), x.end()] for x in rx.finditer(piece)]
        return piece, marks
    return None, []


def tags_of(conn, ids):
    """Return {speech id: [tag dicts]} for the speeches. Same as speech_rows, but the scan is limited to these speeches."""
    out = {}
    if not ids:
        return out
    rows = conn.execute(text(f"""
        WITH {speech_tags_cte("si.speech_id = ANY(:ids)")}
        SELECT st.speech_id, t.tag, t.type, st.source
        FROM speech_tags st JOIN tags t ON t.id = st.tag_id
        WHERE st.speech_id = ANY(:ids)
        ORDER BY st.speech_id, CASE st.source WHEN 'llm' THEN 0 WHEN 'dictionary' THEN 1 ELSE 2 END, t.tag"""),
        {"ids": list(ids)}).mappings().all()
    for r in rows:
        out.setdefault(r["speech_id"], []).append({"name": r["tag"], "slug": slug(r["tag"]), "type": r["type"], "source": r["source"]})
    return out


def rows_for(conn, ids):
    """Speech rows for the ids, in order, with tags."""
    rows = speech_rows(conn, ids, with_tags=False)
    tags = tags_of(conn, ids)
    for r in rows:
        r["tags"] = tags.get(r["id"], [])
    return rows


def add_excerpts(conn, rows, q):
    """Add excerpt and marks to each row: the first own turn of the speech that holds a word of q."""
    words = highlight_words(q)
    found = {}
    for sid, txt in conn.execute(text("""
        SELECT t.speech_id, t.text FROM turns t JOIN speeches s ON s.id = t.speech_id
        WHERE t.speech_id = ANY(:ids) AND t.person_id IS NOT DISTINCT FROM s.person_id
        ORDER BY t.speech_id, t.seq"""), {"ids": [r["id"] for r in rows]}):
        if sid not in found:
            ex, marks = make_excerpt(txt, words)
            if ex:
                found[sid] = (ex, marks)
    for r in rows:
        r["excerpt"], r["marks"] = found.get(r["id"], (None, []))


def add_meaning(conn, f, conds):
    """Widen the q condition with the nearest summaries. Return (their ids, True), or ([], False) when the model call fails."""
    store = dashboard_db.get_engine()
    vector = query_vector(store, f["q"])
    if vector is None:
        return [], False
    w, p, party = where(conds, ("q",))
    no_filter = len(conds) == 1
    near = stored_near(store, f["q"]) if no_filter else None
    if near is None:
        near = nearest_speeches(conn, vector, from_sql(party), w, p)
        if no_filter:
            save_near(store, f["q"], near)
    if near:
        sql, params = conds["q"]
        conds["q"] = (f"({sql} OR s.id = ANY(:near_ids))", {**params, "near_ids": near})
    return near, True


def add_match_kind(conn, rows, q, near):
    """Say why each row is in the list: words, meaning, or both."""
    with_words = {r[0] for r in conn.execute(text("""SELECT speech_id FROM speech_search
        WHERE speech_id = ANY(:ids) AND words @@ plainto_tsquery('simple', :q)"""), {"ids": [r["id"] for r in rows], "q": q})}
    near = set(near)
    for r in rows:
        r["match"] = "both" if r["id"] in near and r["id"] in with_words else "meaning" if r["id"] in near else "words"


def do_not_store():
    """Stop nginx from keeping an answer with no matches by meaning: the model call can work again a moment later."""
    if has_request_context():
        @after_this_request
        def _no_store(resp):
            resp.headers["Cache-Control"] = "no-store"
            return resp


def facets(conn, conds, f, labels):
    """Return the counts by term, session, subject, party and kind. Each leaves out its own filter."""
    out = {}
    w, p, party = where(conds, OWN_FILTERS["term"])
    out["term"] = [{"term": t, "n": n} for t, n in conn.execute(text(
        f"SELECT d.loksabha, count(*) {from_sql(party)} WHERE {w} AND d.loksabha IS NOT NULL GROUP BY 1 ORDER BY 1"), p)]
    w, p, party = where(conds, OWN_FILTERS["session"])
    out["session"] = [{"term": t, "session": s, "label": (labels.get((t, s)) or {}).get("label"), "n": n}
                      for t, s, n in conn.execute(text(
        f"SELECT d.loksabha, d.session, count(*) {from_sql(party)} WHERE {w} AND d.loksabha IS NOT NULL "
        "GROUP BY 1, 2 ORDER BY 1, 2"), p)]
    w, p, _ = where(conds, OWN_FILTERS["party"])
    colours = party_colours(conn)
    out["party"] = [{"party": pa, "colour": colours.get(pa), "n": n} for pa, n in conn.execute(text(
        f"SELECT pa.party, count(*) {from_sql(True)} WHERE {w} AND pa.party IS NOT NULL AND s.person_id IS NOT NULL "
        "GROUP BY 1 ORDER BY 2 DESC, 1"), p)]
    w, p, party = where(conds, OWN_FILTERS["kind"])
    kinds = {}
    for dtype, n in conn.execute(text(f"SELECT d.debate_type, count(*) {from_sql(party)} WHERE {w} GROUP BY 1"), p):
        k = speech_kind(dtype)
        kinds[k] = kinds.get(k, 0) + n
    out["kind"] = [{"kind": k, "label": KIND_LABELS[k], "n": n}
                   for k, n in sorted(kinds.items(), key=lambda kv: (-kv[1], kv[0]))]
    out["subject"] = []
    if f.get("tag_id"):
        w, p, party = where(conds, OWN_FILTERS["subject"])
        p["tag_id"] = f["tag_id"]
        out["subject"] = [{"id": i, "label": lab, "n": n} for i, lab, n in conn.execute(text(f"""
            SELECT su.id, su.label, count(DISTINCT s.id) {from_sql(party)}
            JOIN speech_items si ON si.speech_id = s.id AND si.kept
            JOIN subject_names sn ON sn.entity_name_id = si.entity_name_id
            JOIN subjects su ON su.id = sn.subject_id
            WHERE {w} AND su.parent_tag_id IN (SELECT id FROM tags WHERE id = :tag_id OR merged_into = :tag_id)
            GROUP BY su.id, su.label ORDER BY 3 DESC, su.label LIMIT {FACET_SUBJECTS}"""), p)]
    return out


def named_facets(conn, conds, names):
    """Return the counts of each named facet in the list, for the values with at least one speech. Each leaves out its own filter."""
    out = {}
    for name in names:
        w, p, party = where(conds, OWN_FILTERS[name])
        if name in ("state", "seat"):
            out[name] = [{name: v, "n": n} for v, n in conn.execute(text(
                f"SELECT pa.{name}, count(*) {from_sql(True)} WHERE {w} AND pa.{name} IS NOT NULL GROUP BY 1 ORDER BY 2 DESC, 1"), p)]
        elif name == "lang":
            out[name] = [{"lang": v, "label": LANG_LABELS.get(v, v), "n": n} for v, n in conn.execute(text(
                f"SELECT e.language, count(*) {from_sql(party)} JOIN speech_extractions e ON e.speech_id = s.id "
                f"WHERE {w} AND e.language IS NOT NULL GROUP BY 1 ORDER BY 2 DESC, 1"), p)]
        elif name == "member":
            out[name] = [{"id": i, "name": v, "n": n} for i, v, n in conn.execute(text(
                f"SELECT pe.id, pe.name, count(*) {from_sql(party)} JOIN persons pe ON pe.id = s.person_id "
                f"WHERE {w} GROUP BY 1, 2 ORDER BY 3 DESC, 2"), p)]
        elif name == "subject_all":
            def subject_rows(w=w, p=p, party=party):
                return [{"id": i, "label": v, "n": n} for i, v, n in conn.execute(text(f"""
                    SELECT su.id, su.label, count(DISTINCT s.id) {from_sql(party)}
                    JOIN speech_items si ON si.speech_id = s.id AND si.kept
                    JOIN subject_names sn ON sn.entity_name_id = si.entity_name_id
                    JOIN subjects su ON su.id = sn.subject_id
                    WHERE {w} GROUP BY 1, 2 ORDER BY 3 DESC, 2"""), p)]
            out[name] = cached("facet_subject_all", subject_rows) if w == "true" else subject_rows()
        else:
            type_sql = "t.type = 'place'" if name == "place" else "t.type <> 'place'"
            limit = f"LIMIT {FACET_TAGS}" if name == "tag" else ""
            def tag_rows(w=w, p=p, party=party, type_sql=type_sql, limit=limit):
                return [{"tag": t, "slug": slug(t), "n": n} for t, n in conn.execute(text(f"""
                    WITH {speech_tags_cte(f"si.speech_id IN (SELECT s.id {from_sql(party)} WHERE {w})")}
                    SELECT t.tag, count(DISTINCT st.speech_id) FROM speech_tags st JOIN tags t ON t.id = st.tag_id
                    WHERE {type_sql} GROUP BY t.id, t.tag ORDER BY 2 DESC, t.tag {limit}"""), p)]
            # The count over all speeches takes seconds and is the same for every reader, so it is kept in memory.
            out[name] = cached(f"facet_{name}_all", tag_rows) if w == "true" else tag_rows()
    return out


def member_groups(conn, conds, sort, page, per_page, tag_sets=None):
    """Return (rows, number of members): one row for each member with matching speeches.

    With tag_sets, a member must have at least one speech for each tag, in any speeches. Each row counts the speeches of each tag.
    """
    w, p, needs_party = where(conds)
    p = dict(p)
    counts, having = "", ""
    if tag_sets:
        for i, t in enumerate(tag_sets):
            p[f"set{i}"] = t["ids"]
        counts = "".join(f", count(*) FILTER (WHERE s.id = ANY(:set{i})) AS n_set{i}" for i in range(len(tag_sets)))
        having = "HAVING " + " AND ".join(f"count(*) FILTER (WHERE s.id = ANY(:set{i})) > 0" for i in range(len(tag_sets)))
    n_members = conn.execute(text(f"""SELECT count(*) FROM (SELECT s.person_id {from_sql(needs_party)}
        WHERE {w} AND s.person_id IS NOT NULL GROUP BY s.person_id {having}) x"""), p).scalar()
    order = GROUP_SORTS[sort]
    p = {**p, "lim": per_page, "off": (page - 1) * per_page}
    got = conn.execute(text(f"""
        SELECT pe.id, pe.name, count(*) AS n, sum(s.word_count) AS words, min(d.debate_date) AS first, max(d.debate_date) AS last,
               (array_agg(pa.party ORDER BY d.debate_date DESC NULLS LAST))[1] AS party,
               (array_agg(pa.seat ORDER BY d.debate_date DESC NULLS LAST))[1] AS seat,
               (array_agg(pa.state ORDER BY d.debate_date DESC NULLS LAST))[1] AS state,
               array_agg(DISTINCT d.loksabha ORDER BY d.loksabha) AS terms,
               array_agg(s.id) AS sids{counts}
        {from_sql(True)} JOIN persons pe ON pe.id = s.person_id
        WHERE {w} GROUP BY pe.id {having} ORDER BY {order} LIMIT :lim OFFSET :off"""), p).mappings().all()
    top = {}
    for r in got:  # the tag that the matching speeches of the member carry most often
        sids = r["sids"]
        t = conn.execute(text(f"""
            WITH {speech_tags_cte("si.speech_id = ANY(:ids)")}
            SELECT t.tag, count(*) FROM speech_tags st JOIN tags t ON t.id = st.tag_id
            WHERE st.speech_id = ANY(:ids) GROUP BY t.id ORDER BY 2 DESC, t.tag LIMIT 1"""), {"ids": sids}).first()
        top[r["id"]] = {"name": t[0], "slug": slug(t[0]), "n": t[1]} if t else None
    rows = [{"id": r["id"], "name": r["name"], "party": r["party"], "seat": r["seat"], "state": r["state"],
             "terms": r["terms"], "n": r["n"], "words": r["words"],
             "first": r["first"].isoformat() if r["first"] else None,
             "last": r["last"].isoformat() if r["last"] else None, "most_on": top[r["id"]],
             **({"tag_counts": [{"name": t["name"], "slug": t["slug"], "n": r[f"n_set{i}"]} for i, t in enumerate(tag_sets)]}
                if tag_sets else {})} for r in got]
    return rows, n_members


CSV_COLUMNS = ["date", "term", "session", "debate", "kind", "words", "summary", "tags", "source URL", "Torko speech id"]


def csv_response(rows):
    """Return every row as one CSV file. Internal: for reports made by hand, not for the pages.

    TODO: make it faster before any page uses it. It builds all rows in memory with speech_rows and the tags,
    up to MAX_CSV_ROWS. A tag with about 15,000 speeches takes about 21 s and gives 8.8 MB.
    Stream the rows in batches, and read only the columns of the file.
    """
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(CSV_COLUMNS)
    for r in rows:
        w.writerow([r["date"], r["term"], r["session"], r["debate"], r["kind_label"], r["words"], r["summary"] or "",
                    "; ".join(t["name"] for t in r["tags"]), r["source_url"], r["id"]])
    return Response(buf.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": 'attachment; filename="torko_speeches.csv"'})


def speeches(conn, args):
    f, bad = parse_args(conn, args)
    if bad:
        return None
    tag_sets = f.get("tag_sets")
    if tag_sets and args.get("group") == "member":
        f["tag_ids"] = sorted(set().union(*(set(x["ids"]) for x in tag_sets)))
    conds = conditions(f)
    words_query = f["q"] and not f["phrase"]
    sort = args.get("sort")
    # Most speeches first orders only the Members view.
    if sort not in SORTS and not (sort == "best" and words_query) and not (sort == "most" and args.get("group") == "member"):
        sort = "best" if words_query else "latest"
    page = int_arg(args.get("page"), 1, 1, 10**6)
    per_page = int_arg(args.get("per_page"), DEFAULT_PER_PAGE, 1, MAX_PER_PAGE)
    near, by_meaning = [], False
    if words_query:
        base_where, base_params, base_party = where(conds, ("q",))
        near, by_meaning = add_meaning(conn, f, conds)
        if not by_meaning:
            do_not_store()
    w, p, party = where(conds)
    total = conn.execute(text(f"SELECT count(*) {from_sql(party)} WHERE {w}"), p).scalar()

    if args.get("format") == "csv":
        ids = [r[0] for r in conn.execute(text(
            f"SELECT s.id {from_sql(party)} WHERE {w} ORDER BY {SORTS.get(sort, SORTS['latest'])} LIMIT {MAX_CSV_ROWS}"), p)]
        rows = rows_for(conn, ids)
        if f["q"]:
            add_excerpts(conn, rows, f["phrase"] or f["q"])
        return csv_response(rows)

    out = {"total": total, "page": page, "per_page": per_page, "sort": sort,
           "counts_note": COUNTS_NOTE, "names": filter_names(conn, f)}
    if f["q"]:
        out["by_meaning"] = by_meaning
    if args.get("group") == "member":
        rows, n_members = member_groups(conn, conds, sort if sort in GROUP_SORTS else "latest", page, per_page, tag_sets)
        out.update({"group": "member", "members_total": n_members, "pages": -(-n_members // per_page), "members": rows})
    else:
        if sort == "best":
            ranked = fuse([word_speeches(conn, f["q"], from_sql(base_party), base_where, base_params), near])
            out["pages"] = -(-len(ranked) // per_page)  # Best match orders only the top of the list. Latest first reaches all of it.
            ids = ranked[(page - 1) * per_page:page * per_page]
        else:
            out["pages"] = -(-total // per_page)
            ids = [r[0] for r in conn.execute(text(
                f"SELECT s.id {from_sql(party)} WHERE {w} ORDER BY {SORTS[sort]} LIMIT :lim OFFSET :off"),
                {**p, "lim": per_page, "off": (page - 1) * per_page})]
        rows = rows_for(conn, ids)
        if f["q"]:
            add_excerpts(conn, rows, f["phrase"] or f["q"])
            if words_query:
                add_match_kind(conn, rows, f["q"], near)
        out["speeches"] = rows
    asked = str_list(args.get("facets"))
    if "1" in asked or "true" in asked:
        out["facets"] = facets(conn, conds, f, session_labels(conn))
        out["facets_note"] = FACET_NOTE
    named = [n for n in asked if n in NAMED_FACETS]
    if named:
        out.setdefault("facets", {}).update(named_facets(conn, conds, named))
        out["facets_note"] = FACET_NOTE
    return out


def speeches_route(conn, args):
    return speeches(conn, args)


ROUTES = [("/speeches", speeches_route)]
