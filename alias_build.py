"""Pure logic for building the mpCode -> person alias table (see
db/init/09-mpcode-aliases.sql).

No database, no network -- everything here is a function of its inputs, so the
never-guess rule can be unit-tested offline (tests/test_alias_build.py).

The bridge exists because debate transcripts number a speaker with `mpCode`
while our roster keys a person on `mpsno` (persons.sansad_id), and the two are
different, colliding namespaces. A code earns an alias only when the SOURCE's
own printed name labels for that code all point to exactly one roster person.

## The gate this file used to be missing

Voting on the RESOLVABLE labels alone is not enough. A code where 344 turns
print "SHRI ARUN SHOURIE" (a Rajya Sabha member, absent from `persons`
entirely, so his labels resolve to nobody) and exactly one turn happens to
fold-match some unrelated roster person used to sail through: zero
resolvable labels disagree with each other, because 343 of them never even
became a vote. `len(pids) == 1` looked like unanimity; it was one stray vote
unopposed.

So before minting, `build_aliases` now also weighs the code's printed labels
against the winning candidate's roster name, using `name_agreement` (in
practice `debate_fetch._name_agreement`, which answers in three states: True
= same person, False = different people, None = nothing usable was compared).

## Why the obvious version of that gate is too blunt

The obvious rule -- "the DOMINANT label (most turns) must positively agree,
or refuse" -- does catch all three poisoned codes. Measured against the 29
rows actually in the table, it also kills a correct one: mpCode 572 is
H.D. Deve Gowda, a former Prime Minister, 161 turns of evidence, and the
source prints him as "SHRI H.D. DEVE GOWDA" while the roster spells him
"H.D. Devegowda" -- one word against two. `_name_agreement` calls that a
disagreement. It is a spelling variant, and the audit says so itself: that
function "flags orthographic variants as disagreements", so a False verdict
is an upper bound on disagreement, not proof of a different human.

The mirror-image rule -- "the labels that positively fold onto the winner
must outnumber the largest label that refutes them" -- also catches all
three, and kills a different correct row: mpCode 586, Sushma Swaraj, whose
biggest label is a Devanagari ministerial designation that fails to collapse
to the name inside its brackets and so reads as a refutation.

Neither rule dominates. What separates the poison from the spelling variants
is not agreement at all -- it is WEIGHT:

    code   winner's own evidence   largest refuting label
    549                        1                      344   <- poison
    545                        1                       56   <- poison
    4473                       1                       30   <- poison
    572                      161                      121   <- Deve Gowda

One stray turn against hundreds is the bug. A former PM's own name, spelled
two ways, is not. So the rule is the UNION of the two tests: mint when EITHER
holds, refuse only when NEITHER does.

  (a) the dominant printed label positively agrees with the roster name, OR
  (b) the turns whose labels positively fold onto the winner are at least as
      many as the single largest label that positively refutes them.

Refuse otherwise -- including when the code carries no name label at all
(only presiding/crowd), because silence is not agreement. Measured over the
real table this refuses exactly four rows: the three poisoned ones (526
turns of misattributed speech) plus mpCode 1200, which has a single turn of
evidence and no printed name to check it against. Loss of one turn to
prevent 526 turns of poison is the trade this project always takes.

Note that a `None` verdict never counts as a refutation. None means nothing
was compared, and treating "no evidence against" as "evidence for" is the
exact mistake recorded in `debate_fetch._name_agreement`'s own docstring.
"""
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
