from __future__ import annotations

import hashlib
import math
import os
import time

import requests

MODEL = "gemini-embedding-001"
DIMS = 1536
BATCH_SIZE = 100
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:batchEmbedContents"

# The two arms of the task-type bake-off: (task type for tags, task type for entities).
ARMS = {
    "A": ("SEMANTIC_SIMILARITY", "SEMANTIC_SIMILARITY"),
    "B": ("RETRIEVAL_DOCUMENT", "RETRIEVAL_QUERY"),
}
TASK_TYPES = {t for pair in ARMS.values() for t in pair}


def clean_aliases(tag: str, aliases: list[str]) -> list[str]:
    # The tag list keeps raw sansad.in spellings such as " Caste Census", which add nothing.
    out: list[str] = []
    for a in aliases:
        a = a.strip()
        if a and a.casefold() != tag.casefold() and a.casefold() not in {o.casefold() for o in out}:
            out.append(a)
    return out


def build_input_text(tag: str, type_: str, domain: str | None, description: str, aliases: list[str]) -> str:
    parts = [tag.strip()]
    names = clean_aliases(tag, aliases)
    if names:
        parts.append("Also called: " + ", ".join(names))
    parts.append(f"Type: {type_}")
    if domain:
        parts.append(f"Domain: {domain}")
    if description.strip():
        parts.append(description.strip().rstrip("."))
    return ". ".join(parts) + "."


def input_hash(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def normalise(values: list[float]) -> list[float]:
    # Google asks for length 1 when the size is below 3,072.
    norm = math.sqrt(sum(v * v for v in values))
    if norm == 0:
        raise ValueError("the model returned a vector of zeros")
    return [v / norm for v in values]


def to_pgvector(values: list[float]) -> str:
    return "[" + ",".join(repr(v) for v in values) + "]"


def api_key() -> str:
    key = os.environ.get("GEMINI_API_KEY", "")
    if not key:
        raise SystemExit("GEMINI_API_KEY is not set. Add it to .env, then run: set -a && source .env && set +a")
    return key


def embed_batch(texts: list[str], task_type: str, key: str, retries: int = 8) -> list[list[float]]:
    """Embed at most BATCH_SIZE texts. Retries on HTTP 429 and server errors."""
    if task_type not in TASK_TYPES:
        raise ValueError(f"unknown task type: {task_type}")
    body = {"requests": [{"model": f"models/{MODEL}", "content": {"parts": [{"text": t}]},
                          "taskType": task_type, "outputDimensionality": DIMS} for t in texts]}
    for attempt in range(retries):
        resp = requests.post(API_URL, json=body, headers={"x-goog-api-key": key}, timeout=120)
        if resp.status_code == 429 or resp.status_code >= 500:
            wait = min(60, 5 * 2 ** attempt)
            print(f"  HTTP {resp.status_code}, wait {wait}s", flush=True)
            time.sleep(wait)
            continue
        if resp.status_code != 200:
            raise SystemExit(f"Gemini API error {resp.status_code}: {resp.text[:500]}")
        vectors = [e["values"] for e in resp.json()["embeddings"]]
        if len(vectors) != len(texts):
            raise SystemExit(f"asked for {len(texts)} vectors, got {len(vectors)}")
        bad = {len(v) for v in vectors if len(v) != DIMS}
        if bad:
            raise SystemExit(f"asked for {DIMS} numbers per vector, got {sorted(bad)}")
        return [normalise(v) for v in vectors]
    raise SystemExit(f"Gemini API still fails after {retries} attempts")


def embed_texts(texts: list[str], task_type: str) -> list[list[float]]:
    key = api_key()
    out: list[list[float]] = []
    for start in range(0, len(texts), BATCH_SIZE):
        out += embed_batch(texts[start:start + BATCH_SIZE], task_type, key)
        print(f"  embedded {len(out)}/{len(texts)} ({task_type})", flush=True)
    return out
