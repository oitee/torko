"""Shared parts of the LLM steps: the API key, one call to the generative LLM, and the table of model names."""
import json
import os
import time

import requests
from sqlalchemy import text


def api_key() -> str:
    key = os.environ.get("GEMINI_API_KEY", "")
    if not key:
        raise SystemExit("GEMINI_API_KEY is not set. Add it to .env, then run: set -a && source .env && set +a")
    return key


class ApiError(Exception):
    pass


def generate(model: str, system: str, body_text: str, key: str, schema: dict, retries: int = 8) -> tuple[dict, dict]:
    """One call to the generative LLM with a JSON answer that keeps to the schema. Returns the parsed answer
    and the token counts. It waits and asks again on HTTP 429 and on server errors."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    body = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": body_text}]}],
        "generationConfig": {"responseMimeType": "application/json", "responseJsonSchema": schema},
    }
    for attempt in range(retries):
        resp = requests.post(url, json=body, headers={"x-goog-api-key": key}, timeout=300)
        if resp.status_code == 429 or resp.status_code >= 500:
            wait = min(60, 5 * 2 ** attempt)
            print(f"  HTTP {resp.status_code}, wait {wait}s", flush=True)
            time.sleep(wait)
            continue
        if resp.status_code != 200:
            raise ApiError(f"HTTP {resp.status_code}: {resp.text[:300]}")
        data = resp.json()
        parts = data["candidates"][0].get("content", {}).get("parts", [])
        raw = "".join(p.get("text", "") for p in parts if not p.get("thought"))
        usage = data.get("usageMetadata", {})
        tokens = {"input": usage.get("promptTokenCount"), "output": usage.get("candidatesTokenCount"),
                  "thinking": usage.get("thoughtsTokenCount")}
        return json.loads(raw), tokens
    raise ApiError(f"still rate-limited after {retries} attempts")


def model_id(conn, name: str) -> int:
    """The id of the model name. A new name is added to the table models.

    The function reads first. An INSERT with ON CONFLICT uses one number of the SMALLINT sequence on each call,
    also when the name exists, so many calls would use up the sequence.
    """
    found = conn.execute(text("SELECT id FROM models WHERE name = :n"), {"n": name}).scalar()
    if found is not None:
        return found
    conn.execute(text("INSERT INTO models (name) VALUES (:n) ON CONFLICT (name) DO NOTHING"), {"n": name})
    return conn.execute(text("SELECT id FROM models WHERE name = :n"), {"n": name}).scalar()
