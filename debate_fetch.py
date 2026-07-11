"""
Step 1: fetch a Lok Sabha debate transcript from sansad.in, clean it into
plain text, and break it down by speaker.

Usage:
    python3 debate_fetch.py --loksabha 18 --session 3 --dbslno 1758
"""
import argparse
import re
import sys

import requests
from bs4 import BeautifulSoup

API_URL = "https://sansad.in/api_ls/debate/debate-details"

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
        if head and head[0] in _HONORIFICS:
            label = inside
            break
    label = _PAREN_RE.sub(" ", label)  # drop remaining (constituency)
    label = re.sub(r"[^\w\s]", " ", label.lower())
    return [tok for tok in label.split() if tok and tok not in _HONORIFICS]


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
    return {
        "by_str": by_str,
        "by_join_ordered": by_join_ordered,
        "by_join_sorted": by_join_sorted,
        "tokenised": tokenised,
    }


def resolve_speaker(label: str, index: dict) -> tuple[str | None, dict | None]:
    """
    Try to match a raw speaker label to an MP list entry.

    Returns (nameSource, entry). nameSource is one of "name-exact",
    "name-join" (matches once spacing/word-order is ignored), "name-partial"
    (one entry's tokens are a subset of the other's), or None when unmatched.
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
        if tset and (tset <= s or s <= tset)
    }
    # unique *person* (mpCode), guarding against a single entry appearing twice
    codes = {m["mpCode"] for m in cands.values()}
    if len(codes) == 1:
        return "name-partial", next(iter(cands.values()))
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

    for p in soup.find_all("p"):
        plain = _clean_inline(p.get_text(" "))
        if not plain:
            continue

        colon = _label_colon_pos(p, plain)
        mp_code, mp_part_code = _anchor_id(p)
        # An anchor is itself definitive proof of a turn start, so open a new
        # turn on either signal — this recovers the handful of anchored turns
        # whose label has no colon or has leaked text before the bold name.
        if colon is not None or mp_code is not None:
            if colon is not None:
                label = STAR_PREFIX_RE.sub("", plain[:colon]).strip()
                body = plain[colon + 1 :].strip()
            else:
                # anchor without a clean colon-label: fall back to the bold lead
                # (or canonical name) for the label and keep the rest as body.
                lead = _leading_bold(p, plain) or code_to_name.get(mp_code, "")
                label = STAR_PREFIX_RE.sub("", lead).strip()
                body = plain[len(lead):].strip() if lead and plain.startswith(lead) else plain
            current = {
                "mpCode": mp_code,
                "mpPartCode": mp_part_code,
                "speakerLabel": label,
                "mpName": code_to_name.get(mp_code, label) if mp_code else label,
                "paras": [body] if body else [],
            }
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
