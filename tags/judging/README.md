tags/judging/README.md# Relevance check of speech items

This folder holds stage 4 of the tag pipeline. Torko reads the debate transcripts of the Lok Sabha, the lower house of India's parliament. Stage 3 (`tags/extraction_v1/`) gives each speech at most 8 topics and 8 other entities, called items. Some items are only background, or the speaker, the Chair, or procedure. Stage 4 decides which items are real subjects of the speech.

A decision model answers fixed questions with a probability for each answer. It writes no text. `scripts/judge_items.py` sends one call per speech.

## The candidates of a speech

Every candidate is a row of `speech_items`. The column `source` tells where the row comes from:

| Source | Added by | List | At most | Question |
|---|---|---|---|---|
| `llm` | stage 3, the extraction | `topic` and `other` | 8 + 8 | topic: `level`. Named item: `role`, `refers`, `type` |
| `dictionary` | `scripts/add_candidates.py` | `other` | 8 (`--k`) | `role`, `refers`, `type` |
| `summary_tag` (a recognised tag) | `scripts/add_candidates.py` | `topic` | 12 (`--n`) | `level`, with the tag type and description |

A `dictionary` row is a known entity name from `tags/entity_dictionary/` whose words are in the speech text, but which the extraction did not list. Its mention is the matched words. A name is not added when every match of its words lies inside a longer name: another dictionary name, or the words of a named item of the extraction (not a topic, not a group). For example, "शिमला" inside "शिमला एग्रीमेंट" does not add the place Shimla. A skipped name frees its place under the cap. A `summary_tag` row is a recognised tag: one of the 12 tags nearest in meaning to the one-sentence summary of the speech. It holds the tag in `tag_id`, so stage 5 does not link it. The column `evidence` keeps why each added row exists: the number of matches and the rank, or the distance and the rank. `db/init/20-candidate-sources.sql` adds these columns.

Run `scripts/add_candidates.py` before `scripts/judge_items.py`. It is idempotent: a speech with rows of one source gets no new rows of that source.

## The questions

The current question version is `q4`. The script writes it into the column `judged_by` of each judged row, together with the model name, for example `jev-1.13.0 q4`. The question texts are in `scripts/judge_items.py`: the constant `QUESTIONS_VERSION`, the answer lists `LEVELS`, `ROLES`, and `TYPES`, and the function `questions_for`.

One call holds every question of one speech. A test on 2026-10-15 sent up to 300 questions in one call with no error. The longest speech of term 18 (10,332 words) fits in one call with 65 questions. So one call per speech is enough.

**Topics and recognised tags** get one `score` question:

> How central is «Railway Projects» (a topic) to this speech?

For a recognised tag, the brackets hold the tag type and description, for example «Bareilly» (a place: District and Lok Sabha constituency in Uttar Pradesh, India). The answer is one of four levels:

- 0, not a subject: it is not in the speech, or it is only the speaker, the Chair, an addressee, or procedure.
- 1, passing: it is named once, as background, as an example, or as the source of a statement.
- 2, supporting: the speech discusses it in more than one sentence, or the member's request depends on it.
- 3, central: the speech is mainly about it.

The item is kept when P(level 2 or 3) is 0.6 or more.

**Places, persons, institutions, laws, schemes, groups, and roles** get three questions. The examples use the dictionary entity «Mailani», found in the words «मैलानी».

- `role` (`choice`): How does this speech use «Mailani» (a place, in the words «मैलानी»)? The answers are `absent` (the speech does not mention it, or it is only the speaker or the Chair), `aside` (only an example, a precedent, a comparison, a courtesy, or one item in a side list), and `point` (part of the member's point: the member asks for something about it, argues about it, or uses it to say where or to whom the point applies; one mention is enough).
- `refers` (`noul`, the probability that a statement is true): In this speech, the words «मैलानी» refer to «Mailani». The speech, with common knowledge, is enough to tell that it is this one specific thing, without a guess.
- `type` (`choice`): What kind of thing is «Mailani», as this speech uses it? The answers are place, person, institution, law, scheme, group, role, topic, and other.

The item is kept when P(point) is 0.6 or more and P(refers) is 0.6 or more. The type never decides keep or drop.

All thresholds are start values. Each item keeps its probabilities in `speech_items` (`db/init/12-entity-links.sql`), so `--rethreshold` applies new thresholds without a new call.

The state is the member, the debate title, the date, and the speech text. When the speech does not fit in the model's context, the state is the stage 3 summary and the mention of each item. The column `judge_state` records which state was used.

## How to run it

Run from the repo root. The database must run, and `.env` must hold `TYPESAFE_API_KEY`.

```bash
set -a && source .env && set +a
python3 scripts/add_candidates.py --speech-ids 260741,340402 --dry-run
python3 scripts/add_candidates.py --speech-ids 260741,340402
python3 scripts/judge_items.py --speech-ids 260741,340402 --dry-run
python3 scripts/judge_items.py --speech-ids 260741,340402 --prefill tags/judging/results/<old marks>.tsv
python3 scripts/judge_items.py --rethreshold --keep-point 0.5
python3 scripts/judge_items.py --score tags/judging/results/<file>.tsv
```

The script is idempotent. It skips each item that the current model and question version judged before. `--force` judges again.

## Results

A sample run writes two files into `results/`: a Markdown file to read, and a TSV file with an empty `review` column. Write `keep` or `drop` in that column for each item. `--prefill FILE` copies the marks of an earlier review file into the new one, so you mark only the new items. Then `--score` compares your marks with the model's decisions, for each source apart.

The current sample review is `results/sample_jev-1.13.0_q4_2026-10-16.tsv`: the 15 speeches of 2019, 365 candidates. Its marks come from the manual review of `results/sample_jev-1.13.0_q4_2026-10-15.tsv`, matched by speech, source, and name. 2 dictionary rows were new. They got a mark on 2026-10-16 that follows the same rules.
