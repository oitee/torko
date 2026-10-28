"""The debate page: one debate turn by turn, with its speakers, its speeches, and its tags."""
import re

from sqlalchemy import text

from pages.common import (KIND_LABELS, PARTY_AT_DATE, SPEECH_TAGS_CTE, clean_layout, slug, speech_kind, speech_rows,
                          tidy_title, tidy_type)

from pages.sessions import session_labels

LAID = re.compile(r"\s*-\s*Laid\s*$", re.I)
HONORIFICS = {"shri", "smt", "dr", "prof", "col", "kumari", "ms", "mr", "mrs", "adv", "sri", "shrimati",
              "alias", "capt", "lt", "gen", "maj"}


def tokens(name):
    """The set of name words without titles and one-letter words."""
    words = re.findall(r"[a-z]+", (name or "").lower().replace("\xa0", " "))
    return {w for w in words if w not in HONORIFICS and len(w) > 1}


def official_list(raw):
    """The participant list of the source page as [{code, name}]. An unreadable list gives []."""
    out = []
    for e in raw or []:
        if isinstance(e, dict):
            out.append({"code": str(e.get("mpCode")), "name": re.sub(r"\s+", " ", e.get("mpName") or "").strip()})
    return out


def is_listed(sansad_id, person_name, person_codes, official):
    """True when the official list has the member: by sansad id, by a turn code, or by a name match."""
    codes = {e["code"] for e in official}
    if str(sansad_id) in codes or (person_codes & codes):
        return True
    mine = tokens(person_name)
    return bool(mine) and any(o and (mine <= o or o <= mine) for o in (tokens(e["name"]) for e in official))


def turn_kind(person, role_kind):
    """member, a role kind such as presiding or crowd, or unattributed."""
    return "member" if person else (role_kind or "unattributed")


def role_in_debate(speech_id, span_id, role_kind):
    """The place of a turn in the debate: speech, interruption, chair, or between.
    speech_id is the speech the turn belongs to. span_id is the speech whose range holds the turn."""
    if speech_id is not None:
        return "speech"
    if span_id is not None:
        return "interruption"
    return "chair" if role_kind == "presiding" else "between"


def kind_counts(turns):
    """Count turns by kind. The denominator is the turns of the debate."""
    out = {}
    for t in turns:
        out[t["kind"]] = out.get(t["kind"], 0) + 1
    return out


def party_at(conn, person_ids, term, date):
    """Party code, seat and state of each member in the term, at the date. Returns {person_id: {party, seat, state}}."""
    if not person_ids:
        return {}
    rows = conn.execute(text("""
        SELECT p.id, pa.party, pa.seat, pa.state FROM persons p
        LEFT JOIN LATERAL (
            SELECT pt.code AS party, sp.constituency AS seat, st.name AS state
            FROM speakers sp LEFT JOIN parties pt ON pt.id = sp.party_id LEFT JOIN states st ON st.id = sp.state_id
            WHERE sp.person_id = p.id AND sp.lok_sabha_term = :term
              AND sp.effective_from <= COALESCE(:date, sp.effective_from)
            ORDER BY sp.effective_from DESC LIMIT 1) pa ON true
        WHERE p.id = ANY(:ids)"""), {"ids": list(person_ids), "term": term, "date": date}).mappings().all()
    return {r["id"]: {"party": r["party"], "seat": r["seat"], "state": r["state"]} for r in rows}


def silent_members(conn, official, spoke_ids, term, date):
    """The members of the official list with no turn. A code matches by sansad id, then by an old code."""
    codes = [e["code"] for e in official if e["code"].isdigit()]
    found = {}
    if codes:
        for r in conn.execute(text("SELECT sansad_id::text AS c, id FROM persons WHERE sansad_id::text = ANY(:c)"),
                              {"c": codes}).mappings():
            found[r["c"]] = r["id"]
        for r in conn.execute(text("SELECT mp_code::text AS c, person_id AS id FROM mpcode_aliases "
                                   "WHERE mp_code::text = ANY(:c)"), {"c": codes}).mappings():
            found.setdefault(r["c"], r["id"])
    names = {}
    ids = set(found.values())
    if ids:
        names = {r["id"]: r["name"] for r in conn.execute(text("SELECT id, name FROM persons WHERE id = ANY(:i)"),
                                                           {"i": list(ids)}).mappings()}
    standing = party_at(conn, ids, term, date)
    out, done = [], set()
    for e in official:
        pid = found.get(e["code"])
        if pid in spoke_ids or (pid is not None and pid in done):
            continue
        done.add(pid)
        out.append({"member_id": pid, "name": names.get(pid) or e["name"], "code": e["code"],
                    "party": standing.get(pid, {}).get("party"), "seat": standing.get(pid, {}).get("seat"),
                    "state": standing.get(pid, {}).get("state")})
    return out


def same_day_debates(conn, d):
    """The other debates of the same date and term, in the order of dbslno."""
    if d["debate_date"] is None:
        return []
    rows = conn.execute(text("""
        SELECT x.id, x.title, x.debate_type, x.dbslno, (SELECT count(*) FROM speeches s WHERE s.debate_id = x.id) AS n
        FROM debates x WHERE x.debate_date = :dt AND x.loksabha = :t AND x.id <> :i ORDER BY x.dbslno, x.id"""),
        {"dt": d["debate_date"], "t": d["loksabha"], "i": d["id"]}).mappings().all()
    return [{"id": r["id"], "title": tidy_title(re.sub(r"\s+", " ", r["title"] or "").strip()),
             "kind": speech_kind(r["debate_type"]), "kind_label": KIND_LABELS[speech_kind(r["debate_type"])],
             "dbslno": r["dbslno"], "speeches": r["n"]} for r in rows]


def debate_page(conn, debate_id, args=None):
    d = conn.execute(text("SELECT id, loksabha, session, dbslno, debate_date, title, debate_type, source_url, "
                          "mp_list_raw, member_names FROM debates WHERE id = :d"), {"d": debate_id}).mappings().first()
    if d is None:
        return None
    official = official_list(d["mp_list_raw"])

    turns = conn.execute(text("""
        SELECT t.seq, t.speaker_label, t.mp_code, t.text, t.word_count, t.speech_id, t.role_kind, t.name_source,
               t.text_source, sr.display_name AS role, pe.id AS pid, pe.name AS person, pe.sansad_id
        FROM turns t LEFT JOIN speaker_roles sr ON sr.id = t.role_id LEFT JOIN persons pe ON pe.id = t.person_id
        WHERE t.debate_id = :d ORDER BY t.seq"""), {"d": debate_id}).mappings().all()
    speeches = conn.execute(text("""
        SELECT id, person_id, seq_start, seq_end, word_count, turn_count, interruption_count
        FROM speeches WHERE debate_id = :d ORDER BY seq_start"""), {"d": debate_id}).mappings().all()

    person_codes = {}
    for t in turns:
        if t["pid"] and t["mp_code"]:
            person_codes.setdefault(t["pid"], set()).add(str(t["mp_code"]))

    def listed(t):
        return is_listed(t["sansad_id"], t["person"], person_codes.get(t["pid"], set()), official)

    standing = party_at(conn, list(person_codes), d["loksabha"], d["debate_date"])
    speech_count = {}
    for s in speeches:
        speech_count[s["person_id"]] = speech_count.get(s["person_id"], 0) + 1

    people = {}
    for t in turns:
        if t["pid"]:
            p = people.setdefault(t["pid"], {"id": t["pid"], "name": t["person"], "turns": 0, "words": 0,
                                            "listed": listed(t), "first": t["seq"],
                                            "party": standing.get(t["pid"], {}).get("party"),
                                            "seat": standing.get(t["pid"], {}).get("seat"),
                                            "state": standing.get(t["pid"], {}).get("state"),
                                            "speeches": speech_count.get(t["pid"], 0)})
            p["turns"] += 1
            p["words"] += t["word_count"] or 0

    def span_of(seq):
        for s in speeches:
            if s["seq_start"] <= seq <= s["seq_end"]:
                return s["id"]
        return None

    def turn_row(t):
        span = span_of(t["seq"])
        place = role_in_debate(t["speech_id"], span, t["role_kind"])
        row = {"role_in_debate": place}
        if place == "interruption":
            row["inside_speech"] = span
        return row, span

    turn_list = [{
        "seq": t["seq"], "label": t["speaker_label"], "text": clean_layout(t["text"]), "words": t["word_count"],
        "kind": turn_kind(t["person"], t["role_kind"]), "attributed": t["person"] is not None,
        "member": t["person"], "member_id": t["pid"], "role": t["role"], "role_kind": t["role_kind"],
        "how": t["name_source"], "repair": t["text_source"], "speech": t["speech_id"], "span": turn_row(t)[1],
        "listed": listed(t) if t["pid"] else None,
        **turn_row(t)[0],
    } for t in turns]

    # Turns and words with no member. The denominator is the turns of this debate.
    unidentified = {"turns": sum(1 for t in turns if not t["pid"]),
                    "words": sum(t["word_count"] or 0 for t in turns if not t["pid"]),
                    "speeches": speech_count.get(None, 0)}

    seen = set(people)
    silent = silent_members(conn, official, seen, d["loksabha"], d["debate_date"])
    same_day = same_day_debates(conn, d)
    speech_list = speech_rows(conn, [s["id"] for s in speeches])
    by_speech = {r["id"]: r for r in speech_list}

    tags = []
    if speeches:
        rows = conn.execute(text(f"""
            WITH {SPEECH_TAGS_CTE}
            SELECT t.tag, t.type, count(DISTINCT st.speech_id) AS n
            FROM speech_tags st JOIN tags t ON t.id = st.tag_id
            WHERE st.speech_id = ANY(:ids) GROUP BY t.tag, t.type ORDER BY n DESC, t.tag LIMIT 40"""),
            {"ids": [s["id"] for s in speeches]}).mappings().all()
        tags = [{"name": r["tag"], "slug": slug(r["tag"]), "type": r["type"], "speeches": r["n"]} for r in rows]

    title = re.sub(r"\s+", " ", d["title"] or "").strip()
    laid = bool(LAID.search(title))
    title = LAID.sub("", title)
    return {
        "id": d["id"], "laid": laid, "term": d["loksabha"], "session": d["session"], "dbslno": d["dbslno"],
        "date": d["debate_date"].isoformat() if d["debate_date"] else None,
        "title": tidy_title(title), "type": tidy_type(d["debate_type"]), "source_url": d["source_url"],
        "kind": speech_kind(d["debate_type"]), "kind_label": KIND_LABELS[speech_kind(d["debate_type"])],
        "session_label": (session_labels(conn).get((d["loksabha"], d["session"])) or {}).get("label"),
        "official": official, "official_count": len(official), "n_names": len(d["member_names"] or []),
        "turn_list": turn_list, "turn_count": len(turn_list), "turn_kinds": kind_counts(turn_list),
        "turn_kinds_note": "Each count is a number of turns of this debate. The total is turn_count.",
        "speeches": [{"id": s["id"], "words": s["word_count"], "turns": s["turn_count"],
                      "interruptions": s["interruption_count"], "start": s["seq_start"], "end": s["seq_end"],
                      "member_id": by_speech[s["id"]]["member_id"], "member": by_speech[s["id"]]["member"],
                      "printed": by_speech[s["id"]]["printed"], "party": by_speech[s["id"]]["party"],
                      "seat": by_speech[s["id"]]["seat"], "state": by_speech[s["id"]]["state"], "summary": by_speech[s["id"]]["summary"],
                      "tags": by_speech[s["id"]]["tags"]}
                     for s in speeches],
        "speeches_note": "A speech with no member has member null and printed, the name as printed in the transcript. "
                         "The denominator of every count is the speeches of this debate.",
        "unidentified": unidentified,
        "silent": silent,
        "silent_note": "Members of the official list who have no turn in this debate. member_id is null when the "
                       "code matches no member.",
        "same_day": same_day,
        "people": sorted(people.values(), key=lambda p: p["first"]),
        "tags": tags,
        "tags_note": "speeches is the number of speeches of this debate that carry the tag. Top 40 tags only.",
    }


ROUTES = [("/debate/<int:debate_id>", debate_page)]
