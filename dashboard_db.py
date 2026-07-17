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

from collections import Counter

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


def summarize_mp_diff(mp_list_raw, attributed) -> dict:
    """Bird's-eye tagged-vs-attributed counts for one debate, for the list view.

    Pure set math over Sansad's tag list (`mp_list_raw`, each entry has
    `mpCode`/`mpName`) versus the sansadIds we attributed a turn to
    (`attributed`, a {sansadId: name} map). NO `raw_html`, NO parsing -- this
    runs per card across a whole page, so it must stay cheap. It therefore has
    NO reason breakdown: `missCount` is the WORST CASE (every tagged MP we did
    not attribute counted as a miss), deliberately. The reasoned split lives in
    `get_mp_diff`, one debate at a time. Counted OVER one debate.
    """
    tagged = {str(m["mpCode"]): (m.get("mpName") or str(m["mpCode"])) for m in (mp_list_raw or [])}
    attr_codes = set(attributed)
    agree = [n for c, n in sorted(tagged.items()) if c in attr_codes]
    miss = [n for c, n in sorted(tagged.items()) if c not in attr_codes]
    return {
        "taggedCount": len(tagged),
        "agreeCount": len(agree),
        "missCount": len(miss),
        "agreeSample": agree[:2],
        "missSample": miss[:2],
    }


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
    debate_types: list[str] | None = None,
    text_query: str | None = None,
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
    if debate_types:
        clauses.append("d.debate_type = ANY(:debate_types)")
        params["debate_types"] = debate_types
    if q:
        clauses.append("d.title ILIKE :q")
        params["q"] = f"%{q}%"
    if text_query:
        # Whole-word keyword match over every turn's body, served by the GIN
        # index in 08-turns-fts.sql. Same 'simple' config as the index, or it
        # would not be used. plainto_tsquery ANDs the words together.
        clauses.append(
            "EXISTS (SELECT 1 FROM turns t WHERE t.debate_id = d.id "
            "AND to_tsvector('simple', t.text) @@ plainto_tsquery('simple', :text_query))"
        )
        params["text_query"] = text_query
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
                       d.debate_type, d.debate_date, d.source_url, d.mp_list_raw,
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
            attributed = {s["sansadId"]: s["name"] for s in present}
            results.append(
                {
                    "id": composite_id(r.loksabha, r.session, r.dbslno),
                    "loksabha": r.loksabha,
                    "session": r.session,
                    "dbslno": r.dbslno,
                    "title": r.title,
                    "debateType": r.debate_type,
                    "debateDate": r.debate_date.isoformat() if r.debate_date else None,
                    "sourceUrl": r.source_url,
                    "speakerCount": len(present),
                    "turnCount": r.turn_count,
                    "speakersPresent": present,
                    "mpDiff": summarize_mp_diff(r.mp_list_raw, attributed),
                }
            )

    return {"total": total, "results": results}


def get_debate_detail(loksabha: int, session: int, dbslno: int) -> dict | None:
    engine = get_engine()
    with engine.connect() as conn:
        debate = conn.execute(
            text(
                "SELECT id, loksabha, session, dbslno, title, debate_type, debate_date, source_url "
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
        "sourceUrl": debate.source_url,
        "speakerCount": len(present),
        "turnCount": len(turns),
        "speakersPresent": present,
        "turns": turns,
    }


def classify_tagged_not_attributed(
    loksabha: int, raw_html: str, mp_list: list[dict], attributed_codes: set[str]
) -> list[dict]:
    """For tagged MPs this debate did NOT attribute a turn to, say why.

    Pure given its inputs (no DB, no network) so it is testable over fixtures.
    `attributed_codes` is the ground truth of who we actually named a turn for
    -- normally read straight from the `turns` table, which is the real
    output of the production pipeline (all resolver tiers, not just anchors).

    The WHY comes from `scripts/audit_sansad_floor.py`'s `audit_debate`: this
    function reuses its exact reason constants and rebuilds the same three
    sets it computes (`colliding` fold keys, `role_keys` for Chair/crowd
    labels, `printed_labels` for every speaker-shaped label in the raw text).
    It cannot simply CALL `audit_debate`, because that function only returns
    an aggregate Counter plus the list of UNEXPLAINED misses -- it has no path
    that names the reason for a specific `not_printed` or `fold_collision` MP,
    which this per-debate panel needs. So the set-building is duplicated here
    rather than the classification rules: same reason names, same buckets,
    same closed set, sourced from the same two modules
    (`debate_fetch` / `debate_fetch_legacy`) `audit_debate` itself calls.
    """
    import html as html_mod

    import debate_fetch
    import debate_fetch_legacy as legacy
    from debate_fetch import _folded_key
    from db_roster import load_db_roster
    from scripts.audit_sansad_floor import (
        REASON_FOLD_COLLISION,
        REASON_NOT_PRINTED,
        REASON_ROLE_ONLY,
        REASON_UNEXPLAINED,
    )

    if not mp_list:
        return []

    roster = load_db_roster(loksabha)
    if legacy.looks_legacy(raw_html):
        segments = legacy.split_by_speaker_legacy(raw_html, mp_list, roster)
    else:
        segments = debate_fetch.split_by_speaker(raw_html, mp_list, roster)

    tagged = {str(m["mpCode"]): m["mpName"] for m in mp_list}

    keys = Counter(_folded_key(n) for n in tagged.values() if _folded_key(n))
    colliding = {k for k, n in keys.items() if n > 1}

    role_keys = set()
    for seg in segments:
        label = seg.get("speakerLabel")
        if label and seg.get("nameSource") in ("presiding", "crowd"):
            key = _folded_key(debate_fetch.decode_legacy_hindi(label))
            if key:
                role_keys.add(key)

    text_body = debate_fetch.html_to_clean_text(html_mod.unescape(raw_html))
    printed_labels = set()
    for block in text_body.split("\n\n"):
        head = block.split(":", 1)[0]
        if not head or len(head) > 120 or head == block:
            continue
        key = _folded_key(debate_fetch.decode_legacy_hindi(head))
        if key:
            printed_labels.add(key)

    out = []
    for code, name in tagged.items():
        if code in attributed_codes:
            continue
        key = _folded_key(name)
        if key and key in colliding:
            reason = REASON_FOLD_COLLISION
        elif key and key in role_keys:
            reason = REASON_ROLE_ONLY
        elif key and key in printed_labels:
            reason = REASON_UNEXPLAINED
        else:
            reason = REASON_NOT_PRINTED
        out.append({"sansadId": code, "name": name, "reason": reason})
    return out


def get_mp_diff(loksabha: int, session: int, dbslno: int) -> dict | None:
    """Tagged-vs-attributed panel for one debate: agreement, honest misses, added value.

    `agreement` -- tagged by Sansad AND attributed a turn by us.
    `taggedNotAttributed` -- tagged, no turn, WITH a reason from the closed set
      in `scripts/audit_sansad_floor.py` (mostly not our fault: `not_printed`
      and `role_only` are properties of the source or of never-guess, not
      defects; `unexplained` is the only real miss).
    `attributedNotTagged` -- MPs we attributed a turn to that Sansad's own
      participant list never mentions. This is the feature's other half: our
      added value over the source, not a discrepancy to apologise for.

    Both `taggedCount` and `attributedCount` are counted OVER THIS ONE DEBATE
    only -- nobody should read a per-debate ratio here as a corpus-wide rate;
    that question belongs to `scripts/audit_sansad_floor.py --all`.
    """
    engine = get_engine()
    with engine.connect() as conn:
        debate = conn.execute(
            text(
                "SELECT id, raw_html, mp_list_raw FROM debates "
                "WHERE loksabha = :ls AND session = :sess AND dbslno = :db"
            ),
            {"ls": loksabha, "sess": session, "db": dbslno},
        ).fetchone()
        if debate is None:
            return None

        mp_list = debate.mp_list_raw or []
        if not mp_list:
            return {
                "taggedCount": 0,
                "attributedCount": 0,
                "agreement": [],
                "taggedNotAttributed": [],
                "attributedNotTagged": [],
            }

        attributed_rows = conn.execute(
            text(
                """
                SELECT DISTINCT p.sansad_id AS sansad_id, sp.name AS name
                FROM turns t
                JOIN persons p ON p.id = t.person_id
                LEFT JOIN speakers sp ON sp.person_id = p.id
                WHERE t.debate_id = :debate_id
                """
            ),
            {"debate_id": debate.id},
        ).fetchall()

    attributed = {str(r.sansad_id): r.name for r in attributed_rows}
    tagged = {str(m["mpCode"]): m["mpName"] for m in mp_list}

    agreement_codes = sorted(set(tagged) & set(attributed))
    added_codes = sorted(set(attributed) - set(tagged))

    not_attributed = classify_tagged_not_attributed(
        loksabha, debate.raw_html, mp_list, set(attributed)
    )

    return {
        "taggedCount": len(tagged),
        "attributedCount": len(attributed),
        "agreement": [{"sansadId": c, "name": tagged[c]} for c in agreement_codes],
        "taggedNotAttributed": sorted(not_attributed, key=lambda r: r["name"] or ""),
        "attributedNotTagged": [{"sansadId": c, "name": attributed[c]} for c in added_codes],
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
                       d.source_url,
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
            "sourceUrl": r.source_url,
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
            {"type": r.debate_type, "count": r.count}
            for r in conn.execute(
                text(
                    "SELECT debate_type, count(*) AS count FROM debates "
                    "WHERE debate_type IS NOT NULL "
                    "GROUP BY debate_type ORDER BY count DESC, debate_type"
                )
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
