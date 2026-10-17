# Tag embeddings, version 1

This step gives each tag a vector, so that a later step can find the tag nearest in meaning to a subject. The input is the table `tags`, loaded from [the seed tag list](../seed_tags_v1/README.md). The output is the table `tag_embeddings` (`db/init/05-tags.sql`). It also holds a test that compares two task types.

The database measures closeness with cosine distance. A vector records its model and its task type, because vectors of different models or unmatched task types cannot be compared.

## How to run

Run from the repo root. The database must run, and `.env` must hold `GEMINI_API_KEY`.

```bash
set -a && source .env && set +a
python3 scripts/load_tags.py
python3 scripts/embed_tags.py --task-type SEMANTIC_SIMILARITY
python3 scripts/embed_tags.py --task-type RETRIEVAL_DOCUMENT
python3 scripts/tag_bakeoff.py
```

1. `load_tags.py` copies `tags/seed_tags_v1/results/seed_tags_v1.tsv` into the table `tags`. It calls no model and is safe to repeat. The option `--dry-run` prints the plan.
2. `embed_tags.py` stores one vector for each tag. It embeds a tag again only when its text changed. The option `--dry-run` calls no model.
3. `tag_bakeoff.py` embeds the search text of each test pair, sorts all tags by distance, and finds the rank of the best acceptable tag. Rank 1 is the nearest tag.

The shared code is `tag_embed.py`. Its tests are in `tests/test_tag_embed.py`.

## Settings

| Setting | Value |
|---|---|
| Model | `gemini-embedding-001` |
| Size | 1,536 numbers, scaled to length 1 |
| Text for each tag | name, aliases, type, domain, and description, in one line |
| Index | none, a full scan is fast enough |

Example of the text for one tag:

```
Road Construction. Also called: Road Development, Road Development Plans, Road Projects. Type: topic. Domain: Roads and Highways. Building or improving roads and highways.
```

## Task types

The task type is a label that tells the model what the vector is for. The test compares two arms:

| Arm | Vectors for tags | Vectors for the search text |
|---|---|---|
| A | `SEMANTIC_SIMILARITY` | `SEMANTIC_SIMILARITY` |
| B | `RETRIEVAL_DOCUMENT` | `RETRIEVAL_QUERY` |

## Files

| Path | Holds |
|---|---|
| `data/test_pairs_v1.tsv` | The hand-approved test pairs. |
| `results/bakeoff_v1.tsv` | One row for each pair: the rank and distance in each arm, and the 3 nearest tags in each arm. |

Each line of `test_pairs_v1.tsv` holds four fields, separated by tab characters:

| Field | Meaning |
|---|---|
| `entity_text` | A subject as a speech can name it, for example `notebandi` or `OROP`. |
| `acceptable_tags` | Each correct tag, with `\|` between the names. `NONE` means that no tag fits. |
| `kind` | The kind of difficulty, for example `hindi_latin`, `short_form`, `misspelling`, `synonym`, `law`, or `specific`. |
| `note` | Free text. |

A tag name in this file must exist in the table `tags`. The script stops if a name is not found. The rates count only the pairs that have an acceptable tag.
