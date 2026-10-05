# Links from entity names to tags

This folder holds stage 5 of the tag pipeline. Torko reads the debate transcripts of the Lok Sabha, the lower house of India's parliament. Stage 4 (`tags/judging/`) keeps the items of each speech that are real subjects. Stage 5 links each kept item to one tag of the tag list (`tags/seed_tags_v1/`), or to no tag (`NONE`).

The unit is one distinct entity name: the name in lower case, with single spaces, without outer punctuation, plus its type. One decision serves every speech that holds the name. The table is `entity_names` (`db/init/12-entity-links.sql`). Each kept item points to its row through `speech_items.entity_name_id`.

`scripts/link_entities.py` does these steps for each name:

1. Exact candidates: tags whose name or alias is the same after normalisation, and the tags of linked names with the same text.
2. Vector candidates: the 20 nearest tags to the name's vector (`gemini-embedding-001`, task type `RETRIEVAL_QUERY` for the name, `RETRIEVAL_DOCUMENT` for the tags).
3. One choice question to a decision model. The state is the name, the type, and up to 3 mentions and summaries from different speeches. The options are the candidates (at most 21) and `NONE`.
4. A link when the top option is a tag with probability 0.7 or more. Otherwise `NONE`. A wrong link is worse than no link.

An exact match is an option, never an automatic link. A link is never written into `tags.aliases`.

## How to run it

Run from the repo root. `.env` must hold `TYPESAFE_API_KEY` and `GEMINI_API_KEY`.

```bash
set -a && source .env && set +a
python3 scripts/link_entities.py --test-pairs
python3 scripts/link_entities.py --dry-run
python3 scripts/link_entities.py
```

`--test-pairs` runs steps 1 to 4 on the owner's 74 test pairs (`tags/embedding_v1/data/test_pairs_v1.tsv`) and writes nothing to the database. It counts four outcomes: correct link, wrong link, missed link (`NONE` where a tag fits), and correct `NONE`.

The script is idempotent. A link stays until the model or question version changes. A `NONE` is tried again when new tags arrive.

## Results

A normal run writes a review file into `results/`: Markdown to read, and TSV with an empty `owner` column. Write `right`, `wrong`, or `missed` in that column.
