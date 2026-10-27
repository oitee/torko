from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

from sqlalchemy import text

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from db import get_engine  # noqa: E402

DATA = ROOT / "data" / "party_history"
TSV = DATA / "results" / "speaker_terms.tsv"
EVENTS = DATA / "party_events.tsv"
NON_MEMBERS = DATA / "non_member_parties.tsv"
OWNED = ("wikipedia", "sansad-term-list", "manual", "last-term-fallback", "event")


def read_rows() -> list[dict]:
    with open(TSV, encoding="utf-8", newline="") as f:
        return [r for r in csv.DictReader(f, delimiter="\t") if r["term"] != r["last_term"]]


def read_events() -> list[dict]:
    with open(EVENTS, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def sansad_last_terms() -> dict[int, dict]:
    out: dict[int, dict] = {}
    for path in sorted((DATA / "raw").glob("sansad_ls*.json")):
        for m in json.loads(path.read_text(encoding="utf-8")):
            out[m["mpsno"]] = m
    return out


def party_names(rows: list[dict]) -> dict[str, str]:
    names: dict[str, str] = {}
    for m in sansad_last_terms().values():
        code, name = (m.get("partySname") or "").strip(), (m.get("partyFname") or "").strip()
        if code and name and code != "Not Available":
            names[code] = re.sub(r"\s+", " ", name)
    with open(DATA / "party_codes.tsv", encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            if r["code"].strip():
                names.setdefault(r["code"].strip(), r["wiki_party"].strip())
    for r in rows:
        if r["party"]:
            names.setdefault(r["party"], r["wiki_party"] or r["party"])
    return names


def load(rows: list[dict], events: list[dict]) -> None:
    engine = get_engine()
    with engine.begin() as conn:
        for code, name in party_names(rows).items():
            conn.execute(text("INSERT INTO parties (code, name) VALUES (:c, :n) "
                              "ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name"), {"c": code, "n": name})
        party_ids = dict(conn.execute(text("SELECT code, id FROM parties")).all())
        persons = dict(conn.execute(text("SELECT sansad_id, id FROM persons WHERE sansad_id IS NOT NULL")).all())
        names = dict(conn.execute(text("SELECT id, name FROM persons")).all())
        starts = dict(conn.execute(text("SELECT number, start_date FROM lok_sabhas")).all())

        unknown = sorted({e["party"] for e in events} - set(party_ids))
        if unknown:
            raise SystemExit(f"party_events.tsv: unknown party codes {unknown}")
        missing = sorted({int(r["mpsno"]) for r in rows} - set(persons))
        if missing:
            print(f"members with no row in persons, skipped: {len(missing)} {missing[:20]}", flush=True)

        removed = conn.execute(text("DELETE FROM speakers WHERE source = ANY(:owned)"),
                               {"owned": list(OWNED)}).rowcount

        # Step 1a: reset the last-term rows to the sansad.in values. The state is set on every last-term row.
        reset = 0
        for code, m in sansad_last_terms().items():
            pid = persons.get(code)
            if pid is None:
                continue
            conn.execute(text("UPDATE speakers SET state = :state WHERE person_id = :pid AND source = 'sansad-last-term'"),
                         {"pid": pid, "state": (m.get("stateName") or "").strip() or None})
            party = (m.get("partySname") or "").strip()
            reset += conn.execute(
                text("UPDATE speakers SET party_id = :party_id, constituency = :constituency, match_method = NULL "
                     "WHERE person_id = :pid AND source = 'sansad-last-term' AND match_method = 'manual'"),
                {"pid": pid, "party_id": party_ids.get(party) if party != "Not Available" else None,
                 "constituency": (m.get("constName") or "").strip() or None},
            ).rowcount

        # Step 1b: the first row of each other (member, term).
        params = []
        for r in rows:
            pid = persons.get(int(r["mpsno"]))
            if pid is None:
                continue
            method = r["method"]
            matched = method != "none"
            params.append({
                "person_id": pid,
                "term": int(r["term"]),
                "start": starts[int(r["term"])],
                "name": names[pid],
                "party_id": party_ids[r["party"]] if matched and r["party"] else None,
                "constituency": (r["constituency"] or None) if matched else None,
                "state": (r["state"] or None) if matched else None,
                "source": "manual" if method == "manual" else "wikipedia" if matched else "sansad-term-list",
                "method": method if matched else None,
            })
        inserted = conn.execute(
            text(
                """
                INSERT INTO speakers (person_id, lok_sabha_term, effective_from, name, party_id, constituency,
                                      state, source, match_method)
                VALUES (:person_id, :term, :start, :name, :party_id, :constituency, :state, :source, :method)
                ON CONFLICT (lok_sabha_term, person_id, effective_from) DO NOTHING
                """
            ),
            params,
        ).rowcount

        # Step 2: the party at the election, from the manual review.
        corrected = 0
        for e in [e for e in events if e["kind"] == "election"]:
            pid = persons[int(e["mpsno"])]
            n = conn.execute(
                text(
                    """
                    UPDATE speakers
                    SET party_id = :party_id,
                        constituency = COALESCE(:constituency, constituency),
                        match_method = 'manual',
                        source = CASE WHEN source = 'sansad-last-term' THEN source ELSE 'manual' END
                    WHERE person_id = :pid AND lok_sabha_term = :term AND effective_from = :start
                    """
                ),
                {"pid": pid, "term": int(e["term"]), "start": starts[int(e["term"])],
                 "party_id": party_ids[e["party"]], "constituency": e["constituency"] or None},
            ).rowcount
            if n != 1:
                raise SystemExit(f"party_events.tsv: no first row for member {e['mpsno']} in term {e['term']}")
            corrected += n

        # Step 3: the dated events.
        dated = 0
        for e in [e for e in events if e["kind"] != "election"]:
            pid = persons[int(e["mpsno"])]
            n = conn.execute(
                text(
                    """
                    INSERT INTO speakers (person_id, lok_sabha_term, effective_from, name, party_id,
                                          constituency, state, source)
                    SELECT person_id, lok_sabha_term, :date, name, :party_id, constituency, state, 'event'
                    FROM speakers
                    WHERE person_id = :pid AND lok_sabha_term = :term AND effective_from = :start
                    """
                ),
                {"pid": pid, "term": int(e["term"]), "start": starts[int(e["term"])],
                 "date": e["effective_from"], "party_id": party_ids[e["party"]]},
            ).rowcount
            if n != 1:
                raise SystemExit(f"party_events.tsv: no first row for member {e['mpsno']} in term {e['term']}")
            dated += n

        # Step 4: speakers with no Lok Sabha seat in the term.
        with open(NON_MEMBERS, encoding="utf-8", newline="") as f:
            non_members = list(csv.DictReader(f, delimiter="\t"))
        hand = 0
        for n in non_members:
            pid = persons.get(int(n["mpsno"]))
            if pid is None:
                raise SystemExit(f"non_member_parties.tsv: no person with code {n['mpsno']}")
            hand += conn.execute(
                text(
                    """
                    INSERT INTO speakers (person_id, lok_sabha_term, effective_from, name, party_id, source)
                    SELECT :pid, ls.number, ls.start_date, :name, :party_id, 'last-term-fallback'
                    FROM lok_sabhas ls WHERE ls.number = :term
                    AND NOT EXISTS (SELECT 1 FROM speakers s WHERE s.person_id = :pid AND s.lok_sabha_term = :term)
                    """
                ),
                {"pid": pid, "term": int(n["term"]), "name": names[pid], "party_id": party_ids[n["party"]]},
            ).rowcount
        fallback = conn.execute(
            text(
                """
                INSERT INTO speakers (person_id, lok_sabha_term, effective_from, name, party_id, constituency, source)
                SELECT pt.person_id, pt.loksabha, ls.start_date, p.name, latest.party_id, NULL, 'last-term-fallback'
                FROM (SELECT DISTINCT t.person_id, d.loksabha
                      FROM turns t JOIN debates d ON d.id = t.debate_id
                      WHERE t.person_id IS NOT NULL) pt
                JOIN persons p ON p.id = pt.person_id
                JOIN lok_sabhas ls ON ls.number = pt.loksabha
                JOIN LATERAL (SELECT s.party_id FROM speakers s
                              WHERE s.person_id = pt.person_id AND s.source = 'sansad-last-term'
                              ORDER BY s.effective_from DESC LIMIT 1) latest ON true
                WHERE NOT EXISTS (SELECT 1 FROM speakers s
                                  WHERE s.person_id = pt.person_id AND s.lok_sabha_term = pt.loksabha)
                """
            )
        ).rowcount

        print(f"removed old rows      : {removed}", flush=True)
        print(f"last-term rows reset  : {reset}", flush=True)
        print(f"first rows inserted   : {inserted} of {len(params)}", flush=True)
        print(f"election corrections  : {corrected}", flush=True)
        print(f"dated event rows      : {dated}", flush=True)
        print(f"non-member parties    : {hand}", flush=True)
        print(f"last-term fallbacks   : {fallback}", flush=True)
        if inserted != len(params):
            print("some rows collided with a sansad-last-term row and were not inserted", flush=True)


def main() -> None:
    load(read_rows(), read_events())


if __name__ == "__main__":
    sys.exit(main())
