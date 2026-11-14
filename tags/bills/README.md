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
- **ordinal**: for a numbered Constitution amendment bill, the number in the printed name is the number of `amendment_ordinal`. The number can be in words or in digits, for example "One Hundred and Fourth" or "104 th". A name such as "Constitution (Scheduled Castes) Order (Amendment) Bill" amends an order, not the Constitution, so it has no number to check.
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

Git does not track `results/`. The scripts write the files again from the database or from a new run.

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

## All debates (2026-11-13)

Each of the 2,379 debates with text has an answer. 2,345 answers use prompt `v2`, and 34 use prompt `v1`. All of them use `gemini-3.8-flash`.

The counts after the checks:

| Count | Value | Counted over |
|---|---|---|
| Debates with at least one kept bill | 2,329 | 2,379 debates |
| Debates with two or more kept bills | 51 | 2,379 debates |
| Kept pairs of a debate and a bill | 2,396 | all names in the answers |
| Kept pairs with no summary | 451 | 2,396 kept pairs |
| Distinct bills (`bills` rows, before any merge) | 1,652 | |
| Bills with two or more debates | 578 | 1,652 bills |
| Debates with no kept bill | 50 | 2,379 debates |

These counts show what the checks kept. They do not show that each kept bill is correct. A hand check of 100 random kept pairs measures that.

**The 50 debates with no kept bill** were in `results/no_bill_2026-11-13_all.tsv`. A manual review put them in two groups:

- About half have no moved bill. Examples: a debate on Demands for Supplementary Grants, a bill that the House deferred, a bill that the Secretary-General only laid on the Table, and a debate with a wrong type in the source.
- About half have a moved bill that the year check dropped, because the text near the name gives no year. Examples: "Introduction of Patents (Amendment) Bill", and the Appropriation bills that give only a financial year, for example "for the year 2000-2001". The rule "no bill is better than a wrong bill" keeps them out. An outside list of bills can give their year later.

**A fix of the ordinal check.** The first version of the check treated each name with "Constitution" and "Amendment" as an amendment of the Constitution. It dropped 63 names such as "Constitution (Scheduled Castes) Order (Amendment) Bill, 2012", and 8 other names. 5 of them are "Sixth Schedule to the Constitution (Amendment) Bill", 2 are "Constitution (Amendment) Bill" with no number, and 1 has the number in digits ("107 th"). `scripts/recheck_bills.py` applied the new check to the stored answers with no model call. The kept pairs went from 2,325 to 2,396.

```bash
set -a && source .env && set +a
python3 scripts/recheck_bills.py            # dry run
python3 scripts/recheck_bills.py --commit
```

**A known risk for the merge step.** Two different bills can have the same name and year when the name has no number, for example "Constitution (Amendment) Bill, 2000". Such bills get the same `bill_key`, so the exact-key merge joins them. 2 kept names have this form today.

## Step 4: the decision model checks the role (2026-11-13)

`scripts/judge_bills.py` asks the decision model one question for each name that passed the checks: is this bill before the House in this debate? The answers are `moved`, `mentioned`, and `unsure`. The model reads the same input text as the extraction. A name is kept when `moved` has a probability of 0.7 or more. `--rethreshold` computes `kept` again from the stored answers with no model call.

```bash
set -a && source .env && set +a
python3 scripts/judge_bills.py --sample 12 --dry-run
python3 scripts/judge_bills.py --all --workers 8
python3 scripts/judge_bills.py --rethreshold --keep-p 0.6
```

**The wording of the question decides the result.** The test set was the 33 debates of prompt `v1`. They hold 34 moved bills and 22 `mentioned` names, mostly the Act that a bill amends. Four versions of the question gave these results (the probability of `moved`):

| Version | Lowest value of a moved bill | Highest value of a mentioned name | Wrong decisions |
|---|---|---|---|
| `b1` | 0.52 | 0.94 | 3 |
| `b2` | 0.17 | 0.50 | 2 |
| `b3` | 0.60 | 0.98 | 8 |
| `b4` (used) | 0.85 | 0.18 | 0 |

`b2` dropped bills in a debate that continues from an earlier day, because nobody moves the motion again. `b3` counted the Act that a bill amends as moved. `b4` says both cases in plain words. On 13 other random debates, `b4` made no wrong decision. Its one drop was a bill whose year came from a wrong source title.

**The full run.** 2,283 debates and 2,418 names, with 0 failed calls. 2,389 names are kept. The model dropped 7 of the 2,396 names that the extraction called `moved` (0.3%). A manual review found two kinds:

- The motion text does not name the bill. For example, the introduction of the Tribunals Reforms Bill, 2021 lists only the Acts that the bill amends.
- The source title gives a different year from the text. For example, the title says "Small and Medium Enterprises Development Bill, 2006", but the Speaker names the "Bill, 2005".

These are accepted misses. 57 debates now have no kept bill, out of 2,379.

The review files were `results/judge_2026-11-13*.md`, which git does not track. The files without a number up to `_4` hold the four versions on the test set. `_5` holds the 13 other debates, and `_6` holds the full run.

## Step 5: one row for each bill, and one summary for each bill (2026-11-13)

`scripts/merge_bills.py` joins the spellings of one bill.

1. Candidates: two kept bills of the same year whose names have a `pg_trgm` similarity of 0.6 or more. There were 961 such pairs.
2. Hard rules in code remove a pair when the amendment numbers differ (50 pairs), when the digits in the names differ (418 pairs, for example "Appropriation (No. 2) Bill" and "Appropriation (No. 3) Bill"), or when the ordinal words differ (84 pairs, for example "Second Amendment" and "Amendment").
3. The decision model reads both names, their debate titles, and their summaries for the other 409 pairs. A pair merges when "same" has a probability of 0.7 or more. 239 pairs merged.
4. `data/bill_merges.tsv` holds every answer. `--apply` reads it and sets `bills.merged_into`, so a rebuild needs no model call. 232 bills went into another bill. 1,415 distinct kept bills remain.

A manual review of the edge cases found the merges correct. They join spelling faults ("Inforamtion"), names without "Bill", and small word changes. The model kept apart the Appropriation bills of different States, and each amendment bill from its parent bill. A few pairs that are one bill stayed apart, for example "Motor Vehicles (Amendment) Bill" and "Motor Vehicles (Amendment)" at 0.53. Such a pair only stays as two rows.

`--summaries` gives each kept bill its summary. 789 bills have one distinct summary, and the script copies it. 490 bills have two or more summaries from different debates. An LLM joins them with the prompt `prompts/merge_summary_v1.md`, which uses only the given summaries. `--join-sample 12` tested the prompt with `gemini-3.8-flash` on 12 bills, and a manual review found each joined summary faithful to its inputs.

```bash
set -a && source .env && set +a
python3 scripts/merge_bills.py --candidates
python3 scripts/merge_bills.py --judge
python3 scripts/merge_bills.py --apply
python3 scripts/merge_bills.py --summaries
python3 scripts/merge_bills.py --join-sample 12
```

**The result.** All 490 bills with two or more summaries have a joined summary from `gemini-3.8-flash` with `merge_summary_v1`. 1,279 of the 1,415 distinct kept bills now have a summary: 789 copied, and 490 joined. 136 bills have no summary, because no debate of the bill says what it does. A manual review of 4 random joined summaries found each one faithful to its inputs.

## What is next

1. The stance of each speech on its bill.
