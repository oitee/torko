# Tag embeddings, version 1

This folder holds the test for the tag vectors. Torko reads the debate transcripts of the Lok Sabha, the lower house of India's parliament. The tag list in `tags/seed_tags_v1/` gives 4,473 tags. A later step finds the subjects in each speech and links each subject to a tag. To find the right tag by meaning, and not only by exact words, each tag gets a vector.

## What a vector is

An embedding model reads a short text and returns a fixed list of numbers. This list is a vector. Two texts with a similar meaning get two vectors that are close. For example, "building highways" is close to the tag `Road Construction`, and far from the tag `Tea`.

The database measures "close" with cosine distance. The value is 0 when two vectors point in the same direction. A larger value means a less similar meaning.

A vector from one model cannot be compared with a vector from another model. A vector made for one task type cannot be compared with a vector made for an unmatched task type. So each stored vector records its model and its task type.

## The decisions

| Decision          | Value                                                                                              |
| ----------------- | -------------------------------------------------------------------------------------------------- |
| Model             | Google `gemini-embedding-001`                                                                      |
| Size              | 1,536 numbers for each vector, scaled to length 1 (Google asks for this below 3,072 numbers)       |
| Text for each tag | name, aliases, type, domain, and description, in one line                                          |
| Storage           | PostgreSQL with the pgvector extension, tables `tags` and `tag_embeddings` (`db/init/05-tags.sql`) |
| Index             | none, because a full scan of 4,473 rows takes a few milliseconds                                   |

Example of the text for one tag:

```
Road Construction. Also called: Road Development, Road Development Plans, Road Projects. Type: topic. Domain: Roads and Highways. Building or improving roads and highways.
```

## Task types

When Torko sends a text to the model, it adds a label that says what the vector is for. Google calls this label the task type. The same text gets a slightly different vector for each task type. This folder compares two choices:

| Arm | Vectors for tags | Vectors for the search text |
|---|---|---|
| A | `SEMANTIC_SIMILARITY` | `SEMANTIC_SIMILARITY` |
| B | `RETRIEVAL_DOCUMENT` | `RETRIEVAL_QUERY` |

`SEMANTIC_SIMILARITY` is for a comparison of two texts of the same kind. `RETRIEVAL_DOCUMENT` and `RETRIEVAL_QUERY` are a pair: one for the stored texts, one for the short text that searches them.

## How to run it

Run from the repo root. The database must run, and `.env` must hold `GEMINI_API_KEY`.

```bash
set -a && source .env && set +a
python3 scripts/load_tags.py
python3 scripts/embed_tags.py --task-type SEMANTIC_SIMILARITY
python3 scripts/embed_tags.py --task-type RETRIEVAL_DOCUMENT
python3 scripts/tag_bakeoff.py
```

1. `load_tags.py` copies `tags/seed_tags_v1/results/seed_tags_v1.tsv` into the table `tags`. It calls no model. A second run changes nothing.
2. `embed_tags.py` makes one vector for each tag and stores it in `tag_embeddings`. It embeds a tag again only when the text of the tag changed. Each run costs less than 1 US cent.
3. `tag_bakeoff.py` embeds the search text of each test pair, sorts all tags by distance, and finds the rank of the best acceptable tag. Rank 1 is the nearest tag.

The shared code is in `tag_embed.py`. The tests are in `tests/test_tag_embed.py`. They use no network.

## The test pairs

`data/test_pairs_v1.tsv` holds 74 pairs. Each pair was manually approved. Each line holds four fields, separated by tab characters:

| Field | Meaning |
|---|---|
| `entity_text` | A subject as a speech can name it, for example `notebandi` or `OROP`. |
| `acceptable_tags` | Each tag that is a correct match, with `\|` between the names. `NONE` means that no tag fits. |
| `kind` | The kind of difficulty, for example `hindi_latin` (a Hindi word in English letters), `short_form`, `misspelling`, or `specific` (a specific thing that maps to a general tag). |
| `note` | Free text. |

A tag name in this file must exist in the table `tags`. The script stops if a name is not found.

## The result (2026-10-02)

`results/bakeoff_v1.tsv` holds one row for each pair: the rank and the distance in each arm, and the 3 nearest tags in each arm.

The rates are counted over the 68 pairs that have an acceptable tag. The 6 pairs with only `NONE` are not in the rates.

| | Arm A | Arm B |
|---|---|---|
| Correct tag in the 10 nearest | 55/68 (81%) | 62/68 (91%) |
| Correct tag is the nearest | 34/68 (50%) | 39/68 (57%) |

Arm B is equal to or better than arm A in each kind. The largest differences are in `synonym` (A 4/7, B 7/7) and `law` (A 2/5, B 4/5).

## Known faults

- 4 test pairs are wrong. `Bharat Jodo Yatra`, `street vendors`, and `Sethusamudram project` are marked `NONE`, but the tags `Bharat Jodo Yatra`, `Vendors`, and `Sethusamudaram Project` exist. `Mullaperiyar dam` does not list the tag `Mullapperiyar Dam`, which both arms put at rank 1. A decision keeps the pairs as they are. So the real rates are slightly higher than the table above.
- The model does not understand every Hindi word in English letters. `jati janganana` (caste census) is at rank 906 in arm B. The other 5 Hindi pairs pass.
- With these pairs, the distance of a correct match and the distance of a no-match overlap. A simple distance limit cannot separate them.
- The vectors show near-duplicate tags that the merge step missed, for example `Naxalism` and `Naxalities` (distance 0.039).

## Done, next, unknown

**Done.** Both arms are embedded for all 4,473 tags. The comparison ran on 74 pairs.

**Done** Choose the winning arm, namely, Arm B.

**Next**. The vectors of the other arm are deleted from `tag_embeddings`.

**Unknown.** How the rates change on real subjects that an LLM takes from speeches. The test pairs were written by hand.
