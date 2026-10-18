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
5. For each group, it writes the counts, a label (the name with the most speeches), and a parent tag (the tag with the most speeches among the linked names).

## Outputs

- `results/groups_v1.tsv`: every group of 2 or more names, at d = 0.10.
- `results/groups_d0.08.tsv`, `results/groups_d0.10.tsv`, `results/groups_d0.14.tsv`: the same at three values of d, for comparison.
- `results/review_tags_v1.md`: the subjects under the 30 tags with the most linked names.
- `results/review_untagged_v1.md`: the 50 largest groups with no linked name. These are candidates for new tags.

## Choosing the settings

`scripts/subject_groups_eval.py` checks the settings. `--prepare` draws name pairs from each distance band for a blind manual label (`same` or `different` subject). `--sweep` scores each combination of neighbours, distance limit, and group-size limit on the labelled pairs. The defaults d = 0.10 and a limit of 15 come from this check. The labels and the score table stay in `eval/`, outside git.
