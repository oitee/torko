"""
Populate the `turns` table from every debate already in `debates.raw_html`.

Read-only against `debates`. Writes `turns`, and DELETES `speeches` for every
debate it touches (see below). Idempotent per debate: delete-then-insert in one
transaction -- NOT an upsert, despite what this docstring said for a long time;
there is no ON CONFLICT clause anywhere in here. Re-running the whole script is
how a crashed run is resumed.

**Running this invalidates `speeches`.** A speech is a span over turns, and this
script replaces the turns. Leaving the old speech rows behind is what let 598
speeches end up naming a different human being than their own first turn, while
the integrity check -- which joined on the `speech_id` this script had just
NULLed -- happily reported "exact" over an empty set. So the speeches for each
re-parsed debate are deleted here, deliberately: poison becomes loss, and loss
is the trade this project always takes. Re-run scripts/populate_speeches.py
afterwards, then `--verify` it.

Run: source .venv/bin/activate && python3 -u scripts/populate_turns.py [--limit N]
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from alias_build import is_synthetic_code
from db import get_engine
from debate_fetch import (
    _folded_key,
    is_crowd_label,
    is_presiding_label,
    split_by_speaker,
)
from debate_fetch_legacy import looks_legacy, split_by_speaker_legacy
from db_roster import load_db_roster
from label_attribution import build_unique_index, resolve_label_to_person


def person_id_lookup(engine) -> dict[str, int]:
    """mpCode (string) -> persons.id."""
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT sansad_id, id FROM persons WHERE sansad_id IS NOT NULL")
        ).fetchall()
    return {str(r.sansad_id): r.id for r in rows}


def alias_lookup(engine) -> dict[str, int]:
    """mpCode (string) -> persons.id, via the mpcode_aliases bridge table.

    The debate anchor code is not always the person's mpsno (see internal_docs
    033); this maps the ones the source's own labels pinned to a single person.
    Empty when the table has not been built yet -- a plain no-op, so this script
    still runs on a fresh DB before scripts/populate_mpcode_aliases.py.
    """
    try:
        with engine.connect() as conn:
            rows = conn.execute(
                text("SELECT mp_code, person_id FROM mpcode_aliases")
            ).fetchall()
        return {str(r.mp_code): r.person_id for r in rows}
    except Exception:
        return {}


def role_id_lookup(engine) -> dict[str, tuple[int, str]]:
    """roleCode -> (speaker_roles.id, kind)."""
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT id, code, kind FROM speaker_roles")).fetchall()
    return {r.code: (r.id, r.kind) for r in rows}


def parse_debate(raw_html: str, mp_list_raw: list[dict], db_roster: list[dict]) -> list[dict]:
    """Mirrors scripts/build_dashboard_fixtures.py's routing exactly: both
    readers already run annotate_speakers/reuse_anchors internally, so segments
    come back fully resolved -- do not re-run either pass over them."""
    if looks_legacy(raw_html):
        return split_by_speaker_legacy(raw_html, mp_list_raw, db_roster)
    return split_by_speaker(raw_html, mp_list_raw, db_roster)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None, help="cap debates processed, for a dry run")
    args = ap.parse_args()

    engine = get_engine()
    roster_cache: dict[int, list] = {}
    persons = person_id_lookup(engine)
    aliases = alias_lookup(engine)
    roles = role_id_lookup(engine)
    with engine.connect() as conn:
        roster_index = build_unique_index(
            {pid: name for pid, name in conn.execute(text("SELECT id, name FROM persons"))},
            _folded_key,
        )

    # IDs first, bodies one at a time. The previous version selected `raw_html`
    # for every debate and called .fetchall(), pulling the entire 539 MB corpus
    # into RAM before debate #1 was parsed -- the peak was at startup, before any
    # progress had printed. Fetching each body by primary key inside the loop
    # costs one indexed round-trip per debate (the loop already does several
    # writes per debate) and holds one debate in memory at a time. Same rows,
    # same order, so the output is unchanged.
    with engine.connect() as conn:
        query = "SELECT id FROM debates ORDER BY id"
        if args.limit:
            query += f" LIMIT {int(args.limit)}"
        debate_ids = [r[0] for r in conn.execute(text(query)).fetchall()]

    print(f"{len(debate_ids)} debates to process", flush=True)

    total_turns = 0
    for n, debate_id in enumerate(debate_ids, 1):
        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT id, loksabha, raw_html, mp_list_raw FROM debates WHERE id = :i"),
                {"i": debate_id},
            ).one()

        if row.loksabha not in roster_cache:
            roster_cache[row.loksabha] = load_db_roster(row.loksabha)
        db_roster = roster_cache[row.loksabha]

        segments = parse_debate(row.raw_html, row.mp_list_raw, db_roster)

        values = []
        for seq, seg in enumerate(segments):
            role_id, role_kind = (None, None)
            if seg.get("roleCode") in roles:
                role_id, role_kind = roles[seg["roleCode"]]

            mp_code = seg.get("mpCode")
            person_id = persons.get(mp_code) if mp_code else None
            name_source = seg.get("nameSource")
            # The anchor code was not this person's mpsno, but the source's own
            # labels pinned it: adopt the alias, unless this turn is itself a
            # role turn (role_id set) or its label is presiding/crowd -- those
            # must never inherit the code's person. See internal_docs 033.
            if person_id is None and role_id is None and mp_code in aliases:
                label = seg.get("speakerLabel") or ""
                if not is_presiding_label(label) and not is_crowd_label(label):
                    person_id = aliases[mp_code]
                    name_source = "mpcode-alias"
            # Ministerial turns: a synthetic role-slot code (>=10000) names no one
            # person, so attribute by the turn's OWN label instead. See 033.
            if person_id is None and role_id is None and mp_code and is_synthetic_code(mp_code):
                pid = resolve_label_to_person(
                    seg.get("speakerLabel"), roster_index, _folded_key,
                    is_presiding_label, is_crowd_label,
                )
                if pid is not None:
                    person_id = pid
                    name_source = "minister-name"
            values.append({
                "debate_id": row.id,
                "seq": seq,
                "speaker_label": seg.get("speakerLabel"),
                "mp_code": mp_code,
                "person_id": person_id,
                "role_id": role_id,
                "role_kind": role_kind,
                "name_source": name_source,
                "text": seg["text"],
                "word_count": len(seg["text"].split()),
                "char_count": len(seg["text"]),
            })

        # The DELETE is UNCONDITIONAL -- outside `if values:` -- because a debate
        # that now parses to zero segments must lose its old rows too. Guarding
        # the delete behind `if values` was harmless into an empty table and
        # wrong on every re-run after a parser change: a rule that legitimately
        # stops emitting a turn (e.g. the heading-line blocklist) would leave the
        # old turn sitting there forever, invisible, indistinguishable from a
        # real one.
        with engine.begin() as conn:
            # Speeches are a grouping OVER turns and are invalidated by this
            # delete: the new turn rows come back with speech_id = NULL, so any
            # surviving speech row would describe turns that no longer exist and
            # would keep asserting an owner that this re-parse may have changed.
            # Dropping them converts poison (a speech naming the wrong human)
            # into loss (no speech at all), which is the trade this project
            # always takes. Re-run scripts/populate_speeches.py afterwards.
            conn.execute(
                text("UPDATE turns SET speech_id = NULL WHERE debate_id = :debate_id"),
                {"debate_id": row.id},
            )
            conn.execute(
                text("DELETE FROM speeches WHERE debate_id = :debate_id"),
                {"debate_id": row.id},
            )
            conn.execute(
                text("DELETE FROM turns WHERE debate_id = :debate_id"),
                {"debate_id": row.id},
            )
            if values:
                conn.execute(
                    text(
                        """
                        INSERT INTO turns
                            (debate_id, seq, speaker_label, mp_code, person_id,
                             role_id, role_kind, name_source, text, word_count, char_count)
                        VALUES
                            (:debate_id, :seq, :speaker_label, :mp_code, :person_id,
                             :role_id, :role_kind, :name_source, :text, :word_count, :char_count)
                        """
                    ),
                    values,
                )
                total_turns += len(values)

        if n % 500 == 0:
            print(f"  {n}/{len(debate_ids)} debates, {total_turns} turns so far", flush=True)

    print(f"done: {len(debate_ids)} debates, {total_turns} turns", flush=True)
    print(
        "\nSPEECHES ARE NOW EMPTY FOR EVERY DEBATE TOUCHED ABOVE. This is deliberate --\n"
        "a speech is a grouping over turns and cannot survive the turns being replaced.\n"
        "Re-run:  python3 -u scripts/populate_speeches.py\n"
        "Then:    python3 -u scripts/populate_speeches.py --verify   (must exit 0)",
        flush=True,
    )


if __name__ == "__main__":
    main()
