"""
Parser for the *legacy* sansad.in transcript format used by older debates
(observed on LS13, 1999) — a plain, pre-Word-export HTML era that breaks
every assumption debate_fetch.py's split_by_speaker() makes:

  - Speaker anchors carry no partCode: <A name="209"> instead of
    <A name="209*1">, so debate_fetch.ANCHOR_NAME_RE never matches and every
    anchor is silently invisible.
  - Most speaker labels carry no <b> bold markup at all, so the bold-colon
    signal that carries ~1/3 of modern turns never fires here either.
  - <p> (and, in Hindi passages, <h6>) tags are never explicitly closed, and
    neither is <A name="...">. Usually the parser recovers fine, but when
    nothing forces the dangling <a> closed before the next unclosed <p>,
    lxml adopts every following paragraph as a descendant of that one <a> —
    collapsing dozens of turns into a single blob, and — because
    find_all("p") returns nested matches too — duplicating that text in the
    output. Confirmed on LS13/session1/dbSlNo=6656: the entire debate after
    the second speaker collapses into one unattributed segment with parts of
    the speech duplicated 2-3x.

With none of the modern signals reliable, this module adds one new one
(ALL-CAPS label detection) and neutralises the unclosed-anchor landmine
before parsing, rather than hoping lxml's tag-soup recovery guesses right.

Usage:
    python3 debate_fetch_legacy.py --loksabha 13 --session 1 --dbslno 6656
"""
import argparse
import re

from bs4 import BeautifulSoup

from debate_fetch import (
    STAR_PREFIX_RE,
    _clean_inline,
    _leading_bold,
    annotate_speakers,
    fetch_debate,
    is_presiding_label,
    reuse_anchors,
    speaker_distribution,
)
from legacy_hindi import decode_legacy_hindi

# Modern anchors are "mpCode*partCode" (e.g. "3972*1"); legacy anchors carry
# no partCode at all (e.g. "209").
MODERN_ANCHOR_RE = re.compile(r'<A\s+name="\d+\*\d+"', re.IGNORECASE)
LEGACY_ANCHOR_NAME_RE = re.compile(r"^(\d+)$")

# Legacy transcripts wrap running text in <p>, and — in Hindi legacy-font
# passages specifically — in <h6> instead.
BLOCK_TAGS = ("p", "h6")

LABEL_MAX_CHARS = 200


def looks_legacy(html: str) -> bool:
    """
    True if `html` is the older, partCode-less anchor format this module
    handles, rather than the modern "mpCode*partCode" format.
    """
    return bool(html) and not MODERN_ANCHOR_RE.search(html)


def _sanitize_legacy_html(html: str) -> str:
    """
    Self-close every <A name="..."> anchor before parsing.

    The source never emits a closing </A>; in practice a following tag
    (often </font>) forces lxml to pop it anyway, but that's incidental to
    the surrounding markup, not guaranteed. When nothing closes it in time,
    the anchor stays open across the rest of the document and silently
    swallows every subsequent paragraph as its descendant. Self-closing here
    removes the landmine outright instead of relying on lxml's tag-soup
    recovery to guess correctly.
    """
    return re.sub(r'(?i)(<a\s+name="[^"]*")\s*>', r"\1/>", html)


def _is_caps_label(text: str) -> bool:
    """
    True if `text` reads as an old-style speaker label rather than a normal
    sentence: legacy transcripts print speaker names and designations
    entirely in capitals ("MR. SPEAKER", "SHRI RUPCHAND PAL (HOOGHLY)"), so
    the absence of any lowercase ASCII letter is a strong, cheap signal.
    Requires at least one letter so bare punctuation doesn't count.
    """
    return bool(re.search(r"[A-Za-z]", text)) and not re.search(r"[a-z]", text)


def _label_colon_pos(para_soup, plain: str) -> int | None:
    """
    Return the index of the colon ending a speaker label, or None.

    Two independent signals open a turn (either is sufficient), mirroring
    debate_fetch's bold-colon test but adding the ALL-CAPS test because most
    legacy labels carry no bold markup at all:
      - bold text at the very start of the paragraph (works when present —
        observed on some but not all legacy debates), or
      - the text up to the colon has no lowercase letters.
    """
    colon = plain.find(":")
    if not (0 < colon <= LABEL_MAX_CHARS):
        return None
    if _leading_bold(para_soup, plain):
        return colon
    if _is_caps_label(plain[:colon]):
        return colon
    return None


def _anchor_id(para_soup) -> str | None:
    """Return the mpCode from a legacy <A name="mpCode"> in this block, if any."""
    for a in para_soup.find_all("a"):
        m = LEGACY_ANCHOR_NAME_RE.match(a.get("name", "") or "")
        if m:
            return m.group(1)
    return None


def split_by_speaker_legacy(
    html: str, mp_part_detail_list: list[dict], db_roster: list[dict] | None = None
) -> list[dict]:
    """
    Split a legacy-format transcript into per-intervention segments.

    Structurally the same walk as debate_fetch.split_by_speaker (open a new
    turn on a label-colon or an anchor, otherwise glue the block onto the
    current turn), but over <p>+<h6> blocks, a partCode-less anchor, and the
    bold-or-ALL-CAPS label test above. `db_roster`, when given, backs the
    last-resort "name-db" tier in `annotate_speakers` -- legacy debates are
    exactly where mpPartDetailList is thinnest, so this tier matters most here.
    """
    code_to_name = {str(m["mpCode"]): m["mpName"] for m in mp_part_detail_list}
    soup = BeautifulSoup(_sanitize_legacy_html(html), "lxml")

    segments: list[dict] = []
    current: dict | None = None
    # An anchor's <p> is often otherwise empty -- <p><A name="499"></p> with
    # the actual speech starting in the *next* block -- so an anchor found on
    # a text-less block must be carried forward rather than dropped by the
    # `if not plain` skip below.
    pending_mp_code: str | None = None

    for p in soup.find_all(BLOCK_TAGS):
        plain = _clean_inline(p.get_text(" "))
        anchor_here = _anchor_id(p)
        if not plain:
            if anchor_here:
                pending_mp_code = anchor_here
            continue

        colon = _label_colon_pos(p, plain)
        mp_code = anchor_here or pending_mp_code
        pending_mp_code = None

        if colon is not None and STAR_PREFIX_RE.sub("", plain[:colon]).strip().rstrip(":").lower() == "title":
            # document title line ("Title: <debate title>"), not a speaker turn
            continue

        if colon is not None or mp_code is not None:
            if colon is not None:
                label = STAR_PREFIX_RE.sub("", plain[:colon]).strip()
                body = plain[colon + 1 :].strip()
            else:
                # anchor without a clean colon-label: fall back to the bold
                # lead (or canonical name) for the label, rest is the body.
                lead = _leading_bold(p, plain) or code_to_name.get(mp_code, "")
                label = STAR_PREFIX_RE.sub("", lead).strip()
                body = plain[len(lead):].strip() if lead and plain.startswith(lead) else plain
            current = {
                "mpCode": mp_code,
                "mpPartCode": None,  # legacy anchors don't carry a partCode
                "speakerLabel": label,
                "mpName": code_to_name.get(mp_code, label) if mp_code else label,
                "paras": [body] if body else [],
            }
            segments.append(current)
        else:
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
    annotate_speakers(segments, mp_part_detail_list, db_roster)

    # Legacy transcripts carry their Hindi in a pre-Unicode CDAC-GIST/ISFOC font
    # encoding (see legacy_hindi.py), so the extracted text is glyph "gibberish"
    # like "<ºÉBÉEä ¤ÉÉ®ä àÉå". Decode it to real Devanagari now that the blocks are
    # plain text — decoding is a no-op on already-clean English/Unicode, and
    # Latin runs (English speech, roster names) pass through untouched.
    for seg in segments:
        seg["text"] = decode_legacy_hindi(seg["text"])
        seg["speakerLabel"] = decode_legacy_hindi(seg["speakerLabel"] or "") or None
        seg["mpName"] = decode_legacy_hindi(seg["mpName"] or "") or None

    # after decoding, so labels compare in the same (Devanagari) script
    for seg in segments:
        if (
            seg.get("mpCode") is None
            and seg.get("nameSource") == "unresolved"
            and is_presiding_label(seg["speakerLabel"])
        ):
            seg["nameSource"] = "presiding"
            seg["mpName"] = seg["speakerLabel"]

    reuse_anchors(segments)
    return segments


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--loksabha", type=int, required=True)
    parser.add_argument("--session", type=int, required=True)
    parser.add_argument("--dbslno", type=int, required=True)
    parser.add_argument("--summary-only", action="store_true")
    args = parser.parse_args()

    data = fetch_debate(args.loksabha, args.session, args.dbslno)
    html = data.get("debateDesc", "")
    if not html:
        print("No debateDesc found for this debate item.")
        return

    print(f"Format: {'legacy' if looks_legacy(html) else 'modern'}")
    mp_part_detail_list = data.get("mpPartDetailList", [])
    from db_roster import load_db_roster

    db_roster = load_db_roster(args.loksabha)
    segments = split_by_speaker_legacy(html, mp_part_detail_list, db_roster)

    print(f"Debate date: {data.get('debateDate')}  |  Type: {data.get('debateType')}")
    print(f"Segments found: {len(segments)}")

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
