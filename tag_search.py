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

from pages.common import SPEECH_TAGS_CTE, slug

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


MAX_NAMED = 3


def name_key(text: str) -> tuple:
    """The stems of all the words of a text, in order. Short function words stay, so that a run of words must be the whole name."""
    return tuple(stem(w) for w in re.findall(r"[^\W_]+", text.replace("'", "")))


def named_pages(query: str, tags: list, limit: int = MAX_NAMED) -> list:
    """The places and tags whose whole name is a run of words in the query: the cards above the search results.

    1. Walk the query from the left. At each word, take the longest run of words that is the name or an alias of a tag.
       The words of that run are used. A word that starts no name is skipped.
    2. A place wins over a tag with the same name. Two places or two tags with one name are left out,
       because a wrong page is worse than no page.
    3. Order: places first, then tags with the fewest speeches first, because a smaller tag is usually more specific.
    Example: "raipur corruption" gives the place Raipur, then the tag Corruption.
    """
    index = defaultdict(list)
    for t in tags:
        if not t.get("n_speeches"):
            continue
        for x in [t["tag"]] + t.get("aliases", []):
            key = name_key(x)
            if key and not all(w in STOP for w in key) and t not in index[key]:
                index[key].append(t)
    longest = max((len(k) for k in index), default=0)
    words_ = name_key(query)
    found, i = [], 0
    while i < len(words_):
        for n in range(min(longest, len(words_) - i), 0, -1):
            hits = index.get(words_[i:i + n])
            if hits:
                places = [t for t in hits if t.get("type") == "place"]
                pick = places or hits
                if len(pick) == 1 and pick[0] not in found:
                    found.append(pick[0])
                i += n
                break
        else:
            i += 1
    found.sort(key=lambda t: (t.get("type") != "place", t["n_speeches"]))
    return [{**tag_fields(t), "name": t["tag"], "n_speeches": t["n_speeches"]} for t in found[:limit]]


MAX_SUGGESTED = 5
# The largest cosine distance of a suggested tag. Real searches had their good tags at 0.25 to 0.36.
# Text with no topic, such as "the" or "asdf qwerty", had its nearest tag at 0.387 or more.
MAX_SUGGESTED_DISTANCE = 0.36


def nearest_tag_ids(conn, vector: str, model: str, limit: int = 20) -> list:
    """The ids and distances of the tags nearest in meaning to a search vector, nearest first."""
    return [(r.tag_id, r.distance) for r in conn.execute(text("""
        SELECT tag_id, embedding <=> CAST(:v AS vector) AS distance FROM tag_embeddings
        WHERE task_type = 'RETRIEVAL_DOCUMENT' AND model = :m ORDER BY distance LIMIT :lim"""),
        {"v": vector, "m": model, "lim": limit})]


def suggested_tags(nearest: list, tags: list, skip=(), limit: int = MAX_SUGGESTED,
                   max_distance: float = MAX_SUGGESTED_DISTANCE) -> list:
    """The tags near the search in meaning, for the chips above the results. Example: "farmers suicide" suggests
    Farmers' Suicide and Farmers' Debt. nearest is a list of (tag id, distance). A tag with no speeches, a tag
    that is not live, and a tag in skip (slugs that have a card already) are left out."""
    by_id = {t["id"]: t for t in tags if t.get("id") is not None}
    out = []
    for tag_id, distance in nearest:
        t = by_id.get(tag_id)
        if distance > max_distance or not t or not t["n_speeches"]:
            continue
        page = {**tag_fields(t), "name": t["tag"], "n_speeches": t["n_speeches"], "distance": round(distance, 3)}
        if page["slug"] in skip:
            continue
        out.append(page)
        if len(out) == limit:
            break
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
                        "n_speeches": t["n_speeches"], "subjects": kids})
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
                        "n_speeches": parent.get("n_speeches", 0), "subjects": kids})
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
    # n_speeches is the rule of the tag page: each speech once. A speech under a subject is also a speech of its tag.
    rows = conn.execute(text(f"""
        WITH {SPEECH_TAGS_CTE}, counts AS (SELECT tag_id, count(*) n FROM speech_tags GROUP BY tag_id)
        SELECT t.id, t.tag, t.aliases, COALESCE(c.n, 0) n, t.type, t.domain, t.description
        FROM tags t LEFT JOIN counts c ON c.tag_id = t.id
        WHERE t.status NOT IN ('rejected', 'merged')""")).fetchall()
    tags = [{"id": i, "tag": t, "aliases": list(a or []), "n_speeches": n, "type": ty, "domain": dom, "description": desc}
            for i, t, a, n, ty, dom, desc in rows]
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
