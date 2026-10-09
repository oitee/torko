# The entity dictionary

This folder holds the entity dictionary. The dictionary is a list of frequent entity names. For each name, it holds the exact words that speeches use for it. Torko reads the debate transcripts of the Lok Sabha, the lower house of India's parliament. An LLM extracts at most 8 other entities from each speech. The LLM sometimes misses an entity that the speech names. The lookup uses the dictionary to find these missed entities in the speech text. The judging step then decides which candidates are real subjects of the speech.

The file `results/entity_dictionary.csv` is the dictionary. The script `scripts/build_entity_dictionary.py` builds the file. Nobody edits the file by hand. To change the dictionary, change the script and build the file again.

## Source

The script reads the table `speech_items`. It uses only the items with `list = 'other'` and `mention_found = true`. It reads the items of every extraction and every model. Topics are never in the dictionary. The script reads the database. It calls no model and writes no database row.

The script puts each model in one of two groups. The group "lite" holds each model with `lite` in its name. The group "strong" holds each other model. The model `rule-stub` has no items.

## Rules

The script applies these rules in this order.

1. Keep only items with `mention_found = true`.
2. Merge spelling variants of one name. The script gives each name a spelling key (`spelling_key` in `entity_lookup.py`). The key ignores case, spaces, and punctuation between letters. It folds Latin letters with `translit.fold`. It keeps each run of digits exactly, apart from its neighbours. So `Siddharthnagar` and `Siddharth Nagar` merge, `Insolvency and Bankruptcy Code 2016` and `Insolvency and Bankruptcy Code, 2016` merge, and `Article 21` and `Article 12` never merge. The most frequent spelling is the name. The other spellings go into `name_variants`. This merge runs before the speech count and before the ambiguity rule.
3. Drop the names and mentions in `data/exclude.tsv` (see the next section). Also drop each mention of a person item that contains an office word. The constant `OFFICE_WORDS` in the script lists the words, for example `प्रधानमंत्री`, `PM`, `minister`, `president`. The match is on whole words.
4. Keep an entity name that occurs in 3 or more distinct speeches.
5. Drop a mention that the kept names use fewer than 2 times in all. The script compares mentions as `mention_key` does: without case, spaces, and zero-width characters.
6. Drop a mention of 3 characters or fewer. The script counts the characters of the mention key, so spaces do not count. Short mentions such as `UP` match ordinary words.
7. Drop an ambiguous mention. A mention is ambiguous when two or more names use it and no name has 80% or more of its uses. The script lists the dropped mention in the column `ambiguous_mentions` of each name that used it.
8. A mention with variant names goes under its most frequent name. The other names go into `name_variants`.
9. Each mention keeps two counts: the uses by strong models and the uses by lite models.

After the rules, the script drops each name that has no mention left. The script also drops a mention that contains the character `|`, because the file uses ` | ` as a separator. No mention has this character today.

The rules count the uses of a mention over the items of the kept names only. An excluded name or a name with fewer than 3 speeches does not make a mention ambiguous.

## The exclusion file

The file `data/exclude.tsv` is tracked and has three columns: `kind` (`name` or `mention`), `value`, and `reason`. A `name` row drops every item whose name has the same spelling key as the value. A `mention` row drops every item that has this mention, whatever its name. The script prints the number of dropped mention uses for each reason.

The file follows the "do not extract" rules of the extraction prompt. It holds the House and its bodies and procedure, titles and offices with no named person, and India itself. The prompt allows India only in a comparison with another country, and the lookup cannot see a comparison. The owner reviews the file. Change the file and build the dictionary again to change the result.

## Columns

The file is a CSV in UTF-8 with a byte order mark. One row holds one entity name. The rows are in order of the speech count, the largest first. Each list in one cell uses ` | ` between the parts.

| Column | Meaning |
|---|---|
| `name` | The most frequent spelling of the entity name. |
| `type` | The most frequent type. |
| `other_types` | Other types that the name had, most frequent first. |
| `speeches` | The number of distinct speeches that have this name (rule 2 count). |
| `avg_salience` | The mean model salience of the items of this name. The pipeline uses it for no decision. |
| `mentions` | The kept mentions as `text (uses)`, most used first. The uses count all models. |
| `n_mentions` | The number of kept mentions. |
| `mentions_strong` | The same mentions as `text (uses)` for the strong models only. A mention with 0 uses is not listed. |
| `mentions_lite` | The same for the lite models only. |
| `ambiguous_mentions` | Mentions that the name used and that rule 5 dropped, as `text (uses of this name)`. |
| `name_variants` | Other names or spellings that used the kept mentions, as `name (uses)`. |
| `example_ids` | Up to 5 speech ids, the smallest first. |

For each mention, `mentions` equals the sum of `mentions_strong` and `mentions_lite`.

## The lookup

The module `entity_lookup.py` in the repository root loads the file. Use `EntityDictionary.load().lookup(text, already_has, k)`. It returns at most `k` triples (name, type, matched mention). The default for `k` is 8. It skips each name in `already_has`, compared by spelling key, so a spelling variant counts as the same name.

The lookup ranks the additions by a score. The score is the number of matches of all mentions of the name in this speech, times the natural logarithm of (the number of speeches in the dictionary source divided by the speeches of the name). A rare name ranks higher than a common name. The highest score comes first. A tie goes by name. The build script writes the number of source speeches to `results/entity_dictionary_meta.json`, and the lookup reads it. The match uses the normalisation of `mention_key`. It also needs a word boundary on both sides. A letter, a digit, or a combining mark next to the match is not a boundary. This rule keeps `किसान` from matching inside `किसानों`.

## How to rebuild

```bash
source .venv/bin/activate
set -a && source .env && set +a
python3 scripts/build_entity_dictionary.py      # writes results/entity_dictionary.csv, takes about 4 seconds
python3 scripts/entity_lookup_gate.py           # writes results/gate_report.md, takes about 1 minute
```

## Build result (2026-10-09)

Before the three fixes (2026-10-07), the build had these numbers. After the fixes, they are in the second column. Each count is a number of items (mention uses) out of 166,478 items read.

| | Before | After |
|---|---|---|
| Names in 3 or more speeches | 6,630 | 6,586 |
| Dropped by exclusion | 0 | 701 (India), 593 (body or procedure), 634 (title or office), 445 (person mention with an office word) |
| Dropped because the name has fewer than 3 speeches | 26,032 | 24,608 |
| Dropped because the mention has fewer than 2 uses | 14,960 | 15,366 |
| Dropped because the mention has 3 characters or fewer | 3,661 | 3,630 |
| Dropped as ambiguous | 17,936 | 15,518 |
| Kept | 103,889 | 104,983 |
| Names in the dictionary | 5,003 | 5,045 |

The merge joined 1,648 groups that had more than one spelling. The source holds 42,264 distinct speeches.

## Gate result (2026-10-09)

`results/gate_report.md` has the full tables and every denominator. Before the fixes, the values are in brackets.

- Precision and recall proxies. The test used the 3,764 speeches that `gemini-3.8-flash` extracted. The lookup ran with an empty "already has" set. With K = 8, 6,796 of 21,460 looked-up names (31.7%, before 25.6%) are names that the LLM also extracted. With no cap, 10,230 of 56,682 (18.0%, before 16.2%). Of 13,132 LLM names that are in the dictionary, the lookup found 6,796 with K = 8 (51.8%, before 44.9%) and 10,230 with no cap (77.9%, before 76.7%).
- The precision proxy is a lower bound. The LLM extracts at most 8 other entities. A speech can name more entities that are real. The proxies are also optimistic, because the dictionary comes from the same speeches.
- Added entities per speech. The test used 2,000 random speeches of the 45,687 that lite models extracted. The "already has" set was every item name of the speech. With K = 8, the mean is 4.35 (before 5.05), 163 speeches (8.2%) get no addition, and 577 speeches (28.9%, before 35.4%) reach the cap. With no cap, the mean is 6.31, the 90th percentile is 15, and the maximum is 53.
- The owner sets K and accepts the gate.

## Done, next, unknown

Done: the build script, the lookup module, the gate script, and the offline tests.

Next: read the gate report and set K. The judging step then reads the added entities as candidates.

Unknown: how many of the 56,682 looked-up names are real subjects of their speech. Only the judging step can tell. Also unknown: how often a common word is a mention of a rare name. The Hindi word `दिशा` (direction) is a mention of the scheme DISHA and ranks high because the scheme is rare.
