# New tags

This folder holds the tags that Torko adds to its tag list from the speeches themselves. Torko reads the debate transcripts of the Lok Sabha, the lower house of India's parliament, and gives tags to each speech. The first tag list came from the keywords of sansad.in (`tags/seed_tags_v1/`) and from the districts and constituencies (`tags/places/`). Some subjects that members discuss often had no tag in these lists.

## Where the new tags come from

1. `tags/subject_groups/` groups the entity names of the speeches into subjects. A subject with no parent tag, 10 or more speeches, and 3 or more debates is a candidate for a new tag (`scripts/new_tag_candidates.py`).
2. An LLM review batch classified each candidate: `new` (a new tag, with a name, type, and domain), `existing` (a tag that exists already fits), `general` (too general for a tag), or `other`. A manual review then checked every row and edited some. All decisions are in `tags/subject_groups/data/new_tag_reviews_v1.tsv`.
3. This folder turns the rows with decision `new` into tags.

## Layout

- `data/fills_v1.tsv`: a type or domain for a new tag whose rows have none. These are the rows that the manual review changed from `existing` to `new`. Columns: tag, field, value, note.
- `data/descriptions_v1.tsv`: one description for each new tag, written by an LLM. Columns: tag, description, model. A rerun of the LLM gives other text, so keep this file.
- `results/new_tags_v1.tsv`: the list of new tags, with the columns of the seed list. `build` writes it again from the files above.

## How to run

```bash
source .venv/bin/activate
set -a && source .env && set +a
python3 scripts/build_new_tags.py describe --dry-run   # count the tags without a description
python3 scripts/build_new_tags.py describe             # ask the LLM for the missing descriptions
python3 scripts/build_new_tags.py build                # write results/new_tags_v1.tsv, no model call
python3 scripts/load_tags.py --dry-run
python3 scripts/load_tags.py
```

`describe` sends the tags in batches of 40. For each tag, it sends the name, type, domain, and up to 6 entity names of its subjects, so that the model can choose the right meaning of an ambiguous name. It adds only the tags that have no description, so a second run sends nothing.

`build` stops with a list of problems, and writes nothing, when a tag has no type, no domain, no description, a type or domain that is not in use, or two rows with different values for one field. When two rows propose one tag, the values of a row that the manual review edited win.

`scripts/load_tags.py` loads the list as source `subjects_v1`, with status `reviewed`, because a manual review checked every row. After a load, embed the new tags (`scripts/embed_tags.py --task-type RETRIEVAL_DOCUMENT`), then run stage 5 (`scripts/link_entities.py`) and the parent step (`scripts/subject_parents.py`) again.
