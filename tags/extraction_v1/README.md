# Speech summaries and entities, version 1

This folder holds the first test of step 3 of the tag plan. Torko reads the debate transcripts of the Lok Sabha, the lower house of India's parliament. Torko groups the turns of one member into a speech. For each speech, an LLM writes a one-sentence summary and two lists: at most 8 topics, and at most 8 other entities. A later step links each entity to a tag in `tags/seed_tags_v1/`, with the vectors in `tags/embedding_v1/`.

An entity is a subject that a reader can search for: a topic, a law, a scheme, an institution, a place, a person, a group of people, or an office. A topic is a subject or an issue, for example `Air Pollution`. The other entities are named things of the 7 other types. The model gives each item a salience from 1 to 5. 5 means the main subject of the speech. 1 means a passing mention.

Nothing in this folder goes into the database. The output is for a human review.

## How to run it

Run from the repo root. The database must run, and `.env` must hold `GEMINI_API_KEY`.

```bash
set -a && source .env && set +a
python3 scripts/extract_entities.py --year 2019
```

The options:

| Option | Default | Meaning |
|---|---|---|
| `--year` | (required) | The year of the debates. |
| `--debates` | 10 | The number of random debates. |
| `--per-debate` | 3 | The largest number of random speeches from one debate. |
| `--min-words`, `--max-words` | 100, 5000 | Only speeches in this range of words. |
| `--seed` | 1 | The same seed gives the same sample. |
| `--model` | `gemini-3.8-flash` | The Gemini model. |

Only speeches with a known member are used. The text of a speech is the member's own turns, in order. A speech never holds the words of another member. This was checked on 2026-10-03: 0 of 198,507 turns.

## The files

| Path | Holds |
|---|---|
| `prompts/extract_v1.md` | The instructions that the model reads. Each result names this file and stores the md5 of its text, so a changed prompt is visible. |
| `results/<year>_seed<seed>_<model>_<date>.jsonl` | One record per speech: the speech facts, the summary, `topics`, `other_entities`, any warnings, the raw model answer, the token counts, and the prompt md5. |
| `results/<year>_seed<seed>_<model>_<date>.md` | The review file. One section per speech, with an excerpt, a link to the source page, the summary, a table of topics, a table of other entities, and an empty `review:` line. The script never overwrites a result: a second run with the same name gets `_2`, `_3`. |

The script checks each model answer against the rules: at most 8 items in each list, no name in both lists, a known type, a salience from 1 to 5, at least one topic when there are other entities, at most 2 items at salience 5, and a summary of at most 30 words. A broken rule shows as a warning in both files. The script never uses the answer of the model without this check.

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
