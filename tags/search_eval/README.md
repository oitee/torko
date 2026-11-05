# Search test set

This folder holds 30 search questions with known correct speeches. It answers one question: does a change make search find more of the correct speeches?

`data/questions.tsv` holds the questions: English, Hindi, misspellings, a member with a subject, exact phrases, passing remarks, and questions that use other words than the speeches.

`data/reviews/` holds the marks of two blind LLM reviewers. No person reviewed the marks. A speech is in `data/known.tsv` only when both reviewers mark it yes, or, for an exact phrase, when the text holds the phrase (`data/known_phrase.tsv`).

The candidates came from several ways, and no way gave its own order to the reviewers: the nearest summaries, the speeches of a matching tag, word matches on hand-written variants in English and Hindi, and a text scan of the summaries. Each way gave at most 6 random speeches, and the nearest summaries gave 10.

## Run

```bash
python3 scripts/search_eval.py pool
python3 scripts/search_eval.py pool-top
python3 scripts/search_eval.py combine
python3 scripts/search_eval.py score --method words
```

The score is recall at 10: the known speeches in the top 10 results, over the smaller of 10 and the number of known speeches.

## Scores

| Method | Recall at 10 | Top 10 results with no mark |
|---|---|---|
| `words`: every word in one turn, newest first | 0.447 | 0 |
| `best`: word matches and nearest summaries, joined by rank | 0.790 | 0 |

The first run gave `words` 0.137 and `best` 0.517, because a correct speech that no reviewer saw counted as a miss. `pool-top` then sent the 242 unmarked top 10 results of both methods to the same two reviewers.

## Limits

The denominator is the known speeches of the pool, not all correct speeches in the corpus. Most questions have more than 10 known speeches, so the score of such a question is the share of correct speeches among the top 10. `score` prints the number of top 10 results with no mark. Run `pool-top` and the reviewers again after a change to a method, or the comparison favours the older method.

The questions were written before the method, but one person wrote all of them, and no person checked the marks.

A rerun of `pool` needs the summary vectors and a model call for each question.
