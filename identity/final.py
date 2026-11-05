"""Choose one answer for each label, from the answers of the deciders. No model and no database."""
from __future__ import annotations

from identity.gate import DEFAULT_LIMIT
from identity.types import NONE


def choose(answers: dict[str, tuple[str, float | None]], fallback: str | None = None,
           limit: float = DEFAULT_LIMIT) -> tuple[str, str] | None:
    """Return (answer, decider). A person wins, then a rule, then the model above the limit, then the fallback.

    NONE from the model says only that the list did not hold the person, so a fallback can still answer.
    """
    if "person" in answers:
        return answers["person"][0], "person"
    if "rule" in answers:
        return answers["rule"][0], "rule"
    model = answers.get("decision-model")
    if model and model[1] is not None and model[1] >= limit and model[0] != NONE:
        return model[0], "decision-model"
    if fallback and fallback in answers:
        return answers[fallback][0], fallback
    return None


def person_key(answer: str, rajya_sabha_links: dict[str, int], added: dict[str, int]) -> int | None:
    """The person id of an answer, or None when the answer names no person."""
    if answer.startswith("P") and answer[1:].isdigit():
        return int(answer[1:])
    if answer in rajya_sabha_links:
        return rajya_sabha_links[answer]
    return added.get(answer)
