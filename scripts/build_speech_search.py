"""Fill the table speech_search: the stored words of each speech, for word search and its ranking.

Run it from the repo root after each data load that changes speeches or summaries:

    python3 scripts/build_speech_search.py

words holds the text of the own turns of the speech and the name of the member.
head holds the title, the name and the summary. A match in head ranks higher, and it is fast to read.
A tsvector cannot hold more than 1 MB, so the script cuts a very long text.
"""
import sys
import time
from pathlib import Path

from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import dashboard_db  # noqa: E402

MAX_CHARS = 400_000
MIN_REPEAT_WORDS = 20
BATCH = 5000


def main():
    start = time.monotonic()
    with dashboard_db.get_engine().begin() as conn:
        conn.execute(text("DELETE FROM speech_search"))
        last, done = 0, 0
        while True:
            ids = [r[0] for r in conn.execute(text("SELECT id FROM speeches WHERE id > :l ORDER BY id LIMIT :n"), {"l": last, "n": BATCH})]
            if not ids:
                break
            conn.execute(text("""
                INSERT INTO speech_search (speech_id, words, head)
                SELECT s.id,
                    to_tsvector('simple', left(coalesce(own.body, ''), :max)) ||
                      to_tsvector('simple', coalesce(pe.name, '')),
                    to_tsvector('simple', coalesce(d.title, '') || ' ' || coalesce(pe.name, '') || ' ' || coalesce(e.summary, ''))
                FROM speeches s JOIN debates d ON d.id = s.debate_id
                LEFT JOIN persons pe ON pe.id = s.person_id
                LEFT JOIN speech_extractions e ON e.speech_id = s.id
                LEFT JOIN LATERAL (SELECT string_agg(t.text, ' ' ORDER BY t.seq) AS body FROM turns t
                    WHERE t.speech_id = s.id AND t.person_id IS NOT DISTINCT FROM s.person_id) own ON true
                WHERE s.id = ANY(:ids)"""), {"ids": ids, "max": MAX_CHARS})
            last, done = ids[-1], done + len(ids)
            print(f"{done} speeches, {time.monotonic() - start:.0f} s", flush=True)
        # A repeat: the same member, the same text, with enough words to be more than a set phrase.
        n = conn.execute(text("""
            WITH own AS (
                SELECT s.id, s.person_id, md5(string_agg(t.text, ' ' ORDER BY t.seq)) AS h FROM speeches s
                JOIN turns t ON t.speech_id = s.id AND t.person_id = s.person_id
                WHERE s.person_id IS NOT NULL AND s.word_count >= :w GROUP BY s.id),
            firsts AS (SELECT id, min(id) OVER (PARTITION BY person_id, h) AS first FROM own)
            UPDATE speech_search x SET repeat_of = f.first FROM firsts f WHERE f.id = x.speech_id AND f.first <> f.id"""),
            {"w": MIN_REPEAT_WORDS}).rowcount
        conn.execute(text("UPDATE query_vectors SET near_ids = NULL"))  # The stored lists can name old speeches.
        print(f"{n} repeats. Done in {time.monotonic() - start:.0f} s", flush=True)
    with dashboard_db.get_engine().connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        conn.execute(text("ANALYZE speech_search"))


if __name__ == "__main__":
    main()
