tags/judging/README.md# Relevance check of speech items

This folder holds stage 4 of the tag pipeline. Torko reads the debate transcripts of the Lok Sabha, the lower house of India's parliament. Stage 3 (`tags/extraction_v1/`) gives each speech at most 8 topics and 8 other entities, called items. Some items are only background, or the speaker, the Chair, or procedure. Stage 4 decides which items are real subjects of the speech.

A decision model answers fixed questions with a probability for each answer. It writes no text. `scripts/judge_items.py` sends one call per speech.

## The candidates of a speech

Every candidate is a row of `speech_items`. The column `source` tells where the row comes from:

| Source | Added by | List | At most | Question |
|---|---|---|---|---|
| `llm` | stage 3, the extraction | `topic` and `other` | 8 + 8 | topic: `subject`. Named item: `use` |
| `dictionary` | `scripts/add_candidates.py` | `other` | 8 (`--k`) | `use` |
| `summary_tag` (a recognised tag) | `scripts/add_candidates.py` | `topic` | 12 (`--n`) | `subject`, with the tag type only |

A `dictionary` row is a known entity name from `tags/entity_dictionary/` whose words are in the speech text, but which the extraction did not list. Its mention is the matched words. A name is not added when every match of its words lies inside a longer name: another dictionary name, or the words of a named item of the extraction (not a topic, not a group). For example, "शिमला" inside "शिमला एग्रीमेंट" does not add the place Shimla. A skipped name frees its place under the cap. A `summary_tag` row is a recognised tag: one of the 12 tags nearest in meaning to the one-sentence summary of the speech. It holds the tag in `tag_id`, so stage 5 does not link it. The column `evidence` keeps why each added row exists: the number of matches and the rank, or the distance and the rank. `db/init/20-candidate-sources.sql` adds these columns.

Run `scripts/add_candidates.py` before `scripts/judge_items.py`. It is idempotent: a speech with rows of one source gets no new rows of that source.

## The questions

The current question version is `q5`. The script writes it into the column `judged_by` of each judged row, together with the model name, for example `jev-1.13.0 q5`. The question texts are in `scripts/judge_items.py`: the constant `QUESTIONS_VERSION`, the answer list `USES`, and the function `questions_for`. Do not change a question text without a new version and a new gate.

One call holds every question of one speech. A test on 2026-10-15 sent up to 300 questions in one call with no error. The longest speech of term 18 (10,332 words) fits in one call with 65 questions. So one call per speech is enough.

**Topics and recognised tags** get one true-or-false statement (`noul`):

> «Railway Projects» (a topic) is a main or supporting subject of this speech, not only a passing mention.

A recognised tag shows its type only, for example «Bareilly» (a place). It does not show the tag description.

**Places, persons, institutions, laws, schemes, groups, and roles** get one `choice` question. The example uses the dictionary entity «Mailani», found in the words «मैलानी»:

> How does this speech use «Mailani» (a place, in the words «मैलानी»)?

- `absent`: not mentioned, or only the speaker or the Chair.
- `aside`: only an example, precedent, comparison, courtesy, or side list item.
- `point`: part of the member's point: asked for, argued about, or says where or to whom it applies.
- `other_meaning`: the words mean something else than this name.

## The keep rule

An item is kept when P(true), or P(point) for a named item, reaches the limit of its source. The two kinds of source have different limits, because they have opposite risks.

| Source | Limit | Why |
|---|---|---|
| `llm` | 0.4 (`--keep-llm`) | The extraction chose the item. Stage 4 is an extra check. The bad error is to drop a correct item. To keep a wrong item is acceptable. |
| `dictionary` and `summary_tag` | 0.8 (`--keep-other`) | The item is an addition. The bad error is to keep a wrong item, because it adds noise to the tags. To drop a correct item is acceptable. |

Each item keeps its probabilities in `speech_items`: `judge_subject_p` and `judge_use_p` (`db/init/21-judge-q5.sql`). So `--rethreshold` applies new limits without a new call. q5 asks no type question, so stage 5 uses the extraction type.

The state is the member, the debate title, the date, and the speech text. When the speech does not fit in the model's context, the state is the stage 3 summary and the mention of each item. The column `judge_state` records which state was used.

**Term 18 used the older version q4.** q4 gave a recognised tag its description, used four long levels for topics, asked three questions for each named item (`role`, `refers`, `type`), and kept every source at 0.6. The term 18 results stay as they are. `--questions q4` reads those rows for `--rethreshold` and `--score`.

## How to run it

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

The script is idempotent. It skips each item that the current model and question version judged before. `--force` judges again.

## Results

A sample run writes two files into `results/`: a Markdown file to read, and a TSV file with an empty `review` column. Write `keep` or `drop` in that column for each item. `--prefill FILE` copies the marks of an earlier review file into the new one, so you mark only the new items. Then `--score` compares your marks with the model's decisions, for each source apart.

The current sample review is `results/sample_jev-1.13.0_q4_2026-10-16.tsv`: the 15 speeches of 2019, 365 candidates. Its marks come from the manual review of `results/sample_jev-1.13.0_q4_2026-10-15.tsv`, matched by speech, source, and name. 2 dictionary rows were new. They got a mark on 2026-10-16 that follows the same rules.
