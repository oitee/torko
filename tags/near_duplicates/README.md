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

`data/merges_v1.tsv` holds the merges that a manual review accepted: `tag_from` merges into `tag_into`. `new_name` and `new_type` are set when the merged tag gets a new name or type. `note` is the reason from the review.

The rule from the review: a merge must not make a tag more general than what the speeches say. A specific subject, for example "farmers' arrears", becomes a subject under a tag (`tags/subject_groups/`) or a new tag. It does not go into a broad tag.

## Groups and kept tags

Merge rows can form chains and loops. For example, `Encroachment` merges into `Land Encroachment`, `Land Encroachment` merges into `Unauthorized Encroachments`, and `Unauthorized Encroachments` merges into `Encroachment`. All tags that the rows join form one group, and the whole group goes into one kept tag. `tag_merges.py` finds the groups:

- A group with exactly one tag that is never a `tag_from` keeps that tag.
- Any other group needs a row in `data/group_targets_v1.tsv`. The row names the kept tag (`target`), an optional `new_name`, and the reason. A row can also choose a kept tag that is not the end of a chain.

The 185 rows make 173 groups with 183 merged tags. Two tags (`SC&ST`, `CG Grants`) appear in two rows each.

## How to apply the merges

```bash
source .venv/bin/activate
set -a && source .env && set +a
python3 scripts/apply_tag_merges.py --dry-run
python3 scripts/apply_tag_merges.py
python3 scripts/embed_tags.py --task-type RETRIEVAL_DOCUMENT
python3 scripts/link_entities.py
```

`scripts/apply_tag_merges.py` calls no model. It writes these changes in one transaction:

- Each kept tag gets the names and aliases of its merged tags as aliases, and its new name or type.
- Each merged tag gets status `merged` and `merged_into` = the kept tag. The row stays.
- The links of entity names, the recognised-tag rows of `speech_items`, and the parents of subjects move to the kept tag.
- An entity name with no tag is decided again by stage 5 when two or more tags of one group together got 0.7 or more of its vote. The script clears `tag_set_version` of these names, so the next run of `scripts/link_entities.py` decides them again.

A second run changes nothing. `scripts/load_tags.py` applies the same groups to the rows of the tag lists, so a reload keeps the merges. Every step that offers tags as options skips the status `merged`.

After a merge, one speech can have two recognised-tag rows that point to one kept tag. Each row keeps its own relevance decision. A count per speech and tag must count each pair once.
