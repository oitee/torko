"""The arguments of a speech for or against its bill: the input text, the checks of the answer, and the store.

The input is one pair of a speech and a bill whose stance is 'for' or 'against' (speech_stances).
The model lists up to 5 points. Each point has a side, one neutral sentence, and a quote copied from the speech.
The checks keep a point only when its keys are valid. A quote that is not in the speech text is stored with
quote_found = false.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from sqlalchemy import text

import stance as st
from llm import model_id
from text_match import norm

PROMPTS = Path(__file__).resolve().parent / "tags" / "arguments" / "prompts"
SIDES = {"for", "against"}
MAX_POINTS = 5
MAX_POINT_WORDS = 30

SCHEMA = {
    "type": "object",
    "properties": {"points": {"type": "array", "items": {
        "type": "object",
        "properties": {"side": {"type": "string", "enum": sorted(SIDES)},
                       "point": {"type": "string"}, "quote": {"type": "string"}},
        "required": ["side", "point", "quote"]}}},
    "required": ["points"],
}

PAIRS_SQL = """
    SELECT st.speech_id, st.bill_id, st.stance, s.word_count
    FROM speech_stances st JOIN speeches s ON s.id = st.speech_id
    WHERE st.stance IN ('for', 'against')
    ORDER BY st.speech_id, st.bill_id"""


def pair_id(speech_id: int, bill_id: int) -> str:
    return f"{speech_id}-{bill_id}"


def latest_prompt_version() -> str:
    return max((p.stem for p in PROMPTS.glob("v*.md")), key=lambda v: int(v[1:]))


def input_text(pair: dict, stance: str) -> str:
    summary = pair["bill_summary"] or "(no summary: only the name of the bill is known)"
    return (f"Bill: {pair['bill']}\nWhat the bill does: {summary}\n"
            f"Position of the speaker on the bill: {stance}\n"
            f"Debate: {pair['title']} ({pair['debate_date']})\nMember: {pair['member'] or '(no name)'}\n\n"
            f"Speech:\n{pair['text'].strip()}")


def build_input(conn, speech_id: int, bill_id: int, stance: str) -> dict:
    pair = st.load_pair(conn, speech_id, bill_id)
    body = input_text(pair, stance)
    return {"id": pair_id(speech_id, bill_id), "speech_id": speech_id, "bill_id": bill_id,
            "words": pair["words"], "input": body, "input_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest()}


def check_answer(answer: dict, speech_text: str) -> tuple[list[dict], list[str]]:
    """Returns (points, warnings). A point with a bad key is dropped with a warning."""
    warnings, points = [], []
    raw = answer.get("points")
    if not isinstance(raw, list):
        return [], ["points is not a list"]
    if len(raw) > MAX_POINTS:
        warnings.append(f"{len(raw)} points, only the first {MAX_POINTS} kept")
    body = norm(speech_text)
    for i, raw_point in enumerate(raw[:MAX_POINTS], 1):
        if not isinstance(raw_point, dict):
            warnings.append(f"point {i} is not an object")
            continue
        side, point, quote = raw_point.get("side"), raw_point.get("point"), raw_point.get("quote")
        if side not in SIDES:
            warnings.append(f"point {i}: side {side!r}")
            continue
        if not isinstance(point, str) or not point.strip() or len(point.split()) > MAX_POINT_WORDS:
            warnings.append(f"point {i}: point is empty or too long")
            continue
        if not isinstance(quote, str) or not quote.strip():
            warnings.append(f"point {i}: no quote")
            continue
        found = norm(quote) in body
        if not found:
            warnings.append(f"point {i}: quote not in the speech")
        points.append({"side": side, "point": point.strip(), "quote": quote.strip(), "quote_found": found})
    return points, warnings


def store(conn, speech_id: int, bill_id: int, answer: dict, model: str, prompt_version: str,
          input_sha256: str, speech_text: str) -> dict:
    """Replaces the stored answer of the pair. Returns counts of the stored points."""
    points, warnings = check_answer(answer, speech_text)
    conn.execute(text("DELETE FROM argument_extractions WHERE speech_id = :s AND bill_id = :b"),
                 {"s": speech_id, "b": bill_id})
    ext = conn.execute(text("""
        INSERT INTO argument_extractions (speech_id, bill_id, model_id, prompt_version, input_sha256, raw, warnings)
        VALUES (:s, :b, :m, :v, :h, CAST(:raw AS jsonb), :w) RETURNING id"""),
        {"s": speech_id, "b": bill_id, "m": model_id(conn, model), "v": prompt_version, "h": input_sha256,
         "raw": json.dumps(answer, ensure_ascii=False), "w": warnings}).scalar()
    for pos, point in enumerate(points, 1):
        conn.execute(text("""
            INSERT INTO speech_arguments (extraction_id, speech_id, bill_id, position, side, point, quote, quote_found)
            VALUES (:e, :s, :b, :pos, :side, :point, :quote, :found)"""),
            {"e": ext, "s": speech_id, "b": bill_id, "pos": pos, "side": point["side"], "point": point["point"],
             "quote": point["quote"], "found": point["quote_found"]})
    return {"points": len(points), "quote_missing": sum(not point["quote_found"] for point in points),
            "warnings": len(warnings)}
