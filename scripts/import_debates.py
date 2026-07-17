"""
Bulk-import every Lok Sabha debate's raw transcript into the `debates` table.

The corpus is ~64,911 debates across terms 13-18 (LS13: 7,616, LS14: 11,027,
LS15: 11,216, LS16: 15,831, LS17: 13,272, LS18: 5,949). At ~0.19s per fetch
that is ~3.4 hours sequential; with the default 6 workers, well under an hour.

WHY RAW ONLY. This script does not parse. It stores what the API returned and
stops. Parsing is a separate, re-runnable step, and freezing today's parser
output into the source-of-truth table would make every future parser fix a
refetch. See internal_docs/022_DEBATE_IMPORT.md.

TWO RESPONSES, ONE ROW. Neither API response is complete on its own: the search
record has the title/type/keywords but its `debateDesc` is always empty; the
details payload has the text but no title. We fetch both and shred them into
typed columns. The shred is lossless -- `rebuild_payload()` reconstructs the
details payload exactly, and a test pins that property.

IDEMPOTENT. Re-running is always safe and is the intended way to resume: rows
already present are skipped (unless --refetch), and every write is an upsert on
the natural key (loksabha, session, dbslno). A run that dies at debate 40,000
is resumed by running the exact same command again.

BE GENTLE. This is a public government API. The default of 6 workers is
deliberate and modest; --workers exists to turn it DOWN as much as up. Batches
are committed as they complete, so progress survives a Ctrl-C.

Run from the repo root:
    python -m scripts.import_debates                      # everything, 6 workers
    python -m scripts.import_debates --workers 2          # gentler
    python -m scripts.import_debates --loksabha 18        # one term
    python -m scripts.import_debates --limit 50 --dry-run # smoke test, no writes
    python -m scripts.import_debates --refetch            # re-fetch rows we already have
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime
from pathlib import Path

import requests
from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db import get_engine  # noqa: E402
from debate_fetch import fetch_debate  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sample_unverified import search_page  # noqa: E402

TERMS = (13, 14, 15, 16, 17, 18)
DEBATE_PAGE = "https://sansad.in/ls/debates/view-debate"

# A search page that takes longer than this is worth saying out loud. The search
# endpoint's latency is wildly uneven -- measured at 0.2s median with a tail past
# 27s on the same term, minutes apart -- so a slow page is normal, not an error.
# We log it anyway: a run with no output for ten minutes is indistinguishable
# from a hung one, and that ambiguity has cost this project several runs.
SLOW_PAGE_SECONDS = 5.0


def log(msg: str) -> None:
    """Timestamped, flushed. Both halves matter.

    Flushed because stdout redirected to a file is block-buffered, so an
    unflushed run writes *nothing* for its first several KB -- an empty log file
    reads exactly like a hang, and that is precisely how this importer has been
    misdiagnosed. Timestamped because "is it stuck?" is a question about elapsed
    time, and without a clock on each line there is no way to answer it.
    """
    print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)

# Keys we model explicitly. Anything else the API returns lands in `extra` rather
# than being dropped, so the shred stays lossless even if sansad adds a field.
PAYLOAD_KNOWN = {"contents", "debateDesc", "debateDate", "debateType", "mpPartDetailList"}
SEARCH_KNOWN = {
    "loksabha", "session", "dbSlno", "debateTitle", "contents", "memberName",
    "debateType", "debateTypeDesc", "debateDate", "debateDesc", "keywordUsed",
    "mpPartDetailList",
}


# --------------------------------------------------------------------------
# Pure functions. No network, no database -- this is the part the tests pin.
# --------------------------------------------------------------------------

def parse_sansad_date(value: str | None) -> date | None:
    """`"05/02/2004"` -> date(2004, 2, 5). Anything unparseable -> None.

    Deliberately total: one malformed date in 64,911 debates must not end a
    three-hour run. A None here is visible afterwards (`WHERE debate_date IS
    NULL`) and costs nothing, whereas a crash costs the whole import.
    """
    if not value:
        return None
    try:
        return datetime.strptime(value.strip(), "%d/%m/%Y").date()
    except (ValueError, AttributeError):
        return None


def unmodelled_keys(payload: dict, search_record: dict) -> dict:
    """Whatever the API sent that we did not model, namespaced by source.

    Expected to be empty -- key sets were stable across 90 sampled debates. But
    90 is 0.14% of the corpus, so this is the difference between an unexpected
    field being *discovered* (`WHERE extra <> '{}'`) and being silently lost.
    """
    extra = {f"payload.{k}": payload[k] for k in sorted(set(payload) - PAYLOAD_KNOWN)}
    extra.update({f"search.{k}": search_record[k] for k in sorted(set(search_record) - SEARCH_KNOWN)})
    return extra


def row_from_responses(loksabha: int, search_record: dict, payload: dict) -> dict:
    """Shred the two API responses into one `debates` row.

    THE TRAP THIS FUNCTION EXISTS TO CONTAIN: `debateType` names two different
    fields. In the *search record* it is an int (39); in the *details payload*
    it is the string ("PRIVATE MEMBERS' BILLS"), which equals the search
    record's `debateTypeDesc` (verified 36/36). Read the wrong one and
    `debate_type_code` is a meaningless string for 65,000 rows.

    Fields taken from the search record only: debateTitle, debateTypeDesc,
    debateType (the int), keywordUsed, memberName -- the payload has none of
    them. Fields taken from the payload only: debateDesc, contents -- the
    search record's copies of both are always empty. Fields present and
    identical in both (90/90), so taken once: debateDate, mpPartDetailList.
    """
    raw_html = payload.get("debateDesc") or ""
    session = int(search_record["session"])
    dbslno = int(search_record["dbSlno"])
    return {
        "loksabha": loksabha,
        "session": session,
        "dbslno": dbslno,
        "raw_html": raw_html,
        "mp_list_raw": json.dumps(payload.get("mpPartDetailList") or []),
        "title": search_record.get("debateTitle"),
        "debate_type": search_record.get("debateTypeDesc"),
        "debate_type_code": search_record.get("debateType"),
        "debate_date": parse_sansad_date(payload.get("debateDate") or search_record.get("debateDate")),
        "contents": payload.get("contents"),
        "keywords": list(search_record.get("keywordUsed") or []),
        "member_names": list(search_record.get("memberName") or []),
        "source_url": f"{DEBATE_PAGE}?ls={loksabha}&session={session}&dbslno={dbslno}",
        "raw_html_sha256": hashlib.sha256(raw_html.encode("utf-8")).hexdigest(),
        "extra": json.dumps(unmodelled_keys(payload, search_record)),
    }


def rebuild_payload(row: dict) -> dict:
    """Reconstruct the details payload from a stored row.

    Not used by the importer. It exists so a test can assert the shred is
    *lossless* against live data, which is the whole justification for storing
    typed columns instead of the raw JSON blob. If this ever stops round-
    tripping, the schema has started losing something.
    """
    mp_list = row["mp_list_raw"]
    if isinstance(mp_list, str):
        mp_list = json.loads(mp_list)
    d = row["debate_date"]
    return {
        "contents": row["contents"],
        "debateDesc": row["raw_html"],
        "debateDate": d.strftime("%d/%m/%Y") if isinstance(d, date) else d,
        "debateType": row["debate_type"],
        "mpPartDetailList": mp_list,
    }


# --------------------------------------------------------------------------
# I/O
# --------------------------------------------------------------------------

UPSERT = text("""
    INSERT INTO debates (
        loksabha, session, dbslno, raw_html, mp_list_raw, title, debate_type,
        debate_type_code, debate_date, contents, keywords, member_names,
        source_url, raw_html_sha256, extra
    ) VALUES (
        :loksabha, :session, :dbslno, :raw_html, :mp_list_raw, :title, :debate_type,
        :debate_type_code, :debate_date, :contents, :keywords, :member_names,
        :source_url, :raw_html_sha256, :extra
    )
    ON CONFLICT (loksabha, session, dbslno) DO UPDATE SET
        raw_html         = EXCLUDED.raw_html,
        mp_list_raw      = EXCLUDED.mp_list_raw,
        title            = EXCLUDED.title,
        debate_type      = EXCLUDED.debate_type,
        debate_type_code = EXCLUDED.debate_type_code,
        debate_date      = EXCLUDED.debate_date,
        contents         = EXCLUDED.contents,
        keywords         = EXCLUDED.keywords,
        member_names     = EXCLUDED.member_names,
        source_url       = EXCLUDED.source_url,
        raw_html_sha256  = EXCLUDED.raw_html_sha256,
        extra            = EXCLUDED.extra,
        fetched_at       = now()
""")


def enumerate_refs(loksabha: int) -> list[dict]:
    """Every search record for a term, walked page by page. Pages are 1-indexed
    (page 0 returns HTTP 500).

    Deduplicated on (session, dbSlno), and the dedup is load-bearing twice over.
    The search API really does serve the same debate twice: a full LS18 walk
    returns 5,949 records but only 5,899 distinct debates -- ~0.85%, all
    byte-identical, clustered on adjacent page pairs. That is offset pagination
    over a collection that is still growing (LS18 is the sitting term; its
    `totalElements` drifts between calls minutes apart). Closed terms do not do
    it: LS13 returns exactly its 7,616, no duplicates.

    Load-bearing twice because (1) it keeps the corpus count honest and (2) the
    batch upsert would otherwise fail outright -- Postgres rejects an
    ON CONFLICT DO UPDATE that touches the same row twice in one statement.

    THE RESIDUAL RISK, stated because dedup does NOT cover it: the same drift
    that duplicates a record could in principle *skip* one, and nothing here
    would notice. Two full LS18 walks minutes apart were compared key-by-key
    and agreed exactly (5,899 each, zero either way), so it is not happening at
    a rate we can see -- but "measured once, not found" is not "cannot happen".
    The mitigation is free: re-running the importer re-walks the search from
    scratch, so a second run picks up anything a first run never saw. See the
    reconciliation summary at the end of a run.

    The walk is the slowest, quietest part of a run -- ~113 pages for LS15 at a
    second-to-half-a-minute each, before a single debate is fetched. It reports
    per page for that reason.
    """
    meta = search_page_retrying(loksabha, 1).get("_metadata", {})
    total_pages = max(int(meta.get("totalPages", 1)), 1)
    log(f"LS{loksabha}: walking {total_pages} search pages")
    seen: dict[tuple[int, int], dict] = {}
    walk_started = time.time()
    for page in range(1, total_pages + 1):
        for rec in search_page_retrying(loksabha, page).get("records", []):
            seen.setdefault((int(rec["session"]), int(rec["dbSlno"])), rec)
        if page % 10 == 0 or page == total_pages:
            log(f"  LS{loksabha}: search page {page}/{total_pages}  "
                f"distinct={len(seen)}  {time.time() - walk_started:.0f}s elapsed")
    log(f"LS{loksabha}: search walk done, {len(seen)} distinct debates "
        f"in {(time.time() - walk_started) / 60:.1f} min")
    return list(seen.values())


def search_page_retrying(loksabha: int, page: int, retries: int = 5) -> dict:
    """One search page, retried with linear backoff.

    Without this, one timeout ends the run. That is not hypothetical: a full
    multi-hour walk died on a single ConnectTimeout at LS14 page 3 after
    importing 7,616 debates of LS13. The endpoint is not blocking us -- it is
    just erratic -- so a page that times out is very likely to succeed on the
    next ask, and giving up on the whole term is the wrong response to it.

    Raises only if every attempt fails: enumeration cannot proceed on a partial
    walk, and silently importing a term minus one page would be a data gap
    nobody would ever notice.
    """
    for attempt in range(1, retries + 1):
        started = time.time()
        try:
            payload = search_page(loksabha, page)
            elapsed = time.time() - started
            if elapsed > SLOW_PAGE_SECONDS:
                log(f"  LS{loksabha}: search page {page} was slow ({elapsed:.0f}s) "
                    f"-- the endpoint is erratic, not stuck")
            return payload
        except requests.RequestException as exc:
            log(f"  LS{loksabha}: search page {page} failed after {time.time() - started:.0f}s "
                f"(attempt {attempt}/{retries}): {type(exc).__name__}: {exc}")
            if attempt == retries:
                raise
            backoff = 5 * attempt
            log(f"  LS{loksabha}: retrying search page {page} in {backoff}s")
            time.sleep(backoff)
    raise RuntimeError("unreachable")


def fetch_one(loksabha: int, rec: dict, retries: int = 3) -> tuple[dict | None, str | None]:
    """Fetch one debate. Returns (row, error). Never raises.

    A single bad debate must not end a multi-hour run, so failures are returned
    and reported in a summary rather than propagated. Backoff is linear and
    deliberately unhurried -- if the API is struggling, hammering it is wrong.
    """
    session, dbslno = int(rec["session"]), int(rec["dbSlno"])
    for attempt in range(1, retries + 1):
        try:
            payload = fetch_debate(loksabha, session, dbslno)
            return row_from_responses(loksabha, rec, payload), None
        except requests.RequestException as exc:
            if attempt == retries:
                return None, f"LS{loksabha}/{session}/{dbslno}: {type(exc).__name__}: {exc}"
            time.sleep(2 * attempt)
        except (ValueError, KeyError, TypeError) as exc:
            return None, f"LS{loksabha}/{session}/{dbslno}: {type(exc).__name__}: {exc}"
    return None, f"LS{loksabha}/{session}/{dbslno}: exhausted retries"


def existing_keys(engine) -> set[tuple[int, int, int]]:
    """Every (loksabha, session, dbslno) already stored -- what resume skips."""
    with engine.connect() as conn:
        return {
            (int(r[0]), int(r[1]), int(r[2]))
            for r in conn.execute(text("SELECT loksabha, session, dbslno FROM debates"))
        }


def stored_count(engine, loksabha: int) -> int:
    """How many debates of a term are actually in the table."""
    with engine.connect() as conn:
        return int(conn.execute(
            text("SELECT count(*) FROM debates WHERE loksabha = :ls"), {"ls": loksabha},
        ).scalar_one())


def import_term(engine, loksabha: int, workers: int, batch_size: int,
                skip: set[tuple[int, int, int]], limit: int | None,
                dry_run: bool) -> tuple[int, list[str], int]:
    """Import one term. Returns (rows written, errors, debates enumerated)."""
    refs = enumerate_refs(loksabha)
    todo = [r for r in refs if (loksabha, int(r["session"]), int(r["dbSlno"])) not in skip]
    stored = len(refs) - len(todo)
    if limit is not None:
        todo = todo[:limit]
    log(f"LS{loksabha}: {len(refs)} debates, {stored} already stored, {len(todo)} to fetch")
    if not todo:
        return 0, [], len(refs)

    written, errors = 0, []
    for start in range(0, len(todo), batch_size):
        batch = todo[start:start + batch_size]
        with ThreadPoolExecutor(max_workers=workers) as pool:
            results = list(pool.map(lambda r: fetch_one(loksabha, r), batch))
        rows = [row for row, err in results if row is not None]
        errors.extend(err for _, err in results if err)
        if rows and not dry_run:
            # One transaction per batch: a killed run keeps everything committed
            # so far, and re-running resumes from there.
            with engine.begin() as conn:
                conn.execute(UPSERT, rows)
        written += len(rows)
        done = min(start + batch_size, len(todo))
        log(f"  LS{loksabha}: {done}/{len(todo)}  written={written}  errors={len(errors)}")
        # Errors are summarised at the end of a run, which is no help while one is
        # still going: a batch quietly failing every fetch looks the same as a batch
        # succeeding until the summary lands hours later. Say it as it happens.
        for err in (e for _, e in results if e):
            log(f"    error: {err}")
    return written, errors, len(refs)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Bulk-import raw Lok Sabha debate transcripts into the debates table.",
    )
    parser.add_argument("--workers", type=int, default=6,
                        help="parallel fetches (default 6). Lower it to be gentler on the API.")
    parser.add_argument("--loksabha", type=int, choices=TERMS, action="append",
                        help="limit to a term; repeatable. Default: all of 13-18.")
    parser.add_argument("--limit", type=int, help="cap debates fetched per term (smoke test)")
    parser.add_argument("--batch-size", type=int, default=200,
                        help="debates per commit (default 200)")
    parser.add_argument("--refetch", action="store_true",
                        help="re-fetch debates already stored (default: skip them)")
    parser.add_argument("--dry-run", action="store_true", help="fetch but do not write")
    args = parser.parse_args()

    if args.workers < 1:
        parser.error("--workers must be >= 1")

    engine = get_engine()
    terms = tuple(sorted(set(args.loksabha))) if args.loksabha else TERMS
    skip = set() if args.refetch else existing_keys(engine)
    log(f"terms={list(terms)} workers={args.workers} already stored={len(skip)}"
        f"{' DRY RUN' if args.dry_run else ''}")

    started = time.time()
    total, all_errors, enumerated = 0, [], {}
    for ls in terms:
        written, errors, found = import_term(engine, ls, args.workers, args.batch_size,
                                             skip, args.limit, args.dry_run)
        total += written
        all_errors.extend(errors)
        enumerated[ls] = found

    mins = (time.time() - started) / 60
    print(f"\ndone: {total} rows in {mins:.1f} min, {len(all_errors)} errors")
    for err in all_errors[:20]:
        print(f"  {err}")
    if len(all_errors) > 20:
        print(f"  ... and {len(all_errors) - 20} more")

    # Reconciliation. The search API is paginated over a collection that can shift
    # mid-walk (see enumerate_refs), so "we fetched everything we saw" is not the
    # same as "we saw everything". This compares what the walk enumerated against
    # what is actually in the table, and says so out loud rather than letting a
    # gap pass as success. A gap is not necessarily loss -- with --limit it is
    # expected -- but it should never be discovered later by accident.
    if not args.dry_run and args.limit is None:
        print("\nreconciliation (enumerated by the search walk vs stored in the table):")
        for ls in terms:
            have = stored_count(engine, ls)
            gap = enumerated[ls] - have
            flag = "OK" if gap == 0 else f"GAP {gap}"
            print(f"  LS{ls}: enumerated={enumerated[ls]:>6}  stored={have:>6}  {flag}")
        print("  a gap means those debates errored, or the walk never saw them;")
        print("  re-run to close it -- the search is re-walked from scratch each run.")

    if all_errors:
        # Re-running is the fix: successful rows are skipped, failures retried.
        print("\nre-run the same command to retry failures (stored rows are skipped)")


if __name__ == "__main__":
    main()
