"""The figures of the Method page: /api/method.

The page explains how Torko works, step by step. Each step shows one figure with its denominator.
The figures over the whole data are cached, because they change only when new data loads.
"""
from sqlalchemy import text

from legacy_hindi import decode_legacy_hindi
from pages.common import cached, slug, speech_tags_cte, tidy_title
from pages.home import corpus_figures

# A speech of this many words or more gets a TLDR and tags. The same threshold as on every other page.
MIN_WORDS = 50

# The example of one member under many printed names. Adhir Ranjan Chowdhury has printed forms in Latin
# and in Hindi script, with and without the seat, and with three spellings of the seat.
EXAMPLE_MEMBER = 368
EXAMPLE_LABELS = 10

# The share of the source text that the readers do not read. It comes from a measurement of the stored
# debate pages: text outside the paragraph tags is lost. No query computes it.
UNREAD_TEXT = {
    "value": 0.136, "text": "about 13.6%", "counts": "of the source text",
    "first_term": {"term": 13, "text": "32.5%"}, "recent_terms": "about 3%",
    "source": "Measurement of the stored debate pages. The figure is fixed text. No query computes it.",
}

# The example of old-font Hindi: the start of one turn, as the stored page of debate 32612 of the 14th Lok Sabha
# holds it. The route decodes it with the same code as the reader, so the page shows what the reader really makes.
LEGACY_EXAMPLE = {
    "term": 14, "dbslno": 32612,
    "text": 'àÉcÉänªÉ, àÉé +ÉÉ{ÉBÉEÉ ¤ÉcÖiÉ +ÉÉ£ÉÉ®ÉÒ cÚÆ ÉÊBÉE +ÉÉ{ÉxÉä àÉÖZÉä ABÉE AäºÉä <¶ªÉÖ {É® ¤ÉÉäãÉxÉä BÉEÉ àÉÉèBÉEÉ ÉÊnªÉÉ,',
}

# The examples of steps 3, 4 and 5. Each is a reference into the database. The route reads every name, date
# and text live. None leaves the example out, and the answer then has null for it.
SPEECH_EXAMPLE = None       # speeches.id of a short speech with a few short interruptions
SUBJECTS_EXAMPLE = None     # speeches.id of a short speech with subjects that the check kept and dropped
SUBJECT_GROUP_EXAMPLE = None  # subjects.id of a specific subject with several names
SPEECH_TEXT_WORDS = 60      # the words of each turn that the speech example sends
GROUP_NAMES = 8             # the names of the subject group that the example sends

COUNTS_NOTE = (
    "turns.total counts all rows of the table turns. turns.member counts the turns with a member. "
    "turns.chair_or_crowd counts the turns with no member and a role of the chair or of many members at once. "
    "turns.no_name counts the turns with no member and no role. The three parts add up to turns.total. "
    "speeches.total counts all speeches. speeches.with_member counts the speeches with a member. "
    "speeches.eligible counts the speeches with a member and min_words words or more. "
    "speeches.with_tldr counts the eligible speeches with a TLDR from a model (not a fixed rule text). "
    "speeches.with_tag counts the eligible speeches with at least one tag. "
    "example.labels lists the most frequent printed labels of one member, with the number of turns of each. "
    "unread_text is fixed text from a measurement of the stored pages. No query computes it. "
    "examples.legacy.source_text is fixed text from a stored page. examples.legacy.text is its decoded form. "
    "examples.speech.turns lists every turn inside one speech: own is true for the turns of the member. "
    "examples.subjects.items lists the subjects that the model named for one speech, with kept from the check. "
    "examples.subject_group.names lists the most frequent names joined into one specific subject."
)


def turn_figures(conn):
    def load():
        r = conn.execute(text("""
            SELECT count(*),
                   count(*) FILTER (WHERE person_id IS NOT NULL),
                   count(*) FILTER (WHERE person_id IS NULL AND role_kind IS NOT NULL),
                   count(*) FILTER (WHERE person_id IS NULL AND role_id IS NULL AND role_kind IS NULL)
            FROM turns""")).one()
        return {"total": r[0], "member": r[1], "chair_or_crowd": r[2], "no_name": r[3]}
    return cached("method_turns", load)


def speech_figures(conn):
    def load():
        r = conn.execute(text("""
            SELECT count(*),
                   count(*) FILTER (WHERE person_id IS NOT NULL),
                   count(*) FILTER (WHERE person_id IS NOT NULL AND word_count >= :w)
            FROM speeches"""), {"w": MIN_WORDS}).one()
        with_tldr = conn.execute(text("""
            SELECT count(*) FROM speech_extractions e
            JOIN models m ON m.id = e.model_id JOIN speeches s ON s.id = e.speech_id
            WHERE m.name <> 'rule-stub' AND s.person_id IS NOT NULL AND s.word_count >= :w"""),
            {"w": MIN_WORDS}).scalar()
        with_tag = conn.execute(text(f"""
            WITH {speech_tags_cte()}
            SELECT count(DISTINCT st.speech_id) FROM speech_tags st JOIN speeches s ON s.id = st.speech_id
            WHERE s.person_id IS NOT NULL AND s.word_count >= :w"""), {"w": MIN_WORDS}).scalar()
        return {"total": r[0], "with_member": r[1], "min_words": MIN_WORDS, "eligible": r[2],
                "with_tldr": with_tldr, "with_tag": with_tag}
    return cached("method_speeches", load)


def example_member(conn):
    name = conn.execute(text("SELECT name FROM persons WHERE id = :p"), {"p": EXAMPLE_MEMBER}).scalar()
    if name is None:
        return None
    rows = conn.execute(text("""
        SELECT speaker_label, count(*) AS n FROM turns
        WHERE person_id = :p AND speaker_label IS NOT NULL
        GROUP BY 1 ORDER BY 2 DESC, 1 LIMIT :lim"""), {"p": EXAMPLE_MEMBER, "lim": EXAMPLE_LABELS}).all()
    return {"member_id": EXAMPLE_MEMBER, "name": name, "labels": [{"label": r[0], "n": r[1]} for r in rows]}


def words(text_, n):
    """The first n words of text_, with an ellipsis mark when it is longer."""
    parts = (text_ or "").split()
    return " ".join(parts[:n]) + (" …" if len(parts) > n else "")


def legacy_example(conn):
    decoded = decode_legacy_hindi(LEGACY_EXAMPLE["text"])
    row = conn.execute(text("""
        SELECT d.debate_date, d.title, d.source_url, p.id AS member_id, p.name AS member
        FROM debates d LEFT JOIN turns t ON t.debate_id = d.id AND t.text LIKE :frag
        LEFT JOIN persons p ON p.id = t.person_id
        WHERE d.loksabha = :t AND d.dbslno = :n
        ORDER BY t.seq LIMIT 1"""),
        {"t": LEGACY_EXAMPLE["term"], "n": LEGACY_EXAMPLE["dbslno"], "frag": "%" + decoded[:40] + "%"}).mappings().first()
    out = {"source_text": LEGACY_EXAMPLE["text"], "text": decoded, "debate": None}
    if row:
        out["debate"] = {"date": str(row["debate_date"]) if row["debate_date"] else None, "title": tidy_title(row["title"]),
                         "source_url": row["source_url"], "member_id": row["member_id"], "member": row["member"]}
    return out


def speech_row(conn, speech_id):
    return conn.execute(text("""
        SELECT s.id, s.person_id, s.debate_id, s.seq_start, s.seq_end, s.word_count, pe.name AS member,
               d.debate_date, d.title
        FROM speeches s JOIN debates d ON d.id = s.debate_id LEFT JOIN persons pe ON pe.id = s.person_id
        WHERE s.id = :i"""), {"i": speech_id}).mappings().first()


def speech_example(conn, speech_id=None):
    speech_id = speech_id or SPEECH_EXAMPLE
    s = speech_row(conn, speech_id) if speech_id else None
    if s is None:
        return None
    rows = conn.execute(text("""
        SELECT t.seq, t.person_id, t.role_kind, t.speaker_label, t.word_count, t.text, p.name
        FROM turns t LEFT JOIN persons p ON p.id = t.person_id
        WHERE t.debate_id = :d AND t.seq BETWEEN :a AND :b ORDER BY t.seq"""),
        {"d": s["debate_id"], "a": s["seq_start"], "b": s["seq_end"]}).mappings().all()
    turns = [{"seq": r["seq"], "own": r["person_id"] == s["person_id"], "member_id": r["person_id"],
              "speaker": r["name"] or ("The Chair" if r["role_kind"] == "presiding" else r["speaker_label"]),
              "words": r["word_count"], "text": words(r["text"], SPEECH_TEXT_WORDS)} for r in rows]
    return {"speech_id": s["id"], "member_id": s["person_id"], "member": s["member"],
            "date": str(s["debate_date"]) if s["debate_date"] else None, "debate": tidy_title(s["title"]),
            "words": s["word_count"], "turns": turns}


def subjects_example(conn, speech_id=None):
    speech_id = speech_id or SUBJECTS_EXAMPLE
    s = speech_row(conn, speech_id) if speech_id else None
    if s is None:
        return None
    body = conn.execute(text("SELECT string_agg(text, ' ' ORDER BY seq) FROM turns WHERE speech_id = :i"),
                        {"i": speech_id}).scalar()
    summary = conn.execute(text("SELECT summary FROM speech_extractions WHERE speech_id = :i"), {"i": speech_id}).scalar()
    rows = conn.execute(text("""
        SELECT si.name, si.mention, si.kept, tg.tag, sub.label AS subject
        FROM speech_items si
        LEFT JOIN entity_names en ON en.id = si.entity_name_id
        LEFT JOIN tags tg ON tg.id = en.tag_id AND en.link_status = 'linked'
        LEFT JOIN subject_names sn ON sn.entity_name_id = en.id
        LEFT JOIN subjects sub ON sub.id = sn.subject_id
        WHERE si.speech_id = :i AND si.source = 'llm'
        ORDER BY si.list DESC, si.position"""), {"i": speech_id}).mappings().all()
    items = [{"name": r["name"], "mention": r["mention"], "kept": bool(r["kept"]), "subject": r["subject"],
              "tag": r["tag"], "tag_slug": slug(r["tag"]) if r["tag"] else None} for r in rows]
    return {"speech_id": s["id"], "member_id": s["person_id"], "member": s["member"],
            "date": str(s["debate_date"]) if s["debate_date"] else None, "debate": tidy_title(s["title"]),
            "words": s["word_count"], "text": body, "summary": summary, "items": items}


def subject_group_example(conn, subject_id=None):
    subject_id = subject_id or SUBJECT_GROUP_EXAMPLE
    if not subject_id:
        return None
    sub = conn.execute(text("""
        SELECT sub.id, sub.label, sub.n_speeches, sub.n_names, tg.tag
        FROM subjects sub LEFT JOIN tags tg ON tg.id = sub.parent_tag_id WHERE sub.id = :i"""),
        {"i": subject_id}).mappings().first()
    if sub is None:
        return None
    names = [r[0] for r in conn.execute(text("""
        SELECT en.name FROM subject_names sn JOIN entity_names en ON en.id = sn.entity_name_id
        WHERE sn.subject_id = :i ORDER BY en.n_speeches DESC, en.name LIMIT :lim"""),
        {"i": subject_id, "lim": GROUP_NAMES})]
    return {"subject_id": sub["id"], "label": sub["label"], "speeches": sub["n_speeches"], "n_names": sub["n_names"],
            "names": names, "tag": sub["tag"], "tag_slug": slug(sub["tag"]) if sub["tag"] else None}


def method_page(conn, args):
    return {
        "corpus": corpus_figures(conn), "turns": turn_figures(conn), "speeches": speech_figures(conn),
        "example": example_member(conn), "unread_text": UNREAD_TEXT, "counts_note": COUNTS_NOTE,
        "examples": {"legacy": legacy_example(conn), "speech": speech_example(conn),
                     "subjects": subjects_example(conn), "subject_group": subject_group_example(conn)},
    }


ROUTES = [("/method", method_page)]
