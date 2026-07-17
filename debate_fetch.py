"""
Fetch a Lok Sabha debate transcript from sansad.in and break it down by speaker.

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
from legacy_hindi import decode_legacy_hindi
from urdu_names import urdu_label_to_name

API_URL = "https://sansad.in/api_ls/debate/debate-details"

# Minimum similarity for two name tokens to match, and the minimum share of roster tokens found in the label.
ANCHOR_TOKEN_MIN = 0.8
ANCHOR_COVERAGE_MIN = 0.6

# Matches the speaker anchors sansad.in embeds in the transcript HTML, e.g.
# <A name="3972*1">  ->  mpCode=3972, mpPartCode=1
ANCHOR_RE = re.compile(r'<A\s+name="(\d+)\*(\d+)"[^>]*>', re.IGNORECASE)

# Anchor `name` attribute as seen by BeautifulSoup, e.g. "3972*1".
ANCHOR_NAME_RE = re.compile(r"^(\d+)\*(\d+)$")

# A label ends at a colon within this many characters. The colon works in English, Hindi and Urdu.
LABEL_MAX_CHARS = 200

# Some labels start with a question marker such as "*57" or "*m25".
STAR_PREFIX_RE = re.compile(r"^\*[a-zA-Z]?\d+\s*")

_PAREN_RE = re.compile(r"\(([^)]*)\)")
_HONORIFICS = {
    "shri", "shrimati", "smt", "sushri", "km", "kumari", "ku", "dr", "prof",
    "adv", "advocate", "mr", "mrs", "ms", "sardar", "sarvashri",
    # to_latin spellings of Devanagari honorifics.
    "shree", "shreemati", "sushree", "kunvar", "kunvara", "do", "pro", "da",
}

# "Sri" is an honorific only at the start of a name. Inside a name it is a real part ("Lavu Sri Krishna").
_LEADING_HONORIFICS = {"sri"}


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
    # A ministerial title keeps the name in brackets, led by an honorific.
    for inside in _PAREN_RE.findall(label):
        head = re.sub(r"[^\w\s]", " ", inside).lower().split()
        # A group that holds only an honorific, as in "Dr. (Smt.) V. Saroja", is not a title.
        if head and head[0] in _HONORIFICS and any(t not in _HONORIFICS for t in head):
            label = inside
            break
    label = _PAREN_RE.sub(" ", label)  # drop remaining (constituency)
    label = re.sub(r"[^\w\s]", " ", label.lower())
    toks = [tok for tok in label.split() if tok and tok not in _HONORIFICS]
    # Test "sri" only after "shri" is gone, so it is judged at the start of the name.
    if toks and toks[0] in _LEADING_HONORIFICS:
        toks = toks[1:]
    return toks


# Honorifics after transliteration and folding (श्री -> "shri"). The cluster rule folds "sardar" to "srdar".
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
    full, _ = _name_parts(name)
    return "".join(sorted(full))


def _name_agreement(label: str, roster_name: str) -> bool | None:
    # None means neither side had a usable word. Callers treat that differently.
    lab_full, lab_initials = _name_parts(label)
    ros_full, _ = _name_parts(roster_name)
    if not ros_full or not (lab_full or lab_initials):
        return None  # nothing usable on one side: no evidence either way

    strong = weak = unexplained = 0
    for r in ros_full:
        if any(SequenceMatcher(None, r, l).ratio() >= ANCHOR_TOKEN_MIN for l in lab_full):
            strong += 1
        elif r[0] in lab_initials:
            weak += 1
        else:
            unexplained += 1

    # An unexplained roster word is a disagreement, so initials no longer count.
    covered = strong if unexplained else strong + weak
    return strong >= 1 and covered / len(ros_full) >= ANCHOR_COVERAGE_MIN


def anchor_contradicts_label(label: str, roster_name: str) -> bool:
    return _name_agreement(label, roster_name) is False


def labels_name_same_person(label_a: str, label_b: str) -> bool:
    return (
        _name_agreement(label_a, label_b) is True
        and _name_agreement(label_b, label_a) is True
    )


def _folded_lookup(mp_part_detail_list: list[dict]) -> dict[str, dict]:
    by_folded: dict[str, dict] = {}
    folded_codes: dict[str, set] = {}
    for m in mp_part_detail_list:
        key = _folded_key(m["mpName"])
        if not key:
            continue
        by_folded.setdefault(key, m)
        folded_codes.setdefault(key, set()).add(m["mpCode"])
    # Drop any key that names more than one person.
    return {k: v for k, v in by_folded.items() if len(folded_codes[k]) == 1}


def build_speaker_index(mp_part_detail_list: list[dict], db_roster: list[dict] | None = None) -> dict:
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

    by_folded = _folded_lookup(mp_part_detail_list)
    by_folded_db = _folded_lookup(db_roster) if db_roster else {}

    return {
        "by_str": by_str,
        "by_join_ordered": by_join_ordered,
        "by_join_sorted": by_join_sorted,
        "tokenised": tokenised,
        "by_folded": by_folded,
        "by_folded_db": by_folded_db,
    }


def resolve_speaker(label: str, index: dict) -> tuple[str | None, dict | None]:
    label = urdu_label_to_name(label) or label
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
    # Count people, not entries, because one entry can appear twice.
    codes = {m["mpCode"] for m in cands.values()}
    if len(codes) == 1:
        return "name-partial", next(iter(cands.values()))

    # Decode legacy-font labels first. Decoding already decoded text changes nothing.
    decoded_label = decode_legacy_hindi(label)
    key = _folded_key(decoded_label)
    if key and (m := index["by_folded"].get(key)):
        return "name-translit", m

    # Last resort: the wider database roster.
    if key and (m := index["by_folded_db"].get(key)):
        return "name-db", m

    return None, None


_PRESIDING_RE = re.compile(
    # "deputy" matches only next to "speaker", so "Deputy Minister" is not caught.
    r"\bspeaker\b|\bchair(?:man|person)\b|deputy[-\s]*speaker"
    # Devanagari: अध्यक्ष and उपाध्यक्ष both contain ध्यक्ष.
    r"|ध्यक्ष|सभापति",
    re.IGNORECASE,
)


def is_presiding_label(label: str) -> bool:
    if not label:
        return False
    return bool(_PRESIDING_RE.search(label))


_CROWD_RE = re.compile(
    # "SEVERAL HON. MEMBERS". The loose separator also accepts "HON'BLE" and "HON . MEMBERS".
    r"\b(?:several|some|many)\b[\s.'’A-Za-z]*\bmembers\b"
    r"|(?:अनेक|कई|कुछ)\s*माननीय\s*सदस्य",
    re.IGNORECASE,
)


def is_crowd_label(label: str) -> bool:
    if not label:
        return False
    return bool(_CROWD_RE.search(label))


# Order matters: each deputy title contains its principal title, so test the deputy first.
_ROLE_CODES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("deputy_chairman", re.compile(r"deputy[-\s]*chair(?:man|person)", re.IGNORECASE)),
    ("deputy_speaker", re.compile(r"deputy[-\s]*speaker|उपाध्यक्ष", re.IGNORECASE)),
    ("chairman", re.compile(r"chair(?:man|person)|सभापति", re.IGNORECASE)),
    ("speaker", re.compile(r"\bspeaker\b|अध्यक्ष", re.IGNORECASE)),
)


def role_code_for_label(label: str) -> str | None:
    """Map a speaker label to a canonical `speaker_roles.code`, or None.

    Returns one of the office slugs seeded in db/init/06-speaker-roles.sql --
    'speaker', 'deputy_speaker', 'chairman', 'members_crowd' -- so a turn that
    names no person still records WHICH non-person it named.

    The corpus prints 143 distinct role spellings, but they are 3 offices plus
    spacing/punctuation/typo noise. We search for the office word instead of
    matching whole strings, which absorbs "MR.SPEAKER", "HON . SPEAKER",
    "M R . CHAIRMAN", the "*m75 " index-marker prefix and the "DEPUPTY" typo
    without a rule per variant. The Devanagari forms are the same three
    offices, not extra ones.

    Args:
        label: the raw speaker label as printed in the transcript.
    """
    if not label:
        return None
    if is_crowd_label(label):
        return "members_crowd"
    for code, pattern in _ROLE_CODES:
        if pattern.search(label):
            return code
    return None


def annotate_speakers(
    segments: list[dict], mp_part_detail_list: list[dict], db_roster: list[dict] | None = None
) -> list[dict]:
    index = build_speaker_index(mp_part_detail_list, db_roster)
    for seg in segments:
        if seg.get("mpCode"):
            seg["nameSource"] = "anchor"
            continue
        if not seg.get("speakerLabel"):
            seg["nameSource"] = None
            continue
        # Test crowd before presiding, so the two categories stay disjoint.
        if is_crowd_label(seg["speakerLabel"]):
            seg["nameSource"] = "crowd"
            seg["mpName"] = seg["speakerLabel"]
            seg["roleCode"] = "members_crowd"
            continue
        if is_presiding_label(seg["speakerLabel"]):
            seg["nameSource"] = "presiding"
            seg["mpName"] = seg["speakerLabel"]
            seg["roleCode"] = role_code_for_label(seg["speakerLabel"])
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
    resolved: dict[str, tuple[str, str]] = {}
    ambiguous: set[str] = set()
    for seg in segments:
        code, label = seg.get("mpCode"), seg.get("speakerLabel")
        if not code or not label:
            continue
        # A name-db match is not evidence from this debate. This pass may correct it.
        if seg.get("nameSource") == "name-db":
            continue
        prior = resolved.get(label)
        if prior and prior[0] != code:
            ambiguous.add(label)
        resolved.setdefault(label, (code, seg.get("mpName") or label))

    for seg in segments:
        if not seg.get("speakerLabel"):
            continue
        # A name-db turn is reconsidered here. Every other tier keeps its answer.
        if seg.get("mpCode") and seg.get("nameSource") != "name-db":
            continue
        if seg.get("nameSource") == "presiding":
            continue
        label = seg["speakerLabel"]
        for anchored_label, (code, name) in resolved.items():
            if anchored_label in ambiguous:
                continue
            if labels_name_same_person(label, anchored_label):
                seg["mpCode"] = code
                seg["mpName"] = name
                seg["nameSource"] = "anchor-reuse"
                break
    return segments


def _clean_inline(text: str) -> str:
    text = re.sub(r"\s+", " ", text.replace("\xa0", " "))
    text = re.sub(r"\s+([।?!,.;:])", r"\1", text)
    return text.strip()


def fetch_debate(loksabha: int, session: int, db_slno: int) -> dict:
    params = {
        "loksabha": loksabha,
        "sessionNumber": session,
        "dbSlNo": db_slno,
    }
    resp = requests.get(API_URL, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def load_debate(loksabha: int, session: int, db_slno: int, source: str = "auto") -> dict:
    if source not in ("db", "api", "auto"):
        raise ValueError(f"source must be 'db', 'api' or 'auto', not {source!r}")

    if source == "api":
        return fetch_debate(loksabha, session, db_slno)

    try:
        from debate_store import load_debate as load_from_corpus

        payload = load_from_corpus(loksabha, session, db_slno)
    except Exception:
        if source == "db":
            raise
        payload = None  # In "auto" mode a database error falls back to the API.

    if payload is not None:
        return payload
    if source == "db":
        raise LookupError(
            f"debate {loksabha}/{session}/{db_slno} is not in the corpus "
            f"(use --source auto to fall back to the API)"
        )
    return fetch_debate(loksabha, session, db_slno)


def html_to_clean_text(html: str) -> str:
    # Whitespace would collapse in get_text(), so mark paragraph breaks with a token.
    sentinel = "@@PARA_BREAK@@"
    marked = re.sub(r"(?i)</p\s*>|<br\s*/?>", sentinel, html)
    soup = BeautifulSoup(marked, "lxml")
    text = soup.get_text(separator=" ").replace("\xa0", " ")

    paragraphs = [_clean_inline(p) for p in text.split(sentinel)]
    return "\n\n".join(p for p in paragraphs if p)


def _leading_bold(para_soup, plain: str) -> str:
    for bold in para_soup.find_all("b"):
        lead = _clean_inline(bold.get_text(" "))
        if lead:
            return lead if plain.startswith(lead[:8]) else ""
    return ""


def _is_caps_label(text: str) -> bool:
    return bool(re.search(r"[A-Za-z]", text)) and not re.search(r"[a-z]", text)


def _label_colon_pos(para_soup, plain: str) -> int | None:
    colon = plain.find(":")
    if not (0 < colon <= LABEL_MAX_CHARS):
        return None
    if _leading_bold(para_soup, plain):
        return colon
    if _is_caps_label(plain[:colon]):
        return colon
    return None


def _anchor_id(para_soup) -> tuple[str | None, str | None]:
    for a in para_soup.find_all("a"):
        m = ANCHOR_NAME_RE.match(a.get("name", "") or "")
        if m:
            return m.group(1), m.group(2)
    return None, None


def split_by_speaker(
    html: str, mp_part_detail_list: list[dict], db_roster: list[dict] | None = None
) -> list[dict]:
    code_to_name = {str(m["mpCode"]): m["mpName"] for m in mp_part_detail_list}
    soup = BeautifulSoup(html, "lxml")

    segments: list[dict] = []
    current: dict | None = None
    # An anchor often sits alone in an empty <p>, and the speech starts in the next block.
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
        # A carried anchor applies to one paragraph only.
        pending_code = pending_part = None

        colon = _label_colon_pos(p, plain)
        # Some anchored labels are not bold, so the colon alone ends the label.
        if colon is None and mp_code is not None:
            c = plain.find(":")
            if 0 < c <= LABEL_MAX_CHARS:
                colon = c

        # An anchor alone also starts a turn.
        if colon is not None:
            label = STAR_PREFIX_RE.sub("", plain[:colon]).strip()
            body = plain[colon + 1 :].strip()
        elif mp_code is not None:
            # No colon label: use the bold lead or the roster name.
            lead = _leading_bold(p, plain) or code_to_name.get(mp_code, "")
            label = STAR_PREFIX_RE.sub("", lead).strip()
            body = plain[len(lead):].strip() if lead and plain.startswith(lead) else plain
        else:
            label = body = None

        rejected = None
        if carried and mp_code and anchor_contradicts_label(label, code_to_name.get(mp_code, "")):
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
            # A continuation of the current turn, or an unattributed preamble.
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
    reuse_anchors(segments)
    return segments


def speaker_distribution(segments: list[dict]) -> list[dict]:
    stats: dict[str, dict] = {}

    for seg in segments:
        # Speakers without a code key on their label.
        key = seg["mpCode"] or seg["speakerLabel"] or "unattributed"
        name = seg["mpName"] or "(unattributed)"
        word_count = len(seg["text"].split())
        char_count = len(seg["text"])

        entry = stats.setdefault(
            key,
            {
                "mpCode": seg["mpCode"],
                "mpName": name,
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
    parser.add_argument(
        "--source",
        choices=("auto", "db", "api"),
        default="auto",
        help="Where to read the debate from: the corpus, the API, or corpus-then-API (default)",
    )
    args = parser.parse_args()

    data = load_debate(args.loksabha, args.session, args.dbslno, source=args.source)
    html = data.get("debateDesc", "")
    if not html:
        print("No debateDesc found for this debate item.", file=sys.stderr)
        sys.exit(1)

    mp_part_detail_list = data.get("mpPartDetailList", [])
    from db_roster import load_db_roster

    db_roster = load_db_roster(args.loksabha)
    segments = split_by_speaker(html, mp_part_detail_list, db_roster)

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
