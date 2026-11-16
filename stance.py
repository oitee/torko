"""The stance of a speech on a bill: the state that the decision model reads, its questions, and the rules after it.

One call for each pair of a speech and a bill. The call asks three questions about the same state:
- stance: for, against, mixed, unclear (choice)
- reasons: how many different reasons about the bill (score)
- on_bill: how much of the speech is about the bill (score)
"""
from __future__ import annotations

from sqlalchemy import text

from decision_model import choice_probabilities, choice_q, score_probabilities, score_q

QUESTIONS_VERSION = "s1"
STANCES = ["for", "against", "mixed", "unclear"]
REASON_LEVELS = ["none", "one", "two", "three or more"]
ON_BILL_LEVELS = ["none", "a small part", "about half", "most", "all"]
STANCE_P = 0.5

STANCE_MEANINGS = {
    "for": "The speaker supports the passing of the bill. This includes a speaker who supports it and also "
           "criticises some parts, asks for changes, or objects only to the procedure (an ordinance, the hurry, "
           "the timing). The minister who moves or defends the bill is for it.",
    "against": "The speaker opposes the passing of the bill, or its introduction. This includes a speaker who "
               "asks that the House not pass it in this form: to withdraw it, or to send it to a committee first, "
               "or who will support it only after such a change.",
    "mixed": "The speaker supports some parts of the bill and opposes other parts, and gives no position on the "
             "passing of the whole bill.",
    "unclear": "The speech gives no position on this bill. For example: a point of order, a question, a short "
               "remark to another member, a local demand, or a speech about another subject or another bill.",
}


def stance_instruction(bill: str) -> str:
    return (f"What is the position of the speaker on the passing of «{bill}»? Judge only this bill, from the "
            f"words of this speaker. Other bills of the same debate do not count.")


def questions(bill: str) -> dict[str, dict]:
    return {
        "stance": choice_q(stance_instruction(bill), STANCE_MEANINGS),
        "reasons": score_q(f"How many different reasons for or against «{bill}» does the speaker give? A reason "
                           f"that the speaker repeats counts one time. Praise, thanks, and procedural points are "
                           f"not reasons.", REASON_LEVELS),
        "on_bill": score_q(f"How much of the speech is about «{bill}»?", ON_BILL_LEVELS),
    }


def bill_label(name: str, year: int) -> str:
    return f"{name}, {year}"


def state(pair: dict, body: str, body_kind: str = "speech") -> str:
    """body_kind is 'speech' for the full text, or 'summary' when the speech is too long."""
    others = "; ".join(pair["other_bills"]) or "none"
    summary = pair["bill_summary"] or "(no summary: only the name of the bill is known)"
    label = "Speech" if body_kind == "speech" else "Summary of the speech (the speech is too long to show)"
    return (f"Debate: {pair['title']}\nDate: {pair['debate_date']}\n"
            f"Bill asked about: {pair['bill']}\nWhat the bill does: {summary}\n"
            f"Other bills of this debate: {others}\n\n"
            f"Member: {pair['member'] or '(no name)'}\n{label}:\n{body}")


def parse(answers: dict) -> dict:
    return {"stance_p": choice_probabilities(answers["stance"], STANCES),
            "reasons_p": score_probabilities(answers["reasons"], REASON_LEVELS),
            "on_bill_p": score_probabilities(answers["on_bill"], ON_BILL_LEVELS)}


def pick_stance(stance_p: dict[str, float], limit: float = STANCE_P) -> str:
    best = max(STANCES, key=lambda s: stance_p[s])
    return best if stance_p[best] >= limit else "unclear"


PAIRS_SQL = """
    SELECT DISTINCT s.id AS speech_id, COALESCE(b.merged_into, b.id) AS bill_id, s.word_count
    FROM debate_bills db JOIN bills b ON b.id = db.bill_id
    JOIN debates d ON (d.loksabha, d.session, d.dbslno) = (db.loksabha, db.session, db.dbslno)
    JOIN speeches s ON s.debate_id = d.id
    WHERE db.kept"""


def load_pair(conn, speech_id: int, bill_id: int) -> dict:
    """bill_id is the kept bill after the merge of spellings."""
    speech = conn.execute(text("""
        SELECT s.id, s.word_count, p.name AS member, d.title, d.debate_date, d.loksabha, d.session, d.dbslno,
               COALESCE((SELECT string_agg(t.text, E'\n' ORDER BY t.seq) FROM turns t WHERE t.speech_id = s.id), '')
                   AS body,
               (SELECT x.summary FROM speech_extractions x WHERE x.speech_id = s.id) AS speech_summary
        FROM speeches s JOIN debates d ON d.id = s.debate_id LEFT JOIN persons p ON p.id = s.person_id
        WHERE s.id = :s"""), {"s": speech_id}).mappings().one()
    bills = conn.execute(text("""
        SELECT DISTINCT b2.id, b2.name, b2.year, b2.summary
        FROM debate_bills db JOIN bills b ON b.id = db.bill_id JOIN bills b2 ON b2.id = COALESCE(b.merged_into, b.id)
        WHERE db.kept AND (db.loksabha, db.session, db.dbslno) = (:ls, :se, :no)"""),
        {"ls": speech["loksabha"], "se": speech["session"], "no": speech["dbslno"]}).mappings().all()
    mine = [bill for bill in bills if bill["id"] == bill_id]
    if not mine:
        raise ValueError(f"bill {bill_id} is not a kept bill of the debate of speech {speech_id}")
    bill = mine[0]
    return {"speech_id": speech_id, "bill_id": bill_id, "member": speech["member"],
            "title": " ".join((speech["title"] or "(no title)").split()), "debate_date": speech["debate_date"],
            "debate": f"LS{speech['loksabha']}-{speech['session']}-{speech['dbslno']}",
            "loksabha": speech["loksabha"], "session": speech["session"], "dbslno": speech["dbslno"],
            "words": speech["word_count"],
            "bill": bill_label(bill["name"], bill["year"]), "bill_summary": bill["summary"],
            "other_bills": sorted(bill_label(other["name"], other["year"]) for other in bills if other["id"] != bill_id),
            "text": speech["body"], "speech_summary": speech["speech_summary"]}
