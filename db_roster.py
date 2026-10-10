from __future__ import annotations


def load_db_roster(term: int) -> list[dict]:
    """Speakers of `term` or later, from each person's last-term row, in `mpPartDetailList` shape. Returns [] on any failure."""
    # Imported here so that importing this module never needs SQLAlchemy or a database.
    try:
        from sqlalchemy import text

        from db import get_engine

        engine = get_engine()
        with engine.connect() as conn:
            rows = conn.execute(
                text(
                    """
                    SELECT persons.sansad_id AS mp_code,
                           COALESCE(speakers.name, persons.name) AS mp_name
                    FROM speakers
                    JOIN persons ON persons.id = speakers.person_id
                    WHERE speakers.lok_sabha_term >= :term
                      AND speakers.source = 'sansad-last-term'
                    """
                ),
                {"term": term},
            ).all()
        return [{"mpCode": str(r.mp_code), "mpName": r.mp_name} for r in rows]
    except Exception:
        return []
