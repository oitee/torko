"""Search tags and subjects with one query: the rule of the two-level search.

A broad word returns the tag and every subject under it. A specific phrase returns the subject, with its parent tag.
1. Word match. A query word matches a word of a text when both have the same stem (lower case, without
   punctuation and a final "s"). A text matches when it holds every query word.
2. A tag matches when its name or an alias matches. A subject matches when its label or one of its names matches.
3. The result for a tag is the tag and every subject whose parent is that tag.
   The result for a subject is the subject, with its parent tag for context.
4. Ranking: a tag or subject whose words are exactly the query words comes first, a tag before a subject.
   Then the results by the number of speeches.
   When no tag matches by its own name, the query can still mean a tag: when 2 or more matching subjects share one
   parent tag, and that tag holds at least half of the speeches of all matching subjects. That tag comes first with
   its subjects. Example: "MGNREGA" matches several subjects of the tag that says "MNREGA".
"""
from __future__ import annotations

import re
from collections import defaultdict

from sqlalchemy import text

from pages.common import slug

STOP = frozenset({"of", "the", "and", "for", "in", "to", "a", "an", "on", "by", "with"})


def stem(word: str) -> str:
    w = word.lower()
    for suffix in ("ies", "s"):
        if len(w) > 4 and w.endswith(suffix):
            return w[: -len(suffix)] + ("y" if suffix == "ies" else "")
    return w


def words(text: str) -> set:
    """The stems of the words of a text, without short function words."""
    return {stem(w) for w in re.findall(r"[^\W_]+", text.replace("'", "")) if w.lower() not in STOP}


def matches(query: str, text: str) -> bool:
    q = words(query)
    return bool(q) and q <= words(text)


STATE_IN_NOTE = re.compile(r" in ([A-Z][A-Za-z &]+), India")
MAX_MEMBERS = 8


def place_state(description: str | None) -> str | None:
    """The state of a place, read from its note, for example "District in Bihar, India." gives "Bihar"."""
    m = STATE_IN_NOTE.search(description or "")
    return m.group(1) if m else None


def place_label(name: str, description: str | None) -> str:
    """The name to show for a place: "Aurangabad (Bihar)" and "Latur" become "Aurangabad, Bihar" and "Latur, Maharashtra"."""
    base = re.sub(r"\s*\([^)]*\)$", "", name)
    state = place_state(description)
    return f"{base}, {state}" if state and state != base else base


def member_label(seat: str | None, state: str | None) -> str | None:
    return f"{seat}, {state}" if seat and state else seat


def tag_fields(t: dict) -> dict:
    """The kind and the link fields of a tag result. A tag of type place gets kind place."""
    out = {"kind": "place" if t.get("type") == "place" else "tag", "slug": slug(t["tag"]),
           "type": t.get("type"), "domain": t.get("domain")}
    if out["kind"] == "place":
        out.update(note=t.get("description"), state=place_state(t.get("description")),
                   label=place_label(t["tag"], t.get("description")))
    return out


def search(query: str, tags: list, subjects: list, limit: int = 10, members: list = ()) -> list:
    """tags: dicts with tag, aliases (list), n_speeches, and optional type, domain, description.
    subjects: dicts with subject_id, label, names (list), parent_tag, n_speeches.
    members: dicts with id, name, seats (every seat name), seat, state, terms, n_speeches.
    Return a ranked list of results: {"kind": "tag", "place", "subject" or "member", ...}.
    A place is a tag of type place. Two places with one name stay two results: they are two tags."""
    children = defaultdict(list)
    for s in subjects:
        if s["parent_tag"]:
            children[s["parent_tag"]].append(s)
    q = " ".join(sorted(words(query)))
    out = []
    for t in tags:
        texts = [t["tag"]] + t.get("aliases", [])
        if any(matches(query, x) for x in texts):
            exact = any(" ".join(sorted(words(x))) == q for x in texts)
            kids = sorted(children.get(t["tag"], []), key=lambda s: -s["n_speeches"])
            out.append({**tag_fields(t), "name": t["tag"], "exact": exact,
                        "n_speeches": t["n_speeches"] + sum(s["n_speeches"] for s in kids), "subjects": kids})
    for s in subjects:
        if matches(query, s["label"]) or any(matches(query, n) for n in s["names"]):
            exact = " ".join(sorted(words(s["label"]))) == q
            out.append({"kind": "subject", "name": s["label"], "exact": exact, "n_speeches": s["n_speeches"],
                        "parent_tag": s["parent_tag"], "parent_tag_slug": slug(s["parent_tag"]) if s["parent_tag"] else None,
                        "subject_id": s["subject_id"]})
    if not any(r["kind"] in ("tag", "place") for r in out):
        hit, n_hit = defaultdict(int), defaultdict(int)
        hits = [r for r in out if r["kind"] == "subject"]
        for r in hits:
            hit[r["parent_tag"]] += r["n_speeches"]
            n_hit[r["parent_tag"]] += 1
        best = max((t for t in hit if t and n_hit[t] >= 2), key=lambda t: hit[t], default=None)
        if best and hit[best] * 2 >= sum(hit.values()):
            kids = sorted(children[best], key=lambda s: -s["n_speeches"])
            parent = next((t for t in tags if t["tag"] == best), {"tag": best})
            out.append({**tag_fields(parent), "name": best, "exact": True, "via_subjects": True,
                        "n_speeches": sum(s["n_speeches"] for s in kids), "subjects": kids})
    covered = {k["subject_id"] for r in out if r["kind"] in ("tag", "place") and r["exact"] for k in r["subjects"]}
    out = [r for r in out if not (r["kind"] == "subject" and r["subject_id"] in covered)]
    found = []
    for m in members:
        if matches(query, m["name"]) or any(matches(query, x) for x in m["seats"]):
            found.append({"kind": "member", "id": m["id"], "name": m["name"], "seat": m["seat"], "state": m["state"],
                          "seat_label": member_label(m["seat"], m["state"]), "terms": m["terms"],
                          "n_speeches": m["n_speeches"], "exact": " ".join(sorted(words(m["name"]))) == q})
    found.sort(key=lambda r: (not r["exact"], -r["n_speeches"]))
    out += found[:MAX_MEMBERS]
    out.sort(key=lambda r: (not r["exact"], r["kind"] not in ("tag", "place") if r["exact"] else False, -r["n_speeches"]))
    return out[:limit]


def load_index(conn) -> tuple[list, list]:
    """Read the tags and the subjects (tables subjects and subject_names) for search()."""
    names = defaultdict(list)
    for sid, name in conn.execute(text("""SELECT sn.subject_id, en.name FROM subject_names sn
            JOIN entity_names en ON en.id = sn.entity_name_id""")):
        names[sid].append(name)
    subjects = [{"subject_id": sid, "label": label, "names": names[sid], "parent_tag": tag or "", "n_speeches": n}
                for sid, label, tag, n in conn.execute(text("""SELECT s.id, s.label, t.tag, s.n_speeches
            FROM subjects s LEFT JOIN tags t ON t.id = s.parent_tag_id"""))]
    rows = conn.execute(text("""
        SELECT t.tag, t.aliases, count(DISTINCT si.speech_id) n, t.type, t.domain, t.description
        FROM tags t LEFT JOIN entity_names en ON en.tag_id = t.id AND en.link_status = 'linked'
        LEFT JOIN speech_items si ON si.entity_name_id = en.id AND si.kept
        WHERE t.status NOT IN ('rejected', 'merged') GROUP BY t.id""")).fetchall()
    tags = [{"tag": t, "aliases": list(a or []), "n_speeches": n} for t, a, n, ty, dom, desc in rows]
    tags = [{**t, "type": ty, "domain": dom, "description": desc} for t, (_, _, _, ty, dom, desc) in zip(tags, rows)]
    return tags, subjects


def load_members(conn) -> list:
    """Read the members who have at least one speech, for search().

    seat and state are those of the latest term. seats holds the seat names of all terms, so a search for a
    seat finds a member who held it in an older term. n_speeches counts the speeches of the member.
    """
    rows = conn.execute(text("""
        SELECT pe.id, pe.name, n.n, sp.lok_sabha_term, sp.constituency, st.name
        FROM persons pe JOIN (SELECT person_id, count(*) n FROM speeches WHERE person_id IS NOT NULL GROUP BY 1) n
          ON n.person_id = pe.id
        LEFT JOIN speakers sp ON sp.person_id = pe.id LEFT JOIN states st ON st.id = sp.state_id
        ORDER BY pe.id, sp.lok_sabha_term"""))
    out = {}
    for pid, name, n, term, seat, state in rows:
        m = out.setdefault(pid, {"id": pid, "name": name, "n_speeches": n, "seats": [], "terms": [], "seat": None, "state": None})
        if term is not None:
            m["terms"].append(term)
        if seat:
            m["seats"].append(seat)
            m["seat"], m["state"] = seat, state  # rows come in term order: the last one is the latest
    for m in out.values():
        m["terms"] = sorted(set(m["terms"]))
        m["seats"] = sorted(set(m["seats"]))
    return list(out.values())
