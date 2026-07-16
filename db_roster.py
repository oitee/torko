"""
Load a Postgres-backed speaker roster to fall back on when a debate's own
`mpPartDetailList` is too thin to resolve names against (see
internal_docs/006_SCHEMA.md for the `persons`/`speakers` shape).

Legacy debates ship a near-empty `mpPartDetailList` -- LS14/2/613 lists ONE
member for a transcript full of speakers -- so `resolve_speaker`'s tiers have
nothing to match against even though the speaker is a known MP sitting in our
`persons`/`speakers` tables. `load_db_roster` returns that wider roster in the
same `{"mpCode": ..., "mpName": ...}` shape as `mpPartDetailList`, so it can be
handed straight to `build_speaker_index` as `db_roster`.

The DB is optional: the CLI/server must keep working with no Postgres running,
so any connection or query failure here is swallowed and an empty list is
returned rather than raised. `debate_fetch.py` must never require SQLAlchemy
to connect just to be imported, so the engine is created lazily inside this
function, not at module import time.
"""
from __future__ import annotations


def load_db_roster(term: int) -> list[dict]:
    """
    Return every known speaker who served in Lok Sabha `term` or later, in
    `mpPartDetailList` shape.

    Scoped by `lok_sabha_term >= term`, not `==`. `db/init/04-speakers.sql`
    loads exactly one row per person, attached to that person's LAST term, so
    someone who served in term T is recorded under their last term, which is
    always >= T. Scoping by equality would wrongly exclude anyone whose career
    continued past `term`.

    Returns [] on any connection or query failure -- callers rely on this to
    make the DB tier a silent no-op when Postgres is unavailable.
    """
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
                    """
                ),
                {"term": term},
            ).all()
        return [{"mpCode": str(r.mp_code), "mpName": r.mp_name} for r in rows]
    except Exception:
        return []
