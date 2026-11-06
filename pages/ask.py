"""Read a question in plain language as the filters of the speech list: /api/ask?q=...

Example: "What did Kerala MPs say about fishermen after 2019?" gives state=Kerala, tag=fishermen and date_from=2020-01-01.
The Search page then shows the speeches of /api/speeches with these filters.

Two steps:
1. Rules. Each word group is compared with the names of members, parties, states, tags and places, and with fixed
   forms of years, terms and kinds of debate. A name must match exactly, as a whole word group. A name that fits two
   members is left out, because a wrong filter is worse than no filter. The words that match nothing are the search text.
2. An LLM, only when the rules cannot read the question: Hindi script, or Hindi words in Latin letters. The LLM gives
   names in English as JSON. The same lookup of step 1 then checks each name. A name that is not known is dropped,
   so the LLM can never make a filter that does not exist. Each LLM answer is stored by question, and a daily limit
   stops the calls. When the limit is reached or the call fails, the answer of the rules stands.
"""
from __future__ import annotations

import json
import os
import re
import unicodedata
from datetime import date

import requests
from flask import after_this_request, has_request_context
from sqlalchemy import text

import dashboard_db
from pages.common import KINDS, KIND_LABELS, cached, slug

MAX_QUESTION_CHARS = 300
MAX_WORDS_IN_NAME = 8
TERMS = range(13, 19)
LLM_MODEL = os.environ.get("ASK_MODEL", "gemini-3.5-flash-lite")
LLM_TIMEOUT = 8
# Change PROMPT_VERSION with each change of the prompt, so that the stored answers of the old prompt are not used.
PROMPT_VERSION = "p2"
DEFAULT_DAILY_LIMIT = 500

# The words that only carry the form of a question. They are never search text.
STOP = set("""
a an the of on in at to for from by with about and or as is are was were be been do does did what which who whom whose
how when where why say said says tell told talk talked talks speak spoke speaks speech speeches debate debates discuss
discussed discussion raise raised raises mention mentioned most more much many all any some me show find list give
mp mps member members parliament parliamentarians lok sabha their they them his her its this that these those has have had
ke ki ka ko ne par pe kya kaha kahi bola boli bole mein me se aur ya hai hain tha the thi sabse zyada jyada kisne kaun
bhashan bhashanon saansad saansadon sansad sansadon baad pehle tak
after before since between until till during new best good top latest recent important famous major happened happen
minister ministers
के की का को ने पर क्या कहा कही बोला बोली बोले में से और या है हैं था थे थी सबसे ज़्यादा ज्यादा किसने कौन भाषण भाषणों
सांसद सांसदों बहस बाद पहले तक लोकसभा
""".split())
# The words that call a member: "Kerala MPs" means members from Kerala, not speeches about Kerala.
POSTPOSITIONS = {"ke", "ki", "ka", "के", "की", "का"}
KIND_ORDER = ["member", "party", "state", "place", "tag", "kind"]
MEMBER_WORDS = {"mp", "mps", "member", "members", "saansad", "saansadon", "sansad", "sansadon", "सांसद", "सांसदों"}
# A question that asks who, or which members, wants the list of members, most speeches first.
WHO = [re.compile(p) for p in (
    r"\b(which|what) (mps|mp|members|member|parliamentarians)\b", r"\bwho\b", r"\bkisne\b", r"\bkaun\b",
    r"किसने", r"कौन")]
# Hindi words in Latin letters. One of them sends the question to the LLM.
HINGLISH = {"ke", "ki", "ka", "ne", "par", "kya", "kaha", "bola", "mein", "se", "sabse", "zyada", "jyada", "kisne",
            "kaun", "pehle", "baad", "bhashan", "saansad", "sansad"}
PARTY_ALIASES = {
    "congress": "INC", "congress party": "INC", "indian national congress": "INC", "trinamool": "AITC", "tmc": "AITC",
    "trinamool congress": "AITC", "cpm": "CPI(M)", "cpi m": "CPI(M)", "jdu": "JD(U)", "jd u": "JD(U)", "jds": "JD(S)",
    "jd s": "JD(S)", "ysrcp": "YSR Congress Party", "brs": "TRS", "shiv sena": "SS", "samajwadi": "SP",
    "भाजपा": "BJP", "बीजेपी": "BJP", "कांग्रेस": "INC", "समाजवादी पार्टी": "SP", "सपा": "SP", "बसपा": "BSP",
    "तृणमूल": "AITC", "राजद": "RJD",
}
# Party codes that are also common words. They match only in capital letters, as typed.
CASE_CODES = {"SP", "SS", "AAP", "CPI", "KEC"}
KIND_WORDS = {
    "zero hour": "zero_hour", "rule 377": "rule_377", "budget speech": "budget", "budget speeches": "budget",
    "budget debate": "budget", "budget debates": "budget", "bill debate": "bill", "bill debates": "bill",
    "statement by minister": "statement", "statement by the minister": "statement", "statement by ministers": "statement",
    "ministerial statement": "statement", "statement by prime minister": "statement",
    "statement by the prime minister": "statement",
}
# The kinds that the LLM may set, each with the words that the question must hold. "discussion" is too vague.
LLM_KINDS = {
    "zero_hour": re.compile(r"zero hour|शून्य काल|शून्यकाल"), "rule_377": re.compile(r"377"),
    "bill": re.compile(r"\bbill|विधेयक|बिल"), "budget": re.compile(r"budget|बजट"),
    "statement": re.compile(r"statement|बयान|वक्तव्य"),
}
ORDINAL = r"(1[3-8])(?:st|nd|rd|th|वीं|वी)?"
TERM_RX = [re.compile(ORDINAL + r"\s*lok\s*sabha\b"), re.compile(r"\blok\s*sabha\s*(1[3-8])\b"), re.compile(r"\bls\s*(1[3-8])\b"),
           re.compile(ORDINAL + r"\s*लोकसभा"), re.compile(r"\b(1[3-8])(?:st|nd|rd|th) term\b")]
YEAR = r"((?:19|20)\d\d)"


def fold(value: str) -> str:
    """Lower case, no marks of accent, and one space between words. The apostrophe goes, other marks become a space."""
    value = unicodedata.normalize("NFC", value or "").lower().replace("’", "'").replace("'", "")
    value = re.sub(r"[^\wऀ-ॿ]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def singular(word: str) -> str:
    """A simple singular form, the same for the name and the question: floods -> flood, railways -> railway."""
    if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def key_of(value: str) -> tuple:
    return tuple(singular(w) for w in fold(value).split())


# The stop words in both forms, because the question and the names compare in the singular form.
STOP_KEYS = STOP | {singular(w) for w in STOP}


def name_keys(name: str):
    """The keys of one name: the whole name, and the acronym in brackets, for example GST from 'Goods and Services Tax (GST)'."""
    yield key_of(name)
    for inner in re.findall(r"\(([^)]+)\)", name):
        if len(inner) >= 3 and inner.upper() == inner:
            yield key_of(inner)


def build_vocab(members, parties, states, tags):
    """Return the lookup of the rules: {key (tuple of words): [(kind, value, label), ...]}.

    members: [(id, name)]. parties: [(code, name)]. states: [name]. tags: [(name, type, aliases)].
    A member also gets the key of the first and last word ("Smriti Irani" for "Smriti Zubin Irani"), and of the last
    word alone, when it has at least 4 letters. A key with two different members is kept, so that the reader knows the name is unclear.
    """
    vocab: dict[tuple, list] = {}

    def add(key, entry):
        # A name made only of question words, such as the tag "Lok Sabha", is never a filter.
        if not key or all(w in STOP_KEYS for w in key):
            return
        rows = vocab.setdefault(key, [])
        if entry not in rows:
            rows.append(entry)

    names, surnames = {}, set()
    for mid, name in members:
        words = key_of(name)
        keys = {words}
        if len(words) >= 3:
            keys.add((words[0], words[-1]))
        if len(words) >= 2 and len(words[-1]) >= 4:
            keys.add((words[-1],))
            surnames.add((words[-1],))
        for k in keys:
            names.setdefault(k, set()).add((mid, name, len(k) == len(words)))
    for k, found in names.items():
        full = [f for f in found if f[2]]
        # The whole name of one member wins over a part of the name of another member.
        chosen = full if len(full) == 1 else found
        for mid, name, _ in chosen:
            add(k, ("member", str(mid), name))
    for code, name in parties:
        add(key_of(name), ("party", code, name))
        if code in CASE_CODES:
            vocab.setdefault(("__case__", code), []).append(("party", code, name))
        else:
            add(key_of(code), ("party", code, name))
    party_names = dict(parties)
    for alias, code in PARTY_ALIASES.items():
        if code in party_names:
            add(key_of(alias), ("party", code, party_names[code]))
    for name in states:
        add(key_of(name), ("state", name, name))
    for name, type_, aliases in tags:
        if type_ in ("role", "person"):
            continue
        kind = "place" if type_ == "place" else "tag"
        for one in [name, *(aliases or [])]:
            for k in name_keys(one):
                add(k, (kind, slug(name), name))
    for words, kind in KIND_WORDS.items():
        add(key_of(words), ("kind", kind, KIND_LABELS[kind]))
    # A surname alone never wins over a tag, place, state or party of the same word, for example a member named Bihari.
    for k in surnames:
        rows = vocab.get(k, [])
        if any(e[0] != "member" for e in rows):
            vocab[k] = [e for e in rows if e[0] != "member"]
    return vocab


def load_vocab(conn):
    def load():
        members = conn.execute(text("""SELECT pe.id, pe.name FROM persons pe
            WHERE EXISTS (SELECT 1 FROM speeches s WHERE s.person_id = pe.id)""")).all()
        parties = conn.execute(text("SELECT code, name FROM parties")).all()
        states = [r[0] for r in conn.execute(text("SELECT name FROM states"))]
        tags = conn.execute(text("SELECT tag, type, aliases FROM tags WHERE status NOT IN ('rejected', 'merged')")).all()
        return build_vocab(members, parties, states, tags)
    return cached("ask_vocab", load)


def year_filters(question: str):
    """Return ({date_from, date_to}, text without the year words). After 2019 starts in 2020, since 2019 starts in 2019."""
    t = question
    out = {}
    rules = [
        (r"\bbetween\s+" + YEAR + r"\s+(?:and|to|-)\s+" + YEAR + r"\b", lambda a, b: (f"{a}-01-01", f"{b}-12-31")),
        (r"\b(?:from\s+)?" + YEAR + r"\s*(?:-|–|to)\s*" + YEAR + r"\b", lambda a, b: (f"{a}-01-01", f"{b}-12-31")),
        (r"\b(?:after)\s+" + YEAR + r"\b", lambda a: (f"{int(a) + 1}-01-01", None)),
        (r"\b(?:since|from)\s+" + YEAR + r"\b", lambda a: (f"{a}-01-01", None)),
        (r"\b(?:before)\s+" + YEAR + r"\b", lambda a: (None, f"{int(a) - 1}-12-31")),
        (r"\b(?:until|till|up to)\s+" + YEAR + r"\b", lambda a: (None, f"{a}-12-31")),
        (YEAR + r"\s*(?:ke baad|के बाद)", lambda a: (f"{int(a) + 1}-01-01", None)),
        (YEAR + r"\s*(?:se pehle|से पहले)", lambda a: (None, f"{int(a) - 1}-12-31")),
        (YEAR + r"\s*(?:se|से)(?!\w)", lambda a: (f"{a}-01-01", None)),
        (r"\b(?:in\s+)?" + YEAR + r"\b(?!\s*(?:st|nd|rd|th))", lambda a: (f"{a}-01-01", f"{a}-12-31")),
    ]
    for pattern, make in rules:
        m = re.search(pattern, t, re.I)
        if m:
            start, end = make(*m.groups())
            if start:
                out["date_from"] = start
            if end:
                out["date_to"] = end
            t = t[:m.start()] + " " + t[m.end():]
            break
    return out, t


def term_filter(question: str):
    """Return (term, text without the term words). The search is in lower case, and the text keeps its case."""
    t = question.lower()
    for rx in TERM_RX:
        m = rx.search(t)
        if m:
            return int(m.group(1)), question[:m.start()] + " " + question[m.end():]
    return None, question


def wants_members(question: str) -> bool:
    t = fold(question)
    return any(rx.search(t) for rx in WHO)


def needs_llm(question: str, words_left: list[str]) -> bool:
    """True when the rules cannot read the question: Hindi script, or Hindi words in Latin letters."""
    if re.search(r"[ऀ-ॿ]", question):
        return True
    return any(w in HINGLISH for w in fold(question).split())


def read_rules(question: str, vocab: dict) -> dict:
    """Return {params, picked, dropped, words}. params holds the address values. picked lists each match for the Read as line."""
    params, picked, dropped = {}, [], []
    dates, rest = year_filters(question)
    params.update(dates)
    term, rest = term_filter(rest)
    if term:
        params["term"] = str(term)
    if wants_members(question):
        params["view"], params["sort"] = "members", "most"
    raw = rest.split()
    folded = [fold(w) for w in raw]
    words = [" ".join(singular(x) for x in w.split()) for w in folded]
    used = [False] * len(words)
    i = 0
    while i < len(words):
        hit = None
        for n in range(min(MAX_WORDS_IN_NAME, len(words) - i), 0, -1):
            key = tuple(x for w in words[i:i + n] for x in w.split())
            if not key:
                continue
            entries = vocab.get(key)
            if not entries and n == 1 and raw[i].strip("?,.!") in CASE_CODES:
                entries = vocab.get(("__case__", raw[i].strip("?,.!")))
            if entries:
                hit = (n, entries)
                break
        if hit is None:
            i += 1
            continue
        n, entries = hit
        phrase = " ".join(raw[i:i + n]).strip("?,.!")
        after = [w for w in words[i + n:i + n + 3] if w and w not in POSTPOSITIONS]
        before = words[max(0, i - 2):i]
        members_near = bool(set(after[:1]) & MEMBER_WORDS) or (bool(set(before) & MEMBER_WORDS) and "from" in before)
        kinds = {e[0] for e in entries}
        if "state" in kinds:
            entries = [e for e in entries if e[0] == "state"] if members_near else [e for e in entries if e[0] != "state"]
        if not entries:  # a state with no place tag, not after MPs: the word stays in the search text
            i += 1
            continue
        kind = next(k for k in KIND_ORDER if any(e[0] == k for e in entries))
        entries = [e for e in entries if e[0] == kind]
        if len({e[1] for e in entries}) > 1:
            dropped.append({"text": phrase, "why": f"{len(entries)} {kind}s have this name"})
            for k in range(i, i + n):
                used[k] = True
            i += n
            continue
        _, value, label = entries[0]
        key = kind
        current = params.get(key)
        if current and value not in current.split(","):
            # Two places mean speeches about either place, and two tags mean speeches with both tags.
            if key in ("tag", "place"):
                params[key] = current + "," + value
            else:
                dropped.append({"text": phrase, "why": f"a second {key} in one question"})
        elif not current:
            params[key] = value
        picked.append({"key": key, "value": value, "label": label, "text": phrase})
        for k in range(i, i + n):
            used[k] = True
        i += n
    left = [raw[k].strip("?,.!\"'") for k in range(len(raw))
            if not used[k] and words[k] and words[k] not in STOP_KEYS]
    left = [w for w in left if w and not re.fullmatch(r"\d+", w)]
    return {"params": params, "picked": picked, "dropped": dropped, "words": " ".join(left)}


# ---------------------------------------------------------------- the LLM step

LLM_PROMPT = """You turn a question about the debates of the Lok Sabha (India) into search filters.
The question can be in English, Hindi, or Hindi in Latin letters. Write every value in English.
Answer with one JSON object and nothing else. Leave out a field that the question does not ask for.

Fields:
- "members": full names of members of parliament that the question names, in English spelling.
- "parties": party codes from this list only: {parties}
- "member_states": states whose members the question asks about ("Kerala MPs" -> ["Kerala"]). From this list only: {states}
  A state that the speeches are about is a place, not a member state ("Tharoor on Kerala floods" -> places ["Kerala"]).
- "places": places that the speeches are about (a state, city, district or country), in English.
- "subjects": the subjects, as short English names, for example "Floods", "Price Rise", "Goods and Services Tax (GST)", "Fishermen".
- "term": a Lok Sabha number from 13 to 18.
- "date_from", "date_to": dates as YYYY-MM-DD. "after 2019" -> date_from 2020-01-01. "before 2014" -> date_to 2013-12-31.
- "kind": only when the question names this kind of business: zero_hour, rule_377, bill, budget, discussion, statement.
  The word "debate" or "speech" alone is not a kind.
- "who_most": true when the question asks which members spoke most, or who spoke.
- "words": the other words that matter for a text search, in English. Leave out question words.

Question: {question}"""


def answer_key() -> str:
    return f"{LLM_MODEL}@{PROMPT_VERSION}"


def daily_limit() -> int:
    try:
        return int(os.environ.get("ASK_LLM_DAILY_LIMIT", DEFAULT_DAILY_LIMIT))
    except ValueError:
        return DEFAULT_DAILY_LIMIT


def stored_answer(store, question_key: str):
    with store.connect() as conn:
        return conn.execute(text("SELECT answer FROM ask_answers WHERE question = :q AND model = :m"),
                            {"q": question_key, "m": answer_key()}).scalar()


def take_call(store, limit: int) -> bool:
    """Count one LLM call for today. Return False when today already has `limit` calls."""
    with store.begin() as conn:
        got = conn.execute(text("""INSERT INTO ask_llm_days (day, calls) VALUES (current_date, 1)
            ON CONFLICT (day) DO UPDATE SET calls = ask_llm_days.calls + 1 WHERE ask_llm_days.calls < :limit
            RETURNING calls"""), {"limit": limit}).scalar()
    return got is not None and got <= limit


def call_llm(question: str, parties: list[str], states: list[str]) -> dict:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{LLM_MODEL}:generateContent"
    prompt = LLM_PROMPT.format(parties=", ".join(parties), states=", ".join(states), question=question)
    body = {"contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json", "temperature": 0}}
    resp = requests.post(url, json=body, headers={"x-goog-api-key": os.environ["GEMINI_API_KEY"]}, timeout=LLM_TIMEOUT)
    resp.raise_for_status()
    answer = json.loads(resp.json()["candidates"][0]["content"]["parts"][0]["text"])
    if not isinstance(answer, dict):
        raise ValueError("the LLM answer is not a JSON object")
    return answer


def as_list(value):
    if value is None:
        return []
    return [str(v) for v in value] if isinstance(value, list) else [str(value)]


def checked_llm(answer: dict, vocab: dict, question: str = "") -> dict:
    """Return the filters of an LLM answer that the lookup knows. A name that is not known goes to the search words."""
    params, picked, words = {}, [], []

    def look(name, kinds):
        entries = [e for e in vocab.get(key_of(name), []) if e[0] in kinds]
        return entries if len({(e[0], e[1]) for e in entries}) == 1 else None

    def put(key, value, label, said):
        current = params.get(key)
        if current and value in current.split(","):
            return
        if current and key not in ("tag", "place"):
            return
        params[key] = f"{current},{value}" if current else value
        picked.append({"key": key, "value": value, "label": label, "text": said})

    for field, kinds, unknown_to_words in (("members", {"member"}, False), ("parties", {"party"}, False),
                                           ("member_states", {"state"}, False), ("places", {"place"}, True),
                                           ("subjects", {"tag", "place"}, True)):
        for name in as_list(answer.get(field)):
            got = look(name, kinds)
            if field == "parties" and not got:
                got = [e for rows in vocab.values() for e in rows if e[0] == "party" and e[1] == name][:1] or None
            if got:
                kind, value, label = got[0]
                put(kind, value, label, name)
            elif unknown_to_words:
                words.append(name)
    term = answer.get("term")
    # The LLM can add a term or a kind that the question does not name. So each needs its own words in the question.
    named_term = re.search(r"(?<!\d)1[3-8](?!\d)", question) is not None
    if named_term and str(term).isdigit() and int(term) in TERMS:
        put("term", str(int(term)), f"{int(term)}th Lok Sabha", str(term))
    for field in ("date_from", "date_to"):
        value = str(answer.get(field) or "")
        try:
            date.fromisoformat(value)
            params[field] = value
        except ValueError:
            pass
    if params.get("date_from") and params.get("date_to") and params["date_from"] > params["date_to"]:
        params.pop("date_to")
    kind = answer.get("kind")
    if kind in KINDS and kind in LLM_KINDS and LLM_KINDS[kind].search(fold(question)):
        put("kind", kind, KIND_LABELS[kind], kind)
    if answer.get("who_most") is True:
        params["view"], params["sort"] = "members", "most"
    words += [w for w in as_list(answer.get("words")) if w.strip()]
    # The words of a filter that was found, and the question words, would only narrow the word search.
    found = {x for p in picked for x in key_of(p["label"])} | {x for p in picked for x in key_of(p["text"])}
    kept = [w for phrase in words for w in phrase.split()
            if singular(fold(w)) not in STOP_KEYS and singular(fold(w)) not in found and fold(w)]
    return {"params": params, "picked": picked, "words": " ".join(dict.fromkeys(kept))}


def merge(rules: dict, llm: dict) -> dict:
    """The rules win for each filter that they found. The LLM adds the filters that the rules did not find."""
    params = dict(rules["params"])
    picked = list(rules["picked"])
    taken = {p["label"].lower() for p in picked if p["key"] in ("state", "place")}
    for k, v in llm["params"].items():
        if k in params:
            continue
        extra = [p for p in llm["picked"] if p["key"] == k]
        # One name is a state or a place, never both: the rules read the words around it, so their choice stands.
        if k in ("state", "place") and extra and all(p["label"].lower() in taken for p in extra):
            continue
        params[k] = v
        picked += extra
    return {"params": params, "picked": picked, "dropped": rules["dropped"], "words": llm["words"]}


def do_not_store():
    if has_request_context():
        @after_this_request
        def _no_store(resp):
            resp.headers["Cache-Control"] = "no-store"
            return resp


def ask(conn, question: str, store=None, llm=call_llm, use_llm=True):
    """Return the filters of the question. use_llm=False gives the answer of the rules alone, for the test set."""
    question = (question or "").strip()[:MAX_QUESTION_CHARS]
    vocab = load_vocab(conn)
    got = read_rules(question, vocab)
    state = "not needed"
    if question and needs_llm(question, got["words"].split()) and not use_llm:
        state = "off"
    elif question and needs_llm(question, got["words"].split()):
        store = store or dashboard_db.get_engine()
        key = fold(question)
        answer = stored_answer(store, key)
        state = "stored" if answer is not None else None
        if answer is None:
            if not take_call(store, daily_limit()):
                state = "daily limit"
            else:
                try:
                    parties = [r[0] for r in conn.execute(text("SELECT code FROM parties ORDER BY code"))]
                    states = [r[0] for r in conn.execute(text("SELECT name FROM states ORDER BY name"))]
                    answer = llm(question, parties, states)
                    with store.begin() as w:
                        w.execute(text("""INSERT INTO ask_answers (question, model, answer) VALUES (:q, :m, CAST(:a AS jsonb))
                            ON CONFLICT (question, model) DO NOTHING"""), {"q": key, "m": answer_key(), "a": json.dumps(answer)})
                    state = "called"
                except Exception as err:  # The answer of the rules stands when the call fails.
                    print(f"ask LLM failed: {err}", flush=True)
                    state = "failed"
        if answer is not None:
            got = merge(got, checked_llm(answer, vocab, question))
        else:
            do_not_store()
    params = dict(got["params"])
    if got["words"]:
        params["q"] = got["words"]
    return {"question": question, "params": params, "read_as": read_as(got["picked"], params),
            "dropped": got["dropped"], "words": got["words"], "llm": state}


def day_text(iso: str) -> str:
    """2020-01-01 -> 1 Jan 2020."""
    d = date.fromisoformat(iso)
    return f"{d.day} {d.strftime('%b')} {d.year}"


def read_as(picked, params):
    """The Read as line in parts, in a fixed order: who, about what, when, how."""
    order = ["member", "party", "state", "tag", "place", "kind", "term"]
    labels = {"member": "by {}", "party": "by members of {}", "state": "by members from {}", "tag": "on {}",
              "place": "about {}", "kind": "in {}", "term": "in the {}"}
    out = []
    for key in order:
        for p in picked:
            if p["key"] == key and p["value"] in params.get(key, "").split(","):
                label = p["label"] if key != "term" else f"{p['value']}th Lok Sabha"
                if key == "party":
                    label = p["value"]
                out.append({"key": key, "value": p["value"], "text": labels[key].format(label)})
    start, end = params.get("date_from"), params.get("date_to")
    if start and end:
        out.append({"key": "date", "text": f"from {day_text(start)} to {day_text(end)}"})
    elif start:
        out.append({"key": "date", "text": f"from {day_text(start)}"})
    elif end:
        out.append({"key": "date", "text": f"up to {day_text(end)}"})
    if params.get("view") == "members":
        out.append({"key": "view", "text": "members with the most speeches first"})
    seen, unique = set(), []
    for o in out:
        k = (o["key"], o.get("value"))
        if k not in seen:
            seen.add(k)
            unique.append(o)
    return unique


def ask_route(conn, args):
    return ask(conn, args.get("q") or "")


ROUTES = [("/ask", ask_route)]
