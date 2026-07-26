"""
Populate the `speeches` table by stitching the `turns` already in the DB.

No reparse: turns already carry person_id / role_kind / word_count, so speeches
are a pure grouping over them (see speech_stitch.py). Read-only against the
parser; writes `speeches` and back-fills `turns.speech_id`.

Idempotent per debate: delete this debate's speeches (which NULLs turns.speech_id
via ON DELETE... actually we NULL them explicitly first), then re-insert. Safe to
re-run after a rule change.

Monitor from the DB, never the log (block-buffered stdout has faked a hang twice
here): SELECT count(*) FROM speeches;  -- prints use flush=True regardless.

Run: source .venv/bin/activate && python3 -u scripts/populate_speeches.py [--limit N]
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from db import get_engine
from speech_stitch import check_integrity, stitch_turns


def verify(engine) -> int:
    """Corpus-wide integrity check. Returns a process exit code (0 == healthy).

    Every number below is counted over the WHOLE table, not a sample, and the
    emptiness cases are checked first -- see speech_stitch.check_integrity for
    why that ordering is the whole point of this function existing.
    """
    with engine.connect() as conn:
        speech_count, speech_turn_total, speech_word_total = conn.execute(
            text(
                "SELECT count(*), coalesce(sum(turn_count),0), coalesce(sum(word_count),0) "
                "FROM speeches"
            )
        ).one()
        linked_turn_count, linked_turn_words = conn.execute(
            text(
                "SELECT count(*), coalesce(sum(word_count),0) FROM turns "
                "WHERE speech_id IS NOT NULL"
            )
        ).one()
        owner_disagreements = conn.execute(
            text(
                """SELECT count(*) FROM speeches s
                   JOIN turns t ON t.debate_id = s.debate_id AND t.seq = s.seq_start
                   WHERE s.person_id IS DISTINCT FROM t.person_id"""
            )
        ).scalar()

    print(f"  speeches                  {speech_count:>12,}", flush=True)
    print(f"  sum(speeches.turn_count)  {speech_turn_total:>12,}", flush=True)
    print(f"  turns carrying speech_id  {linked_turn_count:>12,}", flush=True)
    print(f"  sum(speeches.word_count)  {speech_word_total:>12,}", flush=True)
    print(f"  words in linked turns     {linked_turn_words:>12,}", flush=True)
    print(f"  owner disagreements       {owner_disagreements:>12,}", flush=True)

    failures = check_integrity(
        speech_count=speech_count,
        speech_turn_total=speech_turn_total,
        speech_word_total=speech_word_total,
        linked_turn_count=linked_turn_count,
        linked_turn_words=linked_turn_words,
        owner_disagreements=owner_disagreements,
    )
    if not failures:
        print("\nOK: speeches agree with turns, over a non-empty set.", flush=True)
        return 0
    print("\nFAILED:", flush=True)
    for f in failures:
        print(f"  - {f}", flush=True)
    return 1


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None, help="cap debates, for a dry run")
    ap.add_argument(
        "--verify",
        action="store_true",
        help="check speeches against turns and exit non-zero on drift; write nothing",
    )
    args = ap.parse_args()

    engine = get_engine()

    if args.verify:
        sys.exit(verify(engine))

    with engine.connect() as conn:
        q = "SELECT DISTINCT debate_id FROM turns ORDER BY debate_id"
        if args.limit:
            q += f" LIMIT {int(args.limit)}"
        debate_ids = [r[0] for r in conn.execute(text(q)).fetchall()]

    print(f"{len(debate_ids)} debates to stitch", flush=True)

    total_speeches = 0
    for n, did in enumerate(debate_ids, 1):
        with engine.connect() as conn:
            rows = conn.execute(
                text(
                    """SELECT id, seq, person_id, role_kind, word_count, char_count
                       FROM turns WHERE debate_id = :d ORDER BY seq"""
                ),
                {"d": did},
            ).fetchall()

        by_seq = {r.seq: r.id for r in rows}
        turns = [
            {
                "seq": r.seq,
                "person_id": r.person_id,
                "role_kind": r.role_kind,
                "word_count": r.word_count,
                "char_count": r.char_count,
            }
            for r in rows
        ]
        speeches = stitch_turns(turns)

        with engine.begin() as conn:
            # Idempotent: drop this debate's prior speeches and unlink its turns.
            conn.execute(
                text("UPDATE turns SET speech_id = NULL WHERE debate_id = :d"), {"d": did}
            )
            conn.execute(
                text("DELETE FROM speeches WHERE debate_id = :d"), {"d": did}
            )
            for sp in speeches:
                speech_id = conn.execute(
                    text(
                        """INSERT INTO speeches
                             (debate_id, person_id, seq_start, seq_end, turn_count,
                              interruption_count, word_count, char_count)
                           VALUES
                             (:debate_id, :person_id, :seq_start, :seq_end, :turn_count,
                              :interruption_count, :word_count, :char_count)
                           RETURNING id"""
                    ),
                    {"debate_id": did, **{k: sp[k] for k in (
                        "person_id", "seq_start", "seq_end", "turn_count",
                        "interruption_count", "word_count", "char_count")}},
                ).scalar()
                turn_ids = [by_seq[s] for s in sp["turn_seqs"]]
                conn.execute(
                    text("UPDATE turns SET speech_id = :sid WHERE id = ANY(:ids)"),
                    {"sid": speech_id, "ids": turn_ids},
                )
            total_speeches += len(speeches)

        if n % 500 == 0:
            print(f"  {n}/{len(debate_ids)} debates, {total_speeches} speeches", flush=True)

    print(f"done: {len(debate_ids)} debates, {total_speeches} speeches", flush=True)


if __name__ == "__main__":
    main()
