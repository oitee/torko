"""Decide what each label needs, on all CPU cores. The result does not depend on the number of cores."""
from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass

from identity import labels, retrieve
from identity.types import Answer, Entry, LabelRow, NOT_A_PERSON, OFFICE, ParsedLabel


@dataclass(frozen=True)
class Plan:
    row: LabelRow
    parsed: ParsedLabel
    options: list[Entry]
    answer: Answer | None  # An answer from a rule. None means that the label needs the model.


_seated: dict[int, list[Entry]] = {}
_outside: list[Entry] = []
_sizes: tuple[int, int] = (0, 0)


def _setup(seated, outside, sizes) -> None:
    global _seated, _outside, _sizes
    _seated, _outside, _sizes = seated, outside, sizes


def plan_label(row: LabelRow, seated: dict[int, list[Entry]], outside: list[Entry], sizes: tuple[int, int]) -> Plan:
    parsed = labels.read_label(row.label)
    if parsed.kind != "name":
        key = OFFICE if parsed.kind == "office" else NOT_A_PERSON
        return Plan(row, parsed, [], Answer(key, None, "rule"))
    members = seated.get(row.term, [])
    entry = retrieve.rule_answer(parsed, members)
    if entry:
        return Plan(row, parsed, [entry], Answer(entry.key, None, "rule"))
    return Plan(row, parsed, retrieve.build_options(parsed, members, outside, *sizes), None)


def _work(row: LabelRow) -> Plan:
    return plan_label(row, _seated, _outside, _sizes)


def plan_all(rows: list[LabelRow], seated, outside, sizes, processes: int | None = None) -> list[Plan]:
    with ProcessPoolExecutor(processes, initializer=_setup, initargs=(seated, outside, sizes)) as pool:
        plans = []
        for n, plan in enumerate(pool.map(_work, rows, chunksize=20), 1):
            plans.append(plan)
            if n % 500 == 0:
                print(f"options: {n} of {len(rows)}", flush=True)
    return plans
