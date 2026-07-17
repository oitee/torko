"""
Read debates out of the corpus instead of off the wire.

`scripts/import_debates.py` put all 64,921 debates into the `debates` table --
`raw_html` plus the debate's own member list (`mp_list_raw`), which is
everything the parser needs (see internal_docs/022_DEBATE_IMPORT.md). This
module hands that back in the *exact shape the details API returns*, so
`debate_fetch` and `debate_fetch_legacy` cannot tell the difference and no
parsing code has to change.

WHY THIS EXISTS. Parsing used to make one live HTTP call per debate. That was
never a correctness problem; it was a cost problem, and the cost was measured:
the search endpoint's slow tail runs past 27 seconds (022). At 64,921 debates
that is the difference between a corpus-wide measurement we run this afternoon
and one we never run at all -- and "measurements we never run" is precisely how
this project keeps acquiring blind spots. See internal_docs/025_THE_OPEN_ITEMS.md
item 2.

FAILURES ARE LOUD HERE, unlike `db_roster.load_db_roster`, which swallows every
exception and returns []. That is right for the roster: it is an *optional*
last-resort tier, and a missing DB should leave the CLI working. It would be
wrong here. The corpus is the *primary* source, and a silent fallback would
turn one unnoticed connection error into 64,921 HTTP requests -- the exact
failure this module removes, restored quietly and at the worst moment. A caller
that genuinely wants "DB, else the wire" asks for it by name (`--source auto`),
which makes the fallback a decision someone wrote down rather than an accident.
"""
from __future__ import annotations

from typing import Any

# The details payload's own date format ("14/12/2024"), verified against a live
# call. `debate_date` is a real DATE in the table, so it has to be put back into
# the source's string form or every caller sees a different type depending on
# where the debate came from -- the sort of difference that shows up as a bug
# somewhere far away.
_API_DATE_FMT = "%d/%m/%Y"


def _row_to_payload(row: Any) -> dict:
    """Rebuild the details-API payload shape from one `debates` row.

    Only the five keys the parsers actually read are reconstructed. This is
    deliberately NOT a general-purpose round-trip of the API response -- the
    lossless-shred story lives in the importer and its tests
    (`tests/test_import_debates.py`), and duplicating it here would mean two
    places to keep honest.
    """
    return {
        "debateDesc": row.raw_html,
        # JSONB comes back already parsed, with mpCode still an int -- the same
        # type the API sends. Verified, and load-bearing: `resolve_speaker`
        # compares mpCodes for identity, so an int/str drift here would split
        # one person into two without anything raising.
        "mpPartDetailList": row.mp_list_raw or [],
        "debateDate": row.debate_date.strftime(_API_DATE_FMT) if row.debate_date else None,
        "debateType": row.debate_type,
        "contents": row.contents,
    }


def load_debate(loksabha: int, session: int, db_slno: int) -> dict | None:
    """Return one debate in details-API payload shape, or None if not stored.

    None means "this debate is not in the corpus", which is a real and expected
    answer -- it is how a caller decides to go to the wire. Connection and query
    failures are NOT None; they raise. See the module docstring.
    """
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
