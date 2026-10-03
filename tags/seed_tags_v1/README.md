# Seed tag list, version 1

This folder holds the first tag vocabulary for Torko. Torko reads the debate transcripts of the Lok Sabha, the lower house of India's parliament. The official website sansad.in attaches keywords to each debate. This folder turns those keywords into a list of tags. A later step uses the list to tag each speech.

## The result

`results/seed_tags_v1.tsv` holds 4,473 tags. They come from the 5,319 sansad.in keywords that appear in 2 or more debates. Each tag has a type, a domain, a one-line description, and its aliases. An alias is another spelling or another name for the same tag. Each keyword appears exactly one time in the file, as a tag or as an alias. The only exceptions are the 44 keywords that was manually dropped: 14 junk tags and 30 general words with no subject, for example `Delay` and `Reports`.

Each tag of the types `topic`, `institution`, `law`, and `scheme` has a domain. The domains follow the Union ministries, plus one domain manually added: `Society and Communities`. A place, a group, a role, or a person can have no domain (`-`). That is on purpose, because no ministry owns a state or a class of people.

The `debate_count` column counts keyword-to-debate links, not debates. One debate can carry about 59 keywords. The counts measure coverage, not accuracy. A manual review checked a sample of the list, not every row. Read "Known faults" before you trust a single tag.

To see the list in a browser, run the build script. Then serve the `atlas/` folder (for example with `python3 -m http.server` in that folder) and open `index.html`.

## How it was made

| Step | Who | Input | Output |
|---|---|---|---|
| 1. Classify | LLM batch run, `claude-haiku-4-5` | `results/chunks/` | `data/llm_classify/` |
| 2. Merge near-duplicates | LLM batch run, `claude-sonnet-5` | `results/merge_in/` | `data/llm_merge/` |
| 3. Assemble | `scripts/build_seed_tags.py` | `data/llm_merge/` | `results/seed_tags_v1.tsv` |
| 4. Repair the assembly | manual rule | | `data/fixes_assembly.tsv` |
| 5. Fix the types | manual rule | | `data/fixes_types.tsv` |
| 6. Review | manual review | | `data/review.tsv` |

What each step does:

1. **Classify.** Each run got 400 keywords. For each keyword, it gave a type (for example `topic`, `law`, `place`), a domain from a fixed list of 28 that follow the Union ministries, and a description of below 20 words.
2. **Merge near-duplicates.** The keywords were grouped by type and domain, because near-duplicates usually share both. Each run got one pack of at most 350 keywords. It put the keywords that mean the same thing into one group, chose one name for the group, and made the other names aliases. The rule was: when unsure, do not merge.
3. **Assemble.** The script joins the groups into one list. It makes sure that each keyword appears exactly one time. When the merge run changed the spelling of a keyword, for example `Nfdc` to `NFDC`, the script attaches the original spelling as an alias. Some sansad.in keywords start or end with a space, for example ` Caste Census`. The script removes these spaces from the tag name and keeps the original spelling as an alias. 5 tag names had such spaces.
4. **Repair the assembly.** A manual repair merged 6 groups with near-identical names, for example `Agroindustry` and `Agro-industry`, and attached 3 keywords that the script could not place.
5. **Fix the types.** The classify run had put job titles and classes of people under `person`. A rule was manually set during review: `person` is one named human, `role` is an office that one person holds at a time, and `group` is a class of many people. A manual fix applied the rule to each tag. It also gave each place a subtype, to separate real geography (`state`, `river`) from general areas (`Drought Prone Areas`).
6. **Review.** A sample of the list was manually reviewed and each decision was written as one line in `data/review.tsv`.

The prompts are in `prompts/`. Each `run.json` file gives the model and the date of one LLM step.

## The rule for this folder

`data/` holds the files that no script can make again. A new model run gives a different result, and a script cannot compute a human decision.

`results/` holds the files that the script makes. Do not edit them. Run the script:

```bash
python3 scripts/build_seed_tags.py
```

The script calls no model. It reads `data/` and writes `results/` and `atlas/tags.json`. On every run, it checks that each keyword appears exactly one time and that the debate counts balance. Git ignores `results/chunks/`, `results/merge_in/`, and `atlas/tags.json`. Git keeps `results/seed_tags_v1.tsv`, so that a reader can see the list without a run.

## Files

| Path | Holds |
|---|---|
| `prompts/classify_v1.md` | The prompt for step 1. |
| `prompts/merge_v1.md` | The prompt for step 2. |
| `data/tags_raw.tsv` | The 5,319 keywords with their debate counts, from the `debates.keywords` column. |
| `data/llm_classify/` | The output of step 1. One file for each input chunk. |
| `data/llm_merge/` | The output of step 2. One file for each input pack. |
| `data/fixes_assembly.tsv` | 11 repairs: 6 merges of groups with near-identical names, 3 keyword spellings that the merge run changed, and 2 extra aliases without a trailing space. |
| `data/fixes_types.tsv` | 252 edits: the types `role` and `group`, and a subtype for each place. |
| `data/review.tsv` | The manual review decisions: merges, drops, types, and descriptions. |
| `results/seed_tags_v1.tsv` | The tag list. |
| `results/assembly_log.txt` | Every repair that the assembly step made. |
| `results/chunks/`, `results/merge_in/` | The exact inputs of steps 1 and 2. |
| `atlas/index.html` | A browser view of the tag list. |

## After this folder

`scripts/load_tags.py` loads `results/seed_tags_v1.tsv` into the database table `tags`. The vectors for each tag, the test pairs, and the result of the comparison of task types are in `tags/embedding_v1/`. Read its `README.md`.

## Known faults

- `data/llm_classify/` is not the unedited model output. A manual rule corrected 328 domains inside these files. The unedited output was not kept.

## How to fix a tag

Do not edit `results/seed_tags_v1.tsv`. The script writes it again on each run. Add one line to `data/review.tsv` for each decision, then run the script. Each line holds four fields, separated by tab characters: `tag`, `field`, `value`, `note`.

| `field` | `value` | Meaning |
|---|---|---|
| `drop` | empty | Delete this tag and all its aliases. |
| `type` | the right type | The type is wrong. |
| `subtype` | the right subtype | The place subtype is wrong. |
| `domain` | the right domain | The domain is wrong. |
| `description` | the new text | The description is wrong or weak. |
| `merge` | the other tag | This tag and the other tag are the same thing. This tag becomes an alias of the other tag. |
| `split` | one alias of this tag | The alias means a different thing. It becomes a new tag of its own, with the same type and domain. Set its description with another line. |
| `aliases` | names, with `\|` between them, or `-` | Set the full alias list. |
| `add_alias` | one name | Add one alias. |
| `todo` | anything | No action. A note for a decision that the script cannot apply, for example a split. |

The script stops with an error if a line names a tag that does not exist. In `note`, write only the date of the review, for example `Reviewed on 2026-09-26`.
