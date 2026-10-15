from __future__ import annotations

import csv
import random
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from db import get_engine
from scripts.build_place_tags import PLACES, RESULTS, SEED_FILE, existing_index, read_existing, read_tsv
from scripts.link_entities import MODEL_ONLY, norm_name


def tag_index(rows: list[dict]) -> dict[str, set[str]]:
    idx: dict[str, set[str]] = defaultdict(set)
    for r in rows:
        aliases = [] if r["aliases"] in ("", "-") else r["aliases"].split("|")
        for n in [r["tag"], *aliases]:
            idx[norm_name(n)].add(r["tag"])
    return idx


def main() -> None:
    new_rows = read_tsv(RESULTS / "place_tags.tsv")
    new_idx = tag_index(new_rows)
    old_idx = {n: {r["tag"] for r, _ in hits} for n, hits in existing_index(read_existing(SEED_FILE)).items()}
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text("SET TRANSACTION READ ONLY"))
        rows = conn.execute(text("""
            SELECT name, count(*) AS n, count(*) FILTER (WHERE kept) AS n_kept
            FROM speech_items WHERE type = 'place' AND list = 'other' AND source = 'llm' GROUP BY name""")).all()
        names: dict[str, dict] = defaultdict(lambda: {"n": 0, "kept": 0, "forms": defaultdict(int)})
        for r in rows:
            d = names[norm_name(r.name)]
            d["n"] += r.n
            d["kept"] += r.n_kept
            d["forms"][r.name] += r.n
        others = conn.execute(text("""
            SELECT name, type, count(*) AS n FROM speech_items
            WHERE type <> 'place' AND list = 'other' AND source = 'llm' GROUP BY name, type""")).all()
        groups: dict[str, list[str]] = defaultdict(list)
        for n, d in names.items():
            k = "new1" if len(new_idx.get(n, ())) == 1 else "new2" if len(new_idx.get(n, ())) > 1 else \
                "existing" if n in old_idx else "nothing"
            groups[k].append(n)
        examples = {}
        rnd = random.Random(7)
        pick = rnd.sample(sorted(groups["new1"]), min(20, len(groups["new1"])))
        for n in pick:
            ex = conn.execute(text("""
                SELECT mention FROM speech_items WHERE type = 'place' AND list = 'other' AND source = 'llm' AND lower(name) = :n
                AND mention IS NOT NULL LIMIT 1"""), {"n": next(iter(names[n]["forms"])).lower()}).scalar()
            examples[n] = " ".join((ex or "").split())[:150]

    other_hits = defaultdict(int)
    with (RESULTS / "db_entity_names.tsv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", quoting=csv.QUOTE_NONE, quotechar=None, lineterminator="\n", escapechar="\\")
        w.writerow(["norm_name", "type", "n_items"])
        agg: dict[tuple[str, str], int] = defaultdict(int)
        for r in others:
            n = norm_name(r.name)
            if n in new_idx:
                agg[(n, r.type)] += r.n
        for (n, t), c in sorted(agg.items()):
            w.writerow([n, t, c])

    with (RESULTS / "db_unmatched_names.tsv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", quoting=csv.QUOTE_NONE, quotechar=None, lineterminator="\n", escapechar="\\")
        w.writerow(["norm_name", "n_items", "top_form"])
        for n in sorted(groups["nothing"], key=lambda n: (-names[n]["n"], n)):
            w.writerow([n, names[n]["n"], max(names[n]["forms"], key=names[n]["forms"].get).replace("\t", " ")])

    total_items = sum(d["n"] for d in names.values())
    total_kept = sum(d["kept"] for d in names.values())
    def items(k): return sum(names[n]["n"] for n in groups[k])
    def kept(k): return sum(names[n]["kept"] for n in groups[k])
    lines = ["# Coverage check of the place tags", "",
             "Source: read-only SELECT from `speech_items`, type `place`, list `other`. A name is its `norm_name`.",
             "These numbers measure coverage (the share of names that equal a tag name or alias). They do not measure accuracy.",
             "The denominators are the distinct place names and the place items in the database.", "",
             f"Distinct place names: {len(names)}. Place items: {total_items} (kept by the judge: {total_kept}).", "",
             "| Group | Names | Items | Kept items |", "|---|---|---|---|"]
    for k, label in [("new1", "equals exactly one new tag"), ("new2", "equals two or more new tags"),
                     ("existing", "equals an existing tag"), ("nothing", "equals nothing")]:
        lines.append(f"| {label} | {len(groups[k])} | {items(k)} | {kept(k)} |")
    model_only = [n for n in groups["new1"] if n in MODEL_ONLY]
    lines += ["", f"Of the names that equal exactly one new tag, {len(model_only)} names ({sum(names[n]['n'] for n in model_only)} items) "
              "are on the MODEL_ONLY list of scripts/link_entities.py. The exact rule skips them and the decision model decides."]
    lines += ["", "## The 30 most frequent place names that match nothing", "", "| Items | Name (most common spelling) |", "|---|---|"]
    for n in sorted(groups["nothing"], key=lambda n: -names[n]["n"])[:30]:
        top = max(names[n]["forms"], key=names[n]["forms"].get)
        lines.append(f"| {names[n]['n']} | {top} |")
    lines += ["", "## 20 random names that equal exactly one new tag (seed 7)", "",
              "| Items | Name | New tag | One mention from a speech |", "|---|---|---|---|"]
    for n in pick:
        tag = next(iter(new_idx[n]))
        lines.append(f"| {names[n]['n']} | {max(names[n]['forms'], key=names[n]['forms'].get)} | {tag} | {examples[n]} |")
    lines += ["", "## Names that equal two or more new tags (top 15)", "", "| Items | Name | Tags |", "|---|---|---|"]
    for n in sorted(groups["new2"], key=lambda n: -names[n]["n"])[:15]:
        lines.append(f"| {names[n]['n']} | {n} | {' / '.join(sorted(new_idx[n]))} |")
    lines += ["", "## Names that equal an existing tag (top 15)", "", "| Items | Name | Tag |", "|---|---|---|"]
    for n in sorted(groups["existing"], key=lambda n: -names[n]["n"])[:15]:
        lines.append(f"| {names[n]['n']} | {n} | {' / '.join(sorted(old_idx[n]))} |")
    (RESULTS / "coverage_check.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
