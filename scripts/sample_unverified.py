"""
Sample UNVERIFIED speakers from real debates.

An "unverified" speaker is a parsed intervention that has a speaker *label* but no
`mpCode` -- i.e. the parser found someone speaking but could not tie them to a
member-list entry. Examples fall into three categories:
  * Hindi-script names (label is Devanagari),
  * speakers present in the transcript text but absent from the debate's
    mpPartDetailList (no anchor to match against),
  * presiding officers (Mr. Speaker / Chairman / etc.).

Sampling is stratified by era so the legacy corpus is not drowned out by the
better-anchored modern debates:
    legacy  = LS 13-14   (legacy-font / partCode-less anchors)
    modern  = LS 15-18

Random debates are drawn, alternating strata, until TARGET (100) unverified
examples are gathered, then written to a fresh, self-contained run file: a
markdown rollup plus a JSONL file beside it.

Each run writes its own immutable, timestamped pair of files (migration-file
style) — runs are never appended to or overwritten. Legacy CDAC-font names are
decoded to Unicode Hindi, each row links to its source debate, and debates that
parsed but had no unverified speakers are tabled separately as a false-positive
check.

Run from the repo root:
    python -m scripts.sample_unverified                       # 100 examples (default)
    python -m scripts.sample_unverified --target 50
    python -m scripts.sample_unverified --out reports/today.md    # explicit path
    python -m scripts.sample_unverified --replay-file <prior_run.md>  # re-parse a run
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

import requests

import debate_fetch
import debate_fetch_legacy
import legacy_hindi

SEARCH_API = "https://sansad.in/api_ls/debate/debate-search"
# Human-facing debate page, e.g.
#   https://sansad.in/ls/debates/view-debate?ls=18&session=3&dbslno=1700
DEBATE_PAGE = "https://sansad.in/ls/debates/view-debate"

STRATA = {"legacy": [13, 14], "modern": [15, 16, 17, 18]}

DEVANAGARI_RE = re.compile(r"[ऀ-ॿ]")
PRESIDING_RE = re.compile(
    r"speaker|chairman|chairperson|chair\b|deputy|panel|adhyaksh|sabhapati"
    r"|hon.{0,3}member|presiding",
    re.IGNORECASE,
)

DEFAULT_OUT_DIR = Path("internal_docs")

# polite scraping: undocumented API, so pace requests and back off on errors.
REQUEST_DELAY_S = 0.6


def classify(label: str) -> str:
    """Bucket an unverified label so the rollup separates the real problems.

    Expects a *decoded* (Unicode) label: legacy-font names must be run through
    `legacy_hindi.decode_legacy_hindi` first, otherwise their Devanagari would be
    hidden behind CDAC glyphs and they'd be misfiled as `in_text_no_anchor`.
    """
    if DEVANAGARI_RE.search(label):
        return "hindi_name"
    if PRESIDING_RE.search(label):
        return "presiding_officer"
    return "in_text_no_anchor"


def default_out_path(now: datetime | None = None) -> Path:
    """A fresh timestamped rollup path for a run, migration-file style.

    Each run gets its own immutable file (e.g. 20260715_143005_unverified_run.md)
    so runs never collide or overwrite; pass --out to target a specific file.
    """
    now = now or datetime.now()
    return DEFAULT_OUT_DIR / f"{now:%Y%m%d_%H%M%S}_unverified_run.md"


def debate_url(ls: int, session: int, db_slno: int) -> str:
    """Human-facing debate page URL, so a row can be verified against the source."""
    return f"{DEBATE_PAGE}?ls={ls}&session={session}&dbslno={db_slno}"


def search_page(loksabha: int, page: int, size: int = 100) -> dict:
    resp = requests.get(
        SEARCH_API,
        params={"loksabha": loksabha, "page": page, "size": size},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()


def random_debate_refs(loksabha: int, k: int) -> list[dict]:
    """Return up to k random debate refs (session + dbSlno) for a Lok Sabha."""
    meta = search_page(loksabha, 1).get("_metadata", {})
    total_pages = max(int(meta.get("totalPages", 1)), 1)
    page = random.randint(1, total_pages)
    records = search_page(loksabha, page).get("records", [])
    random.shuffle(records)
    return records[:k]


def parse_segments(payload: dict) -> list[dict]:
    """Run the era-appropriate parser and return its speaker segments."""
    html = payload.get("debateDesc") or ""
    mp_list = payload.get("mpPartDetailList", []) or []
    if not html:
        return []
    if debate_fetch_legacy.looks_legacy(html):
        return debate_fetch_legacy.split_by_speaker_legacy(html, mp_list)
    return debate_fetch.split_by_speaker(html, mp_list)


def unverified_from_debate(ref: dict, era: str) -> tuple[list[dict], int]:
    """Fetch+parse one debate.

    Returns (distinct unverified-speaker examples, number of parsed segments).
    The segment count lets the caller tell a genuinely clean debate (parsed fine,
    every speaker resolved) apart from one the parser simply couldn't read.
    """
    ls, session, db_slno = ref["loksabha"], ref["session"], ref["dbSlno"]
    payload = debate_fetch.fetch_debate(ls, session, db_slno)
    segments = parse_segments(payload)

    seen: set[str] = set()
    examples: list[dict] = []
    for seg in segments:
        label = seg.get("speakerLabel")
        if seg.get("mpCode") or not label or label in seen:
            continue
        seen.add(label)
        # Decode legacy CDAC-font names to Unicode Hindi so the label is readable
        # and classifies correctly; already-clean labels pass through untouched.
        display = legacy_hindi.decode_legacy_hindi(label)
        examples.append(
            {
                "loksabha": ls,
                "session": session,
                "dbSlno": db_slno,
                "era": era,
                "debate_type": ref.get("debateTypeDesc") or ref.get("debateType"),
                "debate_date": ref.get("debateDate"),
                "speaker_raw": label,
                "speaker": display,
                "name_source": seg.get("nameSource"),
                "category": classify(display),
                "text_excerpt": (seg.get("text") or "")[:160],
                "url": debate_url(ls, session, db_slno),
            }
        )
    return examples, len(segments)


def _md_cell(text: str) -> str:
    """Escape a value for a markdown table cell."""
    return str(text).replace("|", "\\|").replace("\n", " ")


def write_outputs(
    out_md: Path,
    out_jsonl: Path,
    stamp: str,
    examples: list[dict],
    clean_debates: list[dict],
    replay_of: str | None = None,
) -> None:
    """Write this run's self-contained rollup to a fresh markdown + JSONL pair.

    `stamp` is the run's single canonical timestamp (it also names the files).
    Run files are immutable: writing refuses to touch a path that already exists.
    """
    for path in (out_md, out_jsonl):
        if path.exists():
            raise SystemExit(f"{path} already exists; run files are immutable")
    out_md.parent.mkdir(parents=True, exist_ok=True)

    with out_jsonl.open("w", encoding="utf-8") as f:
        for ex in examples:
            f.write(json.dumps({"run": stamp, **ex}, ensure_ascii=False) + "\n")

    by_cat = Counter(ex["category"] for ex in examples)
    by_era = Counter(ex["era"] for ex in examples)

    title = f"# Unverified speakers — run {stamp} — {len(examples)} examples"
    if replay_of:
        title += f" (replay of {replay_of})"

    lines = [
        title,
        "",
        "> Auto-generated by `scripts/sample_unverified.py` over randomly sampled debates, "
        "stratified legacy (LS13-14) vs modern (LS15-18). An example is one "
        "distinct speaker label with no `mpCode`.",
        "",
    ]
    if replay_of:
        lines += [
            f"> Re-parsed the exact debates linked from `{replay_of}`. Compare "
            "against that run: the examples table should shrink and/or the "
            "clean-debates table should grow.",
            "",
        ]

    lines += [
        "### Breakdown by category",
        "",
        "| category | count | meaning |",
        "| --- | --- | --- |",
        f"| hindi_name | {by_cat['hindi_name']} | label is Devanagari script (legacy-font names decoded first) |",
        f"| presiding_officer | {by_cat['presiding_officer']} | Chair / Speaker / etc. — role, not an MP row |",
        f"| in_text_no_anchor | {by_cat['in_text_no_anchor']} | named speaker with no anchor / not in mpPartDetailList |",
        "",
        f"By era: legacy={by_era['legacy']}, modern={by_era['modern']}",
        "",
        "### Examples",
        "",
        "| # | era | LS/sess/db | source | category | speaker | nameSource |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for i, ex in enumerate(examples, 1):
        key = f"{ex['loksabha']}/{ex['session']}/{ex['dbSlno']}"
        lines.append(
            f"| {i} | {ex['era']} | {key} | [view]({ex['url']}) "
            f"| {ex['category']} | {_md_cell(ex['speaker'])} | {ex['name_source']} |"
        )

    lines += [
        "",
        "### Debates with no unverified speakers (false-positive check)",
        "",
        "> Parsed cleanly with segments, but every speaker resolved to an "
        "`mpCode`. Spot-check these against the source to confirm the parser "
        "isn't silently missing unverified speakers.",
        "",
        "| LS/sess/db | era | segments | source |",
        "| --- | --- | --- | --- |",
    ]
    if clean_debates:
        for d in clean_debates:
            key = f"{d['loksabha']}/{d['session']}/{d['dbSlno']}"
            lines.append(
                f"| {key} | {d['era']} | {d['segments']} "
                f"| [view]({debate_url(d['loksabha'], d['session'], d['dbSlno'])}) |"
            )
    else:
        lines.append("| _(none this run)_ | | | |")
    lines.append("")

    with out_md.open("w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


DEBATE_URL_RE = re.compile(r"view-debate\?ls=(\d+)&session=(\d+)&dbslno=(\d+)")


def era_of(loksabha: int) -> str:
    return next(e for e, lss in STRATA.items() if loksabha in lss)


def refs_from_file(run_file: Path) -> list[dict]:
    """Every distinct debate linked from a prior run's markdown file."""
    if not run_file.exists():
        raise SystemExit(f"No such run file: {run_file}")
    text = run_file.read_text(encoding="utf-8")

    refs: dict[tuple, dict] = {}
    for ls, session, db in DEBATE_URL_RE.findall(text):
        key = (int(ls), int(session), int(db))
        refs.setdefault(
            key,
            {"loksabha": key[0], "session": key[1], "dbSlno": key[2], "era": era_of(key[0])},
        )
    return list(refs.values())


def collect_refs(refs: list[dict]) -> tuple[list[dict], list[dict]]:
    """Fetch+parse an explicit list of debates (no sampling, no target cap)."""
    examples: list[dict] = []
    clean_debates: list[dict] = []

    for i, ref in enumerate(refs, 1):
        key = (ref["loksabha"], ref["session"], ref["dbSlno"])
        era = ref["era"]
        try:
            found, n_segments = unverified_from_debate(ref, era)
        except requests.RequestException as e:
            print(f"  fetch error {key}: {e}; skipping", file=sys.stderr)
            time.sleep(2)
            continue
        time.sleep(REQUEST_DELAY_S)
        examples.extend(found)
        if not found and n_segments:
            clean_debates.append({**ref, "segments": n_segments})
        print(f"  [{i}/{len(refs)}] {key} -> {len(found)} unverified, {n_segments} segments")

    return examples, clean_debates


def collect(target: int) -> tuple[list[dict], list[dict]]:
    """Sample debates until `target` examples are gathered.

    Returns (examples, clean_debates) where clean_debates are debates that parsed
    into segments but yielded zero unverified speakers — the false-positive check.
    """
    examples: list[dict] = []
    clean_debates: list[dict] = []
    visited: set[tuple] = set()
    era_names = list(STRATA)
    turn = 0
    empty_streak = 0

    while len(examples) < target and empty_streak < 40:
        era = era_names[turn % len(era_names)]
        turn += 1
        ls = random.choice(STRATA[era])
        try:
            refs = random_debate_refs(ls, k=3)
        except requests.RequestException as e:
            print(f"  search error (LS{ls}): {e}; backing off", file=sys.stderr)
            time.sleep(2)
            continue

        got_any = False
        for ref in refs:
            key = (ref["loksabha"], ref["session"], ref["dbSlno"])
            if key in visited:
                continue
            visited.add(key)
            try:
                found, n_segments = unverified_from_debate(ref, era)
            except requests.RequestException as e:
                print(f"  fetch error {key}: {e}; skipping", file=sys.stderr)
                time.sleep(2)
                continue
            time.sleep(REQUEST_DELAY_S)
            if found:
                got_any = True
                examples.extend(found)
                print(f"  {key} -> +{len(found)} (total {len(examples)})")
            elif n_segments:
                # Parsed fine but nothing unverified: candidate false positive.
                clean_debates.append(
                    {
                        "loksabha": ref["loksabha"],
                        "session": ref["session"],
                        "dbSlno": ref["dbSlno"],
                        "era": era,
                        "segments": n_segments,
                    }
                )
            if len(examples) >= target:
                break

        empty_streak = 0 if got_any else empty_streak + 1

    return examples[:target], clean_debates


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--target", type=int, default=100, help="how many examples")
    ap.add_argument("--seed", type=int, default=None, help="RNG seed (reproducible)")
    ap.add_argument(
        "--out",
        type=Path,
        default=None,
        help="markdown path for this run's rollup; the JSONL sits beside it with "
        f"a .jsonl suffix. Default: a fresh timestamped file under {DEFAULT_OUT_DIR}/",
    )
    ap.add_argument(
        "--replay-file",
        type=Path,
        metavar="PATH",
        help="re-parse the debates linked from an earlier run file instead of "
        "sampling new ones; results are written to a new run file",
    )
    args = ap.parse_args()

    now = datetime.now()
    out_md = args.out or default_out_path(now)
    out_jsonl = out_md.with_suffix(".jsonl")
    stamp = now.strftime("%Y-%m-%d %H:%M:%S")

    if args.seed is not None:
        random.seed(args.seed)

    if args.replay_file:
        refs = refs_from_file(args.replay_file)
        print(f"Replaying {len(refs)} debates from {args.replay_file}")
        examples, clean_debates = collect_refs(refs)
        replay_of = args.replay_file.name
    else:
        examples, clean_debates = collect(args.target)
        replay_of = None

    write_outputs(out_md, out_jsonl, stamp, examples, clean_debates, replay_of=replay_of)
    print(
        f"\nWrote {len(examples)} examples "
        f"({len(clean_debates)} clean debates) to {out_md} and {out_jsonl}"
    )


if __name__ == "__main__":
    main()
