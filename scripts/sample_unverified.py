"""
Sample UNVERIFIED speakers from real debates.

An "unverified" speaker is a parsed intervention that has a speaker *label* but no
`mpCode` -- i.e. the parser found someone speaking but could not tie them to a
member-list entry. Examples fall into three categories:
  * Hindi-script names (label is Devanagari),
  * speakers present in the transcript text but absent from the debate's
    mpPartDetailList (no anchor to match against),
  * presiding officers (Mr. Speaker / Chairman / etc.) that the parser missed:
    genuine presiding labels are now tagged `nameSource` "presiding" by the
    parser itself and reported in their own classified section, not as
    unverified examples; the presiding_officer category here only catches
    chair-like labels the parser failed to tag.

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

Once a benchmark's name-resolution failures hit zero (every remaining example
is a presiding officer, as happened to the 62-debate `008` sample), targeting
examples no longer shows headroom -- there's nothing left to draw. `--debates`
switches the sampling unit to debates instead, with an explicit era split, and
can seed itself from an existing run so the old benchmark stays a strict
subset of the new one.

Run from the repo root:
    python -m scripts.sample_unverified                       # 100 examples (default)
    python -m scripts.sample_unverified --target 50
    python -m scripts.sample_unverified --out reports/today.md    # explicit path
    python -m scripts.sample_unverified --replay-file <prior_run.md>  # re-parse a run
    python -m scripts.sample_unverified --debates 100 --legacy-frac 0.67 --seed 1
    python -m scripts.sample_unverified --debates 100 --include-file internal_docs/008_UNVERIFIED_SPEAKERS_SAMPLE.md
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
from db_roster import load_db_roster

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


# The sampler walks ~62 debates but only six Lok Sabha terms, so loading the DB
# roster per debate would fire the same query dozens of times. Cache it per
# term for the life of the run.
#
# The cache is here rather than on `load_db_roster` itself deliberately: this
# script is short-lived and its DB either is or isn't up for the whole run, so
# caching a `[]` (no Postgres) is right here -- it stops 62 connection attempts
# from timing out one by one. Caching that same `[]` inside `load_db_roster`
# would poison the long-lived server.py process, where Postgres coming back up
# later must be picked up. `load_db_roster` stays uncached and side-effect free.
_DB_ROSTER_CACHE: dict[int, list[dict]] = {}


def db_roster_for(term: int) -> list[dict]:
    """The DB roster for a Lok Sabha term, loaded at most once per run."""
    if term not in _DB_ROSTER_CACHE:
        _DB_ROSTER_CACHE[term] = load_db_roster(term)
    return _DB_ROSTER_CACHE[term]


def parse_segments(payload: dict, db_roster: list[dict] | None = None) -> list[dict]:
    """Run the era-appropriate parser and return its speaker segments."""
    html = payload.get("debateDesc") or ""
    mp_list = payload.get("mpPartDetailList", []) or []
    if not html:
        return []
    if debate_fetch_legacy.looks_legacy(html):
        return debate_fetch_legacy.split_by_speaker_legacy(html, mp_list, db_roster)
    return debate_fetch.split_by_speaker(html, mp_list, db_roster)


def speakers_from_debate(
    ref: dict, era: str
) -> tuple[list[dict], list[dict], list[dict], int]:
    """Fetch+parse one debate.

    Returns (unverified examples, resolved speakers, presiding rows, number of
    parsed segments). Unverified examples are distinct speaker labels with no
    `mpCode`; resolved speakers are one row per distinct `mpCode`, with how
    that code was matched and how many turns it covers. Presiding rows are one
    per distinct label tagged `nameSource` "presiding" by the parser (a chair
    label, classified as a role rather than an unverified example), with its
    turn count. The segment count lets the caller tell a genuinely clean
    debate (parsed fine, every speaker resolved or presiding) apart from one
    the parser simply couldn't read.
    """
    ls, session, db_slno = ref["loksabha"], ref["session"], ref["dbSlno"]
    payload = debate_fetch.fetch_debate(ls, session, db_slno)
    segments = parse_segments(payload, db_roster_for(ls))

    seen: set[str] = set()
    examples: list[dict] = []
    resolved_by_code: dict[str, dict] = {}
    presiding_by_label: dict[str, dict] = {}
    for seg in segments:
        label = seg.get("speakerLabel")
        code = seg.get("mpCode")
        if code:
            row = resolved_by_code.setdefault(
                code,
                {
                    "loksabha": ls,
                    "session": session,
                    "dbSlno": db_slno,
                    "era": era,
                    "mp_code": code,
                    "mp_name": seg.get("mpName"),
                    "speaker_raw": label,
                    "name_sources": [],
                    "turns": 0,
                },
            )
            row["turns"] += 1
            source = seg.get("nameSource")
            if source and source not in row["name_sources"]:
                row["name_sources"].append(source)
            continue
        if seg.get("nameSource") == "presiding":
            row = presiding_by_label.setdefault(
                label,
                {
                    "loksabha": ls,
                    "session": session,
                    "dbSlno": db_slno,
                    "era": era,
                    "speaker": label,
                    "turns": 0,
                    "url": debate_url(ls, session, db_slno),
                },
            )
            row["turns"] += 1
            continue
        if not label or label in seen:
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
    return (
        examples,
        list(resolved_by_code.values()),
        list(presiding_by_label.values()),
        len(segments),
    )


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
    resolved: list[dict] | None = None,
    presiding: list[dict] | None = None,
    draw_note: str | None = None,
) -> None:
    """Write this run's self-contained rollup to a fresh markdown + JSONL pair.

    `stamp` is the run's single canonical timestamp (it also names the files).
    When `resolved` is given, those rows go to a `*_resolved.jsonl` beside the
    markdown and a summary section is added to it — the regression baseline for
    "verified speakers never go down". When `presiding` is given, those rows
    go to a `*_presiding.jsonl` beside the markdown and a section is added
    listing chair labels the parser tagged `nameSource` "presiding" (classified,
    not unverified). `draw_note`, when given, is a one-line record of how the
    sample was drawn (debate count, era split, seed, seed file) so a later
    reader doesn't have to reconstruct it from the CLI invocation. Run files
    are immutable: writing refuses to touch a path that already exists.
    """
    out_resolved = out_md.with_name(out_md.stem + "_resolved.jsonl")
    out_presiding = out_md.with_name(out_md.stem + "_presiding.jsonl")
    paths = (
        [out_md, out_jsonl]
        + ([out_resolved] if resolved is not None else [])
        + ([out_presiding] if presiding is not None else [])
    )
    for path in paths:
        if path.exists():
            raise SystemExit(f"{path} already exists; run files are immutable")
    out_md.parent.mkdir(parents=True, exist_ok=True)

    with out_jsonl.open("w", encoding="utf-8") as f:
        for ex in examples:
            f.write(json.dumps({"run": stamp, **ex}, ensure_ascii=False) + "\n")

    if resolved is not None:
        with out_resolved.open("w", encoding="utf-8") as f:
            for row in resolved:
                f.write(json.dumps({"run": stamp, **row}, ensure_ascii=False) + "\n")

    if presiding is not None:
        with out_presiding.open("w", encoding="utf-8") as f:
            for row in presiding:
                f.write(json.dumps({"run": stamp, **row}, ensure_ascii=False) + "\n")

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

    if draw_note:
        lines += [f"> {draw_note}", ""]

    lines += [
        "### Breakdown by category",
        "",
        "| category | count | meaning |",
        "| --- | --- | --- |",
        f"| hindi_name | {by_cat['hindi_name']} | label is Devanagari script (legacy-font names decoded first) |",
        f"| presiding_officer | {by_cat['presiding_officer']} | chair-like label the parser did NOT tag (leakage: candidates for is_presiding_label) |",
        f"| in_text_no_anchor | {by_cat['in_text_no_anchor']} | named speaker with no anchor / not in mpPartDetailList |",
        "",
        f"By era: legacy={by_era['legacy']}, modern={by_era['modern']}",
        "",
    ]

    if resolved is not None:
        by_source = Counter(
            (row["name_sources"] or ["unknown"])[0] for row in resolved
        )
        distinct_codes = len({row["mp_code"] for row in resolved})
        lines += [
            "### Resolved speakers (regression baseline)",
            "",
            f"> {len(resolved)} resolved speaker rows (one per debate+mpCode), "
            f"{distinct_codes} distinct mpCodes. Full rows in "
            f"`{out_resolved.name}`. Any future run over the same debates must "
            "not lose any of these.",
            "",
            "| primary nameSource | rows |",
            "| --- | --- |",
        ]
        lines += [f"| {src} | {n} |" for src, n in by_source.most_common()]
        lines.append("")

    if presiding is not None:
        lines += [
            "### Presiding officers (classified)",
            "",
            f"> {len(presiding)} chair rows (one per debate + label), "
            f"{len({row['speaker'] for row in presiding})} distinct labels, "
            'tagged nameSource "presiding" by the parser — catalogued as the '
            f"role, never mapped to a member. Full rows in `{out_presiding.name}`.",
            "",
            "| # | era | LS/sess/db | source | label | turns |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
        if presiding:
            for i, row in enumerate(presiding, 1):
                key = f"{row['loksabha']}/{row['session']}/{row['dbSlno']}"
                lines.append(
                    f"| {i} | {row['era']} | {key} | [view]({row['url']}) "
                    f"| {_md_cell(row['speaker'])} | {row['turns']} |"
                )
        else:
            lines.append("| _(none this run)_ | | | | | |")
        lines.append("")

    lines += [
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


def split_counts(n: int, legacy_frac: float) -> tuple[int, int]:
    """How many of n debates come from legacy vs modern, summing exactly to n.

    `round()` on the legacy share and subtracting from n (rather than rounding
    both shares independently) is what guarantees the sum is exact.
    """
    n_legacy = round(n * legacy_frac)
    return n_legacy, n - n_legacy


def sample_debate_refs(
    n_debates: int, legacy_frac: float, exclude: set[tuple] | None = None
) -> list[dict]:
    """Draw n_debates fresh debate refs, split legacy/modern per legacy_frac.

    Unlike `collect`, the unit here is debates, not unverified examples: this
    draws exactly n_debates refs (era-split, not stopping early) and does no
    fetching or parsing -- that's `collect_refs`'s job once the ref list is
    final. `exclude` is a set of (loksabha, session, dbSlno) keys that must
    never be drawn, so a debate already pulled in via --include-file is never
    drawn a second time.
    """
    n_legacy, n_modern = split_counts(n_debates, legacy_frac)
    targets = {"legacy": n_legacy, "modern": n_modern}
    visited: set[tuple] = set(exclude or ())
    drawn: dict[str, list[dict]] = {"legacy": [], "modern": []}
    era_names = list(STRATA)
    turn = 0
    empty_streak = 0

    while sum(len(v) for v in drawn.values()) < n_debates and empty_streak < 40:
        era = era_names[turn % len(era_names)]
        turn += 1
        if len(drawn[era]) >= targets[era]:
            continue
        ls = random.choice(STRATA[era])
        try:
            refs = random_debate_refs(ls, k=3)
        except requests.RequestException as e:
            print(f"  search error (LS{ls}): {e}; backing off", file=sys.stderr)
            time.sleep(2)
            empty_streak += 1
            continue

        got_any = False
        for ref in refs:
            key = (ref["loksabha"], ref["session"], ref["dbSlno"])
            if key in visited:
                continue
            visited.add(key)
            drawn[era].append({**ref, "era": era})
            got_any = True
            if len(drawn[era]) >= targets[era]:
                break
        empty_streak = 0 if got_any else empty_streak + 1

    return drawn["legacy"] + drawn["modern"]


def collect_refs(
    refs: list[dict],
) -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    """Fetch+parse an explicit list of debates (no sampling, no target cap).

    Returns (unverified examples, clean debates, resolved speakers, presiding
    rows).
    """
    examples: list[dict] = []
    clean_debates: list[dict] = []
    resolved: list[dict] = []
    presiding: list[dict] = []

    for i, ref in enumerate(refs, 1):
        key = (ref["loksabha"], ref["session"], ref["dbSlno"])
        era = ref["era"]
        try:
            found, solved, chairs, n_segments = speakers_from_debate(ref, era)
        except requests.RequestException as e:
            print(f"  fetch error {key}: {e}; skipping", file=sys.stderr)
            time.sleep(2)
            continue
        time.sleep(REQUEST_DELAY_S)
        examples.extend(found)
        resolved.extend(solved)
        presiding.extend(chairs)
        if not found and n_segments:
            clean_debates.append({**ref, "segments": n_segments})
        print(
            f"  [{i}/{len(refs)}] {key} -> {len(found)} unverified, "
            f"{len(chairs)} presiding, {len(solved)} resolved, {n_segments} segments"
        )

    return examples, clean_debates, resolved, presiding


def collect(target: int) -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    """Sample debates until `target` examples are gathered.

    Returns (examples, clean_debates, resolved, presiding) where clean_debates
    are debates that parsed into segments but yielded zero unverified
    speakers — the false-positive check — resolved lists every speaker tied to
    an `mpCode`, and presiding lists every chair label the parser tagged
    `nameSource` "presiding".
    """
    examples: list[dict] = []
    clean_debates: list[dict] = []
    resolved: list[dict] = []
    presiding: list[dict] = []
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
                found, solved, chairs, n_segments = speakers_from_debate(ref, era)
            except requests.RequestException as e:
                print(f"  fetch error {key}: {e}; skipping", file=sys.stderr)
                time.sleep(2)
                continue
            time.sleep(REQUEST_DELAY_S)
            resolved.extend(solved)
            presiding.extend(chairs)
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

    return examples[:target], clean_debates, resolved, presiding


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    target_group = ap.add_mutually_exclusive_group()
    target_group.add_argument(
        "--target", type=int, default=None,
        help="how many unverified examples to gather (default 100 if neither "
        "--target nor --debates is given). Obsolete for benchmarks that have "
        "hit zero name-resolution failures -- see --debates.",
    )
    target_group.add_argument(
        "--debates", type=int, default=None,
        help="sample exactly this many debates (unit = debates, not examples), "
        "split by era per --legacy-frac",
    )
    ap.add_argument(
        "--legacy-frac", type=float, default=0.67,
        help="fraction of --debates drawn from the legacy strata (LS13-14); "
        "the rest come from modern (LS15-18). Default 0.67. Ignored without "
        "--debates.",
    )
    ap.add_argument(
        "--include-file", type=Path, metavar="PATH", default=None,
        help="seed the sample with every debate ref already linked from PATH "
        "(a prior run .md, or 008_UNVERIFIED_SPEAKERS_SAMPLE.md) in addition "
        "to --debates N; deduped against the newly drawn refs so no debate is "
        "parsed twice. Requires --debates.",
    )
    ap.add_argument(
        "--dry-run", action="store_true",
        help="with --debates, print the chosen refs and exit without "
        "fetching or parsing any of them",
    )
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

    if args.include_file and args.debates is None:
        ap.error("--include-file requires --debates")
    if args.target is None and args.debates is None:
        args.target = 100

    now = datetime.now()
    out_md = args.out or default_out_path(now)
    out_jsonl = out_md.with_suffix(".jsonl")
    stamp = now.strftime("%Y-%m-%d %H:%M:%S")

    if args.seed is not None:
        random.seed(args.seed)

    draw_note = None

    if args.debates is not None:
        seed_refs = refs_from_file(args.include_file) if args.include_file else []
        exclude = {(r["loksabha"], r["session"], r["dbSlno"]) for r in seed_refs}
        n_legacy_target, n_modern_target = split_counts(args.debates, args.legacy_frac)
        drawn = sample_debate_refs(args.debates, args.legacy_frac, exclude=exclude)
        refs = seed_refs + drawn

        n_legacy_drawn = sum(1 for r in drawn if r["era"] == "legacy")
        n_modern_drawn = len(drawn) - n_legacy_drawn
        draw_note = (
            f"Drew {args.debates} debates (target legacy={n_legacy_target}/"
            f"modern={n_modern_target}, legacy_frac={args.legacy_frac}; actual "
            f"legacy={n_legacy_drawn}/modern={n_modern_drawn}), seed={args.seed}."
        )
        if args.include_file:
            draw_note += (
                f" Seeded {len(seed_refs)} refs from {args.include_file.name}; "
                f"combined sample is {len(refs)} debates."
            )

        if args.dry_run:
            print(draw_note)
            for r in refs:
                key = f"{r['loksabha']}/{r['session']}/{r['dbSlno']}"
                print(f"  {r['era']:7s} {key}")
            print(f"\n{len(refs)} refs selected ({len(seed_refs)} seeded, {len(drawn)} drawn); dry run, nothing parsed")
            return

        print(f"Parsing {len(refs)} debates ({draw_note})")
        examples, clean_debates, resolved, presiding = collect_refs(refs)
        replay_of = None
    elif args.replay_file:
        refs = refs_from_file(args.replay_file)
        print(f"Replaying {len(refs)} debates from {args.replay_file}")
        examples, clean_debates, resolved, presiding = collect_refs(refs)
        replay_of = args.replay_file.name
    else:
        examples, clean_debates, resolved, presiding = collect(args.target)
        replay_of = None

    write_outputs(
        out_md, out_jsonl, stamp, examples, clean_debates,
        replay_of=replay_of, resolved=resolved, presiding=presiding,
        draw_note=draw_note,
    )
    print(
        f"\nWrote {len(examples)} examples ({len(presiding)} presiding) "
        f"({len(clean_debates)} clean debates) to {out_md} and {out_jsonl}"
    )


if __name__ == "__main__":
    main()
