"""The speech page: one speech, its turns, and the reason for each of its tags."""
import re

from sqlalchemy import text

from pages.common import PARTY_AT_DATE, slug, speech_tag_map, tidy_title, tidy_type

LAID = re.compile(r"\s*-\s*Laid\s*$", re.I)
# Layout marks of the source page, such as [r11], (l1/1150 and /rc. Only these marks go. No word goes.
LAYOUT = re.compile(r"\[[rl]\d+\]|\(l\d+/\d+|(?<=\s)/rc\b")

# Meaning of each source, for the reader.
SOURCE_NOTE = {
    "llm": "The extraction model named this in the speech text.",
    "dictionary": "The name matched a known tag name in the speech text.",
    "summary_tag": "The tag is near the speech summary in the embedding space.",
}


def clean_layout(t):
    """Remove layout marks from the shown text. Runs of spaces collapse."""
    t = LAYOUT.sub("", t or "")
    return re.sub(r"[ \t]{2,}", " ", t)


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
    turn_list = [{
        "seq": t["seq"], "label": t["speaker_label"], "text": clean_layout(t["text"]), "words": t["word_count"],
        "repair": t["text_source"], "own": t["speech_id"] == speech_id,
        "member": t["person"], "member_id": t["mid"], "role": t["role"], "role_kind": t["role_kind"],
        "attributed": t["person"] is not None,
    } for t in turns]

    # One row per kept item. The tag is the kept tag after merges. The subject is the specific subject, if any.
    rows = conn.execute(text("""
        SELECT COALESCE(km.tag, kt.tag) AS tag, si.source, si.name AS item_name, si.mention, si.mention_found,
               si.list, su.label AS subject
        FROM speech_items si
        LEFT JOIN entity_names en ON en.id = si.entity_name_id AND en.link_status = 'linked'
        LEFT JOIN tags kt ON kt.id = COALESCE(si.tag_id, en.tag_id)
        LEFT JOIN tags km ON km.id = kt.merged_into
        LEFT JOIN subject_names sn ON sn.entity_name_id = si.entity_name_id
        LEFT JOIN subjects su ON su.id = sn.subject_id
        WHERE si.speech_id = :i AND si.kept AND kt.id IS NOT NULL
        ORDER BY si.id"""), {"i": speech_id}).mappings().all()
    items = [{"tag": r["tag"], "source": r["source"], "item_name": r["item_name"],
              "mention": r["mention"] or None, "mention_found": r["mention_found"],
              "list": r["list"], "subject": r["subject"]} for r in rows]
    tags = group_reasons(speech_tag_map(conn, [speech_id]).get(speech_id, []), items)

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
        "tags": tags,
        "tags_note": "Each tag counts once for this speech. why lists every kept item that gave the tag.",
    }


ROUTES = [("/speech/<int:speech_id>", speech_page)]
