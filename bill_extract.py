"""Find the bill or bills that the House considered in a government-bill debate.

The module builds the input text of one debate, checks a model answer against that text, and stores the
answer in the tables bills, bill_extractions, and debate_bills (db/init/07-bills.sql).
scripts/extract_bills.py asks the model.

The rules that the checks keep:
- The model copies each bill name from the input. A name that is not in the input is not kept.
- The year comes from the text near the name, never from the debate date.
- Two bills with a different year never share a bill_key.
- A bill does not continue into a new Lok Sabha. The stored bill_key ends with the term, so two terms never share a bills row.
- Only a bill that the House considers in the debate ('moved') keeps a summary.
"""
from __future__ import annotations

import hashlib
import json
import re

from sqlalchemy import text

from llm import model_id
from text_match import norm

BILL_TYPES = ("GOVERNMENT BILLS", "STATUTORY RESOLUTION AND GOVERNMENT BILL")

MIN_SPEECHES = 5        # the start of the debate holds at least this many speeches
MIN_WORDS = 1200        # or more speeches, until it holds this many words
MAX_WORDS = 4000        # the start of the debate stops at this word
LAST_TURNS = 2          # the last turns often say "The Bill was passed"
YEAR_WINDOW = 12        # the year can be this many characters after the printed name

ROLES = ("moved", "mentioned")
OUTCOMES = ("passed", "not passed", "introduced", "withdrawn", "unknown")

SCHEMA = {
    "type": "object",
    "properties": {
        "bills": {"type": "array", "items": {
            "type": "object",
            "properties": {
                "printed": {"type": "string"},
                "name": {"type": "string"},
                "year": {"type": ["integer", "null"]},
                "amendment_ordinal": {"type": ["string", "null"]},
                "quote": {"type": "string"},
                "role": {"type": "string", "enum": list(ROLES)},
                "summary": {"type": ["string", "null"]},
            },
            "required": ["printed", "name", "year", "amendment_ordinal", "quote", "role", "summary"],
        }},
        "outcome": {"type": "string", "enum": list(OUTCOMES)},
        "outcome_quote": {"type": ["string", "null"]},
        "none_reason": {"type": ["string", "null"]},
    },
    "required": ["bills", "outcome", "outcome_quote", "none_reason"],
}


# ---------------------------------------------------------------- the input

def fetch_debate(conn, loksabha: int, session: int, dbslno: int) -> dict | None:
    """Returns the debate with its turns in order, or None when the debate is not in the database."""
    row = conn.execute(text("""
        SELECT id, loksabha, session, dbslno, title, debate_type, debate_date, source_url
        FROM debates WHERE loksabha = :ls AND session = :s AND dbslno = :d
    """), {"ls": loksabha, "s": session, "d": dbslno}).mappings().first()
    if row is None:
        return None
    turns = conn.execute(text("""
        SELECT t.seq, coalesce(p.name, t.speaker_label) AS label, t.text, t.speech_id
        FROM turns t LEFT JOIN persons p ON p.id = t.person_id
        WHERE t.debate_id = :id ORDER BY t.seq
    """), {"id": row["id"]}).mappings().all()
    debate = {k: row[k] for k in ("loksabha", "session", "dbslno", "title", "debate_type", "source_url")}
    debate["debate_date"] = row["debate_date"].isoformat() if row["debate_date"] else None
    debate["turns"] = [dict(t) for t in turns]
    return debate


def speech_ends(turns: list[dict]) -> list[int]:
    """The seq of the last turn of each speech, in the order in which the speeches start."""
    first: dict[int, int] = {}
    last: dict[int, int] = {}
    for t in turns:
        sid = t["speech_id"]
        if sid is None:
            continue
        first.setdefault(sid, t["seq"])
        last[sid] = t["seq"]
    return [last[sid] for sid in sorted(first, key=first.get)]


def select_turns(turns: list[dict]) -> tuple[list[dict], list[dict]]:
    """Returns (the start of the debate, the last turns that the start does not hold).

    The start holds the first MIN_SPEECHES speeches, with every chair turn and interruption between them.
    If they hold less than MIN_WORDS words, the start takes the next speeches one by one. The start stops
    at word MAX_WORDS, and the turn at that point is cut.
    """
    ends = speech_ends(turns)
    target = ends[min(MIN_SPEECHES, len(ends)) - 1] if ends else -1
    start: list[dict] = []
    words = 0
    for t in turns:
        if t["seq"] > target:
            if words >= MIN_WORDS:
                break
            later = [e for e in ends if e >= t["seq"]]
            target = min(later) if later else t["seq"]   # no speech left: one turn at a time
        tokens = t["text"].split()
        room = MAX_WORDS - words
        if len(tokens) > room:
            start.append({**t, "text": " ".join(tokens[:room]), "cut": True})
            words = MAX_WORDS
            break
        start.append(t)
        words += len(tokens)
    taken = {t["seq"] for t in start}
    last = [t for t in turns[-LAST_TURNS:] if t["seq"] not in taken]
    return start, last


def one_line(value: str | None) -> str:
    return " ".join((value or "").split())


def turn_text(t: dict) -> str:
    body = " ".join(t["text"].split())
    return f"{t['label'] or '(no name)'}: {body}{' [the text is cut here]' if t.get('cut') else ''}"


def input_text(debate: dict) -> str:
    """The text that the model reads for one debate. The hash of this text goes into bill_extractions."""
    start, last = select_turns(debate["turns"])
    out = [f"Title: {one_line(debate['title']) or '(no title)'}",
           f"Type: {debate['debate_type']}",
           f"Date: {debate['debate_date']}",
           "", "Start of the debate:", ""]
    out += [turn_text(t) for t in start] or ["(no text)"]
    if last:
        out += ["", "[Some turns are left out here.]", "", "End of the debate:", ""]
        out += [turn_text(t) for t in last]
    return "\n".join(out) + "\n"


def build_input(conn, debate: tuple[int, int, int]) -> dict | None:
    """Returns the debate key, its input text, and the hash of the text. None when the debate is not found."""
    found = fetch_debate(conn, *debate)
    if found is None:
        return None
    body = input_text(found)
    return {"loksabha": found["loksabha"], "session": found["session"], "dbslno": found["dbslno"],
            "title": one_line(found["title"]), "debate_date": found["debate_date"],
            "source_url": found["source_url"], "input": body, "input_sha256": sha256(body)}


def sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------- the checks

def bill_key(name: str, year: int) -> str:
    """The name in lower case with only letters and digits, then '-', then the year. A leading 'The' goes."""
    name = re.sub(r"^\s*the\s+", "", name or "", flags=re.IGNORECASE)
    return "".join(ch for ch in norm(name) if ch.isalnum()) + f"-{year}"


def term_key(key: str, loksabha: int) -> str:
    """The stored key of a bill: the bill_key, then '-ls', then the Lok Sabha number of its debate."""
    return f"{key}-ls{loksabha}"


def year_near(year, printed: str, body: str) -> bool:
    """True when the year is inside the printed name, or in the YEAR_WINDOW characters after one copy of it."""
    if not isinstance(year, int) or not 1800 <= year <= 2100:
        return False
    year_text = str(year)
    if re.search(rf"(?<!\d){year_text}(?!\d)", printed):
        return True
    printed_norm, body_norm = norm(printed), norm(body)
    if not printed_norm:
        return False
    i = body_norm.find(printed_norm)
    while i >= 0:
        after = body_norm[i + len(printed_norm): i + len(printed_norm) + YEAR_WINDOW]
        if re.search(rf"(?<!\d){year_text}(?!\d)", after):
            return True
        i = body_norm.find(printed_norm, i + 1)
    return False


# The text between "Constitution (" and "Amendment", for example "One Hundred and Twenty-Third" in
# "Constitution (One Hundred and Twenty-Third Amendment) Bill" or "Constitution (104 th) Amendment Bill".
# "Constitution (Scheduled Castes) Order (Amendment) Bill" does not match: it amends an order, not the Constitution.
_AMENDMENT = re.compile(r"constitution\w*\s*\(\s*([^()]*?)\s*\)?\s*amendment\b", re.IGNORECASE)

def _number_words() -> dict[str, int]:
    """The value of each cardinal and ordinal number word below one hundred, for example 'four' and 'fourth' give 4."""
    units = zip("one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen "
                "seventeen eighteen nineteen".split(),
                "first second third fourth fifth sixth seventh eighth ninth tenth eleventh twelfth thirteenth "
                "fourteenth fifteenth sixteenth seventeenth eighteenth nineteenth".split())
    tens = zip("twenty thirty forty fifty sixty seventy eighty ninety".split(),
               "twentieth thirtieth fortieth fiftieth sixtieth seventieth eightieth ninetieth".split())
    out = {}
    for value, (cardinal, ordinal) in enumerate(units, 1):
        out[cardinal] = out[ordinal] = value
    for value, (cardinal, ordinal) in enumerate(tens, 2):
        out[cardinal] = out[ordinal] = value * 10
    return out


_NUMBER_WORDS = _number_words()


def ordinal_number(value: str | None) -> int | None:
    """The number of an ordinal in words or digits: 'one hundred and fourth' and '104 th' give 104."""
    cleaned = norm(value).replace("-", " ")
    digits = re.fullmatch(r"(\d+)\s*(st|nd|rd|th)?", cleaned)
    if digits:
        return int(digits.group(1))
    total = 0
    for word in cleaned.split():
        if word == "and":
            continue
        if word in ("hundred", "hundredth"):
            total = (total or 1) * 100
        elif word in _NUMBER_WORDS:
            total += _NUMBER_WORDS[word]
        else:
            return None
    return total or None


def amendment_number_text(printed: str) -> str | None:
    """The number text of a numbered Constitution amendment in the printed name, or None."""
    m = _AMENDMENT.search(printed or "")
    return m.group(1).strip() if m and m.group(1).strip() else None


def check_bill(bill: dict, body: str) -> tuple[dict, list[str]]:
    """Checks one bill of the answer against the input text. Returns the clean bill and the failed checks."""
    body_norm = norm(body)
    printed = (bill.get("printed") or "").strip()
    name = (bill.get("name") or "").strip()
    quote = (bill.get("quote") or "").strip()
    role = bill.get("role")
    ordinal = bill.get("amendment_ordinal")
    ordinal = norm(ordinal) or None
    summary = (bill.get("summary") or "").strip() or None
    failed = []
    name_found = bool(norm(printed)) and norm(printed) in body_norm
    if not name_found:
        failed.append("name")
    if not name or not year_near(bill.get("year"), printed, body):
        failed.append("year")
    # A numbered Constitution amendment needs the same number in the printed name and in the answer.
    # Any other bill keeps no ordinal.
    number_text = amendment_number_text(printed)
    if number_text is None:
        ordinal = None
    elif ordinal is None or (answered := ordinal_number(ordinal)) is None or answered != ordinal_number(number_text):
        failed.append("ordinal")
    if not quote or norm(quote) not in body_norm or norm(printed) not in norm(quote):
        failed.append("quote")
    if role not in ROLES:
        failed.append("role")
    if role != "moved":
        summary = None
    return {"printed": printed, "name": name, "year": bill.get("year"), "amendment_ordinal": ordinal,
            "quote": quote, "role": role if role in ROLES else None, "summary": summary,
            "name_found": name_found}, failed


def check_answer(answer: dict, body: str) -> tuple[list[dict], list[str]]:
    """Checks every bill of an answer. Returns the bills, each with checks_failed, kept and bill_key, and the warnings."""
    warnings: list[str] = []
    if answer.get("outcome") not in OUTCOMES:
        warnings.append(f"unknown outcome {answer.get('outcome')!r}")
    out: list[dict] = []
    seen: set[str] = set()
    for raw in answer.get("bills") or []:
        clean, failed = check_bill(raw, body)
        if raw.get("summary") and clean["summary"] is None and clean["role"] == "mentioned":
            warnings.append(f"summary of the mentioned bill {clean['printed']!r} removed")
        key = bill_key(clean["name"], clean["year"]) if not failed else None
        if key is not None and key in seen:
            warnings.append(f"double bill dropped: {clean['printed']!r}")
            continue
        if key is not None:
            seen.add(key)
        for f in failed:
            warnings.append(f"{clean['printed'] or '(no name)'!r}: the {f} check failed")
        # A mentioned bill passes the checks but is not kept. The decision model can keep it later.
        out.append({**clean, "checks_failed": failed, "kept": not failed and clean["role"] == "moved",
                    "bill_key": key})
    if not any(b["kept"] for b in out):
        warnings.append("no kept bill")
    return out, warnings


# ---------------------------------------------------------------- the store

def bill_id(conn, bill: dict, loksabha: int) -> int:
    """The id of the bills row of this bill in this Lok Sabha. A new row is made when there is none."""
    key = term_key(bill["bill_key"], loksabha)
    conn.execute(text("""
        INSERT INTO bills (name, year, loksabha, bill_key, amendment_ordinal) VALUES (:n, :y, :ls, :k, :o)
        ON CONFLICT (bill_key) DO NOTHING
    """), {"n": bill["name"], "y": bill["year"], "ls": loksabha, "k": key, "o": bill["amendment_ordinal"]})
    return conn.execute(text("SELECT id FROM bills WHERE bill_key = :k"), {"k": key}).scalar()


def check_and_store(conn, debate: dict, answer: dict, model: str, prompt_version: str,
                    tokens: dict | None = None, replace: bool = False) -> tuple[list[dict], list[str]]:
    """Checks the answer for one debate and stores it. debate is the result of build_input.

    A debate that has a row is replaced only when replace is true. Otherwise the call raises ValueError.
    """
    key = {"ls": debate["loksabha"], "s": debate["session"], "d": debate["dbslno"]}
    old = conn.execute(text("""
        SELECT id FROM bill_extractions WHERE loksabha = :ls AND session = :s AND dbslno = :d
    """), key).scalar()
    if old is not None:
        if not replace:
            raise ValueError(f"LS{debate['loksabha']}-{debate['session']}-{debate['dbslno']} has an extraction")
        conn.execute(text("DELETE FROM bill_extractions WHERE id = :id"), {"id": old})
    bills, warnings = check_answer(answer, debate["input"])
    ext = conn.execute(text("""
        INSERT INTO bill_extractions (loksabha, session, dbslno, model_id, prompt_version, input_sha256,
                                      raw, warnings, tokens)
        VALUES (:ls, :s, :d, :m, :v, :h, CAST(:raw AS jsonb), :w, CAST(:t AS jsonb))
        RETURNING id
    """), {**key, "m": model_id(conn, model), "v": prompt_version, "h": debate["input_sha256"],
           "raw": json.dumps(answer, ensure_ascii=False), "w": warnings,
           "t": json.dumps(tokens or {})}).scalar()
    rows = [{**key, "e": ext, "pos": pos, "bid": bill_id(conn, bill, debate["loksabha"]) if bill["kept"] else None,
             "printed": bill["printed"], "quote": bill["quote"], "role": bill["role"], "summary": bill["summary"],
             "failed": bill["checks_failed"], "found": bill["name_found"], "kept": bill["kept"]}
            for pos, bill in enumerate(bills, 1)]
    if rows:
        conn.execute(text("""
            INSERT INTO debate_bills (extraction_id, loksabha, session, dbslno, position, bill_id, printed, quote,
                                      extracted_role, summary, checks_failed, name_found, kept)
            VALUES (:e, :ls, :s, :d, :pos, :bid, :printed, :quote, :role, :summary, :failed, :found, :kept)
        """), rows)
    return bills, warnings


def recheck_stored(conn) -> dict[str, int]:
    """Applies the checks again to every stored answer. It calls no model.

    The model, the prompt version, and the tokens of each row stay the same. A debate whose input text
    has another hash today is skipped, because the stored answer is for the old text.
    After the run, a bills row that no debate_bills row uses any more is deleted.
    """
    rows = conn.execute(text("""
        SELECT e.loksabha, e.session, e.dbslno, m.name AS model, e.prompt_version, e.input_sha256,
               e.raw, e.tokens
        FROM bill_extractions e JOIN models m ON m.id = e.model_id
        ORDER BY e.loksabha, e.session, e.dbslno
    """)).mappings().all()
    counts = {"rechecked": 0, "skipped_input_changed": 0,
              "kept_before": conn.execute(text("SELECT count(*) FROM debate_bills WHERE kept")).scalar()}
    for row in rows:
        debate = build_input(conn, (row["loksabha"], row["session"], row["dbslno"]))
        if debate is None or debate["input_sha256"] != row["input_sha256"]:
            counts["skipped_input_changed"] += 1
            continue
        check_and_store(conn, debate, row["raw"], row["model"], row["prompt_version"], row["tokens"], replace=True)
        counts["rechecked"] += 1
    counts["kept_after"] = conn.execute(text("SELECT count(*) FROM debate_bills WHERE kept")).scalar()
    counts["unused_bills_deleted"] = conn.execute(text("""
        DELETE FROM bills b
        WHERE NOT EXISTS (SELECT 1 FROM debate_bills d WHERE d.bill_id = b.id)
          AND NOT EXISTS (SELECT 1 FROM bills x WHERE x.merged_into = b.id)
    """)).rowcount
    return counts
