#!/usr/bin/env python3
"""Choose one answer for each label, and add the named labels to data/label_aliases.tsv.

    python3 scripts/export_label_aliases.py --fallback <decider>

The rows already in the file stay as they are. A later scripts/load_label_aliases.py loads the file.
"""
from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sqlalchemy import text  # noqa: E402

from db import get_engine  # noqa: E402
from debate_fetch import is_crowd_label, is_presiding_label  # noqa: E402
from decision_model import MODEL  # noqa: E402
from identity.final import choose, person_key  # noqa: E402
from identity.labels import read_label  # noqa: E402
from identity.resolver import PROMPT_VERSION  # noqa: E402
from label_attribution import normalize_label  # noqa: E402

FILE = ROOT / "data" / "label_aliases.tsv"
COLUMNS = ["loksabha", "speaker_label", "person_id", "member_name", "basis", "source"]
NAMES = """
    SELECT p.id, coalesce(s.name, p.name) AS name FROM persons p
    LEFT JOIN LATERAL (SELECT name FROM speakers WHERE person_id = p.id ORDER BY lok_sabha_term DESC LIMIT 1) s ON true
"""
DATE = "2026-11-05"


def source_text(decider: str) -> str:
    if decider == "person":
        return f"manual review; {DATE}"
    if decider == "rule":
        return f"one member of the seat, and the name fits; {DATE}"
    if decider == "decision-model":
        return f"decision model {MODEL}, prompt {PROMPT_VERSION}, closed list, limit 0.8; {DATE}"
    return f"review against the member lists, with name and seat checks; {DATE}"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fallback", help="the decider to use when no other answer stands")
    args = ap.parse_args()

    with get_engine().connect() as conn:
        rows = conn.execute(text("SELECT loksabha, speaker_label, decided_by, answer, probability FROM label_resolutions")).all()
        names = dict(conn.execute(text(NAMES)).all())
        people = conn.execute(text("SELECT id, name, rajya_sabha_id, sansad_id FROM persons")).all()
    links = {f"RS{p.rajya_sabha_id}": p.id for p in people if p.rajya_sabha_id}
    added = {f"NEW:{p.name.lower().replace(' ', '-')}": p.id for p in people if not p.sansad_id and not p.rajya_sabha_id}

    answers: dict[tuple[int, str], dict] = defaultdict(dict)
    for r in rows:
        answers[(r.loksabha, r.speaker_label)][r.decided_by] = (r.answer, r.probability)

    with open(FILE, encoding="utf-8", newline="") as f:
        existing = list(csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE))
    have = {(int(r["loksabha"]), r["speaker_label"]) for r in existing}
    new, unknown = [], set()
    for (term, label), by in sorted(answers.items()):
        picked = choose(by, args.fallback)
        clean = normalize_label(label)
        if not picked or (term, clean) in have or is_presiding_label(clean) or is_crowd_label(clean):
            continue
        answer, decider = picked
        pid = person_key(answer, links, added)
        if pid is None:
            if answer[:2] in ("RS", "LS") or answer.startswith("NEW:"):
                unknown.add(answer)
            continue
        basis = "name_and_constituency" if read_label(clean).seat else "name"
        new.append({"loksabha": term, "speaker_label": clean, "person_id": pid,
                    "member_name": normalize_label(names[pid]), "basis": basis, "source": source_text(decider)})
    if unknown:
        raise SystemExit(f"answers with no person: {sorted(unknown)}")
    with open(FILE, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, COLUMNS, delimiter="\t", lineterminator="\n", quoting=csv.QUOTE_NONE, quotechar=None)
        w.writeheader()
        w.writerows(existing + new)
    print(f"{len(existing)} rows kept, {len(new)} rows added.", flush=True)


if __name__ == "__main__":
    main()
