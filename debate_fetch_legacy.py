"""
Read a legacy-format (LS13) debate and print its speaker distribution.

Usage:
    python3 debate_fetch_legacy.py --loksabha 13 --session 1 --dbslno 6656
"""
import argparse
import re

from bs4 import BeautifulSoup

from debate_fetch import (
    STAR_PREFIX_RE,
    _clean_inline,
    _is_caps_label,
    _label_colon_pos,
    _leading_bold,
    annotate_speakers,
    fetch_debate,
    is_crowd_label,
    is_presiding_label,
    role_code_for_label,
    reuse_anchors,
    speaker_distribution,
)
from legacy_hindi import decode_legacy_hindi

# Modern anchors are "mpCode*partCode" ("3972*1"). Legacy anchors are the bare mpCode ("209").
MODERN_ANCHOR_RE = re.compile(r'<A\s+name="\d+\*\d+"', re.IGNORECASE)
LEGACY_ANCHOR_NAME_RE = re.compile(r"^(\d+)$")

# Hindi legacy-font passages use <h6> instead of <p>.
BLOCK_TAGS = ("p", "h6")

LABEL_MAX_CHARS = 200


def looks_legacy(html: str) -> bool:
    return bool(html) and not MODERN_ANCHOR_RE.search(html)


def _sanitize_legacy_html(html: str) -> str:
    # The source never closes <A>. An open anchor makes lxml nest every later paragraph inside it.
    return re.sub(r'(?i)(<a\s+name="[^"]*")\s*>', r"\1/>", html)


def _anchor_id(para_soup) -> str | None:
    for a in para_soup.find_all("a"):
        m = LEGACY_ANCHOR_NAME_RE.match(a.get("name", "") or "")
        if m:
            return m.group(1)
    return None


def split_by_speaker_legacy(
    html: str, mp_part_detail_list: list[dict], db_roster: list[dict] | None = None
) -> list[dict]:
    code_to_name = {str(m["mpCode"]): m["mpName"] for m in mp_part_detail_list}
    soup = BeautifulSoup(_sanitize_legacy_html(html), "lxml")

    segments: list[dict] = []
    current: dict | None = None
    # An anchor often sits alone in an empty <p>, and the speech starts in the next block.
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
                # No colon label: use the bold lead or the roster name as the label.
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

    # Hindi arrives in a legacy font encoding, for example "<ºÉBÉEä ¤ÉÉ®ä àÉå". Decode it to Unicode.
    for seg in segments:
        seg["text"] = decode_legacy_hindi(seg["text"])
        seg["speakerLabel"] = decode_legacy_hindi(seg["speakerLabel"] or "") or None
        seg["mpName"] = decode_legacy_hindi(seg["mpName"] or "") or None

    # after decoding, so labels compare in the same (Devanagari) script
    for seg in segments:
        if seg.get("mpCode") is not None or seg.get("nameSource") != "unresolved":
            continue
        # Test crowd before presiding, as the recent reader does.
        if is_crowd_label(seg["speakerLabel"]):
            seg["nameSource"] = "crowd"
            seg["mpName"] = seg["speakerLabel"]
            seg["roleCode"] = "members_crowd"
        elif is_presiding_label(seg["speakerLabel"]):
            seg["nameSource"] = "presiding"
            seg["mpName"] = seg["speakerLabel"]
            seg["roleCode"] = role_code_for_label(seg["speakerLabel"])

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
