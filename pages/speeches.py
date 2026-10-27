"""The shared, paged list of speeches: /api/speeches.

One list serves the Member, Tag, Search and Place pages. All filters are optional and combine with AND.
A speech with no identified member is in the list, with its printed name. It has no tags and no summary,
so a tag, subject or place filter never finds it. A member or party filter leaves it out.
"""
import csv
import io
import re

from flask import Response
from sqlalchemy import text

from pages.common import (KIND_LABELS, KINDS, PARTY_AT_DATE, clean_layout, party_colours, resolve_tag, slug, speech_kind,
                          speech_rows, speech_tags_cte, tag_speeches)
from pages.sessions import session_labels

MAX_PER_PAGE = 50
DEFAULT_PER_PAGE = 20
MAX_CSV_ROWS = 100000
EXCERPT_CHARS = 300
FACET_SUBJECTS = 20

COUNTS_NOTE = (
    "total counts the speeches that match every filter, each speech once. "
    "A speech with no identified member is in total. It has no tags and no summary, so a tag, subject or place filter "
    "never finds it. Counts by member or party leave out the speeches with no identified member. "
    "A speech with a member but no known party at the date of the debate is also left out of the party counts. "
    "With q, a speech matches when one of its own turns has every word of q. An interruption by another member does not count. "
    "Each facet count uses all the filters except the filter of that facet."
)
FACET_NOTE = (
    "facets.term, session, subject, party and kind count speeches. Each one uses every filter except its own. "
    "facets.subject counts only when tag is given, for the 20 subjects of the tag with most matching speeches. "
    "facets.party leaves out the speeches with no identified member or no known party."
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
    "latest": "last DESC, pe.name",
    "oldest": "first ASC, pe.name",
    "longest": "words DESC, pe.name",
}
# Which filters a facet leaves out of its own count.
OWN_FILTERS = {"term": {"term"}, "session": {"session"}, "subject": {"subject"}, "party": {"party", "party_not"}, "kind": {"kind"}}


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


def parse_args(conn, args):
    """Return (filters, error). filters is a dict of the parsed arguments. error is 'tag' or 'place' for an unknown slug."""
    f = {
        "member": int_list(args.get("member")), "member_not": int_list(args.get("member_not")),
        "term": int_list(args.get("term")), "session": session_pairs(args.get("session")),
        "kind": str_list(args.get("kind")), "party": [p.upper() for p in str_list(args.get("party"))],
        "party_not": [p.upper() for p in str_list(args.get("party_not"))],
        "min_words": int_arg(args.get("min_words"), 0, 0, 10**7),
        "subject": int_list(args.get("subject")), "q": (args.get("q") or "").strip(),
        "tag_ids": None, "place_ids": None,
    }
    if args.get("tag"):
        t = resolve_tag(conn, args["tag"].strip())
        if not t:
            return f, "tag"
        f["tag_id"] = t["id"]
        f["tag_ids"] = [sid for sid, _ in tag_speeches(conn, t["id"])]
    if args.get("place"):
        t = resolve_tag(conn, args["place"].strip(), "place")
        if not t:
            return f, "place"
        f["place_ids"] = [sid for sid, _ in tag_speeches(conn, t["id"])]
    return f, None


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
    if f["q"]:
        c["q"] = ("""s.id IN (SELECT t.speech_id FROM turns t JOIN speeches s2 ON s2.id = t.speech_id
            WHERE to_tsvector('simple', t.text) @@ plainto_tsquery('simple', :q)
              AND t.person_id IS NOT DISTINCT FROM s2.person_id)""", {"q": f["q"]})
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
    return sql, params, any(k in use for k in ("party", "party_not"))


def from_sql(needs_party):
    return "FROM speeches s JOIN debates d ON d.id = s.debate_id" + (f" {PARTY_AT_DATE}" if needs_party else "")


# Sentences end at . ! ? or the Hindi danda.
SENTENCE_END = re.compile(r"(?<=[.!?।])\s+")


def query_words(q):
    return [w for w in re.findall(r"\w+", (q or "").lower())]


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
    """Add excerpt and marks to each row: the first own turn of the speech that matches q."""
    words = query_words(q)
    found = {}
    for sid, txt in conn.execute(text("""
        SELECT t.speech_id, t.text FROM turns t JOIN speeches s ON s.id = t.speech_id
        WHERE t.speech_id = ANY(:ids) AND t.person_id IS NOT DISTINCT FROM s.person_id
          AND to_tsvector('simple', t.text) @@ plainto_tsquery('simple', :q)
        ORDER BY t.speech_id, t.seq"""), {"ids": [r["id"] for r in rows], "q": q}):
        if sid not in found:
            ex, marks = make_excerpt(txt, words)
            if ex:
                found[sid] = (ex, marks)
    for r in rows:
        r["excerpt"], r["marks"] = found.get(r["id"], (None, []))


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


def member_groups(conn, conds, sort, page, per_page):
    """Return (rows, number of members): one row for each member with matching speeches."""
    w, p, _ = where(conds)
    n_members = conn.execute(text(f"SELECT count(DISTINCT s.person_id) {from_sql(False)} WHERE {w} AND s.person_id IS NOT NULL"), p).scalar()
    order = GROUP_SORTS[sort]
    p = {**p, "lim": per_page, "off": (page - 1) * per_page}
    got = conn.execute(text(f"""
        SELECT pe.id, pe.name, count(*) AS n, sum(s.word_count) AS words, min(d.debate_date) AS first, max(d.debate_date) AS last,
               (array_agg(pa.party ORDER BY d.debate_date DESC NULLS LAST))[1] AS party,
               (array_agg(pa.seat ORDER BY d.debate_date DESC NULLS LAST))[1] AS seat,
               (array_agg(pa.state ORDER BY d.debate_date DESC NULLS LAST))[1] AS state,
               array_agg(DISTINCT d.loksabha ORDER BY d.loksabha) AS terms,
               array_agg(s.id) AS sids
        {from_sql(True)} JOIN persons pe ON pe.id = s.person_id
        WHERE {w} GROUP BY pe.id ORDER BY {order} LIMIT :lim OFFSET :off"""), p).mappings().all()
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
             "last": r["last"].isoformat() if r["last"] else None, "most_on": top[r["id"]]} for r in got]
    return rows, n_members


CSV_COLUMNS = ["date", "term", "session", "debate", "kind", "words", "summary", "tags", "source URL", "Torko speech id"]


def csv_response(rows):
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
    conds = conditions(f)
    sort = args.get("sort") if args.get("sort") in SORTS else "latest"
    page = int_arg(args.get("page"), 1, 1, 10**6)
    per_page = int_arg(args.get("per_page"), DEFAULT_PER_PAGE, 1, MAX_PER_PAGE)
    w, p, party = where(conds)
    total = conn.execute(text(f"SELECT count(*) {from_sql(party)} WHERE {w}"), p).scalar()

    if args.get("format") == "csv":
        ids = [r[0] for r in conn.execute(text(
            f"SELECT s.id {from_sql(party)} WHERE {w} ORDER BY {SORTS[sort]} LIMIT {MAX_CSV_ROWS}"), p)]
        rows = rows_for(conn, ids)
        if f["q"]:
            add_excerpts(conn, rows, f["q"])
        return csv_response(rows)

    out = {"total": total, "page": page, "per_page": per_page, "sort": sort,
           "counts_note": COUNTS_NOTE}
    if args.get("group") == "member":
        rows, n_members = member_groups(conn, conds, sort, page, per_page)
        out.update({"group": "member", "members_total": n_members, "pages": -(-n_members // per_page), "members": rows})
    else:
        out["pages"] = -(-total // per_page)
        ids = [r[0] for r in conn.execute(text(
            f"SELECT s.id {from_sql(party)} WHERE {w} ORDER BY {SORTS[sort]} LIMIT :lim OFFSET :off"),
            {**p, "lim": per_page, "off": (page - 1) * per_page})]
        rows = rows_for(conn, ids)
        if f["q"]:
            add_excerpts(conn, rows, f["q"])
        out["speeches"] = rows
    if args.get("facets") in ("1", "true"):
        out["facets"] = facets(conn, conds, f, session_labels(conn))
        out["facets_note"] = FACET_NOTE
    return out


def speeches_route(conn, args):
    return speeches(conn, args)


ROUTES = [("/speeches", speeches_route)]
