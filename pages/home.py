"""The data of the home page: the subjects typical of the newest session, and the chamber.

A subject is typical of a session when its share of the session's tagged speeches is much higher
than its share across the whole term. A general tag has a high count in every session, so a raw count would show it every time.
"""
from sqlalchemy import text

from pages.common import cached, slug, speech_tags_cte

# The shared CTE, limited to the speeches of one term (:t). It reads far fewer items than the whole table.
TERM_SPEECH_TAGS = speech_tags_cte(
    "si.speech_id IN (SELECT s2.id FROM speeches s2 JOIN debates d2 ON d2.id = s2.debate_id WHERE d2.loksabha = :t)")

MIN_SPEECHES = 12
TOP_SUBJECTS = 16
LIT_SUBJECTS = 8

COUNTS_NOTE = (
    "typical.speeches_in_session counts speeches of the newest session that carry the tag. "
    "typical.speeches_in_term counts speeches of the whole term that carry the tag. "
    "lift is (speeches_in_session / session speeches with a kept tag) divided by (speeches_in_term / term speeches with a kept tag). "
    "A subject needs at least 12 speeches in the session. Order: highest lift first. "
    "chamber lists each member of the term who has at least one attributed speech, with the latest party of the term. "
    "debates counts the debates of the newest session. "
    "corpus.debates counts all rows of the table debates. corpus.terms lists the Lok Sabha numbers of those debates. "
    "corpus.first and corpus.last are the earliest and the latest debate date. "
    "corpus.members counts the members with at least one speech that names them. "
    "corpus.tags counts the tags with a status other than rejected and merged. "
    "corpus.error_rate is fixed text from a manual review of a sample of named turns. No query computes it."
)

# The share of named turns with a wrong name. It comes from a manual review, so the API does not compute it.
ERROR_RATE = {
    "value": 0.0024, "text": "about 0.24%", "counts": "named turns with the wrong member name",
    "source": "Manual review of a sample of named turns. The figure is fixed text. No query computes it.",
}


def corpus_figures(conn):
    """The figures over the whole data. They change only when new data loads, so the result is cached."""
    def load():
        debates, first, last = conn.execute(text("SELECT count(*), min(debate_date), max(debate_date) FROM debates")).one()
        terms = [r[0] for r in conn.execute(text("SELECT DISTINCT loksabha FROM debates ORDER BY 1"))]
        members = conn.execute(text("SELECT count(DISTINCT person_id) FROM speeches")).scalar()
        tags = conn.execute(text("SELECT count(*) FROM tags WHERE status NOT IN ('rejected', 'merged')")).scalar()
        return {"debates": debates, "terms": terms, "first": str(first), "last": str(last),
                "members": members, "tags": tags, "error_rate": ERROR_RATE}
    return cached("corpus_figures", load)


def shape_typical(rows):
    return [{"name": r["tag"], "slug": slug(r["tag"]), "type": r["type"],
             "n": r["n_ses"], "speeches_in_session": r["n_ses"],
             "n_term": r["n_term"], "speeches_in_term": r["n_term"],
             "lift": round(r["lift"], 1)} for r in rows]


def home_page(conn, args):
    term, session = conn.execute(text("""
        SELECT loksabha, session FROM debates WHERE debate_date IS NOT NULL
        ORDER BY debate_date DESC LIMIT 1""")).one()
    span = conn.execute(text(
        "SELECT min(debate_date), max(debate_date), count(*) FROM debates WHERE loksabha = :t AND session = :s"),
        {"t": term, "s": session}).one()
    rows = conn.execute(text(f"""
        WITH {TERM_SPEECH_TAGS},
        st AS (SELECT st.tag_id, d.session FROM speech_tags st JOIN speeches s ON s.id = st.speech_id
               JOIN debates d ON d.id = s.debate_id WHERE d.loksabha = :t),
        tot AS (SELECT count(DISTINCT si.speech_id) FILTER (WHERE d.session = :s) AS ses,
                       count(DISTINCT si.speech_id) AS term
                FROM speech_items si JOIN speeches s ON s.id = si.speech_id JOIN debates d ON d.id = s.debate_id
                WHERE si.kept AND d.loksabha = :t)
        SELECT t.tag, t.type, count(*) FILTER (WHERE st.session = :s) AS n_ses, count(*) AS n_term,
               (count(*) FILTER (WHERE st.session = :s))::float / tot.ses / (count(*)::float / tot.term) AS lift
        FROM st JOIN tags t ON t.id = st.tag_id CROSS JOIN tot
        WHERE t.type NOT IN ('role')
        GROUP BY t.id, tot.ses, tot.term HAVING count(*) FILTER (WHERE st.session = :s) >= :minn
        ORDER BY lift DESC, t.tag LIMIT :lim"""),
        {"t": term, "s": session, "minn": MIN_SPEECHES, "lim": TOP_SUBJECTS}).mappings().all()
    chamber = conn.execute(text("""
        WITH m AS (
            SELECT DISTINCT ON (pe.id) pe.id AS mid, pe.name, p.code AS party
            FROM speeches s JOIN debates d ON d.id = s.debate_id JOIN persons pe ON pe.id = s.person_id
            LEFT JOIN speakers sp ON sp.person_id = pe.id AND sp.lok_sabha_term = d.loksabha
            LEFT JOIN parties p ON p.id = sp.party_id
            WHERE d.loksabha = :t
            ORDER BY pe.id, sp.effective_from DESC)
        SELECT mid, name, party, count(*) OVER (PARTITION BY party) AS size FROM m
        ORDER BY size DESC, party, name"""), {"t": term}).all()
    # The members who spoke on each of the top subjects in the newest session, in one query.
    top = [r["tag"] for r in rows[:LIT_SUBJECTS]]
    lit = {slug(n): [] for n in top}
    if top:
        for tag, pid in conn.execute(text(f"""
            WITH {TERM_SPEECH_TAGS}
            SELECT DISTINCT t.tag, s.person_id FROM speech_tags st JOIN tags t ON t.id = st.tag_id
            JOIN speeches s ON s.id = st.speech_id JOIN debates d ON d.id = s.debate_id
            WHERE t.tag = ANY(:tags) AND d.loksabha = :t AND d.session = :s
            ORDER BY t.tag, s.person_id"""), {"tags": top, "t": term, "s": session}).all():
            lit[slug(tag)].append(pid)
    return {
        "chamber": [[r[0], r[1], r[2]] for r in chamber], "lit": lit,
        "term": term, "session": session, "first": str(span[0]), "last": str(span[1]), "debates": span[2],
        "typical": shape_typical(rows), "corpus": corpus_figures(conn), "counts_note": COUNTS_NOTE,
    }


ROUTES = [("/home", home_page)]
