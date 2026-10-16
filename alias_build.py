from __future__ import annotations

from collections import defaultdict
from typing import Callable

# Codes from 10000 up are minister role-slots. The source reuses one code for
# different people across terms, so these codes never get an alias.
SYNTHETIC_MIN = 10000


def is_synthetic_code(mp_code: str) -> bool:
    try:
        return int(mp_code) >= SYNTHETIC_MIN
    except (TypeError, ValueError):
        return False


def build_aliases(
    label_rows,
    unique_person_by_key: dict[str, int],
    person_name_by_id: dict[int, str],
    folded_key: Callable[[str], str],
    is_presiding: Callable[[str], bool],
    is_crowd: Callable[[str], bool],
    name_agreement: Callable[[str, str], bool | None],
) -> tuple[dict[str, dict], dict[str, dict]]:
    """Decide, per orphan mpCode, which single person (if any) it aliases to.

    `label_rows` holds (mp_code, speaker_label, turn_count) for every turn of the code, resolved or not.
    `unique_person_by_key` must not contain folded keys that two people share.
    Returns (aliases, dropped). Drop reasons: "conflict", "no_name_label", "outweighed".
    """
    per_code_votes: dict[str, dict[int, int]] = defaultdict(lambda: defaultdict(int))
    per_code_labels: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for mp_code, label, count in label_rows:
        code = str(mp_code)
        if is_synthetic_code(code):
            continue
        if not label or is_presiding(label) or is_crowd(label):
            continue
        per_code_labels[code][label] += count
        pid = unique_person_by_key.get(folded_key(label))
        if pid is not None:
            per_code_votes[code][pid] += count

    aliases: dict[str, dict] = {}
    dropped: dict[str, dict] = {}
    for code, pids in per_code_votes.items():
        if len(pids) != 1:
            dropped[code] = {"reason": "conflict", "persons": dict(pids)}
            continue

        pid, turns = next(iter(pids.items()))
        labels_for_code = per_code_labels.get(code, {})
        roster_name = person_name_by_id.get(pid)

        if not labels_for_code or not roster_name:
            # No printed name to check the vote against. Silence is not agreement.
            dropped[code] = {"reason": "no_name_label", "person_id": pid}
            continue

        dominant_label, dominant_turns = max(labels_for_code.items(), key=lambda kv: kv[1])
        dominant_agrees = name_agreement(dominant_label, roster_name) is True

        # Only False refutes. None means nothing was compared.
        refuting_turns = max(
            (n for lab, n in labels_for_code.items()
             if name_agreement(lab, roster_name) is False),
            default=0,
        )

        if dominant_agrees or turns >= refuting_turns:
            aliases[code] = {"person_id": pid, "evidence_turns": turns}
        else:
            dropped[code] = {
                "reason": "outweighed",
                "person_id": pid,
                "dominant_label": dominant_label,
                "dominant_turns": dominant_turns,
                "evidence_turns": turns,
                "refuting_turns": refuting_turns,
            }
    return aliases, dropped
