"""
Generate static JSON fixtures for the debate-dashboard FE demo.

Pulls real, already-imported debates straight from the `debates` table (no
network calls — the corpus is local), runs them through the real parser
(`split_by_speaker`), and joins each resolved speaker to their party via the
`speakers` table. Output feeds `server.py`'s /api/dashboard/* endpoints, which
serve it as if a real backend built it — the FE never knows the difference.

See internal_docs/026_DASHBOARD_DEMO.md for why these debates were chosen and
what the output shape means.

Run: source .venv/bin/activate && python3 scripts/build_dashboard_fixtures.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from db import get_engine
from db_roster import load_db_roster
from debate_fetch import split_by_speaker, speaker_distribution
from debate_fetch_legacy import looks_legacy, split_by_speaker_legacy

# (loksabha, session, dbslno) — hand-picked for date/session/party spread and
# a mix of short single-speaker items and one long multi-speaker debate.
# See internal_docs/026_DASHBOARD_DEMO.md for the selection query.
DEBATE_KEYS = [
    (17, 5, 5240), (17, 5, 5247), (17, 5, 5253), (17, 5, 5250), (17, 5, 5249), (17, 5, 5251),
    (17, 12, 11607), (17, 12, 11611), (17, 12, 11601), (17, 12, 11606), (17, 12, 11609), (17, 12, 11612),
    (18, 2, 263), (18, 2, 245), (18, 2, 240), (18, 2, 260), (18, 2, 241), (18, 2, 264),
    (18, 4, 1834), (18, 4, 1835), (18, 4, 1837), (18, 4, 1838), (18, 4, 1995), (18, 4, 2068),
    (18, 5, 4012),
]

OUT_PATH = "fixtures/dashboard_debates.json"


def party_lookup(engine) -> dict[str, dict]:
    """sansad_id (mpCode, as string) -> {party, constituency}, last known term."""
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT p.sansad_id, s.party, s.constituency "
                "FROM speakers s JOIN persons p ON p.id = s.person_id "
                "WHERE p.sansad_id IS NOT NULL"
            )
        ).fetchall()
    return {str(r.sansad_id): {"party": r.party, "constituency": r.constituency} for r in rows}


def clean_title(raw: str | None) -> str:
    if not raw:
        return "(untitled)"
    return " ".join(raw.replace("Title :", "").split())


def main():
    engine = get_engine()
    parties = party_lookup(engine)
    roster_cache: dict[int, list] = {}

    debates_out = []
    with engine.connect() as conn:
        for loksabha, session, dbslno in DEBATE_KEYS:
            row = conn.execute(
                text(
                    "SELECT loksabha, session, dbslno, raw_html, mp_list_raw, title, "
                    "debate_type, debate_date FROM debates "
                    "WHERE loksabha=:ls AND session=:sess AND dbslno=:db"
                ),
                {"ls": loksabha, "sess": session, "db": dbslno},
            ).fetchone()
            if row is None:
                print(f"MISSING {loksabha}/{session}/{dbslno} — skipped")
                continue

            html = row.raw_html
            mp_list = row.mp_list_raw
            if loksabha not in roster_cache:
                roster_cache[loksabha] = load_db_roster(loksabha)
            db_roster = roster_cache[loksabha]

            legacy = looks_legacy(html)
            segments = (
                split_by_speaker_legacy(html, mp_list, db_roster)
                if legacy
                else split_by_speaker(html, mp_list, db_roster)
            )
            dist = speaker_distribution(segments)

            speakers_present = []
            for d in dist:
                code = d["mpCode"]
                party_info = parties.get(str(code), {}) if code else {}
                speakers_present.append(
                    {
                        "sansadId": code,
                        "name": d["mpName"],
                        "party": party_info.get("party"),
                        "constituency": party_info.get("constituency"),
                        "verified": d["verified"],
                        "interventions": d["interventions"],
                        "words": d["words"],
                    }
                )

            turns = []
            for i, seg in enumerate(segments):
                code = seg.get("mpCode")
                party_info = parties.get(str(code), {}) if code else {}
                turns.append(
                    {
                        "turnIndex": i,
                        "sansadId": code,
                        "name": seg.get("mpName"),
                        "party": party_info.get("party"),
                        "verified": bool(code),
                        "nameSource": seg.get("nameSource"),
                        "text": seg.get("text", ""),
                    }
                )

            debates_out.append(
                {
                    "id": f"{loksabha}-{session}-{dbslno}",
                    "loksabha": loksabha,
                    "session": session,
                    "dbslno": dbslno,
                    "title": clean_title(row.title),
                    "debateType": row.debate_type,
                    "debateDate": row.debate_date.isoformat() if row.debate_date else None,
                    "format": "legacy" if legacy else "modern",
                    "speakersPresent": speakers_present,
                    "turnCount": len(turns),
                    "turns": turns,
                }
            )
            print(f"OK {loksabha}/{session}/{dbslno} — {len(turns)} turns, {len(speakers_present)} speakers")

    import os
    os.makedirs("fixtures", exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(debates_out, f, indent=2, ensure_ascii=False)
    print(f"\nWrote {len(debates_out)} debates to {OUT_PATH}")


if __name__ == "__main__":
    main()
