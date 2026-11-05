"""Ask the decision model which option is the speaker. The model can only choose an option."""
from __future__ import annotations

import hashlib
from typing import Callable

from decision_model import choice_probabilities, choice_q
from identity.types import FIXED_ANSWERS, Answer, Entry, LabelRow

PROMPT_VERSION = "identify_v2"
DECIDED_BY = "decision-model"
QUESTION = "Which option is the person who spoke under this label?"

Decide = Callable[[str, dict], dict]


def state_text(row: LabelRow) -> str:
    return (
        "A debate of the Lok Sabha, the lower house of the parliament of India, prints a label above each "
        "speaking turn. A minister from the upper house can also speak in the Lok Sabha. Hindi labels can "
        "hold damaged letters.\n"
        f"Lok Sabha term: {row.term}\nLabel: {row.label}\n"
        f"Debates with this label: {row.first_date} to {row.last_date}\n"
        f"Debate title: {row.title}\nStart of the text: {row.excerpt}"
    )


def options_hash(options: list[Entry]) -> str:
    return hashlib.sha256("\n".join(sorted(f"{e.key} {e.text}" for e in options)).encode()).hexdigest()[:16]


def resolve(row: LabelRow, options: list[Entry], decide: Decide) -> Answer:
    criteria = {**{e.key: e.text for e in options}, **FIXED_ANSWERS}
    data = decide(state_text(row), {"speaker": choice_q(QUESTION, criteria)})
    probs = choice_probabilities(data["answers"]["speaker"], list(criteria))
    ranked = sorted(probs.items(), key=lambda kv: -kv[1])
    tokens = int((data.get("usage") or {}).get("input_tokens") or 0)
    return Answer(ranked[0][0], ranked[0][1], DECIDED_BY, tuple(ranked[:3]), tokens)
