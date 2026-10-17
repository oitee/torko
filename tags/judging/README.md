# Relevance check of speech items

This step is stage 4 of the tag pipeline. Each speech has items: topics and other entities from [the extraction](../extraction_v1/README.md), and added candidates. Stage 4 decides which items are real subjects of the speech. It writes `judge_subject_p`, `judge_use_p`, `kept`, and `judged_by` in `speech_items`.

A decision model answers fixed questions with a probability for each answer. It writes no text. `scripts/judge_items.py` sends one call per speech.

## How to run

Run from the repo root. The database must run, and `.env` must hold `TYPESAFE_API_KEY`.

```bash
set -a && source .env && set +a
python3 scripts/add_candidates.py --speech-ids 260741,340402 --dry-run
python3 scripts/add_candidates.py --speech-ids 260741,340402
python3 scripts/judge_items.py --speech-ids 260741,340402 --dry-run
python3 scripts/judge_items.py --speech-ids 260741,340402 --prefill tags/judging/results/<old marks>.tsv
python3 scripts/judge_items.py --rethreshold --term 18 --questions q4
python3 scripts/judge_items.py --score tags/judging/results/<file>.tsv --questions q4
```

Run `scripts/add_candidates.py` before `scripts/judge_items.py`. Both scripts are idempotent. `judge_items.py` skips each item that the current model and question version judged. `--force` judges again. Scope options: `--year`, `--term`, `--speech-ids`, `--max-words`. Use `--all` for a full run with no review file.

## Candidates

Each candidate is a row of `speech_items`. The column `source` tells where it comes from.

| Source | Added by | List | At most | Question |
|---|---|---|---|---|
| `llm` | the extraction | `topic` and `other` | 8 + 8 | topic: `subject`. Named item: `use` |
| `dictionary` | `scripts/add_candidates.py` | `other` | 8 (`--k`) | `use` |
| `summary_tag` | `scripts/add_candidates.py` | `topic` | 12 (`--n`) | `subject`, with the tag type only |

A `dictionary` row is an entity name from [the entity dictionary](../entity_dictionary/README.md) whose words are in the speech but not in the extraction. A name is not added when every match lies inside a longer name. A `summary_tag` row is one of the nearest tags from [the summary tags](../summary_tags/README.md). It holds the tag in `tag_id`, so stage 5 does not link it. The column `evidence` keeps the matches or the distance, and the rank.

## The questions

The question version is `QUESTIONS_VERSION` in `scripts/judge_items.py`. It is `q5`. The script writes it with the model name into `judged_by`, for example `jev-1.13.0 q5`. Do not change a question text without a new version.

A topic or a recognised tag gets one true-or-false statement: the item is a main or supporting subject, not only a passing mention. Every other item gets one choice question with these answers:

- `absent`: not mentioned, or only the speaker or the Chair.
- `aside`: only an example, precedent, comparison, courtesy, or side list item.
- `point`: part of the member's point.
- `other_meaning`: the words mean something else than this name.

The state is the member, the debate title, the date, and the speech text. When the speech does not fit in the context, the state is the summary and the mention of each item. The column `judge_state` records which state was used.

## The keep rule

An item is kept when P(true), or P(point) for a named item, reaches the limit of its source. The defaults are in `Thresholds` in `scripts/judge_items.py`.

| Source | Limit | Flag |
|---|---|---|
| `llm` (the extraction chose the item) | 0.4 | `--keep-llm` |
| `dictionary` and `summary_tag` (added candidates) | 0.8 | `--keep-other` |

The `llm` limit is low because dropping a correct item is the bad error. The limit of added candidates is high because keeping a wrong one is the bad error.

`--rethreshold` applies new limits to the stored probabilities with no new call.

Term 18 used the older question version `q4`. `--questions q4` reads those rows for `--rethreshold` and `--score`. Only `q4` uses `--keep-refers`.

## Results

A sample run writes a Markdown file and a TSV file into `results/`. The TSV file has an empty `review` column. Write `keep` or `drop` for each item. `--prefill FILE` copies the marks of an earlier review file into the new one. `--score FILE` compares the marks with the decisions of the model, for each source.
