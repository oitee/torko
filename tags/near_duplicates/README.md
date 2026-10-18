# Near-duplicate tags

This folder holds the work on tags that mean the same thing. Torko reads the debate transcripts of the Lok Sabha, the lower house of India's parliament. Each speech gets tags from one tag list (`tags/seed_tags_v1/` and `tags/places/`).

## The problem

Stage 5 of the tag pipeline (`tags/linking/`) links each entity name from a speech to one tag. A decision model gives a probability to each of about 20 candidate tags. The name links only when one tag gets 0.7 or more. When two tags mean the same thing, the model divides its vote between them. For example, a name gets 0.5 for `Rail Budget` and 0.4 for `Railway Budget`, and gets no tag.

## How to run

```bash
source .venv/bin/activate
set -a && source .env && set +a
python3 scripts/split_vote_pairs.py
```

The script reads the stored stage 5 answers of every entity name without a tag. It calls no model and writes nothing to the database. For each name, it takes the two tags with the highest probability. It records the pair when the two probabilities together reach 0.7 and the second reaches 0.2 (`--min-sum`, `--min-second`). It writes `results/split_pairs_v1.tsv`, one row per pair, with counts, both descriptions, the distance of the two tag vectors, and example names.

## The merge decisions

`data/merges_v1.tsv` holds the merges that a manual review accepted: `tag_from` merges into `tag_into`. `new_name` and `new_type` are set when the merged tag gets a new name or type. `note` is the reason from the review. No merge is applied to the database yet.

The rule from the review: a merge must not make a tag more general than what the speeches say. A specific subject, for example "farmers' arrears", becomes a subject under a tag (`tags/subject_groups/`) or a new tag. It does not go into a broad tag.
