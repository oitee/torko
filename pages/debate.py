"""The debate page: one debate turn by turn, with its speakers, its speeches, and its tags."""
import re

from sqlalchemy import text

from pages.common import SPEECH_TAGS_CTE, slug, tidy_title, tidy_type

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


def kind_counts(turns):
    """Count turns by kind. The denominator is the turns of the debate."""
    out = {}
    for t in turns:
        out[t["kind"]] = out.get(t["kind"], 0) + 1
    return out


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

    people = {}
    for t in turns:
        if t["pid"]:
            p = people.setdefault(t["pid"], {"id": t["sansad_id"], "name": t["person"], "turns": 0, "words": 0,
                                            "listed": listed(t), "first": t["seq"]})
            p["turns"] += 1
            p["words"] += t["word_count"] or 0

    def span_of(seq):
        for s in speeches:
            if s["seq_start"] <= seq <= s["seq_end"]:
                return s["id"]
        return None

    turn_list = [{
        "seq": t["seq"], "label": t["speaker_label"], "text": t["text"], "words": t["word_count"],
        "kind": turn_kind(t["person"], t["role_kind"]), "attributed": t["person"] is not None,
        "member": t["person"], "member_id": t["sansad_id"], "role": t["role"], "role_kind": t["role_kind"],
        "how": t["name_source"], "repair": t["text_source"], "speech": t["speech_id"], "span": span_of(t["seq"]),
        "listed": listed(t) if t["pid"] else None,
    } for t in turns]

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
        "official": official, "official_count": len(official), "n_names": len(d["member_names"] or []),
        "turn_list": turn_list, "turn_count": len(turn_list), "turn_kinds": kind_counts(turn_list),
        "turn_kinds_note": "Each count is a number of turns of this debate. The total is turn_count.",
        "speeches": [{"id": s["id"], "words": s["word_count"], "turns": s["turn_count"],
                      "interruptions": s["interruption_count"], "start": s["seq_start"], "end": s["seq_end"]}
                     for s in speeches],
        "people": sorted(people.values(), key=lambda p: p["first"]),
        "tags": tags,
        "tags_note": "speeches is the number of speeches of this debate that carry the tag. Top 40 tags only.",
    }


ROUTES = [("/debate/<int:debate_id>", debate_page)]
