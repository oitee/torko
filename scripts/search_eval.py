"""The search test set: 30 questions with known correct speeches, and the score of a search method.

The steps, from the repo root:

    python3 scripts/search_eval.py pool      # find candidates in several ways, and write files for the reviewers
    python3 scripts/search_eval.py pool-top  # add the top 10 results of each method that no reviewer saw
    python3 scripts/search_eval.py combine   # keep a candidate when two blind reviewers both mark it correct
    python3 scripts/search_eval.py score --method words

The score is recall at 10: the known correct speeches in the top 10 results, over the smaller of 10 and the number of
known correct speeches. A question with no known speech is left out of the score. The denominator is the number of
known speeches that the pool found, so the score cannot count a correct speech that no way of finding it reached.
"""
import argparse
import csv
import json
import random
import re
import sys
from collections import defaultdict
from pathlib import Path

from sqlalchemy import text

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import dashboard_db  # noqa: E402
import tag_search  # noqa: E402
from pages.common import clean_layout, resolve_tag, tag_speeches  # noqa: E402

FOLDER = ROOT / "tags" / "search_eval"
QUESTIONS = FOLDER / "data" / "questions.tsv"
KNOWN = FOLDER / "data" / "known.tsv"
REVIEWS = FOLDER / "data" / "reviews"
BATCHES = FOLDER / "results" / "batches"
PER_WAY = 6
VECTOR_NEAREST = 10
BATCH_QUESTIONS = 5
EXCERPT = 450
SEED = 69


def read_questions(path=QUESTIONS):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE))  # keep the quote marks of a phrase


def recall_at_10(ranked, known):
    """Return the share of known speeches in the first 10 of ranked. The limit is the smaller of 10 and len(known)."""
    if not known:
        return None
    return len(set(ranked[:10]) & set(known)) / min(10, len(known))


def read_known(path=KNOWN):
    known = defaultdict(set)
    with open(path, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            known[r["id"]].add(int(r["speech_id"]))
    return known


def combine_marks(first, second):
    """Keep a speech when both reviewers mark it yes. first and second map (question id, speech id) to yes or no."""
    return sorted(k for k, v in first.items() if v == "yes" and second.get(k) == "yes")


def phrase_of(query):
    m = re.fullmatch(r'"(.+)"', query.strip())
    return m.group(1) if m else None


# The ways to find candidates. Each way returns speech ids.
def by_words(conn, words):
    return [r[0] for r in conn.execute(text("""
        SELECT DISTINCT t.speech_id FROM turns t JOIN speeches s ON s.id = t.speech_id
        WHERE to_tsvector('simple', t.text) @@ plainto_tsquery('simple', :q)
          AND t.person_id IS NOT DISTINCT FROM s.person_id AND s.word_count >= 50"""), {"q": words})]


def by_summary_text(conn, words):
    parts = [w for w in words.split() if len(w) > 2]
    if not parts:
        return []
    cond = " AND ".join(f"e.summary ILIKE :w{i}" for i in range(len(parts)))
    return [r[0] for r in conn.execute(text(f"SELECT e.speech_id FROM speech_extractions e WHERE {cond} ORDER BY 1"),
                                       {f"w{i}": f"%{w}%" for i, w in enumerate(parts)})]


def by_vector(conn, vector, limit, members=None):
    limit_to = "JOIN speeches s ON s.id = v.speech_id WHERE s.person_id = ANY(:m)" if members else ""
    return [r[0] for r in conn.execute(text(f"""
        SELECT v.speech_id FROM speech_summary_embeddings v {limit_to} ORDER BY v.embedding <=> CAST(:v AS vector) LIMIT :n"""),
        {"v": vector, "n": limit, "m": members})]


def by_tag(conn, query, tags, subjects):
    for r in tag_search.search(query, tags, subjects, limit=3):
        if r["kind"] in ("tag", "place"):
            t = resolve_tag(conn, r["slug"])
            if t:
                return [sid for sid, source in tag_speeches(conn, t["id"]) if source == "llm"]
    return []


def phrase_matches(conn, phrase):
    return [r[0] for r in conn.execute(text("""
        SELECT DISTINCT t.speech_id FROM turns t JOIN speeches s ON s.id = t.speech_id
        WHERE to_tsvector('simple', t.text) @@ phraseto_tsquery('simple', :q)
          AND t.person_id IS NOT DISTINCT FROM s.person_id ORDER BY 1"""), {"q": phrase})]


def member_ids(conn, name):
    return [r[0] for r in conn.execute(text("SELECT id FROM persons WHERE name ILIKE :n"), {"n": "%" + "%".join(name.split()) + "%"})]


def describe(conn, ids):
    """Return {speech id: the text that a reviewer reads}: title, speaker, date, summary, and the opening of the speech."""
    rows = conn.execute(text("""
        SELECT s.id, s.word_count, d.title, d.debate_date, pe.name, e.summary
        FROM speeches s JOIN debates d ON d.id = s.debate_id LEFT JOIN persons pe ON pe.id = s.person_id
        LEFT JOIN speech_extractions e ON e.speech_id = s.id WHERE s.id = ANY(:ids)"""), {"ids": list(ids)}).all()
    turns = defaultdict(list)
    for sid, txt in conn.execute(text("""SELECT t.speech_id, t.text FROM turns t JOIN speeches s ON s.id = t.speech_id
        WHERE t.speech_id = ANY(:ids) AND t.person_id IS NOT DISTINCT FROM s.person_id ORDER BY t.speech_id, t.seq"""), {"ids": list(ids)}):
        turns[sid].append(txt)
    return {r[0]: {"speech_id": r[0], "title": re.sub(r"\s+", " ", clean_layout(r[2] or ""))[:120], "year": str(r[3])[:4], "speaker": r[4],
                   "summary": r[5], "full_text": clean_layout(" ".join(turns[r[0]]))} for r in rows}


def window(full, words, limit=EXCERPT):
    """The opening of the speech, and the first place that holds a search word, because a passing remark can be anywhere."""
    out = full[:limit]
    low = full.lower()
    for w in words:
        for part in w.lower().split():
            i = low.find(part)
            if i > limit:
                return out + " [...] " + full[max(0, i - 150):i + 250]
    return out


def write_batch(path, questions):
    """One line for each question and one line for each candidate, so that a reviewer can read a few lines at a time."""
    with open(path, "w", encoding="utf-8") as f:
        for q in questions:
            f.write(f"QUESTION {q['id']} | query: {q['query']} | rule: {q['rule']}\n")
            for c in q["candidates"]:
                text_one_line = re.sub(r"\s+", " ", c["text"])
                summary = re.sub(r"\s+", " ", c["summary"] or "(no summary)")
                f.write(f"{q['id']} speech {c['speech_id']} | {c['year']} | {c['speaker'] or 'no name'} | title: {c['title']} | "
                        f"summary: {summary} | text: {text_one_line}\n")


def pool(args):
    from tag_embed import embed_texts, to_pgvector
    rng = random.Random(SEED)
    questions = read_questions()
    BATCHES.mkdir(parents=True, exist_ok=True)
    with dashboard_db.get_engine().connect() as conn:
        tags, subjects = tag_search.load_index(conn)
        vectors = embed_texts([q["query"].strip('"') for q in questions], "RETRIEVAL_QUERY")
        known_rows = []
        reviewed = []
        for q, vec in zip(questions, vectors):
            phrase = phrase_of(q["query"])
            if phrase:  # An exact phrase needs no reader: the text decides.
                ids = phrase_matches(conn, phrase)
                known_rows += [(q["id"], i) for i in ids]
                print(q["id"], "phrase", len(ids), flush=True)
                continue
            words = [w for w in q["pool_words"].split("|") if w]
            allowed = member_ids(conn, q["member"]) if q["member"] else None
            ways = {"vector": by_vector(conn, to_pgvector(vec), VECTOR_NEAREST, allowed)}
            for w in [q["query"]] + words:
                ways["tag:" + w] = by_tag(conn, w, tags, subjects)
            for w in words:
                ways["words:" + w] = by_words(conn, w)
                ways["summary:" + w] = by_summary_text(conn, w)
            if allowed:
                who = {r[0]: r[1] for r in conn.execute(text("SELECT id, person_id FROM speeches WHERE id = ANY(:i)"),
                                                        {"i": list({i for v in ways.values() for i in v})})}
                ways = {k: [i for i in v if who.get(i) in allowed] for k, v in ways.items()}
            found = defaultdict(list)
            for way, ids in ways.items():
                ids = list(ids)
                rng.shuffle(ids)  # No way gets its own order: a reviewer must not see a rank.
                for i in ids[:VECTOR_NEAREST if way == "vector" else PER_WAY]:
                    found[i].append(way)
            info = describe(conn, found)
            cands = list(info.values())
            rng.shuffle(cands)
            for c in cands:
                c["text"] = window(c.pop("full_text"), words)
            reviewed.append({"id": q["id"], "query": q["query"], "rule": q["rule"], "candidates": cands})
            print(q["id"], {k: len(v) for k, v in ways.items()}, "candidates", len(cands), flush=True)
    with open(FOLDER / "data" / "known_phrase.tsv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["id", "speech_id"])
        w.writerows(known_rows)
    for i in range(0, len(reviewed), BATCH_QUESTIONS):
        write_batch(BATCHES / f"batch_{i // BATCH_QUESTIONS + 1:02d}.txt", reviewed[i:i + BATCH_QUESTIONS])
    print("candidates in all", sum(len(r["candidates"]) for r in reviewed), "batches", -(-len(reviewed) // BATCH_QUESTIONS), flush=True)


def pool_top(args):
    """Write a new batch: the top 10 results of each method that no reviewer saw. Then a method cannot lose by finding new speeches."""
    questions = read_questions()
    seen = set(read_marks("a"))
    batch = []
    with dashboard_db.get_engine().connect() as conn:
        for q in questions:
            if phrase_of(q["query"]):
                continue
            ids = {i for m in METHODS.values() for i in m(conn, q["query"])[:10] if (q["id"], i) not in seen}
            if ids:
                cands = list(describe(conn, ids).values())
                words = [w for w in q["pool_words"].split("|") if w]
                for c in cands:
                    c["text"] = window(c.pop("full_text"), words)
                batch.append({"id": q["id"], "query": q["query"], "rule": q["rule"], "candidates": cands})
    BATCHES.mkdir(parents=True, exist_ok=True)
    number = len(list(BATCHES.glob("batch_*.txt"))) + 1
    write_batch(BATCHES / f"batch_{number:02d}.txt", batch)
    print(f"batch {number}: {sum(len(b['candidates']) for b in batch)} speeches, {len(batch)} questions", flush=True)


def read_marks(reviewer):
    out = {}
    for path in sorted(REVIEWS.glob(f"{reviewer}_batch_*.tsv")):
        with open(path, encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f, delimiter="\t"):
                out[(r["id"], int(r["speech_id"]))] = r["mark"].strip().lower()
    return out


def combine(args):
    a, b = read_marks("a"), read_marks("b")
    same = sum(a.get(k) == v for k, v in b.items())
    pairs = combine_marks(a, b)
    with open(FOLDER / "data" / "known_phrase.tsv", encoding="utf-8", newline="") as f:
        phrase = [(r["id"], int(r["speech_id"])) for r in csv.DictReader(f, delimiter="\t")]
    with open(KNOWN, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["id", "speech_id"])
        w.writerows(sorted(set(pairs) | set(phrase)))
    print(f"reviewer a {len(a)} marks, b {len(b)} marks, same {same}, both yes {len(pairs)}, phrase rows {len(phrase)}", flush=True)


def words_method(conn, query):
    """The word search before this test set: every word in one turn, newest first. Kept here as the fixed baseline."""
    return [r[0] for r in conn.execute(text("""
        SELECT s.id FROM speeches s JOIN debates d ON d.id = s.debate_id
        WHERE s.id IN (SELECT t.speech_id FROM turns t JOIN speeches s2 ON s2.id = t.speech_id
            WHERE to_tsvector('simple', t.text) @@ plainto_tsquery('simple', :q)
              AND t.person_id IS NOT DISTINCT FROM s2.person_id)
        ORDER BY d.debate_date DESC NULLS LAST, s.id DESC LIMIT 10"""), {"q": query})]


def best_method(conn, query):
    """The search of the site: the default order of /api/speeches."""
    from pages.speeches import speeches
    return [r["id"] for r in speeches(conn, {"q": query, "per_page": 10})["speeches"]]


METHODS = {"words": words_method, "best": best_method}


def score(args):
    known = read_known()
    questions = read_questions()
    by_kind, rows = defaultdict(list), []
    marked = set(read_marks("a"))
    with dashboard_db.get_engine().connect() as conn:
        for q in questions:
            ranked = METHODS[args.method](conn, q["query"])
            r = recall_at_10(ranked, known[q["id"]])
            no_mark = 0 if phrase_of(q["query"]) else sum((q["id"], i) not in marked for i in ranked[:10])
            rows.append((q["id"], q["kind"], q["query"], len(known[q["id"]]), "-" if r is None else f"{r:.2f}", no_mark))
            if r is not None:
                by_kind[q["kind"]].append(r)
    for row in rows:
        print("\t".join(map(str, row)))
    every = [x for v in by_kind.values() for x in v]
    for kind, v in sorted(by_kind.items()):
        print(f"{kind}\t{sum(v) / len(v):.3f}\t{len(v)} questions")
    print(f"ALL {args.method}\t{sum(every) / len(every):.3f}\t{len(every)} questions\t"
          f"{sum(r[5] for r in rows)} top 10 results with no mark", flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="step", required=True)
    sub.add_parser("pool").set_defaults(fn=pool)
    sub.add_parser("pool-top").set_defaults(fn=pool_top)
    sub.add_parser("combine").set_defaults(fn=combine)
    s = sub.add_parser("score")
    s.add_argument("--method", default="words", choices=sorted(METHODS))
    s.set_defaults(fn=score)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
