"""Build the mpcode_aliases table from the corpus, then backfill turns.

Reads turns + persons, decides which orphan mpCodes alias to a single person
(alias_build.build_aliases -- pure, tested offline), writes mpcode_aliases, and
sets person_id / name_source='mpcode-alias' on the turns that safely resolve.

Never-guess, restated as code:
  * only codes whose printed name labels unanimously fold to ONE roster person
    get a row (conflicts dropped by build_aliases);
  * that single person's identity is then checked against the code's own
    DOMINANT printed label (most turns, over every label ever printed for the
    code -- not just the ones that resolved) via debate_fetch._name_agreement.
    A label that positively disagrees, or that yields no usable name evidence
    at all, refuses the row -- see internal_docs/036_THE_AUDIT_AND_FIX_LIST.md
    T2 for the bug this closes (a single stray vote, unopposed only because
    hundreds of contrary labels never resolved to anyone, used to mint);
  * the synthetic minister block (>=10000) is excluded (build_aliases);
  * backfill touches only turns with NO person and NO role, and skips any turn
    whose stored label is itself presiding/crowd (belt-and-suspenders: such a
    turn must stay a role/unresolved, never inherit the code's person).

CIRCULARITY (not fixed here, see T2 fix direction #3): this script's own
input is `turns`, which a PRIOR run of this same script already wrote
person_id into. Re-running against a DB that has already been backfilled once
starves the vote: turns that resolved via a previous alias are no longer
"orphan" and never re-enter the count. Candidates should eventually come from
a fresh parse of `raw_html`, not from the already-backfilled table.

Idempotent: DELETEs and rebuilds mpcode_aliases each run; the backfill is a
plain UPDATE guarded by person_id IS NULL so re-running never overwrites a
directly-resolved turn.

Run: source .venv/bin/activate && python3 scripts/populate_mpcode_aliases.py [--dry-run]
"""
import argparse
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from alias_build import build_aliases
from db import get_engine
from debate_fetch import _folded_key, _name_agreement, is_crowd_label, is_presiding_label


def unique_person_by_key(conn) -> dict[str, int]:
    """Folded roster-name key -> person id, colliding keys dropped (never-guess)."""
    key2pids: dict[str, set] = defaultdict(set)
    for pid, name in conn.execute(text("SELECT id, name FROM persons")):
        k = _folded_key(name)
        if k:
            key2pids[k].add(pid)
    return {k: next(iter(v)) for k, v in key2pids.items() if len(v) == 1}


def person_name_by_id(conn) -> dict[int, str]:
    """Person id -> roster name, for the dominant-label agreement gate."""
    return {pid: name for pid, name in conn.execute(text("SELECT id, name FROM persons"))}


def audit_stored_rows(engine, purge: bool = False) -> int:
    """Check every STORED alias row against the gate. Returns an exit code.

    Why this is separate from a rebuild: the build consumes its own evidence.
    `build_aliases` is fed from turns that are still unattributed, and the
    previous run then WROTE person_id onto exactly those turns -- so rebuilding
    against today's database starves the vote and reproduces almost none of the
    29 stored rows. Until that circularity is broken (T2 fix direction #3, not
    done), a rebuild would DESTROY 25 good rows to re-derive 1. So the stored
    table is audited in place instead: each row is re-judged against the labels
    the corpus still holds for its code, and only rows the gate positively
    refuses are removed.

    Refusing a row means the turns it attributed go back to unattributed:
    poison becomes loss, which is the trade this project always takes.
    """
    with engine.connect() as conn:
        stored = {r.mp_code: r.person_id for r in
                  conn.execute(text("SELECT mp_code, person_id FROM mpcode_aliases"))}
        if not stored:
            print("mpcode_aliases is EMPTY -- nothing audited, which proves nothing.")
            return 1
        names = person_name_by_id(conn)
        rows = conn.execute(
            text("""SELECT mp_code, speaker_label, count(*) AS n FROM turns
                    WHERE mp_code = ANY(:codes) AND speaker_label IS NOT NULL
                      AND speaker_label <> ''
                    GROUP BY mp_code, speaker_label"""),
            {"codes": list(stored)},
        ).fetchall()

    by_code: dict[str, dict[str, int]] = {}
    for r in rows:
        by_code.setdefault(str(r.mp_code), {})[r.speaker_label] = r.n

    failing: list[tuple[str, int, str]] = []
    for code, pid in sorted(stored.items(), key=lambda kv: int(kv[0])):
        roster_name = names.get(pid)
        labels = {l: n for l, n in by_code.get(code, {}).items()
                  if not is_presiding_label(l) and not is_crowd_label(l)}
        if not roster_name or not labels:
            failing.append((code, pid, "no printed name label to check against"))
            continue
        dominant, dom_n = max(labels.items(), key=lambda kv: kv[1])
        supporting = sum(n for l, n in labels.items()
                         if _folded_key(l) == _folded_key(roster_name))
        refuting = max((n for l, n in labels.items()
                        if _name_agreement(l, roster_name) is False), default=0)
        if _name_agreement(dominant, roster_name) is True or supporting >= refuting:
            continue
        failing.append((
            code, pid,
            f"dominant label {dominant[:44]!r} ({dom_n} turns) refutes "
            f"{roster_name!r}; support={supporting} vs refuting={refuting}",
        ))

    print(f"audited {len(stored)} stored alias rows over the whole corpus")
    print(f"  pass: {len(stored) - len(failing)}   FAIL: {len(failing)}")
    for code, pid, why in failing:
        print(f"  FAIL {code:>6}  person {pid} ({names.get(pid)})\n         {why}")

    if not failing:
        print("\nOK: every stored alias row survives its own code's printed labels.")
        return 0
    if not purge:
        print("\nRe-run with --purge to delete these rows and unattribute their turns.")
        return 1

    codes = [c for c, _, _ in failing]
    with engine.begin() as conn:
        cleared = conn.execute(
            text("""UPDATE turns SET person_id = NULL, name_source = 'unresolved'
                    WHERE name_source = 'mpcode-alias' AND mp_code = ANY(:c)"""),
            {"c": codes},
        ).rowcount
        conn.execute(text("DELETE FROM mpcode_aliases WHERE mp_code = ANY(:c)"), {"c": codes})
    print(f"\npurged {len(codes)} alias rows; {cleared} turns returned to unattributed.")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="report, write nothing")
    ap.add_argument("--audit", action="store_true",
                    help="re-judge the STORED rows against the gate; exit non-zero on failure")
    ap.add_argument("--purge", action="store_true",
                    help="with --audit: delete failing rows and unattribute their turns")
    args = ap.parse_args()

    engine = get_engine()

    if args.audit:
        sys.exit(audit_stored_rows(engine, purge=args.purge))
    with engine.connect() as conn:
        upk = unique_person_by_key(conn)
        pnbi = person_name_by_id(conn)

        # Candidate codes: those carrying at least one currently-orphan turn
        # (no person, no role). Once we know WHICH codes are orphans, pull
        # EVERY label ever printed for those codes -- not just the orphan
        # rows -- because the dominant-label gate needs the full picture,
        # including labels that already resolved some other way.
        orphan_codes = conn.execute(
            text(
                """
                SELECT DISTINCT mp_code FROM turns
                WHERE person_id IS NULL AND role_id IS NULL
                  AND mp_code IS NOT NULL AND speaker_label <> ''
                """
            )
        ).scalars().all()

        label_rows = conn.execute(
            text(
                """
                SELECT mp_code, speaker_label, count(*) AS n
                FROM turns
                WHERE mp_code = ANY(:codes) AND speaker_label <> ''
                GROUP BY mp_code, speaker_label
                """
            ),
            {"codes": orphan_codes},
        ).fetchall()

    aliases, dropped = build_aliases(
        ((r.mp_code, r.speaker_label, r.n) for r in label_rows),
        upk,
        pnbi,
        _folded_key,
        is_presiding_label,
        is_crowd_label,
        _name_agreement,
    )
    print(f"aliasable codes: {len(aliases)}   dropped: {len(dropped)}")
    for code, info in dropped.items():
        print(f"  DROP {code}: {info}")

    if args.dry_run:
        print("dry run -- nothing written")
        for code, info in sorted(aliases.items(), key=lambda x: -x[1]["evidence_turns"]):
            print(f"  {code:>7} -> person {info['person_id']} ({info['evidence_turns']} name-turns)")
        return

    backfilled = 0
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM mpcode_aliases"))
        for code, info in aliases.items():
            conn.execute(
                text(
                    """INSERT INTO mpcode_aliases (mp_code, person_id, evidence_turns)
                       VALUES (:c, :p, :e)"""
                ),
                {"c": code, "p": info["person_id"], "e": info["evidence_turns"]},
            )
            # Backfill: only unresolved, non-role turns of this code, and skip any
            # turn whose own label is presiding/crowd (checked in Python -- SQL
            # cannot call is_presiding_label).
            cand = conn.execute(
                text(
                    """SELECT id, speaker_label FROM turns
                       WHERE mp_code = :c AND person_id IS NULL AND role_id IS NULL"""
                ),
                {"c": code},
            ).fetchall()
            ids = [
                r.id
                for r in cand
                if not is_presiding_label(r.speaker_label or "")
                and not is_crowd_label(r.speaker_label or "")
            ]
            if ids:
                conn.execute(
                    text(
                        """UPDATE turns SET person_id = :p, name_source = 'mpcode-alias'
                           WHERE id = ANY(:ids)"""
                    ),
                    {"p": info["person_id"], "ids": ids},
                )
                backfilled += len(ids)

    print(f"wrote {len(aliases)} alias rows; backfilled {backfilled} turns")


if __name__ == "__main__":
    main()
