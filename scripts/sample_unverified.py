"""
Sample debates, parse them, and write a rollup of speakers the parser could not tie to a member.

Usage:
    python -m scripts.sample_unverified                       # 100 examples (default)
    python -m scripts.sample_unverified --target 50
    python -m scripts.sample_unverified --out reports/today.md
    python -m scripts.sample_unverified --replay-file <prior_run.md>
    python -m scripts.sample_unverified --debates 100 --legacy-frac 0.67 --seed 1
    python -m scripts.sample_unverified --debates 100 --include-file <prior_run.md>
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
DEBATE_PAGE = "https://sansad.in/ls/debates/view-debate"

STRATA = {"legacy": [13, 14], "modern": [15, 16, 17, 18]}

DEVANAGARI_RE = re.compile(r"[ऀ-ॿ]")
PRESIDING_RE = re.compile(
    r"speaker|chairman|chairperson|chair\b|deputy|panel|adhyaksh|sabhapati"
    r"|hon.{0,3}member|presiding",
    re.IGNORECASE,
)

DEFAULT_OUT_DIR = Path("internal_docs")

# The API is undocumented, so pace the requests.
REQUEST_DELAY_S = 0.6


def classify(label: str) -> str:
    """Bucket a label. Expects a decoded (Unicode) label, not legacy-font text."""
    if DEVANAGARI_RE.search(label):
        return "hindi_name"
    if PRESIDING_RE.search(label):
        return "presiding_officer"
    return "in_text_no_anchor"


def default_out_path(now: datetime | None = None) -> Path:
    now = now or datetime.now()
    return DEFAULT_OUT_DIR / f"{now:%Y%m%d_%H%M%S}_unverified_run.md"


def debate_url(ls: int, session: int, db_slno: int) -> str:
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
    meta = search_page(loksabha, 1).get("_metadata", {})
    total_pages = max(int(meta.get("totalPages", 1)), 1)
    page = random.randint(1, total_pages)
    records = search_page(loksabha, page).get("records", [])
    random.shuffle(records)
    return records[:k]


# Cache per term here, not in load_db_roster, which must stay uncached for the long-lived server.
_DB_ROSTER_CACHE: dict[int, list[dict]] = {}


def db_roster_for(term: int) -> list[dict]:
    if term not in _DB_ROSTER_CACHE:
        _DB_ROSTER_CACHE[term] = load_db_roster(term)
    return _DB_ROSTER_CACHE[term]


def parse_segments(payload: dict, db_roster: list[dict] | None = None) -> list[dict]:
    html = payload.get("debateDesc") or ""
    mp_list = payload.get("mpPartDetailList", []) or []
    if not html:
        return []
    if debate_fetch_legacy.looks_legacy(html):
        return debate_fetch_legacy.split_by_speaker_legacy(html, mp_list, db_roster)
    return debate_fetch.split_by_speaker(html, mp_list, db_roster)


def swallowed_labels(segments: list[dict]) -> list[str]:
    # Finds ALL-CAPS labels inside another turn's text, which are turns the splitter never opened.
    # This is a lower bound: _is_caps_label reads Latin script only.
    found: list[str] = []
    for seg in segments:
        for para in (seg.get("text") or "").split("\n\n"):
            para = para.strip()
            colon = para.find(":")
            if not (0 < colon <= debate_fetch.LABEL_MAX_CHARS):
                continue
            if debate_fetch._is_caps_label(para[:colon]):
                found.append(para[:colon].strip())
    return found


def unfounded_attributions(segments: list[dict]) -> list[str]:
    # Finds "anchor-reuse" labels with no usable name words. Such a label gives nothing to compare.
    found: list[str] = []
    for seg in segments:
        if seg.get("nameSource") != "anchor-reuse":
            continue
        label = seg.get("speakerLabel") or ""
        full, _ = debate_fetch._name_parts(label)
        if not full:
            found.append(label)
    return found


def speakers_from_debate(
    ref: dict, era: str
) -> tuple[list[dict], list[dict], list[dict], list[dict], list[dict], int]:
    """Return (unverified examples, resolved speakers, presiding rows, swallowed rows, unfounded rows, segment count)."""
    ls, session, db_slno = ref["loksabha"], ref["session"], ref["dbSlno"]
    payload = debate_fetch.fetch_debate(ls, session, db_slno)
    segments = parse_segments(payload, db_roster_for(ls))

    swallowed_by_label: dict[str, dict] = {}
    for label in swallowed_labels(segments):
        row = swallowed_by_label.setdefault(
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

    unfounded_by_label: dict[str, dict] = {}
    for label in unfounded_attributions(segments):
        row = unfounded_by_label.setdefault(
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
        list(swallowed_by_label.values()),
        list(unfounded_by_label.values()),
        len(segments),
    )


def _md_cell(text: str) -> str:
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
    swallowed: list[dict] | None = None,
    unfounded: list[dict] | None = None,
    draw_note: str | None = None,
) -> None:
    """Write the rollup and JSONL files. Refuse to overwrite an existing path."""
    out_resolved = out_md.with_name(out_md.stem + "_resolved.jsonl")
    out_presiding = out_md.with_name(out_md.stem + "_presiding.jsonl")
    out_swallowed = out_md.with_name(out_md.stem + "_swallowed.jsonl")
    out_unfounded = out_md.with_name(out_md.stem + "_unfounded.jsonl")
    paths = (
        [out_md, out_jsonl]
        + ([out_resolved] if resolved is not None else [])
        + ([out_presiding] if presiding is not None else [])
        + ([out_swallowed] if swallowed is not None else [])
        + ([out_unfounded] if unfounded is not None else [])
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

    if swallowed is not None:
        with out_swallowed.open("w", encoding="utf-8") as f:
            for row in swallowed:
                f.write(json.dumps({"run": stamp, **row}, ensure_ascii=False) + "\n")

    if unfounded is not None:
        with out_unfounded.open("w", encoding="utf-8") as f:
            for row in unfounded:
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

    if swallowed is not None:
        n_turns = sum(row["turns"] for row in swallowed)
        by_debate = Counter(
            (row["loksabha"], row["session"], row["dbSlno"]) for row in swallowed
        )
        lines += [
            "### Swallowed turns (denominator check)",
            "",
            f"> {n_turns} paragraphs across {len(by_debate)} debates open with an "
            "ALL-CAPS speaker label but sit *inside* another speaker's turn — the "
            "splitter never opened a boundary there, so they were never counted as "
            "labels and every other number on this page is blind to them. A "
            "**lower bound**: the probe only recognises Latin-script labels, so an "
            "unbolded Devanagari label is invisible to it too. Full rows in "
            f"`{out_swallowed.name}`.",
            "",
            "| # | era | LS/sess/db | source | label | turns |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
        if swallowed:
            worst = sorted(swallowed, key=lambda r: -r["turns"])
            for i, row in enumerate(worst, 1):
                key = f"{row['loksabha']}/{row['session']}/{row['dbSlno']}"
                lines.append(
                    f"| {i} | {row['era']} | {key} | [view]({row['url']}) "
                    f"| {_md_cell(row['speaker'])} | {row['turns']} |"
                )
        else:
            lines.append("| _(none this run)_ | | | | | |")
        lines.append("")

    if unfounded is not None:
        n_turns = sum(row["turns"] for row in unfounded)
        by_debate = Counter(
            (row["loksabha"], row["session"], row["dbSlno"]) for row in unfounded
        )
        lines += [
            "### Unfounded attributions (misattribution guard)",
            "",
            f"> {n_turns} turns across {len(by_debate)} debates carry an "
            '"anchor-reuse" `mpCode` whose label names nobody -- the exact '
            "misattribution class fixed in `5f9bd3c` (303 turns credited to "
            "the wrong MP in one debate). This must always read zero; a "
            "nonzero count here means that class of bug is back. Full rows "
            f"in `{out_unfounded.name}`.",
            "",
            "| # | era | LS/sess/db | source | label | turns |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
        if unfounded:
            worst = sorted(unfounded, key=lambda r: -r["turns"])
            for i, row in enumerate(worst, 1):
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
    n_legacy = round(n * legacy_frac)
    return n_legacy, n - n_legacy


def sample_debate_refs(
    n_debates: int, legacy_frac: float, exclude: set[tuple] | None = None
) -> list[dict]:
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
) -> tuple[list[dict], list[dict], list[dict], list[dict], list[dict], list[dict]]:
    """Return (unverified examples, clean debates, resolved, presiding, swallowed, unfounded)."""
    examples: list[dict] = []
    clean_debates: list[dict] = []
    resolved: list[dict] = []
    presiding: list[dict] = []
    swallowed: list[dict] = []
    unfounded: list[dict] = []

    for i, ref in enumerate(refs, 1):
        key = (ref["loksabha"], ref["session"], ref["dbSlno"])
        era = ref["era"]
        try:
            found, solved, chairs, eaten, baseless, n_segments = speakers_from_debate(ref, era)
        except requests.RequestException as e:
            print(f"  fetch error {key}: {e}; skipping", file=sys.stderr)
            time.sleep(2)
            continue
        time.sleep(REQUEST_DELAY_S)
        examples.extend(found)
        resolved.extend(solved)
        presiding.extend(chairs)
        swallowed.extend(eaten)
        unfounded.extend(baseless)
        if not found and n_segments:
            clean_debates.append({**ref, "segments": n_segments})
        n_eaten = sum(r["turns"] for r in eaten)
        n_baseless = sum(r["turns"] for r in baseless)
        print(
            f"  [{i}/{len(refs)}] {key} -> {len(found)} unverified, "
            f"{len(chairs)} presiding, {len(solved)} resolved, {n_segments} segments"
            + (f", {n_eaten} SWALLOWED" if n_eaten else "")
            + (f", {n_baseless} UNFOUNDED" if n_baseless else "")
        )

    return examples, clean_debates, resolved, presiding, swallowed, unfounded


def collect(
    target: int,
) -> tuple[list[dict], list[dict], list[dict], list[dict], list[dict], list[dict]]:
    """Sample debates until `target` examples are gathered.

    Return (examples, clean_debates, resolved, presiding, swallowed, unfounded).
    """
    examples: list[dict] = []
    clean_debates: list[dict] = []
    resolved: list[dict] = []
    presiding: list[dict] = []
    swallowed: list[dict] = []
    unfounded: list[dict] = []
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
                found, solved, chairs, eaten, baseless, n_segments = speakers_from_debate(ref, era)
            except requests.RequestException as e:
                print(f"  fetch error {key}: {e}; skipping", file=sys.stderr)
                time.sleep(2)
                continue
            time.sleep(REQUEST_DELAY_S)
            resolved.extend(solved)
            presiding.extend(chairs)
            swallowed.extend(eaten)
            unfounded.extend(baseless)
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

    return examples[:target], clean_debates, resolved, presiding, swallowed, unfounded


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
        "(for example a prior run .md) in addition "
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
        examples, clean_debates, resolved, presiding, swallowed, unfounded = collect_refs(refs)
        replay_of = None
    elif args.replay_file:
        refs = refs_from_file(args.replay_file)
        print(f"Replaying {len(refs)} debates from {args.replay_file}")
        examples, clean_debates, resolved, presiding, swallowed, unfounded = collect_refs(refs)
        replay_of = args.replay_file.name
    else:
        examples, clean_debates, resolved, presiding, swallowed, unfounded = collect(args.target)
        replay_of = None

    write_outputs(
        out_md, out_jsonl, stamp, examples, clean_debates,
        replay_of=replay_of, resolved=resolved, presiding=presiding,
        swallowed=swallowed, unfounded=unfounded, draw_note=draw_note,
    )
    print(
        f"\nWrote {len(examples)} examples ({len(presiding)} presiding, "
        f"{sum(r['turns'] for r in swallowed)} swallowed, "
        f"{sum(r['turns'] for r in unfounded)} unfounded) "
        f"({len(clean_debates)} clean debates) to {out_md} and {out_jsonl}"
    )


if __name__ == "__main__":
    main()
