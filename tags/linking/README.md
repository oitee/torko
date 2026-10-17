# Links from entity names to tags

This step is stage 5 of the tag pipeline. It reads the items that [the judging step](../judging/README.md) kept. It links each distinct entity name to one tag of the tag list (`tags/seed_tags_v1/`), or to no tag (`NONE`).

The unit is one distinct entity name: lower case, single spaces, no outer punctuation, plus its type. One decision serves every speech that holds the name. The table is `entity_names`. Each kept item points to its row through `speech_items.entity_name_id`.

## How to run

Run from the repo root. `.env` must hold `TYPESAFE_API_KEY` and `GEMINI_API_KEY`.

```bash
set -a && source .env && set +a
python3 scripts/link_entities.py --test-pairs
python3 scripts/link_entities.py --dry-run
python3 scripts/link_entities.py
```

| Flag | Effect |
|---|---|
| `--test-pairs` | Runs the steps on the hand-made test pairs (`tags/embedding_v1/data/test_pairs_v1.tsv`). Writes nothing to the database. |
| `--dry-run` | Prints the counts. Registers nothing and calls no model. |
| `--limit N` | Decides at most N names, the most frequent first. |
| `--force` | Decides every name again, also those done with this version. |
| `--link-p P` | Changes the probability limit for a link (default 0.7). |
| `--model`, `--workers` | Change the decision model and the number of parallel workers. |
| `--no-review` | Writes no review file. |
| `--count-only` | With `--test-pairs`: prints how many pairs link by the rule and how many need a model call, then stops. |

The script is idempotent. A link stays until the model or question version changes. A `NONE` is tried again when new tags arrive.

## Rules the code applies

For each name, the script does these steps in order:

1. Exact match. If the name equals the name or alias of exactly one tag, the name links to that tag with no model call. The names in `MODEL_ONLY` skip this rule.
2. Vector candidates. The 20 nearest tags to the vector of the name (`gemini-embedding-001`).
3. One choice question to the decision model. It holds the name, the type, and up to 3 mentions with summaries from different speeches. The options are the candidates and `NONE`.
4. A link only when the top option is a tag with probability 0.7 or more. Otherwise `NONE`.

The script never writes a link into `tags.aliases`.

## Results

A normal run writes a review file into `results/`: a Markdown file to read, and a TSV file with an empty `review` column. Write `right`, `wrong`, or `missed` in that column.

Git does not track the run outputs in `results/`. The only exception is a review file that holds manual marks.
