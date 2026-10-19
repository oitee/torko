from __future__ import annotations

import os
import time

import requests

MODEL = "jev-1.13.0"
API_URL = "https://api.typesafe.ai/v1/systemone"


class DecisionError(Exception):
    pass


class StateTooLong(DecisionError):
    pass


def api_key() -> str:
    key = os.environ.get("TYPESAFE_API_KEY", "")
    if not key:
        raise SystemExit("TYPESAFE_API_KEY is not set. Add it to .env, then run: set -a && source .env && set +a")
    return key


def choice_q(instructions: str, options: dict[str, str]) -> dict:
    return {"type": "choice", "instructions": instructions, "criteria": dict(options)}


def score_q(instructions: str, levels: list[str]) -> dict:
    if not 2 <= len(levels) <= 10:
        raise ValueError(f"a score question needs 2 to 10 levels, not {len(levels)}")
    return {"type": "score", "instructions": instructions, "criteria": list(levels)}


def noul_q(statement: str) -> dict:
    return {"type": "noul", "instructions": statement}


def looks_too_long(status: int, body: str) -> bool:
    if status == 413:
        return True
    low = body.lower()
    return status == 400 and any(w in low for w in ("context", "too long", "too many tokens", "maximum", "max_tokens_exceeded"))


def decide(state: str, questions: dict[str, dict], key: str, model: str = MODEL, retries: int = 8) -> dict:
    """Retries on HTTP 429, server errors, a timeout, and a dropped connection."""
    body = {"model": model, "state": state, "questions": questions}
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    for attempt in range(retries):
        try:
            resp = requests.post(API_URL, json=body, headers=headers, timeout=120)
        except (requests.Timeout, requests.ConnectionError) as exc:
            wait = min(60, 5 * 2 ** attempt)
            print(f"  {type(exc).__name__}, wait {wait}s", flush=True)
            time.sleep(wait)
            continue
        if resp.status_code == 429 or resp.status_code >= 500:
            wait = min(60, 5 * 2 ** attempt)
            print(f"  HTTP {resp.status_code}, wait {wait}s", flush=True)
            time.sleep(wait)
            continue
        if looks_too_long(resp.status_code, resp.text):
            raise StateTooLong(f"HTTP {resp.status_code}: {resp.text[:300]}")
        if resp.status_code != 200:
            raise DecisionError(f"HTTP {resp.status_code}: {resp.text[:300]}")
        data = resp.json()
        missing = set(questions) - set(data.get("answers") or {})
        if missing:
            raise DecisionError(f"no answer for {len(missing)} questions, for example {sorted(missing)[:3]}")
        return data
    raise DecisionError(f"no answer after {retries} attempts (rate limit, server error, or network)")


def _probabilities(answer: dict) -> dict:
    probs = answer.get("probabilities")
    if not isinstance(probs, dict) or not probs:
        raise DecisionError(f"answer has no probabilities: {str(answer)[:200]}")
    return probs


def choice_probabilities(answer: dict, options: list[str]) -> dict[str, float]:
    """An option that the answer leaves out gets 0."""
    probs = _probabilities(answer)
    unknown = set(probs) - set(options)
    if unknown:
        raise DecisionError(f"answer names options that were not asked: {sorted(unknown)[:3]}")
    return {o: float(probs.get(o, 0.0)) for o in options}


def score_probabilities(answer: dict, levels: list[str]) -> list[float]:
    # The answer can key the levels by index ("0", "1") or by the level text.
    probs = _probabilities(answer)
    out = [0.0] * len(levels)
    for k, p in probs.items():
        if str(k).lstrip("-").isdigit() and 0 <= int(k) < len(levels):
            out[int(k)] = float(p)
        elif k in levels:
            out[levels.index(k)] = float(p)
        else:
            raise DecisionError(f"answer names a level that was not asked: {str(k)[:80]}")
    return out


def noul_probability(answer: dict) -> float:
    for k in ("noul", "probability"):
        if isinstance(answer.get(k), (int, float)) and not isinstance(answer.get(k), bool):
            return float(answer[k])
    probs = _probabilities(answer)
    for k in ("true", "yes", "True", "Yes"):
        if k in probs:
            return float(probs[k])
    raise DecisionError(f"noul answer has no probability of true: {str(answer)[:200]}")


def sum_is_off(probs: list[float]) -> bool:
    # The API rounds each probability to 2 decimals, so the tolerance grows with the answer count.
    return abs(sum(probs) - 1) > 0.005 * len(probs) + 0.01
