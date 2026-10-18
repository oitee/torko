"""Search tags and subjects with one query. A prototype of the two-level search.

The rule:
1. Word match. A query word matches a word of a text when both have the same stem (lower case, without
   punctuation and a final "s"). A text matches when it holds every query word.
2. A tag matches when its name or an alias matches. A subject matches when its label or one of its names matches.
3. The result for a tag is the tag and every subject whose parent is that tag.
   The result for a subject is the subject, with its parent tag for context.
4. Ranking: a tag whose name is exactly the query comes first. Then subjects and tags by the number of speeches.
   When no tag matches by its own name, the query can still mean a tag: when 2 or more matching subjects share one
   parent tag, and that tag holds at least half of the speeches of all matching subjects. That tag comes first with
   its subjects. Example: "MGNREGA" matches several subjects of the tag that says "MNREGA".
   "farmers arrears" matches one subject of the tag Arrears, so it stays a subject result.
5. With --vector, a query with no word match goes to a vector search over subject centres (one embedding call).

    source .venv/bin/activate && set -a && source .env && set +a
    python3 scripts/subject_search.py "arrears"
    python3 scripts/subject_search.py "farmers arrears"
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

RESULTS = Path(__file__).resolve().parent.parent / "tags" / "subject_groups" / "results"
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


def search(query: str, tags: list, subjects: list, limit: int = 10) -> list:
    """tags: dicts with tag, aliases (list), n_speeches. subjects: dicts with subject_id, label, names (list), parent_tag, n_speeches.
    Return a ranked list of results: {"kind": "tag" or "subject", ...}."""
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
            out.append({"kind": "tag", "name": t["tag"], "exact": exact,
                        "n_speeches": t["n_speeches"] + sum(s["n_speeches"] for s in kids), "subjects": kids})
    for s in subjects:
        if matches(query, s["label"]) or any(matches(query, n) for n in s["names"]):
            exact = " ".join(sorted(words(s["label"]))) == q
            out.append({"kind": "subject", "name": s["label"], "exact": exact, "n_speeches": s["n_speeches"],
                        "parent_tag": s["parent_tag"], "subject_id": s["subject_id"]})
    if not any(r["kind"] == "tag" for r in out):
        hit, n_hit = defaultdict(int), defaultdict(int)
        hits = [r for r in out if r["kind"] == "subject"]
        for r in hits:
            hit[r["parent_tag"]] += r["n_speeches"]
            n_hit[r["parent_tag"]] += 1
        best = max((t for t in hit if t and n_hit[t] >= 2), key=lambda t: hit[t], default=None)
        if best and hit[best] * 2 >= sum(hit.values()):
            kids = sorted(children[best], key=lambda s: -s["n_speeches"])
            out.append({"kind": "tag", "name": best, "exact": True, "via_subjects": True,
                        "n_speeches": sum(s["n_speeches"] for s in kids), "subjects": kids})
    covered = {k["subject_id"] for r in out if r["kind"] == "tag" and r["exact"] for k in r["subjects"]}
    out = [r for r in out if not (r["kind"] == "subject" and r["subject_id"] in covered)]
    out.sort(key=lambda r: (not r["exact"], r["kind"] != "tag" if r["exact"] else False, -r["n_speeches"]))
    return out[:limit]


def load(conn) -> tuple[list, list]:
    from sqlalchemy import text
    labels = {}
    lp = RESULTS / "subject_labels_v1.tsv"
    if lp.exists():
        labels = {r["subject_id"]: r["label"] for r in csv.DictReader(lp.open(), delimiter="\t")}
    subjects = []
    for r in csv.DictReader((RESULTS / "subjects_v1.tsv").open(), delimiter="\t"):
        subjects.append({"subject_id": r["subject_id"], "label": labels.get(r["subject_id"], r["label_auto"]),
                         "names": [n.rsplit(" (", 1)[0] for n in r["names"].split(" | ")],
                         "parent_tag": r["parent_tag"], "n_speeches": int(r["n_speeches"])})
    rows = conn.execute(text("""
        SELECT t.tag, t.aliases, count(DISTINCT si.speech_id) n
        FROM tags t LEFT JOIN entity_names en ON en.tag_id = t.id AND en.link_status = 'linked'
        LEFT JOIN speech_items si ON si.entity_name_id = en.id AND si.kept
        WHERE t.status <> 'rejected' GROUP BY t.id""")).fetchall()
    tags = [{"tag": t, "aliases": list(a or []), "n_speeches": n} for t, a, n in rows]
    return tags, subjects


def main() -> None:
    from db import get_engine
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("query", nargs="+")
    args = ap.parse_args()
    with get_engine().connect() as conn:
        tags, subjects = load(conn)
    for q in args.query:
        print(f"\n=== {q}")
        for r in search(q, tags, subjects):
            if r["kind"] == "tag":
                print(f"TAG {r['name']} ({r['n_speeches']} speeches with its subjects)")
                for s in r["subjects"][:8]:
                    print(f"    subject: {s['label']} ({s['n_speeches']})")
            else:
                print(f"SUBJECT {r['name']} ({r['n_speeches']}) under tag: {r['parent_tag'] or '-'}")


if __name__ == "__main__":
    main()
