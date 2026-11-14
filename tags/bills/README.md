# Bills of the government-bill debates

This step reads each government-bill debate and asks an LLM for three things. The first is the bill or bills of the debate. The second is the role of each bill in the debate. The third is a summary of 2 or 3 sentences on what each bill does. A later step uses the summary as context to find the stance of each speech on its bill.

The scope is the debates of the type `GOVERNMENT BILLS` or `STATUTORY RESOLUTION AND GOVERNMENT BILL`. There are 2,381 such debates. 2 of them have no text, so 2,379 debates can be asked.

## The rules

1. The bill comes from the debate, never from one speech.
2. The model copies each name from the input. The script does not keep a name that is not in the input.
3. The year comes from the text near the name, never from the debate date. For example, the House debated the Anti-Maritime Piracy Bill, 2019 in December 2022.
4. Two bills with a different year never share a `bill_key`. Two Constitution amendment bills with a different number never share a `bill_key`.
5. No bill is better than a wrong bill.
6. The summary uses only the facts of the input. If the input does not say what the bill does, the summary is null.
7. Only a bill that the House considers in the debate (role `moved`) has a summary. A bill that a speaker only names (role `mentioned`) has no summary.
8. From prompt `v2`, the model lists only the moved bills. When the model is not sure, it lists the bill, and the decision model of step 4 removes a wrong one.

## The input of one debate

`bill_extract.build_input` writes the input. It holds the debate title, the debate type, the debate date, the start of the debate, and the last 2 turns of the debate. The last turns often say "The Bill was passed".

The start of the debate holds the first 5 speeches, with the chair turns between them. If those speeches hold less than 1,200 words, the start takes the next speeches one by one, until it has 1,200 words. The start stops at word 4,000, and it marks the cut.

## How to run

Run from the repo root. The database must run, and `.env` must hold `GEMINI_API_KEY`.

```bash
set -a && source .env && set +a
python3 scripts/extract_bills.py --sample 12
python3 scripts/extract_bills.py --term 18 --all --dry-run
python3 scripts/extract_bills.py --all --workers 8
```

| Option | Default | Meaning |
|---|---|---|
| `--sample` or `--all` | none, one is required | `--sample N`: N random debates, spread over the six terms. N is 15 or less. `--all`: every debate of the scope. |
| `--term` | none | With `--all`: only one Lok Sabha term, for example `17`. |
| `--seed` | 1 | The same seed gives the same sample. |
| `--model` | `gemini-3.8-flash` | The LLM that extracts. |
| `--prompt` | the highest version | The prompt version, for example `v1`. |
| `--workers` | 4 | API calls at the same time. |
| `--force` | off | Ask again for a debate that has a row, and replace the row. |
| `--no-store` | off | Ask every selected debate, also a debate with a row, and store nothing. Write only the review file. Use it to compare a model or a prompt with the stored answers. |
| `--dry-run` | off | Print the counts and a token estimate. Call no model. |

## The checks (no model)

`bill_extract.check_answer` checks each bill of the answer against the input text:

- **name**: the printed name is in the input. Case, white space, and the type of quote marks and dashes do not matter.
- **year**: the year is inside the printed name, or in the 12 characters after it.
- **ordinal**: for a Constitution amendment bill, the number in words is inside the printed name.
- **quote**: the quote is in the input, and it holds the printed name.
- **role**: the role is `moved` or `mentioned`.

A bill with a failed check is not kept and gets no row in `bills`. A `mentioned` bill passes the checks but is not kept. Its summary is removed.

## The tables

`db/init/07-bills.sql` holds three tables:

| Table | One row for each | Holds |
|---|---|---|
| `bills` | bill | The name, the year, the `bill_key`, the number of a Constitution amendment, and later the summary of the bill. |
| `bill_extractions` | debate | The model answer before the checks, the model, the prompt version, and the hash of the input text. |
| `debate_bills` | bill name in the answer of a debate | The printed name, the quote, the role, the summary, the failed checks, and `kept`. |

A debate is named by its natural key (`loksabha`, `session`, `dbslno`), not by `debates.id`, because a rebuild of the debates gives new ids.

## Files

| Path | Holds |
|---|---|
| `prompts/v<N>.md` | The instructions that the model reads. One file for each version. A file is never edited after a row uses it. |
| `results/review_<date>.md` | The review file of a run. One section for each debate: the bills, the checks, the summaries, and the input. Each section ends with an empty `review:` line. |
| `results/review_<date>_<model>_not_stored.md` | The review file of a `--no-store` run. |
| `results/no_bill_<date>.tsv` | The debates with no kept bill, for a manual look. |

## The first sample (2026-11-13)

`--sample 12` with `gemini-3.8-flash` and prompt `v1` asked 12 debates, 2 from each term. The run used about 77,500 input tokens, 3,700 output tokens, and 25,900 thinking tokens.

- 11 of the 12 debates got 12 kept bills. A manual review found each of the 12 bills correct. One debate got 2 moved bills, and both were found.
- The 12th debate (LS18-3-1202) is a debate on the Demands for Supplementary Grants. It names an Appropriation Act with no year, and no bill is moved in the input. It has no kept bill, and that is correct.
- 10 `mentioned` names failed a check. 8 had no year, and 2 had no amendment number. A mentioned name is not kept in any case.
- Many inputs are in Hindi. The summaries used facts that only the Hindi text gives, for example "ट्रिप्स" (TRIPS) in the Designs Bill, 2000.
- One summary out of 12 adds a general phrase that the input does not give: the Finance Bill, 2026 summary says that the taxes "fund public services".

## Prompt v2 (2026-11-13)

Prompt `v1` asked the model to list each bill and Act that the input names, with the role `moved` or `mentioned`. A `mentioned` name is never kept, but the model spent time on each one. In 34 debates, a manual review found 35 `mentioned` names. Each of the 35 was correctly `mentioned`, for example the parent Act of an amendment bill. None of them was a moved bill.

Prompt `v2` lists only the bills that the House considers in the debate. If the model is not sure, it lists the bill. The summary rules also forbid the reason that a speaker gives for the bill.

The same 12 debates, with `--no-store`:

| Run | Kept bills | Thinking tokens | Notes |
|---|---|---|---|
| `gemini-3.8-flash`, `v1` (stored) | 12 | 25,860 | One summary adds "to fund public services". |
| `gemini-flash-lite-latest`, `v1` | the same 12 | 0 | It listed no `mentioned` name. Two summaries are weak: one is vague, and one gives the reason of the minister. |
| `gemini-3.8-flash`, `v2` | the same 12 | 11,988 | The outcomes are the same. The Finance Bill, 2026 summary no longer adds a fact. |

## What is next

1. Step 4: the decision model checks each name for `moved`, `mentioned`, or `unsure`.
2. Step 5: merge the spellings of one bill, then write one summary for each bill in `bills.summary`.
