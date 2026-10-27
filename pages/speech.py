"""The speech page: one speech, its turns, and the reason for each of its tags."""
import re

from sqlalchemy import text

from pages.common import PARTY_AT_DATE, clean_layout, slug, speech_tag_map, tidy_title, tidy_type

LAID = re.compile(r"\s*-\s*Laid\s*$", re.I)

# Meaning of each source, for the reader.
SOURCE_NOTE = {
    "llm": "The extraction model named this in the speech text.",
    "dictionary": "The name matched a known tag name in the speech text.",
    "summary_tag": "The tag is near the speech summary in the embedding space.",
}


def split_title(title):
    """Return (title without the trailing 'Laid' mark, whether the mark was there)."""
    title = re.sub(r"\s+", " ", title or "").strip()
    return LAID.sub("", title), bool(LAID.search(title))


def group_reasons(tags, items):
    """Attach to each tag the kept items that gave the tag. Tags keep their order.

    tags: list of tag dicts with "name". items: list of dicts with "tag" and the item fields.
    """
    by_tag = {}
    for it in items:
        by_tag.setdefault(it["tag"], []).append({k: v for k, v in it.items() if k != "tag"})
    out = []
    for t in tags:
        why = by_tag.get(t["name"], [])
        out.append({**t, "why": why, "source_note": SOURCE_NOTE.get(t["source"])})
    return out


def turn_dict(t, speech_id):
    return {
        "seq": t["seq"], "label": t["speaker_label"], "text": clean_layout(t["text"]), "words": t["word_count"],
        "repair": t["text_source"], "own": t["speech_id"] == speech_id,
        "member": t["person"], "member_id": t["mid"], "role": t["role"], "role_kind": t["role_kind"],
        "attributed": t["person"] is not None,
    }


def mention_places(mention, turn_list):
    """Return the places of the mention in the cleaned text of the turns of the speech.

    Each place is {"seq", "start", "end"}: character offsets in the cleaned text, end not included.
    The match ignores case, and any run of spaces in the mention matches any run of spaces in the text.
    """
    words = (mention or "").split()
    if not words:
        return []
    pattern = re.compile(r"\s+".join(re.escape(w) for w in words), re.I)
    return [{"seq": t["seq"], "start": m.start(), "end": m.end()}
            for t in turn_list if t["own"] for m in pattern.finditer(t["text"])]


SIDE_SQL = """
    SELECT t.seq, t.speaker_label, t.text, t.word_count, t.text_source, t.speech_id, t.role_kind,
           sr.display_name AS role, pe.name AS person, pe.id AS mid
    FROM turns t LEFT JOIN speaker_roles sr ON sr.id = t.role_id LEFT JOIN persons pe ON pe.id = t.person_id
    WHERE t.debate_id = :d AND {cond} ORDER BY t.seq {order} LIMIT 2"""


def member_counts(conn, s, first_tag):
    """Counts of the member of the speech. The unit is the speech, not the turn.

    term_speeches: speeches of the member in debates of the same Lok Sabha term (all kinds of debate).
    tag_speeches: speeches of the member that carry the first tag of this speech (after merges).
    tag_order: the place of this speech among those, oldest first (date, debate, seq). The first one is 1.
    """
    if s["person_id"] is None:
        return None
    term_n = conn.execute(text("""
        SELECT count(*) FROM speeches x JOIN debates dx ON dx.id = x.debate_id
        WHERE x.person_id = :p AND dx.loksabha = :t"""), {"p": s["person_id"], "t": s["loksabha"]}).scalar()
    out = {"term": s["loksabha"], "term_speeches": term_n, "tag": None, "tag_speeches": None, "tag_order": None}
    if first_tag:
        row = conn.execute(text("""
            WITH ids AS (SELECT id FROM tags WHERE tag = :tag OR merged_into = (SELECT id FROM tags WHERE tag = :tag LIMIT 1)),
            mine AS (
                SELECT DISTINCT x.id, dx.debate_date, x.debate_id, x.seq_start
                FROM speeches x JOIN debates dx ON dx.id = x.debate_id
                JOIN speech_items si ON si.speech_id = x.id AND si.kept
                LEFT JOIN entity_names en ON en.id = si.entity_name_id AND en.link_status = 'linked'
                WHERE x.person_id = :p AND COALESCE(si.tag_id, en.tag_id) IN (SELECT id FROM ids))
            SELECT count(*) AS n,
                   count(*) FILTER (WHERE (debate_date, debate_id, seq_start) <= (:dd, :db, :sq)) AS pos
            FROM mine"""), {"tag": first_tag, "p": s["person_id"], "dd": s["debate_date"], "db": s["debate_id"], "sq": s["seq_start"]}).mappings().first()
        if row["n"]:
            out.update({"tag": first_tag, "tag_speeches": row["n"], "tag_order": row["pos"]})
    return out


def speech_page(conn, speech_id, args=None):
    s = conn.execute(text(f"""
        SELECT s.id, s.debate_id, s.person_id, s.seq_start, s.seq_end, s.turn_count, s.interruption_count,
               s.word_count, pe.id AS mid, pe.name AS member, pa.party, pa.seat, pa.state,
               d.debate_date, d.loksabha, d.session, d.title, d.debate_type, d.source_url,
               se.summary, se.language
        FROM speeches s JOIN debates d ON d.id = s.debate_id
        LEFT JOIN persons pe ON pe.id = s.person_id
        LEFT JOIN speech_extractions se ON se.speech_id = s.id
        {PARTY_AT_DATE}
        WHERE s.id = :i"""), {"i": speech_id}).mappings().first()
    if s is None:
        return None

    turns = conn.execute(text("""
        SELECT t.seq, t.speaker_label, t.text, t.word_count, t.text_source, t.speech_id, t.role_kind,
               sr.display_name AS role, pe.name AS person, pe.id AS mid
        FROM turns t LEFT JOIN speaker_roles sr ON sr.id = t.role_id LEFT JOIN persons pe ON pe.id = t.person_id
        WHERE t.debate_id = :d AND t.seq BETWEEN :a AND :b ORDER BY t.seq"""),
        {"d": s["debate_id"], "a": s["seq_start"], "b": s["seq_end"]}).mappings().all()
    turn_list = [turn_dict(t, speech_id) for t in turns]

    # One row per kept item. The tag is the kept tag after merges. The subject is the specific subject, if any.
    rows = conn.execute(text("""
        SELECT COALESCE(km.tag, kt.tag) AS tag, si.source, si.name AS item_name, si.mention, si.mention_found,
               si.list, su.label AS subject, su.id AS subject_id, pt.tag AS parent_tag
        FROM speech_items si
        LEFT JOIN entity_names en ON en.id = si.entity_name_id AND en.link_status = 'linked'
        LEFT JOIN tags kt ON kt.id = COALESCE(si.tag_id, en.tag_id)
        LEFT JOIN tags km ON km.id = kt.merged_into
        LEFT JOIN subject_names sn ON sn.entity_name_id = si.entity_name_id
        LEFT JOIN subjects su ON su.id = sn.subject_id
        LEFT JOIN tags pt ON pt.id = su.parent_tag_id
        WHERE si.speech_id = :i AND si.kept AND kt.id IS NOT NULL
        ORDER BY si.id"""), {"i": speech_id}).mappings().all()
    items = [{"tag": r["tag"], "source": r["source"], "item_name": r["item_name"],
              "mention": r["mention"] or None, "mention_found": r["mention_found"],
              "list": r["list"], "subject": r["subject"],
              "subject_id": r["subject_id"],
              "parent_tag": {"name": r["parent_tag"], "slug": slug(r["parent_tag"])} if r["parent_tag"] else None,
              "marks": mention_places(r["mention"], turn_list) if r["mention_found"] and r["source"] != "summary_tag" else []}
             for r in rows]
    tags = group_reasons(speech_tag_map(conn, [speech_id]).get(speech_id, []), items)

    # Speeches around this one. Counts are speeches, not turns.
    side = {"d": s["debate_id"]}
    before = conn.execute(text(SIDE_SQL.format(cond="t.seq < :a", order="DESC")), {**side, "a": s["seq_start"]}).mappings().all()
    after = conn.execute(text(SIDE_SQL.format(cond="t.seq > :a", order="ASC")), {**side, "a": s["seq_end"]}).mappings().all()
    dc = conn.execute(text("""
        SELECT count(*) AS n, count(DISTINCT person_id) AS members,
               count(*) FILTER (WHERE seq_start < :a) AS earlier, count(*) FILTER (WHERE seq_start > :a) AS later
        FROM speeches WHERE debate_id = :d"""), {"d": s["debate_id"], "a": s["seq_start"]}).mappings().first()

    title, laid = split_title(s["title"])
    return {
        "id": s["id"], "debate_id": s["debate_id"], "laid": laid,
        "member": s["member"], "member_id": s["mid"], "party": s["party"], "seat": s["seat"], "state": s["state"],
        "date": s["debate_date"].isoformat() if s["debate_date"] else None,
        "term": s["loksabha"], "session": s["session"], "debate": tidy_title(title),
        "debate_type": tidy_type(s["debate_type"]), "source_url": s["source_url"],
        "words": s["word_count"], "turns": s["turn_count"], "interruptions": s["interruption_count"],
        "language": s["language"], "summary": s["summary"],
        "turn_list": turn_list,
        "before": [turn_dict(t, speech_id) for t in reversed(before)],
        "after": [turn_dict(t, speech_id) for t in after],
        "earlier_speeches": dc["earlier"], "later_speeches": dc["later"],
        "debate_speeches": dc["n"], "debate_members": dc["members"],
        "member_counts": member_counts(conn, s, tags[0]["name"] if tags else None),
        "counts_note": "All counts are speeches, not turns. debate_members counts members with at least one speech in the debate. "
                       "tag_order is the place of this speech among the speeches of the member on the first tag, oldest first.",
        "tags": tags,
        "tags_note": "Each tag counts once for this speech. why lists every kept item that gave the tag.",
    }


ROUTES = [("/speech/<int:speech_id>", speech_page)]
