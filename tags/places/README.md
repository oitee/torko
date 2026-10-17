# Place tags for districts and constituencies

This step builds place tags for the districts of India and for the 543 current Lok Sabha constituencies. It reads Wikipedia pages and the hand-made files in `data/`. It writes `results/place_tags.tsv` and does not write to the database.

The [linking step](../linking/README.md) links an entity name to a tag without the decision model when the name equals the name or alias of exactly one tag. So each name and alias here can make an automatic link. A wrong link is worse than no link.

## How to run

```bash
source .venv/bin/activate
python3 -I scripts/build_place_tags.py
```

The script calls no model. The flag `-I` stops Python from loading code from the data folders. It exits with an error when a self check fails.

The coverage check reads the database with SELECT statements only. Run the build again after it, so that the `common_word` rows can use `results/db_entity_names.tsv`.

```bash
set -a && source .env && set +a
python3 scripts/check_place_coverage.py
python3 -I scripts/build_place_tags.py
```

You can change the input paths with `--districts`, `--constituencies`, `--renames`, `--seed`, and `--out`. The tests are in `tests/test_build_place_tags.py`.

## Files

| Path | What it is |
|---|---|
| `data/raw/districts/`, `data/raw/constituencies/` | The rendered Wikipedia pages ("List of districts in India", "List of constituencies of the Lok Sabha"). Do not edit them. |
| `data/same_place.tsv` | Hand-made. One district and one constituency of the same place with two spellings. |
| `data/old_seats.tsv` | Hand-made. One decision for each old Assam seat. |
| `data/renames.tsv` | Hand-made. District renames. |
| `data/common_words.tsv` | Hand-made. Place names that are also ordinary words. |
| `data/extra_aliases.tsv` | Hand-made. One alias for one new tag. |
| `data/near_hints.tsv` | Hand-made. A place and an existing tag that may be the same area. Review only. |
| `results/place_tags.tsv` | The new tags. The columns are the same as the seed tag file. |
| `results/place_sources.tsv` | One row for each source place. The column `reserved` holds the SC or ST class. |
| `results/review_pairs.tsv` | One row for each possible duplicate or risk. Fill the empty `review` column by hand. |
| `results/review_pairs.md` | The first rows of each kind in the review file. |
| `results/alias_review.md` | The evidence for the alias decisions. |
| `results/build_report.md` | The counts for each state and the result of each self check. |
| `results/coverage_check.md` | How many database place names equal a tag. It does not measure correct links. |
| `results/db_entity_names.tsv`, `results/db_unmatched_names.tsv` | Written by the coverage check. Entity names of other types, and place names that match no tag. |

### Formats of the hand-made files

All files are tab-separated and have a header row.

- `same_place.tsv`: `name_a`, `name_b`, `state`, `keep`, `note`. The `keep` value is the district spelling. The other spelling becomes an alias. The build stops when a row names a missing place or two places of one kind.
- `old_seats.tsv`: `old_name`, `state`, `decision`, `target`, `note`, `description`. The decision is `same` (a tag or alias has the name), `alias` (the old name becomes an alias of the tag in `target`), `former` (the seat gets its own tag), or `ignore`. The optional `description` replaces the made description of a `former` tag. Each old Assam seat needs one row.
- `renames.tsv`: `old_name`, `new_name`, `state`, `year`, `source_url`, `checked`. The value `checked` is `yes` when a source confirmed the rename and `no` when it did not. Check a `no` row before you trust its year.
- `common_words.tsv`: `word`, `meaning`.
- `extra_aliases.tsv`: `alias`, `tag`, `state`, `items`, `evidence`, `reason`. Read example mentions before you add a row. The self checks reject an alias that equals the name or alias of another tag.
- `near_hints.tsv`: `place`, `state`, `other`, `note`.

## Rules the code applies

1. Each district and each constituency becomes a tag of type `place` with domain `-`. A suffix `(SC)` or `(ST)` is not part of the name.
2. A district and a constituency with the same name in the same state share ONE tag. The subtype is `district_constituency`. The merge uses the name only.
3. The other subtypes are `district`, `constituency`, and `former_constituency`.
4. Two or more places in different states can claim one name. A claim is a current name or an old name from `renames.tsv`. Each such tag gets the state in brackets, for example `Aurangabad (Bihar)`, and the bare name as an alias. The bare name then equals two or more tags, so the decision model decides.
5. A place whose name equals the name or alias of an existing tag gets no new tag. An alias that equals an existing name or alias is dropped. A review row records each case.
6. An old district name from `renames.tsv` is an alias of the tag with the new name.
7. The script adds only two spelling forms by itself: the name without diacritics, and the name with the other dash character. It adds no Hindi alias.
8. The list `MODEL_ONLY` in `scripts/link_entities.py` holds place names that are also ordinary words, for example `basti` and `mandi`. For these names the linking step always asks the decision model, also when one tag has the name.
