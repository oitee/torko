# Relevance check of speech items

This folder holds stage 4 of the tag pipeline. Torko reads the debate transcripts of the Lok Sabha, the lower house of India's parliament. Stage 3 (`tags/extraction_v1/`) gives each speech at most 8 topics and 8 other entities, called items. Some items are only background, or the speaker, the Chair, or procedure. Stage 4 decides which items are real subjects of the speech.

A decision model answers fixed questions with a probability for each answer. It writes no text. `scripts/judge_items.py` sends one call per speech. Questions version q3:

- Topics get one question, `level`: how central the topic is to the speech, on a rubric from 0 (not a subject) to 3 (the speech is mainly about it). Kept when P(level 2 or 3) is 0.6 or more.
- Places, persons, institutions, laws, schemes, groups, and roles get three questions. `role` (it shows the name and the words of the speech): absent, aside (an example, a precedent, a comparison, a courtesy, a side list), or part of the member's point. `refers`: the words of the speech refer to the item's name without a guess. `type`: what kind of thing the item is. Kept when P(point) is 0.6 or more and P(refers) is 0.6 or more. The type never decides keep or drop.

All thresholds are start values. Each item keeps its probabilities in `speech_items` (`db/init/12-entity-links.sql`), so `--rethreshold` applies new thresholds without a new call.

The state is the member, the debate title, the date, and the speech text. When the speech does not fit in the model's context, the state is the stage 3 summary and the mention of each item. The column `judge_state` records which state was used.

## How to run it

Run from the repo root. The database must run, and `.env` must hold `TYPESAFE_API_KEY`.

```bash
set -a && source .env && set +a
python3 scripts/judge_items.py --year 2019 --max-words 5000 --dry-run
python3 scripts/judge_items.py --year 2019 --max-words 5000
python3 scripts/judge_items.py --rethreshold --keep-point 0.5
python3 scripts/judge_items.py --score tags/judging/results/<file>.tsv
```

The script is idempotent. It skips each item that the current model and question version judged before. `--force` judges again.

## Results

A sample run writes two files into `results/`: a Markdown file to read, and a TSV file with an empty `owner` column. Write `keep` or `drop` in that column for each item. Then `--score` compares your marks with the model's decisions at several thresholds.
