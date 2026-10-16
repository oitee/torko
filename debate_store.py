from __future__ import annotations

from typing import Any

# The details API sends dates as "14/12/2024". Callers must see the same string type from the table.
_API_DATE_FMT = "%d/%m/%Y"


def _row_to_payload(row: Any) -> dict:
    return {
        "debateDesc": row.raw_html,
        # mpCode must stay an int, as the API sends it. `resolve_speaker` compares codes by identity.
        "mpPartDetailList": row.mp_list_raw or [],
        "debateDate": row.debate_date.strftime(_API_DATE_FMT) if row.debate_date else None,
        "debateType": row.debate_type,
        "contents": row.contents,
    }


def load_debate(loksabha: int, session: int, db_slno: int) -> dict | None:
    """Return None when the debate is not stored. Connection and query failures raise."""
    from sqlalchemy import text

    from db import get_engine

    engine = get_engine()
    with engine.connect() as conn:
        row = conn.execute(
            text(
                """
                SELECT raw_html, mp_list_raw, debate_date, debate_type, contents
                FROM debates
                WHERE loksabha = :loksabha AND session = :session AND dbslno = :dbslno
                """
            ),
            {"loksabha": loksabha, "session": session, "dbslno": db_slno},
        ).first()
    return _row_to_payload(row) if row else None


def read_debate_ids(path: str) -> list[int]:
    """Read one debate id per line. Skip blank and "#" lines. Raise ValueError on any other non-number line."""
    ids = []
    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if not line.isdigit():
                raise ValueError(f"{path} line {n}: not a debate id: {line!r}")
            ids.append(int(line))
    return ids
