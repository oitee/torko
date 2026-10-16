# Speech summaries and entities, version 1

This folder holds the first test of step 3 of the tag plan. Torko reads the debate transcripts of the Lok Sabha, the lower house of India's parliament. Torko groups the turns of one member into a speech. For each speech, an LLM writes a one-sentence summary and two lists: at most 8 topics, and at most 8 other entities. A later step links each entity to a tag in `tags/seed_tags_v1/`, with the vectors in `tags/embedding_v1/`.

An entity is a subject that a reader can search for: a topic, a law, a scheme, an institution, a place, a person, a group of people, or an office. A topic is a subject or an issue, for example `Air Pollution`. The other entities are named things of the 7 other types. The model gives each item a salience from 1 to 5. 5 means the main subject of the speech. 1 means a passing mention.

The answers go into the database tables `speech_extractions` and `speech_items` (`db/init/06-tag-pipeline.sql`). A sample run also writes a review file into `results/`.

The script is idempotent. The database holds at most one extraction per speech: the unique key is `speech_id`. The script never sends a speech to a model when the database already holds an extraction for it, whatever model made that extraction. The column `model_id` names the model that made the extraction. It points to the table `models`, which holds one row for each model name. This column is metadata for review and audit only. The model name `rule-stub` means a fixed answer with no model call. It is used for a procedural speech, for example papers laid on the Table, and for a speech with no text. The script never counts a `rule-stub` extraction as stale. An extraction made with an older prompt version is "stale": the script counts it and skips it, and `--redo-stale` replaces it. `--force` replaces every selected extraction, also an extraction made with the current version. The script deletes an old extraction in the same transaction that stores the new one. So a failed answer keeps the old extraction. A speech with no extraction and a failed answer stays without one, and the next run tries again.

## Prompt versions

Each prompt is one file: `prompts/extract_v1.md`, `prompts/extract_v2.md`, and so on. The number after `v` is the version. Each row in `speech_extractions` stores its version in the column `prompt_version`, for example `v1`.

The rules:

1. Do not edit a prompt file after a run writes rows with it. Put the change in a new file with the next number.
2. While you draft a new prompt, you can edit its file as often as necessary. Do this before the first run that stores rows.
3. By default, the script uses the highest version. `--prompt v1` picks another version.

The script does not check rule 1. A person must follow it.

On 2026-10-03, all 136 rows in the database were set to `v1`. Some of these rows came from an earlier text of `extract_v1.md`, before rule 7 (papers laid on the Table) was added. A decision accepted this small inaccuracy.

## Which speeches have an extraction

The scope is every speech of LS 17 and LS 18 with a known member and 99 or more words. Every speech in this scope has an extraction since 2026-10-07: 27,290 speeches.

Most of these rows came from earlier batch runs outside this script, with prompt versions `v1` and `v2`. Each row records the model name and the prompt version of its batch run. A one-off loader stored their answers with the same checks that the script uses. The database then holds 28,394 extractions. 1,103 of them are for speeches under 99 words, because the batch runs counted the words in a different way.

## How to run it

Run from the repo root. The database must run, and `.env` must hold `GEMINI_API_KEY`.

```bash
set -a && source .env && set +a
python3 scripts/extract_entities.py --year 2019
python3 scripts/extract_entities.py --term 18 --all --dry-run
python3 scripts/extract_entities.py --term 18 --all --workers 8
```

The options:

| Option | Default | Meaning |
|---|---|---|
| `--year` or `--term` | (one is required) | The year of the debates, or the Lok Sabha term, for example `17`. |
| `--all` | off | Every qualifying speech in the year or term. No review file. |
| `--debates` | 10 | The number of random debates. |
| `--per-debate` | 3 | The largest number of random speeches from one debate. |
| `--min-words`, `--max-words` | 99, 5000 | Only speeches in this range of words. |
| `--seed` | 1 | The same seed gives the same sample. |
| `--model` | `gemini-3.5-flash-lite` | The LLM that extracts. |
| `--prompt` | the highest version | The prompt version, for example `v1`. |
| `--workers` | 4 | API calls at the same time. |
| `--redo-stale` | off | Extract again the speeches whose extraction came from an older prompt version. |
| `--force` | off | Extract again every selected speech, also the speeches done with the current prompt version. |
| `--dry-run` | off | Print the counts and a token estimate. Call no model. |

Only speeches with a known member are used. The text of a speech is the member's own turns, in order. A speech never holds the words of another member. This was checked on 2026-10-03: 0 of 198,507 turns.

## The files

| Path | Holds |
|---|---|
| `prompts/extract_v<N>.md` | The instructions that the model reads, one file per version. Each row stores its version. |
| `results/*.jsonl` | Only the first three runs (before the database storage). One record per speech. |
| `results/<year or term>_seed<seed>_<model>_<date>.md` | The review file, built from the database. One section per speech, with an excerpt, a link to the source page, the summary, a table of topics, a table of other entities, and an empty `review:` line. The script never overwrites a result: a second run with the same name gets `_2`, `_3`. |

The script checks each model answer against the rules: at most 8 items in each list, no name in both lists, a known type, a salience from 1 to 5, at least one topic when there are other entities, at most 2 items at salience 5, a summary of at most 30 words, and a mention of at most 8 words. For each item, `mention_found` says whether the mention is in the speech text. A broken rule shows as a warning in both files. The script never uses the answer of the model without this check.

## How to review

Open the `.md` file. For each speech, write `ok` after `review:`, or write what is wrong. Useful questions:

- Does the summary say what the member raised, without a judgement?
- Is the main subject at salience 5?
- Is any important subject missing?
- Is any entity not useful for search, for example a party leader that the member thanks?
- Is the English name the usual name?

## Runs

| Run | Speeches | Notes |
|---|---|---|
| 2019, seed 1, `gemini-3.8-flash`, 2026-10-03 | 15 from 10 debates | First prompt (one list of 8). 0 warnings. 11 speeches in Hindi or mixed. About 22,000 input tokens and 12,000 output and thinking tokens. |
| 2019, seed 1, `gemini-3.5-flash-lite`, 2026-10-03 | 15 from 10 debates | First prompt (one list of 8). 0 topics in 10 of 15 speeches. |
| 2019, seed 1, `gemini-3.5-flash-lite`, 2026-10-03, `_2` | 15 from 10 debates | Two lists, 8 + 8. 2 to 5 topics in every speech. Salience 5 still overused. |
