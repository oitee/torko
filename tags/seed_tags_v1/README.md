# Seed tag list, version 1

This step turns the keywords of sansad.in debates into a list of tags. The input is the `debates.keywords` column. The output is `results/seed_tags_v1.tsv`. The script `scripts/load_tags.py` loads this file into the database table `tags`.

Each tag has a type, a domain, a one-line description, and aliases. An alias is another spelling or another name for the same tag. Each keyword appears one time in the file, as a tag or as an alias. Types without a ministry (place, group, role, person) have the domain `-`.

## How the model steps ran

The two model steps, classify and merge, ran as offline LLM batch runs. The build script writes the input files into `results/chunks/` and `results/merge_in/`. An LLM answered each input file with the prompt in `prompts/`. The answers are stored in `data/llm_classify/` and `data/llm_merge/`, with a `run.json` file that names the model and the date. No script in this repository calls a model for these steps.

## How to run

The build script calls no model. It reads `data/` and writes `results/`. It also writes `atlas/tags.json` for a local review page. It checks that each keyword appears one time and that the debate counts balance.

```bash
python3 scripts/build_seed_tags.py
```

## The rule for this folder

`data/` holds the files that no script can make again: model outputs and human decisions. Never edit a file in `data/` after its step ran. The only exception is `review.tsv`, where you add lines.

`results/` holds files that the script makes. Do not edit them. Git ignores `results/chunks/` and `results/merge_in/`.

The `atlas/` folder is a local page for a manual review of the list

## Files

| Path | Holds |
|---|---|
| `prompts/classify_v1.md` | The prompt that gives each keyword a type, a domain, and a description. |
| `prompts/merge_v1.md` | The prompt that groups near-duplicate keywords. |
| `data/tags_raw.tsv` | The keywords with their debate counts. |
| `data/llm_classify/` | The output of the classify step, one file for each input chunk. It holds hand fixes of the domain, so it is not the raw model output. |
| `data/llm_merge/` | The model output of the merge step. One file for each input pack. |
| `data/fixes_assembly.tsv` | Hand repairs of the assembly: merges, changed spellings, extra aliases. |
| `data/fixes_types.tsv` | Hand edits of types (`role`, `group`) and place subtypes. |
| `data/review.tsv` | Review decisions. |
| `results/seed_tags_v1.tsv` | The tag list. |
| `results/assembly_log.txt` | Each repair that the assembly step made. |
| `results/chunks/`, `results/merge_in/` | The exact inputs of the two model steps. |

## Type rules

`person` is one named human. `role` is an office that one person holds at a time. `group` is a class of many people. Each place has a subtype, for example `state` or `river`.

The `debate_count` column counts keyword-to-debate links, not debates.

## How to fix a tag

Add one line to `data/review.tsv` for each decision, then run the build script. Each line holds four fields, separated by tab characters: `tag`, `field`, `value`, `note`. In `note`, write only the date of the review, for example `Reviewed on 2026-09-26`. The files `fixes_assembly.tsv` and `fixes_types.tsv` use the same four columns.

| `field` | `value` | Meaning |
|---|---|---|
| `drop` | empty | Delete this tag and all its aliases. |
| `type` | the right type | The type is wrong. |
| `subtype` | the right subtype | The place subtype is wrong. |
| `domain` | the right domain | The domain is wrong. |
| `description` | the new text | The description is wrong or weak. |
| `merge` | the other tag | This tag becomes an alias of the other tag. |
| `split` | one alias of this tag | The alias becomes a new tag with the same type and domain. Set its description with another line. |
| `aliases` | names, with `\|` between them, or `-` | Set the full alias list. |
| `add_alias` | one name | Add one alias. |
| `todo` | anything | No action. A note for a decision that the script cannot apply. |

The script stops with an error if a line names a tag that does not exist.

## Next step

The vectors for the tags are in [the embedding step](../embedding_v1/README.md).
