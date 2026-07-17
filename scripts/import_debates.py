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

# Log a search page slower than this. The endpoint latency is very uneven.
SLOW_PAGE_SECONDS = 5.0


def log(msg: str) -> None:
    # Flush so that output redirected to a file shows progress.
    print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)

# Keys we model explicitly. Anything else the API returns lands in `extra` rather
# than being dropped, so the shred stays lossless even if sansad adds a field.
PAYLOAD_KNOWN = {"contents", "debateDesc", "debateDate", "debateType", "mpPartDetailList"}
SEARCH_KNOWN = {
    "loksabha", "session", "dbSlno", "debateTitle", "contents", "memberName",
    "debateType", "debateTypeDesc", "debateDate", "debateDesc", "keywordUsed",
    "mpPartDetailList",
}


def parse_sansad_date(value: str | None) -> date | None:
    """Parse "05/02/2004" (day first). Return None for a missing or malformed date."""
    if not value:
        return None
    try:
        return datetime.strptime(value.strip(), "%d/%m/%Y").date()
    except (ValueError, AttributeError):
        return None


def unmodelled_keys(payload: dict, search_record: dict) -> dict:
    extra = {f"payload.{k}": payload[k] for k in sorted(set(payload) - PAYLOAD_KNOWN)}
    extra.update({f"search.{k}": search_record[k] for k in sorted(set(search_record) - SEARCH_KNOWN)})
    return extra


def row_from_responses(loksabha: int, search_record: dict, payload: dict) -> dict:
    # `debateType` is an int in the search record and a string in the details payload.
    # Use the search record for debate_type_code.
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
    # Pages start at 1: page 0 returns HTTP 500.
    # The search API can return the same debate twice. Deduplicate, or the batch upsert fails.
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
    # Raise only when every attempt fails: a partial walk would hide a gap.
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
    """Return (row, error). Never raises."""
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
    with engine.connect() as conn:
        return {
            (int(r[0]), int(r[1]), int(r[2]))
            for r in conn.execute(text("SELECT loksabha, session, dbslno FROM debates"))
        }


def stored_count(engine, loksabha: int) -> int:
    with engine.connect() as conn:
        return int(conn.execute(
            text("SELECT count(*) FROM debates WHERE loksabha = :ls"), {"ls": loksabha},
        ).scalar_one())


def import_term(engine, loksabha: int, workers: int, batch_size: int,
                skip: set[tuple[int, int, int]], limit: int | None,
                dry_run: bool) -> tuple[int, list[str], int]:
    """Import one term. Return (rows written, errors, debates enumerated)."""
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
            # One transaction per batch, so a killed run keeps the committed batches.
            with engine.begin() as conn:
                conn.execute(UPSERT, rows)
        written += len(rows)
        done = min(start + batch_size, len(todo))
        log(f"  LS{loksabha}: {done}/{len(todo)}  written={written}  errors={len(errors)}")
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

    # The search walk can miss debates, so compare the enumerated count with the stored count.
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
        print("\nre-run the same command to retry failures (stored rows are skipped)")


if __name__ == "__main__":
    main()
