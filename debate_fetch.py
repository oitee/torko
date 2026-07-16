"""
Step 1: fetch a Lok Sabha debate transcript from sansad.in, clean it into
plain text, and break it down by speaker.

Usage:
    python3 debate_fetch.py --loksabha 18 --session 3 --dbslno 1758
"""
import argparse
import re
import sys
from difflib import SequenceMatcher

import requests
from bs4 import BeautifulSoup

import translit

API_URL = "https://sansad.in/api_ls/debate/debate-details"

# Thresholds for accepting a carried anchor: how close two name tokens must be
# to count as the same token, and what share of the roster name's tokens must be
# found in the label before we believe they name the same person.
ANCHOR_TOKEN_MIN = 0.8
ANCHOR_COVERAGE_MIN = 0.6

# Matches the speaker anchors sansad.in embeds in the transcript HTML, e.g.
# <A name="3972*1">  ->  mpCode=3972, mpPartCode=1
ANCHOR_RE = re.compile(r'<A\s+name="(\d+)\*(\d+)"[^>]*>', re.IGNORECASE)

# Anchor `name` attribute as seen by BeautifulSoup, e.g. "3972*1".
ANCHOR_NAME_RE = re.compile(r"^(\d+)\*(\d+)$")

# A speaker label is bold text at the very start of a paragraph, terminated by a
# colon that appears within this many characters. This colon is the one
# cross-script invariant: it delimits the label in English, Hindi and Urdu alike
# ("SHRI K. C. VENUGOPAL (ALAPPUZHA):", "श्री किरेन रिजिजू :"). The window is
# generous enough to cover long ministerial designations.
LABEL_MAX_CHARS = 200

# Some labels carry a running marker prefix like "*57" or "*m25"; strip it.
STAR_PREFIX_RE = re.compile(r"^\*[a-zA-Z]?\d+\s*")

# Honorifics / designation-noise dropped when normalising a name for matching.
_PAREN_RE = re.compile(r"\(([^)]*)\)")
_HONORIFICS = {
    "shri", "shrimati", "smt", "sushri", "km", "kumari", "ku", "dr", "prof",
    "adv", "advocate", "mr", "mrs", "ms", "sardar", "sarvashri",
    # to_latin spellings of Devanagari honorifics (श्री, श्रीमती, सुश्री, कुँवर,
    # डॉ, प्रो, डा), so they are recognised before folding runs.
    "shree", "shreemati", "sushree", "kunvar", "kunvara", "do", "pro", "da",
}


def _normalize_name(label: str) -> list[str]:
    """
    Reduce a speaker label to its bare name tokens for matching against
    mpPartDetailList: drop honorifics, drop the constituency in parentheses,
    and strip punctuation. A ministerial designation
    ("THE MINISTER OF ... (SHRI PRALHAD JOSHI)") is collapsed to the person's
    name inside the parentheses. Indic-script labels pass through as their own
    tokens (which won't match the romanised list — that gap needs
    transliteration, tracked separately).
    """
    # ministerial designation: the name sits in parentheses led by an honorific
    for inside in _PAREN_RE.findall(label):
        head = re.sub(r"[^\w\s]", " ", inside).lower().split()
        # require a real name token after the honorific — a paren group that is
        # only an honorific (e.g. "(Smt.)" in "Dr. (Smt.) V. Saroja") is not a
        # ministerial designation and must not replace the actual name.
        if head and head[0] in _HONORIFICS and any(t not in _HONORIFICS for t in head):
            label = inside
            break
    label = _PAREN_RE.sub(" ", label)  # drop remaining (constituency)
    label = re.sub(r"[^\w\s]", " ", label.lower())
    return [tok for tok in label.split() if tok and tok not in _HONORIFICS]


# Honorifics as they look *after* transliteration+folding: श्री -> "shree" -> "shri",
# डॉ -> "do", प्रो -> "pro". _HONORIFICS holds the romanised spellings; this set holds
# the folded forms so honorifics are dropped from Devanagari labels too; the
# cluster-"a" rule also folds "sardar" -> "srdar" and "sarvashri" -> "srvshri".
_FOLDED_HONORIFICS = {
    "shri", "shrimati", "smt", "sushri", "km", "kumari", "ku", "dr", "do", "da",
    "prof", "pro", "adv", "advocate", "mr", "mrs", "ms", "sardar", "sarvashri",
    "srdar", "srvshri",
}


def _name_parts(name: str) -> tuple[list[str], set[str]]:
    """Folded name tokens, script-agnostic, split into full words and initials."""
    toks = [translit.fold(t) for t in _normalize_name(translit.to_latin(name or ""))]
    toks = [t for t in toks if t and t not in _FOLDED_HONORIFICS]
    full = [t for t in toks if len(t) >= 3]
    initials = {t[0] for t in toks if 0 < len(t) < 3}
    return full, initials


def _folded_key(name: str) -> str:
    """Build a spelling- and word-order-insensitive key from a name.

    Reuses the script-agnostic folding of `_name_parts`, keeps only the whole-word
    tokens (initials are too weak to key on), sorts them so a Devanagari label and
    a romanised roster name that order given/family names differently still produce
    the same key, and joins them. Returns "" when the name has no usable whole word,
    so an all-honorific label can never key into (and wildcard-match) the table.
    """
    full, _ = _name_parts(name)
    return "".join(sorted(full))


def anchor_agrees_with_label(label: str, roster_name: str) -> bool:
    """Whether an anchor's roster name names the same person as the label.

    A roster word may appear in the label as an initial ("Salarapatty Kuppusamy
    Kharventhan" / "S.K. KHARVENTHAN"), which counts towards coverage — but
    initials are weak evidence, so at least one whole word must also match
    outright before the two names are treated as the same person.
    """
    lab_full, lab_initials = _name_parts(label)
    ros_full, _ = _name_parts(roster_name)
    if not ros_full or not (lab_full or lab_initials):
        return True  # no usable name on one side: nothing to contradict

    strong = covered = 0
    for r in ros_full:
        if any(SequenceMatcher(None, r, l).ratio() >= ANCHOR_TOKEN_MIN for l in lab_full):
            strong += 1
            covered += 1
        elif r[0] in lab_initials:
            covered += 1
    return strong >= 1 and covered / len(ros_full) >= ANCHOR_COVERAGE_MIN


def build_speaker_index(mp_part_detail_list: list[dict]) -> dict:
    """Index the MP list by several normalised keys for fuzzy name matching."""
    by_str: dict[str, dict] = {}
    by_join_ordered: dict[str, dict] = {}
    by_join_sorted: dict[str, dict] = {}
    tokenised: list[tuple[set, dict]] = []
    for m in mp_part_detail_list:
        toks = _normalize_name(m["mpName"])
        by_str.setdefault(" ".join(toks), m)
        by_join_ordered.setdefault("".join(toks), m)
        by_join_sorted.setdefault("".join(sorted(toks)), m)
        tokenised.append((set(toks), m))

    by_folded: dict[str, dict] = {}
    folded_codes: dict[str, set] = {}
    for m in mp_part_detail_list:
        key = _folded_key(m["mpName"])
        if not key:
            continue
        by_folded.setdefault(key, m)
        folded_codes.setdefault(key, set()).add(m["mpCode"])
    # drop any key that names more than one distinct person: never guess
    by_folded = {k: v for k, v in by_folded.items() if len(folded_codes[k]) == 1}

    return {
        "by_str": by_str,
        "by_join_ordered": by_join_ordered,
        "by_join_sorted": by_join_sorted,
        "tokenised": tokenised,
        "by_folded": by_folded,
    }


def resolve_speaker(label: str, index: dict) -> tuple[str | None, dict | None]:
    """
    Try to match a raw speaker label to an MP list entry.

    Returns (nameSource, entry). nameSource is one of "name-exact",
    "name-join" (matches once spacing/word-order is ignored), "name-partial"
    (one entry's tokens are a subset of the other's), "name-translit"
    (matches once the label is transliterated from Devanagari and folded),
    or None when unmatched.
    """
    toks = _normalize_name(label)
    if not toks:
        return None, None
    if (m := index["by_str"].get(" ".join(toks))):
        return "name-exact", m
    if (m := index["by_join_ordered"].get("".join(toks))):
        return "name-join", m
    if (m := index["by_join_sorted"].get("".join(sorted(toks)))):
        return "name-join", m
    tset = set(toks)
    cands = {
        id(m): m
        for s, m in index["tokenised"]
        if tset and s and (tset <= s or s <= tset)
    }
    # unique *person* (mpCode), guarding against a single entry appearing twice
    codes = {m["mpCode"] for m in cands.values()}
    if len(codes) == 1:
        return "name-partial", next(iter(cands.values()))
    if (key := _folded_key(label)) and (m := index["by_folded"].get(key)):
        return "name-translit", m
    return None, None


def annotate_speakers(segments: list[dict], mp_part_detail_list: list[dict]) -> list[dict]:
    """
    Fill each segment's canonical mpName + nameSource tag.

    Anchored turns already carry the list's name (nameSource "anchor").
    Anchor-less turns are matched by name; on success mpName is replaced with
    the canonical list name and the match method is recorded, otherwise the raw
    label is kept with nameSource "unresolved".
    """
    index = build_speaker_index(mp_part_detail_list)
    for seg in segments:
        if seg.get("mpCode"):
            seg["nameSource"] = "anchor"
            continue
        if not seg.get("speakerLabel"):
            seg["nameSource"] = None
            continue
        source, entry = resolve_speaker(seg["speakerLabel"], index)
        if entry:
            seg["mpCode"] = str(entry["mpCode"])
            seg["mpName"] = entry["mpName"]
            seg["nameSource"] = source
        else:
            seg["nameSource"] = "unresolved"
    return segments


def reuse_anchors(segments: list[dict]) -> list[dict]:
    """Propagate each anchored speaker's mpCode to their unanchored turns.

    sansad.in anchors a speaker only on their first turn, so their later turns
    arrive unresolved under the same name. First collect every anchored
    (mpCode, mpName), then attach it to any still-unresolved turn whose label
    names the same person. A label anchored to two different people in one
    debate is ambiguous and left untouched.
    """
    resolved: dict[str, tuple[str, str]] = {}
    ambiguous: set[str] = set()
    for seg in segments:
        code, label = seg.get("mpCode"), seg.get("speakerLabel")
        if not code or not label:
            continue
        prior = resolved.get(label)
        if prior and prior[0] != code:
            ambiguous.add(label)
        resolved.setdefault(label, (code, seg.get("mpName") or label))

    for seg in segments:
        if seg.get("mpCode") or not seg.get("speakerLabel"):
            continue
        label = seg["speakerLabel"]
        for anchored_label, (code, name) in resolved.items():
            if anchored_label in ambiguous:
                continue
            if anchor_agrees_with_label(label, anchored_label) and anchor_agrees_with_label(
                anchored_label, label
            ):
                seg["mpCode"] = code
                seg["mpName"] = name
                seg["nameSource"] = "anchor-reuse"
                break
    return segments


def _clean_inline(text: str) -> str:
    """Collapse wrap/whitespace noise and tidy space-before-punctuation."""
    text = re.sub(r"\s+", " ", text.replace("\xa0", " "))
    text = re.sub(r"\s+([।?!,.;:])", r"\1", text)
    return text.strip()


def fetch_debate(loksabha: int, session: int, db_slno: int) -> dict:
    """Fetch the raw debate-details JSON for one debate item."""
    params = {
        "loksabha": loksabha,
        "sessionNumber": session,
        "dbSlNo": db_slno,
    }
    resp = requests.get(API_URL, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def html_to_clean_text(html: str) -> str:
    """
    Strip HTML/entities down to clean plain text.

    Paragraphs from the source (<p>, <br>) are preserved as blank-line-separated
    blocks, while the hard line wraps *inside* each paragraph — which are just
    layout noise — are collapsed into flowing prose.
    """
    # mark real paragraph boundaries with a sentinel token *before* the tags
    # are stripped — a whitespace marker would get collapsed by the parser, so
    # use a token that survives get_text() intact.
    sentinel = "@@PARA_BREAK@@"
    marked = re.sub(r"(?i)</p\s*>|<br\s*/?>", sentinel, html)
    soup = BeautifulSoup(marked, "lxml")
    text = soup.get_text(separator=" ").replace("\xa0", " ")

    paragraphs = [_clean_inline(p) for p in text.split(sentinel)]
    return "\n\n".join(p for p in paragraphs if p)


def _leading_bold(para_soup, plain: str) -> str:
    """
    Return the paragraph's leading bold text if it sits at the very start,
    else "". The label's bold may be preceded by an empty bold that only wraps
    the <A name> anchor, so skip to the first bold run that actually has text.
    """
    for bold in para_soup.find_all("b"):
        lead = _clean_inline(bold.get_text(" "))
        if lead:
            return lead if plain.startswith(lead[:8]) else ""
    return ""


def _label_colon_pos(para_soup, plain: str) -> int | None:
    """
    If this paragraph opens a new speaker turn via a bold label, return the
    index of the colon that terminates the label; otherwise None.

    A turn opens when the paragraph *starts* with bold text and a colon appears
    within LABEL_MAX_CHARS. The <A name> anchors only cover ~2/3 of turns, so
    this bold-label test — script-agnostic, keyed on the colon — is the primary
    boundary signal; anchors are used only to attach an authoritative ID.
    """
    if not _leading_bold(para_soup, plain):
        return None
    colon = plain.find(":")
    if 0 < colon <= LABEL_MAX_CHARS:
        return colon
    return None


def _anchor_id(para_soup) -> tuple[str | None, str | None]:
    """Return (mpCode, mpPartCode) from an <A name="code*part"> in this para."""
    for a in para_soup.find_all("a"):
        m = ANCHOR_NAME_RE.match(a.get("name", "") or "")
        if m:
            return m.group(1), m.group(2)
    return None, None


def split_by_speaker(html: str, mp_part_detail_list: list[dict]) -> list[dict]:
    """
    Split the transcript into per-intervention segments.

    Boundaries are detected from bold speaker labels (bold text at a paragraph
    start, ending in a colon) rather than <A name> anchors alone, because ~1/3
    of turns carry no anchor and would otherwise be merged into the preceding
    speaker. When an anchor is present it is used to attach mpCode/mpPartCode
    and the canonical name from mpPartDetailList; the label text is the
    fallback identity so anchor-less speakers are never dropped.
    """
    code_to_name = {str(m["mpCode"]): m["mpName"] for m in mp_part_detail_list}
    soup = BeautifulSoup(html, "lxml")

    segments: list[dict] = []
    current: dict | None = None
    # An anchor often sits alone in an otherwise empty <p> —
    # <p><A name="4444*1"></p> — with the speech starting in the next block, so
    # carry it forward to the first paragraph that has text.
    pending_code: str | None = None
    pending_part: str | None = None

    for p in soup.find_all("p"):
        plain = _clean_inline(p.get_text(" "))
        anchor_code, anchor_part = _anchor_id(p)
        if not plain:
            if anchor_code:
                pending_code, pending_part = anchor_code, anchor_part
            continue

        mp_code, mp_part_code = anchor_code, anchor_part
        carried = mp_code is None and pending_code is not None
        if carried:
            mp_code, mp_part_code = pending_code, pending_part
        # A carried anchor is spent on the first paragraph with text, whatever
        # that turns out to be; it must never reach a second one.
        pending_code = pending_part = None

        colon = _label_colon_pos(p, plain)
        # Some anchored labels aren't bold, so with an anchor in hand the colon
        # alone may delimit the label.
        if colon is None and mp_code is not None:
            c = plain.find(":")
            if 0 < c <= LABEL_MAX_CHARS:
                colon = c

        # An anchor is itself definitive proof of a turn start, so open a new
        # turn on either signal — a colon-delimited label or a bare anchor
        # whose label has no colon or has leaked text before the bold name.
        if colon is not None:
            label = STAR_PREFIX_RE.sub("", plain[:colon]).strip()
            body = plain[colon + 1 :].strip()
        elif mp_code is not None:
            # anchor without a clean colon-label: fall back to the bold lead
            # (or canonical name) for the label and keep the rest as body.
            lead = _leading_bold(p, plain) or code_to_name.get(mp_code, "")
            label = STAR_PREFIX_RE.sub("", lead).strip()
            body = plain[len(lead):].strip() if lead and plain.startswith(lead) else plain
        else:
            label = body = None

        rejected = None
        if carried and mp_code and not anchor_agrees_with_label(label, code_to_name.get(mp_code, "")):
            rejected = mp_code
            mp_code = mp_part_code = None
            if colon is None:
                label = body = None  # no label of its own: not a turn after all

        if label is not None:
            current = {
                "mpCode": mp_code,
                "mpPartCode": mp_part_code,
                "speakerLabel": label,
                "mpName": code_to_name.get(mp_code, label) if mp_code else label,
                "paras": [body] if body else [],
            }
            if rejected:
                current["anchorRejected"] = rejected
            segments.append(current)
        else:
            # continuation of the current turn (or unattributed preamble)
            if current is None:
                current = {
                    "mpCode": None,
                    "mpPartCode": None,
                    "speakerLabel": None,
                    "mpName": None,
                    "paras": [],
                }
                segments.append(current)
            current["paras"].append(plain)

    for seg in segments:
        seg["text"] = "\n\n".join(par for par in seg.pop("paras") if par)

    segments = [s for s in segments if s["text"] or s["speakerLabel"]]
    annotate_speakers(segments, mp_part_detail_list)
    reuse_anchors(segments)
    return segments


def speaker_distribution(segments: list[dict]) -> list[dict]:
    """
    Aggregate per-intervention segments into a per-speaker distribution:
    number of interventions, word count, and character count, sorted by
    word count descending.
    """
    stats: dict[str, dict] = {}

    for seg in segments:
        # anchored speakers key on mpCode; anchor-less ones key on their label
        # so they stay distinct instead of collapsing into one bucket.
        key = seg["mpCode"] or seg["speakerLabel"] or "unattributed"
        name = seg["mpName"] or "(unattributed)"
        word_count = len(seg["text"].split())
        char_count = len(seg["text"])

        entry = stats.setdefault(
            key,
            {
                "mpCode": seg["mpCode"],
                "mpName": name,
                # verified = normalised to an MP-list entry (any turn matched).
                "verified": bool(seg["mpCode"]),
                "nameSource": seg.get("nameSource"),
                "interventions": 0,
                "words": 0,
                "chars": 0,
            },
        )
        entry["interventions"] += 1
        entry["words"] += word_count
        entry["chars"] += char_count

    return sorted(stats.values(), key=lambda e: e["words"], reverse=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--loksabha", type=int, required=True, help="Lok Sabha term number, e.g. 18")
    parser.add_argument("--session", type=int, required=True, help="Session number within the term")
    parser.add_argument("--dbslno", type=int, required=True, help="Debate serial number (dbSlno)")
    parser.add_argument("--summary-only", action="store_true", help="Skip printing segment previews")
    args = parser.parse_args()

    data = fetch_debate(args.loksabha, args.session, args.dbslno)
    html = data.get("debateDesc", "")
    if not html:
        print("No debateDesc found for this debate item.", file=sys.stderr)
        sys.exit(1)

    mp_part_detail_list = data.get("mpPartDetailList", [])
    segments = split_by_speaker(html, mp_part_detail_list)

    print(f"Debate date: {data.get('debateDate')}  |  Type: {data.get('debateType')}")
    print(f"Segments found: {len(segments)}")

    # resolution coverage — how many turns we could map to the MP list, by method
    from collections import Counter
    tally = Counter(seg.get("nameSource") for seg in segments if seg.get("speakerLabel"))
    labelled = sum(tally.values())
    resolved = labelled - tally.get("unresolved", 0)
    print(f"Speaker resolution: {resolved}/{labelled} labelled turns matched to MP list")
    for src, n in tally.most_common():
        print(f"    {src or '(none)':14s} {n}")
    print()

    if not args.summary_only:
        for seg in segments:
            speaker = seg["mpName"] or "(unattributed)"
            preview = seg["text"][:200].replace("\n", " ")
            print(f"--- {speaker}  [{seg.get('nameSource')}] ---")
            print(preview + ("..." if len(seg["text"]) > 200 else ""))
            print()

    dist = speaker_distribution(segments)
    print("=== Speaker-wise distribution ===")
    print(f"{'Speaker':40s} {'Interventions':>13s} {'Words':>8s} {'Chars':>8s}")
    for entry in dist:
        print(f"{entry['mpName']:40s} {entry['interventions']:>13d} {entry['words']:>8d} {entry['chars']:>8d}")


if __name__ == "__main__":
    main()
