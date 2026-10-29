"""The figures of the Method page: /api/method.

The page explains how Torko works, step by step. Each step shows one figure with its denominator.
The figures over the whole data are cached, because they change only when new data loads.
"""
from sqlalchemy import text

from pages.common import cached, speech_tags_cte
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

COUNTS_NOTE = (
    "turns.total counts all rows of the table turns. turns.member counts the turns with a member. "
    "turns.chair_or_crowd counts the turns with no member and a role of the chair or of many members at once. "
    "turns.no_name counts the turns with no member and no role. The three parts add up to turns.total. "
    "speeches.total counts all speeches. speeches.with_member counts the speeches with a member. "
    "speeches.eligible counts the speeches with a member and min_words words or more. "
    "speeches.with_tldr counts the eligible speeches with a TLDR from a model (not a fixed rule text). "
    "speeches.with_tag counts the eligible speeches with at least one tag. "
    "example.labels lists the most frequent printed labels of one member, with the number of turns of each. "
    "unread_text is fixed text from a measurement of the stored pages. No query computes it."
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


def method_page(conn, args):
    return {
        "corpus": corpus_figures(conn), "turns": turn_figures(conn), "speeches": speech_figures(conn),
        "example": example_member(conn), "unread_text": UNREAD_TEXT, "counts_note": COUNTS_NOTE,
    }


ROUTES = [("/method", method_page)]
