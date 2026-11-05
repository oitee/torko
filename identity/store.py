"""Read the labels and the people, and store answers. The only database code of this package."""
from __future__ import annotations

import csv
import json
from pathlib import Path

from sqlalchemy import text

from identity.types import Answer, Entry, LabelRow

SOURCES = Path(__file__).resolve().parent.parent / "data" / "person_sources"
UNNAMED = """
    SELECT d.loksabha AS term, t.speaker_label AS label, coalesce(sum(t.word_count), 0) AS words,
           min(t.mp_code) AS code, min(d.debate_date)::text AS first_date, max(d.debate_date)::text AS last_date,
           (array_agg(d.title ORDER BY t.word_count DESC NULLS LAST))[1] AS title,
           (array_agg(left(t.text, 400) ORDER BY t.word_count DESC NULLS LAST))[1] AS excerpt
    FROM turns t JOIN debates d ON d.id = t.debate_id
    WHERE t.person_id IS NULL AND t.role_id IS NULL AND t.speaker_label IS NOT NULL
    GROUP BY 1, 2
"""
SEATED = """
    SELECT DISTINCT ON (s.person_id, s.lok_sabha_term) s.person_id, s.lok_sabha_term AS term,
           coalesce(s.name, p.name) AS name, s.constituency AS seat, st.name AS state, pa.code AS party
    FROM speakers s JOIN persons p ON p.id = s.person_id
    LEFT JOIN states st ON st.id = s.state_id LEFT JOIN parties pa ON pa.id = s.party_id
    WHERE s.source NOT IN ('last-term-fallback', 'not-a-member')
    ORDER BY s.person_id, s.lok_sabha_term, s.effective_from
"""
UPSERT = """
    INSERT INTO label_resolutions
        (loksabha, speaker_label, decided_by, answer, probability, status, options_count, options_hash,
         prompt_version, evidence)
    VALUES (:term, :label, :decided_by, :answer, :probability, :status, :options_count, :options_hash,
            :prompt_version, CAST(:evidence AS jsonb))
    ON CONFLICT (loksabha, speaker_label, decided_by) DO UPDATE SET
        answer = EXCLUDED.answer, probability = EXCLUDED.probability, status = EXCLUDED.status,
        options_count = EXCLUDED.options_count, options_hash = EXCLUDED.options_hash,
        prompt_version = EXCLUDED.prompt_version, evidence = EXCLUDED.evidence, decided_at = now()
"""


def _clean(value) -> str:
    return " ".join(str(value or "").split())


def unnamed_labels(conn) -> list[LabelRow]:
    return [LabelRow(r.term, _clean(r.label), int(r.words), _clean(r.code), _clean(r.first_date),
                     _clean(r.last_date), _clean(r.title), _clean(r.excerpt))
            for r in conn.execute(text(UNNAMED))]


def _read(name: str) -> list[dict]:
    with open(SOURCES / name, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def person_detail(lok_sabha_terms: list[int], rajya_sabha_row: dict | None) -> str:
    """A person with no seat in a term can still speak from the Rajya Sabha, so the option must say so."""
    detail = f"Has a record in Torko. Lok Sabha member in terms {lok_sabha_terms}."
    if rajya_sabha_row:
        detail += (f" Also a Rajya Sabha member in other years: latest term {rajya_sabha_row['latest_term']}, "
                   f"{rajya_sabha_row['term_count']} terms.")
    return detail


def load_entries(conn) -> tuple[dict[int, list[Entry]], list[Entry]]:
    """Return the seated members of each term, and everybody else who can have spoken.

    A list row whose number is linked to a person in Torko gives no option, so one human stays one option.
    """
    seated: dict[int, list[Entry]] = {}
    terms_of: dict[int, set[int]] = {}
    name_of: dict[int, str] = {}
    for r in conn.execute(text(SEATED)):
        detail = f"Lok Sabha member in term {r.term}, seat {r.seat or 'not known'}, {r.state or 'state not known'}, party {r.party or 'not known'}."
        seated.setdefault(r.term, []).append(Entry("person", r.person_id, r.name, detail, r.seat or ""))
        terms_of.setdefault(r.person_id, set()).add(r.term)
        name_of[r.person_id] = r.name
    rows = conn.execute(text("SELECT id, name, sansad_id, rajya_sabha_id FROM persons")).all()
    known_ls = {r.sansad_id for r in rows if r.sansad_id}
    rajya_sabha = {int(r["mpsno"]): r for r in _read("rajya_sabha_members.tsv")}
    linked_rs = {r.rajya_sabha_id for r in rows if r.rajya_sabha_id}
    outside = [Entry("person", r.id, r.name, person_detail(sorted(terms_of.get(r.id, [])), rajya_sabha.get(r.rajya_sabha_id)))
               for r in rows]
    for number, r in rajya_sabha.items():
        if number not in linked_rs:
            outside.append(Entry("rajya_sabha", number, r["name"],
                                 f"On the Rajya Sabha list. Latest term {r['latest_term']}, {r['term_count']} terms."))
    for r in _read("lok_sabha_members.tsv"):
        if int(r["mpsno"]) not in known_ls:
            outside.append(Entry("lok_sabha", int(r["mpsno"]), r["name"],
                                 f"On the Lok Sabha list, not in Torko. Lok Sabha terms {r['terms']}."))
    return seated, outside


def stored_hashes(conn, decided_by: str, prompt_version: str) -> dict[tuple[int, str], str]:
    rows = conn.execute(text("SELECT loksabha, speaker_label, options_hash FROM label_resolutions "
                             "WHERE decided_by = :d AND prompt_version = :p"), {"d": decided_by, "p": prompt_version})
    return {(r.loksabha, r.speaker_label): r.options_hash for r in rows}


def save(conn, row: LabelRow, answer: Answer, status: str, options_count: int, options_hash: str, version: str) -> None:
    conn.execute(text(UPSERT), {
        "term": row.term, "label": row.label, "decided_by": answer.decided_by, "answer": answer.key,
        "probability": answer.probability, "status": status, "options_count": options_count,
        "options_hash": options_hash, "prompt_version": version, "evidence": json.dumps({"top": answer.top, "input_tokens": answer.tokens}),
    })
