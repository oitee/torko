"""
Postgres-backed queries for /api/dashboard/* (see internal_docs/028_TURNS_TABLE.md
and 026_DASHBOARD_DEMO.md for the shapes these were designed to match). Replaces
the frozen `fixtures/dashboard_debates.json` the routes used before `turns`
existed -- same JSON contract, real corpus underneath.

A debate's public id is the composite string "{loksabha}-{session}-{dbslno}",
not `debates.id` (an internal bigserial) -- kept for URL compatibility with the
existing FE (`debate.html?id=18-5-4012`).

`speakersPresent` never includes role rows (presiding officers, crowd labels):
those aren't people, and mixing them into a "speakers present" list would be
the exact kind of silent misattribution never-guess exists to prevent. They
still show up in the transcript (`turns`), tagged by `roleKind`.
"""
from __future__ import annotations

from sqlalchemy import text

from db import get_engine


def composite_id(loksabha: int, session: int, dbslno: int) -> str:
    return f"{loksabha}-{session}-{dbslno}"


def parse_composite_id(debate_id: str) -> tuple[int, int, int] | None:
    parts = debate_id.split("-")
    if len(parts) != 3:
        return None
    try:
        return int(parts[0]), int(parts[1]), int(parts[2])
    except ValueError:
        return None


def _speakers_present(conn, debate_id: int) -> list[dict]:
    rows = conn.execute(
        text(
            """
            SELECT p.sansad_id AS sansad_id, sp.name AS name, sp.party AS party,
                   sp.constituency AS constituency
            FROM turns t
            JOIN persons p ON p.id = t.person_id
            LEFT JOIN speakers sp ON sp.person_id = p.id
            WHERE t.debate_id = :debate_id
            GROUP BY p.sansad_id, sp.name, sp.party, sp.constituency
            ORDER BY sp.name
            """
        ),
        {"debate_id": debate_id},
    ).fetchall()
    return [
        {
            "sansadId": str(r.sansad_id),
            "name": r.name,
            "party": r.party,
            "constituency": r.constituency,
            "verified": True,  # speakersPresent only ever holds resolved persons
        }
        for r in rows
    ]


def list_debates(
    date_from: str | None,
    date_to: str | None,
    loksabha: int | None,
    session: int | None,
    parties: list[str],
    speaker_codes: list[str],
    q: str,
    page: int,
    page_size: int,
) -> dict:
    clauses = []
    params: dict = {}

    if date_from:
        clauses.append("d.debate_date >= :date_from")
        params["date_from"] = date_from
    if date_to:
        clauses.append("d.debate_date <= :date_to")
        params["date_to"] = date_to
    if loksabha is not None:
        clauses.append("d.loksabha = :loksabha")
        params["loksabha"] = loksabha
    if session is not None:
        clauses.append("d.session = :session")
        params["session"] = session
    if q:
        clauses.append("d.title ILIKE :q")
        params["q"] = f"%{q}%"
    if parties:
        clauses.append(
            "EXISTS (SELECT 1 FROM turns t JOIN speakers sp ON sp.person_id = t.person_id "
            "WHERE t.debate_id = d.id AND sp.party = ANY(:parties))"
        )
        params["parties"] = parties
    if speaker_codes:
        codes = [int(c) for c in speaker_codes if c.isdigit()]
        if codes:
            clauses.append(
                "EXISTS (SELECT 1 FROM turns t JOIN persons p ON p.id = t.person_id "
                "WHERE t.debate_id = d.id AND p.sansad_id = ANY(:speaker_codes))"
            )
            params["speaker_codes"] = codes

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""

    engine = get_engine()
    with engine.connect() as conn:
        total = conn.execute(
            text(f"SELECT count(*) FROM debates d {where}"), params
        ).scalar()

        rows = conn.execute(
            text(
                f"""
                SELECT d.id, d.loksabha, d.session, d.dbslno, d.title,
                       d.debate_type, d.debate_date,
                       (SELECT count(*) FROM turns t WHERE t.debate_id = d.id) AS turn_count
                FROM debates d
                {where}
                ORDER BY d.debate_date DESC NULLS LAST, d.id
                LIMIT :limit OFFSET :offset
                """
            ),
            {**params, "limit": page_size, "offset": (page - 1) * page_size},
        ).fetchall()

        results = []
        for r in rows:
            present = _speakers_present(conn, r.id)
            results.append(
                {
                    "id": composite_id(r.loksabha, r.session, r.dbslno),
                    "loksabha": r.loksabha,
                    "session": r.session,
                    "dbslno": r.dbslno,
                    "title": r.title,
                    "debateType": r.debate_type,
                    "debateDate": r.debate_date.isoformat() if r.debate_date else None,
                    "speakerCount": len(present),
                    "turnCount": r.turn_count,
                    "speakersPresent": present,
                }
            )

    return {"total": total, "results": results}


def get_debate_detail(loksabha: int, session: int, dbslno: int) -> dict | None:
    engine = get_engine()
    with engine.connect() as conn:
        debate = conn.execute(
            text(
                "SELECT id, loksabha, session, dbslno, title, debate_type, debate_date "
                "FROM debates WHERE loksabha = :ls AND session = :sess AND dbslno = :db"
            ),
            {"ls": loksabha, "sess": session, "db": dbslno},
        ).fetchone()
        if debate is None:
            return None

        present = _speakers_present(conn, debate.id)

        turn_rows = conn.execute(
            text(
                """
                SELECT t.seq, t.speaker_label, t.text, t.name_source, t.role_kind,
                       p.sansad_id AS sansad_id, sp.name AS person_name, sp.party AS party,
                       sr.display_name AS role_display_name
                FROM turns t
                LEFT JOIN persons p ON p.id = t.person_id
                LEFT JOIN speakers sp ON sp.person_id = p.id
                LEFT JOIN speaker_roles sr ON sr.id = t.role_id
                WHERE t.debate_id = :debate_id
                ORDER BY t.seq
                """
            ),
            {"debate_id": debate.id},
        ).fetchall()

        turns = []
        for t in turn_rows:
            name = t.person_name or t.role_display_name or t.speaker_label
            turns.append(
                {
                    "turnIndex": t.seq,
                    "sansadId": str(t.sansad_id) if t.sansad_id is not None else None,
                    "name": name,
                    "party": t.party,
                    "verified": t.sansad_id is not None,
                    "nameSource": t.name_source,
                    "roleKind": t.role_kind,
                    "text": t.text,
                }
            )

    return {
        "id": composite_id(debate.loksabha, debate.session, debate.dbslno),
        "loksabha": debate.loksabha,
        "session": debate.session,
        "dbslno": debate.dbslno,
        "title": debate.title,
        "debateType": debate.debate_type,
        "debateDate": debate.debate_date.isoformat() if debate.debate_date else None,
        "speakerCount": len(present),
        "turnCount": len(turns),
        "speakersPresent": present,
        "turns": turns,
    }


def list_speakers(q: str) -> list[dict]:
    engine = get_engine()
    clause = "WHERE sp.name ILIKE :q" if q else ""
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                f"""
                SELECT p.sansad_id AS sansad_id, sp.name AS name, sp.party AS party,
                       sp.constituency AS constituency, count(DISTINCT t.debate_id) AS debate_count
                FROM turns t
                JOIN persons p ON p.id = t.person_id
                LEFT JOIN speakers sp ON sp.person_id = p.id
                {clause}
                GROUP BY p.sansad_id, sp.name, sp.party, sp.constituency
                ORDER BY sp.name
                """
            ),
            {"q": f"%{q}%"} if q else {},
        ).fetchall()
    return [
        {
            "sansadId": str(r.sansad_id),
            "name": r.name,
            "party": r.party,
            "constituency": r.constituency,
            "debateCount": r.debate_count,
        }
        for r in rows
    ]


def get_speaker_detail(sansad_id: str) -> dict | None:
    if not sansad_id.isdigit():
        return None
    engine = get_engine()
    with engine.connect() as conn:
        speaker = conn.execute(
            text(
                """
                SELECT p.sansad_id AS sansad_id, sp.name AS name, sp.party AS party,
                       sp.constituency AS constituency
                FROM persons p
                LEFT JOIN speakers sp ON sp.person_id = p.id
                WHERE p.sansad_id = :sansad_id
                """
            ),
            {"sansad_id": int(sansad_id)},
        ).fetchone()
        if speaker is None:
            return None

        debate_rows = conn.execute(
            text(
                """
                SELECT d.loksabha, d.session, d.dbslno, d.title, d.debate_type, d.debate_date,
                       count(*) AS interventions, sum(t.word_count) AS words
                FROM turns t
                JOIN persons p ON p.id = t.person_id
                JOIN debates d ON d.id = t.debate_id
                WHERE p.sansad_id = :sansad_id
                GROUP BY d.id, d.loksabha, d.session, d.dbslno, d.title, d.debate_type, d.debate_date
                ORDER BY d.debate_date
                """
            ),
            {"sansad_id": int(sansad_id)},
        ).fetchall()

    debates = [
        {
            "id": composite_id(r.loksabha, r.session, r.dbslno),
            "loksabha": r.loksabha,
            "session": r.session,
            "dbslno": r.dbslno,
            "title": r.title,
            "debateType": r.debate_type,
            "debateDate": r.debate_date.isoformat() if r.debate_date else None,
            "interventions": r.interventions,
            "words": int(r.words) if r.words is not None else 0,
        }
        for r in debate_rows
    ]

    return {
        "speaker": {
            "sansadId": str(speaker.sansad_id),
            "name": speaker.name,
            "party": speaker.party,
            "constituency": speaker.constituency,
        },
        "totalDebates": len(debates),
        "debates": debates,
    }


def get_facets() -> dict:
    engine = get_engine()
    with engine.connect() as conn:
        parties = [
            r[0]
            for r in conn.execute(
                text(
                    "SELECT DISTINCT sp.party FROM turns t "
                    "JOIN speakers sp ON sp.person_id = t.person_id "
                    "WHERE sp.party IS NOT NULL ORDER BY sp.party"
                )
            ).fetchall()
        ]
        loksabhas = [r[0] for r in conn.execute(text("SELECT DISTINCT loksabha FROM debates ORDER BY loksabha")).fetchall()]
        session_rows = conn.execute(
            text("SELECT DISTINCT loksabha, session FROM debates ORDER BY loksabha, session")
        ).fetchall()
        debate_types = [
            r[0]
            for r in conn.execute(
                text("SELECT DISTINCT debate_type FROM debates WHERE debate_type IS NOT NULL ORDER BY debate_type")
            ).fetchall()
        ]

    sessions_by_loksabha: dict[str, list[int]] = {}
    for r in session_rows:
        sessions_by_loksabha.setdefault(str(r.loksabha), []).append(r.session)

    return {
        "parties": parties,
        "loksabhas": loksabhas,
        "sessionsByLoksabha": sessions_by_loksabha,
        "debateTypes": debate_types,
    }
