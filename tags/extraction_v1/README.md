# Speech summaries and entities, version 1

This step reads each speech and asks an LLM for a one-sentence summary and two lists: at most 8 topics and at most 8 other entities. A speech is the turns of one member, in order. The answers go into the tables `speech_extractions` and `speech_items` (`db/init/06-tag-pipeline.sql`). A later step links each entity to a tag. See [the linking step](../linking/README.md).

An entity is a subject that a reader can search for. The types are topic, law, scheme, institution, place, person, group, and role. Each item has a salience from 1 (passing mention) to 5 (main subject).

## How to run

Run from the repo root. The database must run, and `.env` must hold `GEMINI_API_KEY`.

```bash
set -a && source .env && set +a
python3 scripts/extract_entities.py --year 2019
python3 scripts/extract_entities.py --term 18 --all --dry-run
python3 scripts/extract_entities.py --term 18 --all --workers 8
```

| Option | Default | Meaning |
|---|---|---|
| `--year` or `--term` | none, one is required | The year of the debates, or the Lok Sabha term, for example `17`. |
| `--all` | off | Every qualifying speech in the year or term. No review file. |
| `--debates` | 10 | Sample mode: the number of random debates. |
| `--per-debate` | 3 | Sample mode: the largest number of random speeches from one debate. |
| `--min-words`, `--max-words` | 99, 5000 | Only speeches in this range of words. |
| `--seed` | 1 | The same seed gives the same sample. |
| `--model` | `gemini-3.5-flash-lite` | The LLM that extracts. |
| `--prompt` | the highest version | The prompt version, for example `v1`. |
| `--workers` | 4 | API calls at the same time. |
| `--redo-stale` | off | Replace the extractions that came from an older prompt version. |
| `--force` | off | Replace every selected extraction, also one made with the current version. |
| `--dry-run` | off | Print the counts and a token estimate. Call no model. |

## Files

| Path | Holds |
|---|---|
| `prompts/extract_v<N>.md` | The instructions that the model reads. One file for each version. |
| `results/*.jsonl` | Records of the first test runs, before the database storage. |
| `results/<year or term>_seed<seed>_<model>_<date>.md` | A review file for a sample run. One section per speech, with an empty `review:` line. The script never overwrites a file and adds `_2`, `_3` to a repeated name. |

To review a sample, write `ok` after each `review:` line, or write what is wrong.

## Prompt versions

The number after `v` in the prompt file name is the version. Each row in `speech_extractions` stores it in the column `prompt_version`.

Never edit a prompt file after a run stored rows with it. Put the change in a new file with the next number. You can edit a draft prompt until its first run that stores rows. The script does not check this rule.

## Rules the code applies

- The database holds at most one extraction for each speech (unique key `speech_id`). The script never sends a speech to a model when an extraction exists, whatever model made it.
- An extraction is stale when its `prompt_version` is older than the selected version. The script counts stale rows and skips them. `--redo-stale` replaces them. `--force` replaces all selected rows.
- The model name `rule-stub` marks a fixed answer with no model call, for a procedural speech or a speech with no text. It is never stale.
- The script deletes the old extraction in the same transaction that stores the new one. A failed answer keeps the old extraction.
- Only speeches with a known member are used.
- The script checks each answer: at most 8 items in each list, no name in both lists, a known type, a salience from 1 to 5, at least one topic when there are other entities, at most 2 items at salience 5, a summary of at most 30 words, and a mention of at most 8 words. A broken rule becomes a warning. The script never uses an unchecked answer.
- For each item, `mention_found` says whether the mention appears in the speech text.
