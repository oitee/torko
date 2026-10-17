# Summary tags

This step finds the tags that are nearest in meaning to the summary of each speech. These tags can add topics that the extraction missed. Input: the summaries of the extraction step and the tag list in [the seed tags](../seed_tags_v1/README.md). Output: the table `speech_summary_embeddings` and the recognised-tag candidates that `scripts/add_candidates.py` adds (see [the judging step](../judging/README.md)).

## How to run

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

The embed script is idempotent. It embeds a summary again only when its md5 hash changes. Summaries of the model `rule-stub` get no vector.

## How it works

The embedding model turns each summary into a vector of 1,536 numbers. The task type is `RETRIEVAL_QUERY` and the code scales the vector to length 1. The tag vectors use `RETRIEVAL_DOCUMENT`. The two task types form a pair.

A SQL query measures the cosine distance (pgvector operator `<=>`) between the summary vector and each tag vector. Tags with the status `rejected` do not count. The query returns the N nearest tags. N is a fixed count, because no distance limit separates a match from a non-match. The default N is 12 (`--n` of `scripts/add_candidates.py`).

## Files

| File | What it is |
|---|---|
| `scripts/embed_summaries.py` | Embeds the summaries. Options: `--term`, `--limit`, `--extraction-ids`, `--dry-run`. `nearest_tags(conn, speech_ids, n=20)` returns the nearest tags with rank and distance. |
| `scripts/summary_tags_review.py` | Writes `results/review_v1.md`, a review file of 30 speeches with their 20 nearest tags. |
| `results/review_v1.md` | The review file. A relevant tag has `[x]`. |
| `data/general_tags.tsv` | Tags that `scripts/add_candidates.py` never makes recognised tags. |

The table `speech_summary_embeddings` has the key `extraction_id`. It keeps `speech_id`, the model, the task type, the dimensions, the summary hash, and the vector. A new extraction replaces the old vector.

## General tags

Some tags name the House, the government, or procedure, for example `Members` and `Parliament`. They are near almost every summary but they are not a subject. The file `data/general_tags.tsv` lists them.

The file has the columns `tag` and `reason`, with a tab between them. The `tag` value is the exact name in the tag list. `scripts/add_candidates.py` skips each listed tag, and the next nearest tags take their places. A speech still gets N recognised tags. The script stops when a name in the file is not in the tag list. A new row applies to speeches that get their candidates later. Speeches that already have recognised tags keep their rows. `--force` adds them again, but it also deletes their stage 4 answers, so a new paid judging run is needed.
