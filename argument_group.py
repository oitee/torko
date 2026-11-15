"""Group the argument points of each bill and side into a few shared arguments, each with one neutral label.

The input of one call is one list: every point of one bill on one side ('for' or 'against') whose quote is in
the speech (speech_arguments.quote_found). Only these points are on the pages, so only they get a group.

The steps:
1. Each point has a vector (table argument_vectors, scripts/embed_arguments.py).
2. order_points() puts the points of one list in a chain: each next point is the nearest point not yet used.
   Close points sit next to each other in the list. The order makes no group.
3. The model reads the ordered list. Each point has a short number. The answer gives groups: a label and numbers.
4. check_answer() refuses a broken answer: a missing number, a number in two groups, a number not in the list,
   a group with no label, or a label that is too long. A refused list is asked again.
5. The join call. One call over a long list of points can leave two groups with the same reason, for example
   "Delays women's reservation by linking it to delimitation" and "Holds women's reservation hostage to
   delimitation". So a list with MERGE_MIN_GROUPS groups or more gets a second call. build_merge_input() shows
   the model each group: its label, its count of points, and a few of its points. The answer names the groups
   that give the same reason, with one new label for each join. check_joins() refuses a broken answer.
   apply_joins() makes the final groups.
6. store() writes one bill_arguments row for each final group, and sets speech_arguments.bill_argument_id.
   Only the final groups go into the database.

A list with one point needs no call: the point is its own group, and its text is the label.
The checks do not prove that a group or a join is correct. A manual review of a sample measures that.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from sqlalchemy import text

ROOT = Path(__file__).resolve().parent
PROMPTS = ROOT / "tags" / "arguments" / "prompts"
MAX_LABEL_WORDS = 14
MAX_LABEL_CHARS = 110
MERGE_MIN_GROUPS = 5
MERGE_POINTS_SHOWN = 4
SIDES = ("for", "against")

LISTS_SQL = """
    SELECT a.id, a.bill_id, a.side, a.point, a.speech_id
    FROM speech_arguments a
    WHERE a.quote_found
    ORDER BY a.bill_id, a.side, a.id"""


def latest_prompt_version(kind: str = "group") -> str:
    """The highest version of the prompts of one kind: "group" for the grouping call, "merge" for the join call."""
    return max((p.stem for p in PROMPTS.glob(f"{kind}_v*.md")), key=lambda v: int(v.split("_v")[1]))


def list_key(bill_id: int, side: str) -> str:
    return f"{bill_id}-{side}"


def order_points(ids: list[int], vectors: dict[int, list[float]]) -> list[int]:
    """A chain of nearest neighbours. It starts at the point that is least like the mean of the list,
    so the chain starts at one edge and not in the middle. Ties go to the lower id. Vectors are unit length."""
    if len(ids) <= 2:
        return sorted(ids)
    dims = len(next(iter(vectors.values())))
    mean = [sum(vectors[i][d] for i in ids) / len(ids) for d in range(dims)]

    def dot(a, b):
        return sum(x * y for x, y in zip(a, b))

    left = sorted(ids)
    cur = min(left, key=lambda i: (dot(vectors[i], mean), i))
    out = [cur]
    left.remove(cur)
    while left:
        cur = max(left, key=lambda i: (dot(vectors[i], vectors[cur]), -i))
        out.append(cur)
        left.remove(cur)
    return out


def build_input(bill: str, year: int, side: str, points: list[str]) -> str:
    """The text of one list. The points are numbered from 1 in the given order."""
    word = "for" if side == "for" else "against"
    lines = "\n".join(f"{n}. {p.strip()}" for n, p in enumerate(points, 1))
    return (f"Bill: {bill}, {year}\nSide: the points that members of the Lok Sabha made {word} the bill.\n"
            f"Points ({len(points)}). Points with a close meaning sit near each other:\n{lines}\n")


def input_hash(body: str) -> str:
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def check_answer(answer: dict, n_points: int) -> tuple[list[dict], list[str]]:
    """Returns (groups, problems). The answer is good only when problems is empty.

    Each group is {"label": str, "points": [numbers from 1]}. Every number from 1 to n_points must be in
    exactly one group."""
    problems: list[str] = []
    raw = answer.get("groups") if isinstance(answer, dict) else None
    if not isinstance(raw, list) or not raw:
        return [], ["groups is not a list with groups"]
    seen: dict[int, int] = {}
    groups = []
    for g_no, group in enumerate(raw, 1):
        if not isinstance(group, dict):
            problems.append(f"group {g_no} is not an object")
            continue
        label = " ".join(str(group.get("label") or "").split())
        if not label:
            problems.append(f"group {g_no} has no label")
        elif len(label.split()) > MAX_LABEL_WORDS or len(label) > MAX_LABEL_CHARS:
            problems.append(f"group {g_no}: the label is too long")
        nums = []
        for item in group.get("points") or []:
            try:
                number = int(item)
            except (TypeError, ValueError):
                problems.append(f"group {g_no}: {item!r} is not a point number")
                continue
            if not 1 <= number <= n_points:
                problems.append(f"group {g_no}: point {number} is not in the list")
            elif number in seen:
                problems.append(f"point {number} is in group {seen[number]} and in group {g_no}")
            else:
                seen[number] = g_no
                nums.append(number)
        if not nums:
            problems.append(f"group {g_no} has no point")
        groups.append({"label": label, "points": nums})
    missing = sorted(set(range(1, n_points + 1)) - set(seen))
    if missing:
        problems.append(f"{len(missing)} points are in no group: {missing[:10]}")
    return groups, problems


def _label_problem(label: str) -> str | None:
    if not label:
        return "has no label"
    if len(label.split()) > MAX_LABEL_WORDS or len(label) > MAX_LABEL_CHARS:
        return "the label is too long"
    return None


def build_merge_input(bill: str, year: int, side: str, groups: list[dict], order: list[int],
                      points: dict[int, str]) -> tuple[str, list[int]]:
    """The text of the join call, and the group that each number of the text names.

    groups is a checked answer of the grouping call. order maps its point numbers to argument ids, and points
    maps an id to its text. The groups are in order of size, largest first. A tie keeps the order of the answer.
    Each group shows at most MERGE_POINTS_SHOWN points, the points with the lowest ids."""
    merge_order = sorted(range(len(groups)), key=lambda group_index: -len(groups[group_index]["points"]))
    lines = [f"Bill: {bill}, {year}", f"Side: the points that members made {side} the bill.",
             f"Groups ({len(groups)}):", ""]
    for number, group_index in enumerate(merge_order, 1):
        ids = sorted(order[point_number - 1] for point_number in groups[group_index]["points"])
        lines.append(f"{number}. {groups[group_index]['label']} ({len(ids)} points)")
        lines += [f"   - {points[i]}" for i in ids[:MERGE_POINTS_SHOWN]]
    return "\n".join(lines), merge_order


def check_joins(answer: dict, n_groups: int) -> tuple[list[dict], list[str]]:
    """Returns (joins, problems). The answer is good only when problems is empty. An answer with no join is good.

    Each join is {"label": str, "groups": [numbers from 1]}. A join has at least 2 groups, and a group is in
    at most one join."""
    raw = answer.get("joins") if isinstance(answer, dict) else None
    if not isinstance(raw, list):
        return [], ["joins is not a list"]
    problems: list[str] = []
    seen: dict[int, int] = {}
    joins = []
    for j_no, join in enumerate(raw, 1):
        if not isinstance(join, dict):
            problems.append(f"join {j_no} is not an object")
            continue
        label = " ".join(str(join.get("label") or "").split())
        if (why := _label_problem(label)):
            problems.append(f"join {j_no}: {why}")
        nums = []
        for item in join.get("groups") or []:
            try:
                number = int(item)
            except (TypeError, ValueError):
                problems.append(f"join {j_no}: {item!r} is not a group number")
                continue
            if not 1 <= number <= n_groups:
                problems.append(f"join {j_no}: group {number} is not in the list")
            elif number in seen:
                problems.append(f"group {number} is in join {seen[number]} and in join {j_no}")
            else:
                seen[number] = j_no
                nums.append(number)
        if len(nums) < 2:
            problems.append(f"join {j_no} has fewer than 2 groups")
        joins.append({"label": label, "groups": nums})
    return joins, problems


def apply_joins(groups: list[dict], merge_order: list[int], joins: list[dict]) -> list[dict]:
    """The final groups. The groups of one join become one group with the label of the join. The other groups
    stay as they are. The final groups are in order of size, largest first. A tie keeps the order of the answer."""
    final: dict[int, dict] = {g: groups[g] for g in range(len(groups))}
    for j in joins:
        members = [merge_order[k - 1] for k in j["groups"]]
        for g in members:
            final.pop(g)
        final[min(members)] = {"label": j["label"],
                               "points": sorted(p for g in members for p in groups[g]["points"])}
    return [final[g] for g in sorted(final, key=lambda g: (-len(final[g]["points"]), g))]


def load_lists(conn) -> dict[str, dict]:
    """{list key: {bill_id, side, bill, year, ids: [argument ids], points: {id: text}}}."""
    names = {r.id: (r.name, r.year) for r in conn.execute(text("SELECT id, name, year FROM bills"))}
    out: dict[str, dict] = {}
    for r in conn.execute(text(LISTS_SQL)):
        k = list_key(r.bill_id, r.side)
        lst = out.setdefault(k, {"bill_id": r.bill_id, "side": r.side, "bill": names[r.bill_id][0],
                                 "year": names[r.bill_id][1], "ids": [], "points": {}})
        lst["ids"].append(r.id)
        lst["points"][r.id] = r.point
    return out


def load_vectors(conn, ids: list[int]) -> dict[int, list[float]]:
    rows = conn.execute(text("SELECT argument_id, vector::text FROM argument_vectors WHERE argument_id = ANY(:i)"),
                        {"i": ids})
    return {i: json.loads(v) for i, v in rows}


def make_input(lst: dict, vectors: dict[int, list[float]]) -> dict:
    """The ordered list of one bill and side, as the model reads it."""
    order = order_points(lst["ids"], vectors)
    body = build_input(lst["bill"], lst["year"], lst["side"], [lst["points"][i] for i in order])
    return {"id": list_key(lst["bill_id"], lst["side"]), "order": order, "input": body,
            "input_sha256": input_hash(body), "n": len(order)}


def store(conn, bill_id: int, side: str, order: list[int], groups: list[dict], model_id: int | None,
          prompt_version: str, input_sha256: str) -> int:
    """Replaces the groups of one list. Returns the number of groups."""
    conn.execute(text("UPDATE speech_arguments SET bill_argument_id = NULL WHERE bill_id = :b AND side = :s"),
                 {"b": bill_id, "s": side})
    conn.execute(text("DELETE FROM bill_arguments WHERE bill_id = :b AND side = :s"), {"b": bill_id, "s": side})
    for pos, group in enumerate(groups, 1):
        gid = conn.execute(text("""
            INSERT INTO bill_arguments (bill_id, side, position, label, model_id, prompt_version, input_sha256)
            VALUES (:b, :s, :p, :l, :m, :v, :h) RETURNING id"""),
            {"b": bill_id, "s": side, "p": pos, "l": group["label"], "m": model_id, "v": prompt_version,
             "h": input_sha256}).scalar()
        conn.execute(text("UPDATE speech_arguments SET bill_argument_id = :g WHERE id = ANY(:ids)"),
                     {"g": gid, "ids": [order[number - 1] for number in group["points"]]})
    return len(groups)
