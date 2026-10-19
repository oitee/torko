# Subject groups (prototype)

This folder holds a read-only prototype. Torko gives tags to speeches of the Lok Sabha, the lower house of India's parliament. A broad tag such as `Arrears` holds many specific subjects, for example sugarcane farmers' arrears and wage arrears. This prototype finds those specific subjects as groups of similar entity names.

An entity name is a name that an LLM took from a speech, for example "Sugarcane farmers' dues". Each name has a vector in `entity_names.embedding_query`. Some names link to a tag and some do not.

## How to run

```bash
source .venv/bin/activate
set -a && source .env && set +a
python3 scripts/subject_groups.py
```

The script needs numpy. numpy is not in `requirements.txt`, because only this prototype uses it. Install it with `pip install numpy`. The script reads the database only. It calls no model and writes nothing to the database. 

## What the script does

1. It reads every entity name with a vector and at least one kept item of source `llm` or `dictionary`. It skips the types `place` and `person`, because the vectors of different towns or people can be close.
2. It finds the 15 nearest names of each name, with an exact cosine search in numpy.
3. It joins two names when each is in the list of the other and the distance is below d (default 0.10).
4. It joins these pairs into groups. A group above 15 names splits again with a smaller d.
5. For each group, it writes the counts, a label (the name with the most speeches), and a vote parent (the tag with the most speeches among the linked names). The vote parent is only a first guess for review files. The parent in the database comes from the decision model (see "Parent tags" below).

## Outputs

- `results/groups_v1.tsv`: every group of 2 or more names, at d = 0.10.
- `results/groups_d0.08.tsv`, `results/groups_d0.10.tsv`, `results/groups_d0.14.tsv`: the same at three values of d, for comparison.
- `results/review_tags_v1.md`: the subjects under the 30 tags with the most linked names.
- `results/review_untagged_v1.md`: the 50 largest groups with no linked name. These are candidates for new tags.

## Choosing the settings

`scripts/subject_groups_eval.py` checks the settings. `--prepare` draws name pairs from each distance band for a blind manual label (`same` or `different` subject). `--sweep` scores each combination of neighbours, distance limit, and group-size limit on the labelled pairs. The defaults d = 0.10 and a limit of 15 come from this check. The labels and the score table stay in `eval/`, outside git.

## Joining small groups

`scripts/subject_join.py` joins small groups that are one subject. A unit is a group, or a single name with 2 or more speeches. `candidates` pairs each unit with its nearest units by the distance of their centres. `jobs` writes task files for an LLM that decides `same` or `different` for each pair. `ingest` reads the answers, and `export-joins` writes the `same` answers to `data/joins_v1.tsv`, keyed by the entity name IDs of each unit. `subjects` joins the units of every pair in that file and writes `results/subjects_v1.tsv`. `approach-a` and `compare` score a fixed distance limit and the LLM answers on labelled candidate pairs.

`label-jobs` and `chain-jobs` write task files for two more LLM steps: a clean label for each subject, and a check of the pairs inside long chains of joins.

## Parent tags

The parent tag of a subject is the tag that means the same thing as the subject, or the tag that the subject is one part of. A tag that is only one part of the subject is not its parent. For example, the subject "Religious tourism development" does not have the parent `PRASAD Scheme`, because that scheme is one part of religious tourism.

A vote over the linked names cannot make this choice. In many subjects, one linked name out of 10 or more decides the vote, and its tag can be narrower than the subject or wrong. So the decision model chooses the parent:

```bash
source .venv/bin/activate
set -a && source .env && set +a
python3 scripts/subject_parents.py --dry-run
python3 scripts/subject_parents.py --review
```

For each subject, the options are the tags of its linked names (at most 10, most speeches first), the 3 tags nearest to the centre of its name vectors, and NONE. The state holds the label, up to 10 names with their speech counts, and up to 3 examples from the speeches. A subject gets a parent only when one tag gets 0.7 or more. The answer goes into the table `subject_parents` by subject key, so a reload of the same subject keeps it. `scripts/load_subjects.py` takes the parent from that table. A subject is decided again when the question version changes, or when it has no parent and the tag list grew.

`--labels` decides only the named subjects. `--review` writes `results/parents_p1_<date>.tsv` with the vote parent next to the model's parent and its top options.
