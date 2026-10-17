# The entity dictionary

This step builds a list of frequent entity names. For each name, it holds the exact words that speeches use for it. The lookup uses the list to find entities that the extraction missed. The judging step then decides which of them are real subjects of the speech (see [the judging step](../judging/README.md)).

Input: the table `speech_items` (items with `list = 'other'` and `mention_found = true`, from every extraction and model). Output: `results/entity_dictionary.csv` and `results/entity_dictionary_meta.json`. The build calls no model and writes no database row.

## How to run

```bash
source .venv/bin/activate
set -a && source .env && set +a
python3 scripts/build_entity_dictionary.py
python3 scripts/entity_lookup_gate.py
```

The build script writes the CSV file. The gate script writes `results/gate_report.md`. Nobody edits the CSV file by hand. To change the dictionary, change the script or `data/exclude.tsv` and build again.

## Files

| File | What it is |
|---|---|
| `data/exclude.tsv` | Names and mentions that the build drops. A person edits it. |
| `results/entity_dictionary.csv` | The dictionary. One row for each entity name, largest speech count first. |
| `results/entity_dictionary_meta.json` | The number of source speeches. The lookup reads it. |
| `results/gate_report.md` | The report of the gate script. |

The file `data/exclude.tsv` is tracked and has the columns `kind`, `value`, and `reason`, with a tab between them. A `name` row drops every item whose name has the same spelling key as the value. A `mention` row drops every item that has this mention, whatever its name. Add a row, then build again.

The file follows the "do not extract" rules of the extraction prompt. It holds the House and its bodies and procedure, titles and offices with no named person, India itself, and general groups of people that the decision model keeps although a speech uses them only in passing.

The CSV file has one row for each name. Columns: `name`, `type`, `other_types`, `speeches`, `avg_salience`, `mentions`, `n_mentions`, `mentions_strong`, `mentions_lite`, `ambiguous_mentions`, `name_variants`, `example_ids`. A cell with a list uses ` | ` between the parts. A mention shows as `text (uses)`.

## Rules the build applies

1. Merge spelling variants of one name with `spelling_key` in `entity_lookup.py`. It ignores case, spaces, and punctuation. It keeps each run of digits exactly, so `Article 21` and `Article 12` stay apart. The most frequent spelling is the name.
2. Drop the names and mentions in `data/exclude.tsv`. Also drop each mention of a person item that contains an office word (`OFFICE_WORDS` in the script).
3. Keep a name only when it occurs in 3 or more distinct speeches.
4. Drop a mention that the kept names use fewer than 2 times.
5. Drop a mention of 3 characters or fewer, counted without spaces.
6. Drop an ambiguous mention. Two or more names use it, and no name has 80% or more of its uses.
7. Drop each name that has no mention left.

The model `rule-stub` has no items. Models with `lite` in the name form the group "lite". Each other model forms the group "strong". Each mention keeps one use count for each group.

## The lookup

The module `entity_lookup.py` in the repository root loads the CSV file. `EntityDictionary.load().lookup(text, already_has, k)` returns at most `k` triples (name, type, matched mention). The default for `k` is 8. It skips each name in `already_has`, compared by spelling key.

The score of a name is the number of matches of its mentions in the speech, times the natural logarithm of (source speeches divided by speeches of the name). A rare name ranks higher. A match needs a word boundary on both sides. A letter, a digit, or a combining mark next to the match is not a boundary.
