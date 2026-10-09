"""Build place tags for the districts of India and the current Lok Sabha constituencies.
This script calls no model and writes nothing to the database.

Reads the Wikipedia pages and the hand-made files in tags/places/data/ and the seed tags.
Writes place_tags.tsv, place_sources.tsv, review_pairs.tsv, review_pairs.md and build_report.md
to tags/places/results/.

Run from the repo root. The -I flag stops Python from loading code from the data folders:

    python3 -I scripts/build_place_tags.py
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
import unicodedata
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from bs4 import BeautifulSoup

from entity_lookup import spelling_key
from scripts.link_entities import norm_name

PLACES = ROOT / "tags" / "places"
SEED_FILE = ROOT / "tags" / "seed_tags_v1" / "results" / "seed_tags_v1.tsv"
DISTRICTS_FILE = PLACES / "data" / "raw" / "districts" / "List_of_districts_in_India.html"
CONSTITUENCIES_FILE = PLACES / "data" / "raw" / "constituencies" / "List_of_constituencies_of_the_Lok_Sabha.html"
RENAMES_FILE = PLACES / "data" / "renames.tsv"
COMMON_WORDS_FILE = PLACES / "data" / "common_words.tsv"
HINTS_FILE = PLACES / "data" / "near_hints.tsv"
SAME_PLACE_FILE = PLACES / "data" / "same_place.tsv"
EXTRA_ALIASES_FILE = PLACES / "data" / "extra_aliases.tsv"
OLD_SEATS_FILE = PLACES / "data" / "old_seats.tsv"
ENTITY_NAMES_FILE = PLACES / "results" / "db_entity_names.tsv"
RESULTS = PLACES / "results"
WORD_LIST = Path("/usr/share/dict/words")

SEED_COLUMNS = ["tag", "type", "subtype", "domain", "description", "aliases", "debate_count"]
EXPECTED_CONSTITUENCIES = 543

# The source writes some states with another name. Keys are source names.
STATE_NAMES = {
    "National Capital Territory of Delhi": "Delhi",
    "NCT of Delhi": "Delhi",
    "Andaman and Nicobar": "Andaman and Nicobar Islands",
    "Dadra Nagar Haveli, Daman and Diu": "Dadra and Nagar Haveli and Daman and Diu",
}
# Words that an existing tag may add to a place name, for example `Kachchh Region`.
GENERIC_WORDS = {"region", "district", "city", "state", "area", "division", "basin", "valley", "plateau"}


# ---------------------------------------------------------------- reading the sources

def clean_cell(text: str) -> str:
    text = re.sub(r"\[[^\]]*\]", "", text)
    return " ".join(text.replace("\xa0", " ").split())


def parse_tables(html: str) -> list[tuple[str, list[list[str]]]]:
    soup = BeautifulSoup(html, "html.parser")
    for bad in soup.find_all(["sup", "style"]):
        bad.decompose()
    out, heading = [], ""
    for node in soup.find_all(["h2", "h3", "h4", "table"]):
        if node.name != "table":
            heading = clean_cell(node.get_text(" "))
            continue
        if "wikitable" not in (node.get("class") or []):
            continue
        rows = [[clean_cell(c.get_text(" ")) for c in tr.find_all(["td", "th"])] for tr in node.find_all("tr")]
        out.append((heading, rows))
    return out


def canon_state(name: str) -> str:
    name = clean_cell(name)
    return STATE_NAMES.get(name, name)


def parse_districts(html: str) -> tuple[list[dict], dict[str, int], list[str]]:
    districts, stated, notes = [], {}, []
    for heading, rows in parse_tables(html):
        if rows and rows[0][:2] == ["Administrative division", "Districts"]:
            for r in rows[1:]:
                if len(r) >= 2 and r[1].isdigit():
                    stated[canon_state(r[0])] = int(r[1])
            continue
        header = next((i for i, r in enumerate(rows) if "District" in r), None)
        m = re.match(r"^(.*) \([A-Z]{2}\)$", heading)
        if header is None or not m:
            continue
        col = rows[header].index("District")
        state = canon_state(m.group(1))
        for r in rows[header + 1:]:
            if len(r) > col and r[0].isdigit() and r[col]:
                districts.append({"name": r[col], "state": state, "source_row": f"{heading} #{r[0]}"})
    return districts, stated, notes


def parse_constituencies(html: str) -> tuple[list[dict], list[str]]:
    """Only the first table under each state heading counts. Later tables hold seats from before a delimitation."""
    out, notes, seen = [], [], set()
    for heading, rows in parse_tables(html):
        m = re.match(r"^(.*) \((\d+)\)$", heading)
        if not m or not any("Constituency" in r for r in rows[:1]):
            continue
        state = canon_state(m.group(1))
        data = [r for r in rows if len(r) >= 3 and r[0].isdigit()]
        if state in seen:
            first = data[0][1] if data else "?"
            notes.append(f"skipped a second constituency table for {state} ({len(data)} rows, first row {first})")
            continue
        seen.add(state)
        for r in data:
            name = re.sub(r"\s*\((SC|ST)\)\s*$", "", r[1]).strip()
            out.append({"name": name, "state": state, "reserved": r[2] if r[2] in ("SC", "ST") else "",
                        "source_row": f"{heading} #{r[0]}"})
    return out, notes


def parse_old_constituencies(html: str) -> list[dict]:
    out, seen = [], set()
    for heading, rows in parse_tables(html):
        m = re.match(r"^(.*) \((\d+)\)$", heading)
        if not m or not any("Constituency" in r for r in rows[:1]):
            continue
        state = canon_state(m.group(1))
        if state not in seen:
            seen.add(state)
            continue
        for r in rows:
            if len(r) >= 3 and r[0].isdigit():
                out.append({"name": re.sub(r"\s*\((SC|ST)\)\s*$", "", r[1]).strip(), "state": state,
                            "reserved": r[2] if r[2] in ("SC", "ST") else "",
                            "source_row": f"{heading} (old table) #{r[0]}"})
    return out


def read_tsv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE))


def read_optional(path: Path) -> list[dict]:
    return read_tsv(path) if path.exists() else []


def read_existing(path: Path) -> list[dict]:
    rows = read_tsv(path)
    for r in rows:
        r["alias_list"] = [] if r["aliases"] in ("", "-") else r["aliases"].split("|")
    return rows


def existing_index(rows: list[dict]) -> dict[str, list[tuple[dict, str]]]:
    idx: dict[str, list[tuple[dict, str]]] = defaultdict(list)
    for r in rows:
        for n in {norm_name(r["tag"])}:
            idx[n].append((r, "name"))
        for a in r["alias_list"]:
            if norm_name(a) != norm_name(r["tag"]):
                idx[norm_name(a)].append((r, "alias"))
    return idx


def near_key(name: str) -> str:
    words = name.replace("&", " and ").split()
    while len(words) > 1 and words[-1].casefold() in GENERIC_WORDS:
        words.pop()
    return spelling_key(" ".join(words))


def ascii_fold(name: str) -> str:
    return "".join(ch for ch in unicodedata.normalize("NFKD", name) if not unicodedata.combining(ch))


# ---------------------------------------------------------------- building the tags

def load_renames(path: Path) -> list[dict]:
    return read_tsv(path) if path.exists() else []


def dash_forms(name: str) -> list[str]:
    if "\u2013" in name:
        return [name.replace("\u2013", "-")]
    if "-" in name:
        return [name.replace("-", "\u2013")]
    return []


def pkey(state: str, name: str) -> tuple[str, str]:
    return state, norm_name(name.replace("\u2013", "-").replace("\u2014", "-"))


def group_places(districts: list[dict], constituencies: list[dict], renames: list[dict]):
    groups: dict[tuple[str, str], dict] = {}

    def get(name: str, state: str) -> dict:
        key = pkey(state, name)
        return groups.setdefault(key, {"name": name, "state": state, "kinds": set(), "reserved": "",
                                       "sources": [], "old_names": [], "alt_names": [], "notes": []})

    # A district that the source lists under an old name gets the new name. The old name becomes an alias.
    rename_of = {pkey(r["state"], r["old_name"]): r for r in renames}
    district_keys = {pkey(d["state"], d["name"]) for d in districts}
    for d in districts:
        r = rename_of.get(pkey(d["state"], d["name"]))
        name = d["name"]
        if r and pkey(d["state"], r["new_name"]) not in district_keys:
            name = r["new_name"]
        g = get(name, d["state"])
        g["kinds"].add("district")
        g["sources"].append(d["source_row"])
    old_to_new = {}
    for r in renames:
        key = pkey(r["state"], r["new_name"])
        if key in groups:
            old_to_new[pkey(r["state"], r["old_name"])] = key
    for c in constituencies:
        key = pkey(c["state"], c["name"])
        if key not in groups and key in old_to_new:
            # The constituency still has the old name of a renamed district. It joins the district.
            g = groups[old_to_new[key]]
            g["notes"].append(f"The constituency is listed as {c['name']}.")
        else:
            g = get(c["name"], c["state"])
        g["kinds"].add("constituency")
        g["reserved"] = c["reserved"]
        g["sources"].append(c["source_row"])
    used = set()
    for r in renames:
        key = pkey(r["state"], r["new_name"])
        if key in groups:
            g = groups[key]
            if r["old_name"] not in g["old_names"]:
                g["old_names"].append(r["old_name"])
            used.add((r["old_name"], r["state"]))
    unused = [r for r in renames if (r["old_name"], r["state"]) not in used]
    return groups, unused


def apply_same_place(groups: dict, rows: list[dict]) -> list[str]:
    log = []
    for r in rows:
        ka, kb = pkey(r["state"], r["name_a"]), pkey(r["state"], r["name_b"])
        kk = pkey(r["state"], r["keep"])
        if ka not in groups or kb not in groups or kk not in (ka, kb):
            raise ValueError(f"same_place.tsv: bad row {r}")
        drop = kb if kk == ka else ka
        keep_g, drop_g = groups[kk], groups.pop(drop)
        if keep_g["kinds"] & drop_g["kinds"]:
            raise ValueError(f"same_place.tsv: both names are the same kind of place: {r}")
        what = "constituency" if "constituency" in drop_g["kinds"] else "district"
        keep_g["kinds"] |= drop_g["kinds"]
        keep_g["sources"] += drop_g["sources"]
        keep_g["reserved"] = keep_g["reserved"] or drop_g["reserved"]
        keep_g["old_names"] += [o for o in drop_g["old_names"] if o not in keep_g["old_names"]]
        keep_g["alt_names"] += [drop_g["name"], *drop_g["alt_names"]]
        keep_g["notes"].append(f"The {what} is listed as {drop_g['name']}.")
        log.append(f"{r['state']}: {keep_g['name']} (kept) and {drop_g['name']} are one place")
    return log


def apply_old_seats(groups: dict, old_seats: list[dict], decisions: list[dict]) -> list[str]:
    by_seat = {(d["state"], norm_name(d["old_name"])): d for d in decisions}
    log = []
    for s in old_seats:
        d = by_seat.get((s["state"], norm_name(s["name"])))
        if d is None:
            raise ValueError(f"old_seats.tsv has no row for the old seat {s['name']!r} ({s['state']})")
        key = pkey(s["state"], s["name"])
        if d["decision"] == "same":
            known = key in groups or any(norm_name(n) == key[1] for g in groups.values() if g["state"] == s["state"]
                                         for n in [*g["old_names"], *g["alt_names"]])
            if not known:
                raise ValueError(f"old_seats.tsv: {s['name']!r} is marked `same` but no current place has this name")
        elif d["decision"] == "alias":
            tk = pkey(s["state"], d["target"])
            if tk not in groups:
                raise ValueError(f"old_seats.tsv: target {d['target']!r} not found for {s['name']!r}")
            groups[tk]["alt_names"].append(s["name"])
            groups[tk]["notes"].append(f"The old constituency was named {s['name']}.")
        elif d["decision"] == "ignore":
            pass
        elif d["decision"] == "former":
            # A filled `target` is the tag name to use instead of the old name (for a name that is also an ordinary phrase).
            name = d["target"] or s["name"]
            key = pkey(s["state"], name)
            if key in groups:
                raise ValueError(f"old_seats.tsv: {s['name']!r} is marked `former` but a current place has this name")
            g = {"name": name, "state": s["state"], "kinds": {"former_constituency"}, "reserved": s["reserved"],
                 "sources": [s["source_row"]], "old_names": [], "alt_names": [], "notes": []}
            groups[key] = g
        else:
            raise ValueError(f"old_seats.tsv: unknown decision {d['decision']!r}")
        log.append(f"{s['state']}: {s['name']} -> {d['decision']}" + (f" {d['target']}" if d["target"] else ""))
    return log


def subtype_of(kinds: set[str]) -> str:
    return "district_constituency" if kinds == {"district", "constituency"} else next(iter(kinds))


def description_of(g: dict) -> str:
    what = {"district": "District", "constituency": "Lok Sabha constituency",
            "district_constituency": "District and Lok Sabha constituency",
            "former_constituency": "Former Lok Sabha constituency"}[subtype_of(g["kinds"])]
    until = " (until 2024)" if g["kinds"] == {"former_constituency"} else ""
    return " ".join([f"{what} in {g['state']}, India{until}.", *g["notes"]])


def build(districts, constituencies, renames, existing_rows, common_words=(), entity_names=None, word_list=None, hints=(),
          same_place=(), extra_aliases=(), old_seats=(), old_decisions=()):
    entity_names = entity_names or {}
    idx = existing_index(existing_rows)
    groups, unused_renames = group_places(districts, constituencies, renames)
    log = {"merged": apply_same_place(groups, list(same_place)),
           "old_seats": apply_old_seats(groups, list(old_seats), list(old_decisions))}

    # Claims on a bare name: the current name of a place, or an old name of a renamed place.
    claims: dict[str, set] = defaultdict(set)
    for key, g in groups.items():
        claims[norm_name(g["name"])].add(key)
        for old in g["old_names"]:
            claims[norm_name(old)].add(key)
    shared = {n: ks for n, ks in claims.items() if len({k[0] for k in ks}) >= 2}

    tags, skipped, review = [], [], []
    for key in sorted(groups, key=lambda k: (k[0], k[1])):
        g = groups[key]
        bare = g["name"]
        bare_norm = norm_name(bare)
        subtype = subtype_of(g["kinds"])
        # 1. existing tag with the same name or alias: no new tag
        hits = idx.get(bare_norm, [])
        if hits:
            skipped.append(g)
            for r, how in hits:
                review.append(row("existing_exact", bare, g["state"], subtype, r["tag"], r["type"], r["subtype"],
                                  f"equals the {how} of an existing tag. No new tag."))
            continue
        is_shared = bare_norm in shared
        name = f"{bare} ({g['state']})" if is_shared else bare
        aliases: list[str] = []
        if is_shared:
            aliases.append(bare)
        for old in g["old_names"]:
            aliases.append(old)
        aliases.extend(g["alt_names"])
        folded = ascii_fold(bare)
        if folded != bare:
            aliases.append(folded)
        aliases.extend(dash_forms(bare))
        # drop an alias that an existing tag already uses
        kept = []
        for a in aliases:
            h = idx.get(norm_name(a), [])
            if h:
                for r, how in h:
                    review.append(row("existing_exact", a, g["state"], subtype, r["tag"], r["type"], r["subtype"],
                                      f"alias of the new tag {name!r} equals the {how} of an existing tag. Alias dropped."))
            elif norm_name(a) != norm_name(name) and norm_name(a) not in {norm_name(x) for x in kept}:
                kept.append(a)
        tags.append({"tag": name, "type": "place", "subtype": subtype, "domain": "-", "description": description_of(g),
                     "aliases": kept, "debate_count": 0, "bare": bare, "state": g["state"], "kinds": g["kinds"],
                     "reserved": g["reserved"], "sources": g["sources"], "old_names": g["old_names"],
                     "alt_names": g["alt_names"], "extra_aliases": [], "shared": is_shared})

    by_tag = {t["tag"]: t for t in tags}
    for e in extra_aliases:
        t = by_tag.get(e["tag"])
        if t is None:
            raise ValueError(f"extra_aliases.tsv: no new tag named {e['tag']!r} (alias {e['alias']!r})")
        if norm_name(e["alias"]) not in {norm_name(a) for a in [t["tag"], *t["aliases"]]}:
            t["aliases"].append(e["alias"])
            t["extra_aliases"].append(e["alias"])
    log["extra_aliases"] = sum(len(t["extra_aliases"]) for t in tags)

    by_bare: dict[str, list[dict]] = defaultdict(list)
    for t in tags:
        by_bare[norm_name(t["bare"])].append(t)
    for n, ts in by_bare.items():
        if n in shared:
            for t in ts:
                others = [o["tag"] for o in ts if o is not t]
                others += [groups[k]["name"] + f" ({groups[k]['state']}, old name)" for k in shared[n]
                           if norm_name(groups[k]["name"]) != n]
                review.append(row("shared_name", t["tag"], t["state"], t["subtype"], "|".join(others), "place", "",
                                  f"bare name {t['bare']!r} is an alias of every tag in the group. The decision model decides."))
    for t in tags:
        for old in t["old_names"]:
            review.append(row("rename", t["tag"], t["state"], t["subtype"], old, "", "",
                              f"alias {old!r} is the old name of this place"))

    review += near_rows(tags, existing_rows, idx)
    review += common_word_rows(tags, common_words, entity_names, word_list)
    review += hint_rows(tags, hints, idx)
    seen, unique = set(), []
    for r in review:
        key = (r["kind"], r["place"], r["other_tag"], r["other_type"], r["detail"].split(":")[0])
        if key not in seen:
            seen.add(key)
            unique.append(r)
    review = unique
    return {"tags": tags, "skipped": skipped, "review": review, "unused_renames": unused_renames,
            "groups": groups, "idx": idx, "log": log}


REVIEW_COLUMNS = ["kind", "place", "state", "place_subtype", "other_tag", "other_type", "other_subtype", "detail", "review"]


def row(kind, place, state, subtype, other, other_type, other_subtype, detail):
    return dict(zip(REVIEW_COLUMNS, [kind, place, state, subtype, other, other_type, other_subtype, detail, ""]))


def near_rows(tags: list[dict], existing_rows: list[dict], idx) -> list[dict]:
    out = []
    keys: dict[str, list[tuple[dict, str]]] = defaultdict(list)
    for r in existing_rows:
        for n in [r["tag"], *r["alias_list"]]:
            k = near_key(n)
            if k:
                keys[k].append((r, n))
    for t in tags:
        for name in [t["bare"], *t["alt_names"]]:
            for r, n in keys.get(near_key(name), []):
                if norm_name(n) != norm_name(name):
                    out.append(row("existing_near", t["tag"], t["state"], t["subtype"], r["tag"], r["type"], r["subtype"],
                                   f"the spelling key of {name!r} equals the key of {n!r}"))
    by_state_key: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for t in tags:
        by_state_key[(t["state"], near_key(t["bare"]))].append(t)
    for ts in by_state_key.values():
        if len(ts) > 1:
            for t in ts:
                out.append(row("new_near", t["tag"], t["state"], t["subtype"],
                               "|".join(o["tag"] for o in ts if o is not t), "place", "",
                               "two new tags of one state have the same spelling key. They may be one place."))
    return out


def hint_rows(tags: list[dict], hints, idx) -> list[dict]:
    out = []
    by_bare = {(t["state"], norm_name(n)): t for t in tags for n in [t["bare"], *t["alt_names"]]}
    by_name = {norm_name(t["tag"]): t for t in tags}
    for h in hints:
        t = by_bare.get((h["state"], norm_name(h["place"])))
        if t is None:
            continue
        o = norm_name(h["other"])
        if o in idx:
            r = idx[o][0][0]
            out.append(row("existing_near", t["tag"], t["state"], t["subtype"], r["tag"], r["type"], r["subtype"],
                           "hand-made hint: " + h["note"]))
        elif o in by_name:
            out.append(row("new_near", t["tag"], t["state"], t["subtype"], by_name[o]["tag"], "place", "",
                           "hand-made hint: " + h["note"]))
    return out


def read_word_list(path: Path) -> set[str]:
    if not path.exists():
        return set()
    return {w for w in path.read_text(encoding="utf-8", errors="ignore").split() if w.islower() and len(w) >= 3}


def common_word_rows(tags, common_words, entity_names, word_list) -> list[dict]:
    out = []
    hand = {norm_name(w["word"]): w["meaning"] for w in common_words}
    for t in tags:
        n = norm_name(t["bare"])
        if word_list and n in word_list and " " not in n:
            out.append(row("common_word", t["tag"], t["state"], t["subtype"], "", "", "",
                           "method english_word: the name is an English word in the system word list"))
        if n in hand:
            out.append(row("common_word", t["tag"], t["state"], t["subtype"], "", "", "",
                           f"method hand_list: {hand[n]}"))
        for typ, count in entity_names.get(n, []):
            out.append(row("common_word", t["tag"], t["state"], t["subtype"], "", typ, "",
                           f"method entity_name: {count} speech items use this name with type {typ}"))
    return out


# ---------------------------------------------------------------- checks

def count_warnings(districts: list[dict], stated: dict[str, int]) -> list[str]:
    per_state: dict[str, int] = defaultdict(int)
    for d in districts:
        per_state[d["state"]] += 1
    out = []
    for state, n in stated.items():
        if state != "Total" and per_state.get(state, 0) != n:
            out.append(f"{state}: the overview table states {n} districts, the state table has {per_state.get(state, 0)}")
    for state in per_state:
        if state not in stated:
            out.append(f"{state}: the state table has districts but the overview table states no count")
    if stated.get("Total") is not None and stated["Total"] != len(districts):
        out.append(f"total: the overview table states {stated['Total']} districts, the state tables have {len(districts)}")
    return out


def check(result: dict, constituencies: list[dict], districts: list[dict], stated: dict[str, int], existing_rows) -> list[str]:
    faults = []
    tags, idx = result["tags"], result["idx"]
    names: dict[str, str] = {}
    for t in tags:
        n = norm_name(t["tag"])
        if n in names:
            faults.append(f"two new tags have the same normalised name: {t['tag']!r} and {names[n]!r}")
        names[n] = t["tag"]
        if n in idx:
            faults.append(f"new tag name equals an existing tag: {t['tag']!r}")
    for t in tags:
        for a in t["aliases"]:
            na = norm_name(a)
            if na in idx:
                faults.append(f"alias {a!r} of {t['tag']!r} equals an existing tag name or alias")
            if na in names and names[na] != t["tag"]:
                faults.append(f"alias {a!r} of {t['tag']!r} equals the name of the new tag {names[na]!r}")
    # An alias shared by several new tags must be an intended bare name or an old name of a shared group.
    alias_owner: dict[str, list[str]] = defaultdict(list)
    for t in tags:
        for a in t["aliases"]:
            alias_owner[norm_name(a)].append(t["tag"])
    shared_bare = {norm_name(t["bare"]) for t in tags if t["shared"]}
    for a, owners in alias_owner.items():
        if len(owners) > 1 and a not in shared_bare and a not in {norm_name(o) for t in tags for o in t["old_names"]}:
            faults.append(f"alias {a!r} belongs to several new tags {owners} and is not an intended shared name")
    n_con = len(constituencies)
    if n_con != EXPECTED_CONSTITUENCIES:
        faults.append(f"{n_con} constituency rows, expected {EXPECTED_CONSTITUENCIES}")
    per_state: dict[str, int] = defaultdict(int)
    for d in districts:
        per_state[d["state"]] += 1
    dup = defaultdict(list)
    for d in districts:
        dup[(d["state"], norm_name(d["name"]))].append(d["source_row"])
    for k, v in dup.items():
        if len(v) > 1:
            faults.append(f"the same district name twice in one state: {k} {v}")
    cdup = defaultdict(list)
    for c in constituencies:
        cdup[(c["state"], norm_name(c["name"]))].append(c["source_row"])
    for k, v in cdup.items():
        if len(v) > 1:
            faults.append(f"the same constituency name twice in one state: {k} {v}")
    return faults


# ---------------------------------------------------------------- writing

def write_tsv(path: Path, columns: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", quoting=csv.QUOTE_NONE, quotechar=None, lineterminator="\n", escapechar="\\")
        w.writerow(columns)
        for r in rows:
            w.writerow([r[c] for c in columns])


def tag_rows(tags: list[dict]) -> list[dict]:
    return [{"tag": t["tag"], "type": t["type"], "subtype": t["subtype"], "domain": t["domain"],
             "description": t["description"], "aliases": "|".join(t["aliases"]) or "-", "debate_count": 0}
            for t in tags]


def report_text(result, districts, constituencies, warnings, notes, faults, sources) -> str:
    tags = result["tags"]
    kinds = defaultdict(int)
    for t in tags:
        kinds[t["subtype"]] += 1
    rev = defaultdict(int)
    for r in result["review"]:
        rev[r["kind"]] += 1
    per_state = defaultdict(lambda: defaultdict(int))
    for t in tags:
        per_state[t["state"]][t["subtype"]] += 1
    skipped = defaultdict(int)
    for g in result["skipped"]:
        skipped[state_kind(g)] += 1
    lines = [f"# Place tags build report ({date.today().isoformat()})", "",
             f"Source rows: {len(districts)} districts, {len(constituencies)} constituencies.", "",
             f"New tags: {len(tags)}. By subtype: " + ", ".join(f"{k} {v}" for k, v in sorted(kinds.items())) + ".",
             f"Skipped places (an existing tag has the name or an alias): {len(result['skipped'])}.",
             f"Tags with the state in the name (shared names): {sum(1 for t in tags if t['shared'])}.",
             f"Aliases from renames.tsv in use: {sum(len(t['old_names']) for t in tags)}.",
             f"Unused rename rows (new name not in the source): {len(result['unused_renames'])}.",
             f"Pairs merged by same_place.tsv: {len(result['log']['merged'])}.",
             f"Aliases added by extra_aliases.tsv: {result['log']['extra_aliases']}.",
             f"Former constituency tags (old_seats.tsv): {sum(1 for t in tags if t['subtype'] == 'former_constituency')}.", "",
             "Review rows by kind: " + ", ".join(f"{k} {v}" for k, v in sorted(rev.items())) + ".", "",
             "## Self checks", ""]
    lines += [f"- FAULT: {f}" for f in faults] or ["- All checks passed."]
    if warnings or notes:
        lines += ["", "## Warnings about the source", ""] + [f"- {n}" for n in warnings + notes]
    if result["log"]["merged"]:
        lines += ["", "## Merged pairs (same_place.tsv)", ""] + [f"- {m}" for m in result["log"]["merged"]]
    if result["log"]["old_seats"]:
        lines += ["", "## Seats of the old constituency table (old_seats.tsv)", ""] + [f"- {m}" for m in result["log"]["old_seats"]]
    if result["unused_renames"]:
        lines += ["", "## Unused rename rows", ""] + [f"- {r['old_name']} to {r['new_name']} ({r['state']})" for r in result["unused_renames"]]
    lines += ["", "## Counts for each state (new tags)", "", "| State | district | constituency | district_constituency |", "|---|---|---|---|"]
    for s in sorted(per_state):
        c = per_state[s]
        lines.append(f"| {s} | {c['district']} | {c['constituency']} | {c['district_constituency']} |")
    lines += ["", "## Sources", ""] + [f"- {s}" for s in sources]
    return "\n".join(lines) + "\n"


def state_kind(g: dict) -> str:
    return subtype_of(g["kinds"])


def review_md(rows: list[dict]) -> str:
    out = ["# Review pairs", "",
           "Each row is a possible duplicate or risk. Fill the column `review` in `review_pairs.tsv`. "
           "This file is a short view. The first 15 rows of each kind are here.", ""]
    for kind in ["existing_exact", "existing_near", "shared_name", "common_word", "rename", "new_near"]:
        sub = [r for r in rows if r["kind"] == kind]
        out += [f"## {kind} ({len(sub)} rows)", ""]
        if not sub:
            out += ["No rows.", ""]
            continue
        out += ["| place | state | other tag | other type | detail |", "|---|---|---|---|---|"]
        for r in sub[:15]:
            out.append(f"| {r['place']} | {r['state']} | {r['other_tag']} | {r['other_type']} {r['other_subtype']} | {r['detail']} |")
        out.append("")
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--districts", type=Path, default=DISTRICTS_FILE)
    ap.add_argument("--constituencies", type=Path, default=CONSTITUENCIES_FILE)
    ap.add_argument("--renames", type=Path, default=RENAMES_FILE)
    ap.add_argument("--seed", type=Path, default=SEED_FILE)
    ap.add_argument("--out", type=Path, default=RESULTS)
    args = ap.parse_args()

    districts, stated, _ = parse_districts(args.districts.read_text(encoding="utf-8"))
    constituencies, notes = parse_constituencies(args.constituencies.read_text(encoding="utf-8"))
    existing = read_existing(args.seed)
    renames = load_renames(args.renames)
    common = read_tsv(COMMON_WORDS_FILE) if COMMON_WORDS_FILE.exists() else []
    hints = read_tsv(HINTS_FILE) if HINTS_FILE.exists() else []
    entity_names: dict[str, list[tuple[str, int]]] = defaultdict(list)
    if ENTITY_NAMES_FILE.exists():
        for r in read_tsv(ENTITY_NAMES_FILE):
            entity_names[r["norm_name"]].append((r["type"], int(r["n_items"])))
    html_old = args.constituencies.read_text(encoding="utf-8")
    result = build(districts, constituencies, renames, existing, common, entity_names, read_word_list(WORD_LIST), hints,
                   read_optional(SAME_PLACE_FILE), read_optional(EXTRA_ALIASES_FILE),
                   parse_old_constituencies(html_old), read_optional(OLD_SEATS_FILE))
    faults = check(result, constituencies, districts, stated, existing)

    args.out.mkdir(parents=True, exist_ok=True)
    write_tsv(args.out / "place_tags.tsv", SEED_COLUMNS, tag_rows(result["tags"]))
    write_tsv(args.out / "place_sources.tsv", ["tag", "state", "subtype", "reserved", "old_names", "source_rows"],
              [{"tag": t["tag"], "state": t["state"], "subtype": t["subtype"], "reserved": t["reserved"] or "-",
                "old_names": "|".join(t["old_names"]) or "-", "source_rows": "|".join(t["sources"])} for t in result["tags"]])
    order = {k: i for i, k in enumerate(["existing_exact", "existing_near", "shared_name", "common_word", "rename", "new_near"])}
    review = sorted(result["review"], key=lambda r: (order[r["kind"]], r["state"], r["place"]))
    write_tsv(args.out / "review_pairs.tsv", REVIEW_COLUMNS, review)
    (args.out / "review_pairs.md").write_text(review_md(review), encoding="utf-8")
    sources = ["Districts: https://en.wikipedia.org/wiki/List_of_districts_in_India (fallback, see tags/places/README.md)",
               "Constituencies: https://en.wikipedia.org/wiki/List_of_constituencies_of_the_Lok_Sabha (fallback, see tags/places/README.md)"]
    (args.out / "build_report.md").write_text(report_text(result, districts, constituencies, count_warnings(districts, stated), notes, faults, sources), encoding="utf-8")
    print(f"{len(result['tags'])} new tags, {len(result['skipped'])} skipped, {len(review)} review rows, {len(faults)} faults")
    for f in faults:
        print("FAULT:", f)
    if faults:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
