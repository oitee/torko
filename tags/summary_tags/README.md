# Summary tags

This folder holds stage 3c of the tag pipeline. Torko reads the debate transcripts of the Lok Sabha, the lower house of India's parliament. The extraction step writes a short summary for each speech. Stage 3c finds the tags of the tag list (`tags/seed_tags_v1/`) that are nearest in meaning to the summary. These tags can add topics that the extraction missed.

## How it works

1. The embedding model turns the summary into a list of 1,536 numbers. The model is `gemini-embedding-001`. The task type is `RETRIEVAL_QUERY`. The code scales the list to length 1.
2. The tag vectors use the task type `RETRIEVAL_DOCUMENT`. The two task types form a pair. The model builders made them to match.
3. A SQL query measures the cosine distance (pgvector operator `<=>`) between the summary vector and each tag vector. Tags with the status `rejected` do not count. The query returns the N nearest tags. No index is needed for about 4,500 tags.

No distance limit separates a match from a non-match. So N is a fixed count, and you choose it.

## Table

`speech_summary_embeddings` (`db/init/14-summary-embeddings.sql`). The key is `extraction_id`. The table keeps `speech_id`, the model, the task type, the number of dimensions, the md5 hash of the summary, and the vector. When a new extraction replaces an old one, the old vector goes with it. The script embeds a summary again only when its hash changes. Summaries of the model `rule-stub` are fixed texts and get no vector.

## Scripts

- `scripts/embed_summaries.py` embeds the summaries. It has the options `--term`, `--limit`, `--extraction-ids`, and `--dry-run`. The function `nearest_tags(conn, speech_ids, n=20)` returns the nearest tags for each speech, with rank and distance.
- `scripts/summary_tags_review.py` writes the review file `results/review_v1.md` for 30 speeches. These are the 15 speeches of the 2019 sample and 15 random speeches of Lok Sabha 16, 17 and 18 (fixed seed).

## The gate

1. Open `results/review_v1.md`. For each speech, mark the relevant tags among the 20 nearest tags with `[x]`.
2. For each N from 5 to 20, count the share of the relevant tags that are in the top N. The denominator is all relevant tags that the manual review marked in the top 20. Tags outside the top 20 are not seen, so the share does not measure the tags that the list missed.
3. You choose N. The start value is 10.

## The gate result (manual review, 2026-10-09)

A manual review marked 150 tags as relevant, over 30 speeches and 600 tags (20 per speech). 1 speech has no relevant tag. The marks are in `results/review_v1.md`: `[x]`, `[ x]`, and `[x ]` count as relevant.

| N | Relevant tags in the top N (of 150) | Share of the top N that is relevant |
|---|---|---|
| 5 | 78 (52%) | 52% |
| 8 | 103 (69%) | 43% |
| 10 | 110 (73%) | 37% |
| 12 | 122 (81%) | 34% |
| 15 | 134 (89%) | 30% |
| 20 | 150 (100%) | 25% |

Relevant tags occur at every rank. 16 of the 150 are at ranks 16 to 20. So the 20 nearest tags probably miss some relevant tags, and the first column is an upper limit. The decision model judges each candidate tag, so a larger N costs more questions but adds no wrong tag by itself.

**Decided: N = 12 (2026-10-09).** With N = 12, the top N holds 122 of the 150 relevant tags (81%). The cost of the tag questions in the judging step was estimated for all 52,630 speeches of LS 16, 17, and 18, at about 130 input tokens per tag question and $0.042 per million input tokens: N = 5 about $1.44, N = 10 about $2.88, N = 12 about $3.46, N = 15 about $4.32, N = 20 about $5.76.

## How to run it

Run from the repo root. `.env` must hold `GEMINI_API_KEY`.

```bash
set -a && source .env && set +a
python3 scripts/embed_summaries.py --dry-run
python3 scripts/embed_summaries.py --term 16 --limit 100
python3 scripts/embed_summaries.py
IDS=$(python3 scripts/summary_tags_review.py --print-extraction-ids)
python3 scripts/embed_summaries.py --extraction-ids $IDS
python3 scripts/summary_tags_review.py
```

The script is idempotent. A second run with no change makes no API call. The full run covers about 49,700 summaries and costs less than 1 US dollar.
