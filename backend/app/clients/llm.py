"""LLM calls through Ollama. Every call returns a validated Pydantic object."""
import base64
import time
from pathlib import Path
from typing import TypeVar

import httpx
from pydantic import BaseModel

from app.config import settings

T = TypeVar("T", bound=BaseModel)
LOAD_RETRIES = 3
RETRY_WAIT_SECONDS = 15


def chat_json(
    system: str, user: str, schema: type[T], temperature: float = 0.7, model: str | None = None,
    think: bool = False, images: list[Path] | None = None,
) -> T:
    """Ask the model for JSON that matches `schema` and return it parsed. `images`: for vision checks."""
    user_msg = {"role": "user", "content": user}
    if images:
        user_msg["images"] = [base64.b64encode(p.read_bytes()).decode() for p in images]
    payload = {
        "model": model or settings.llm_model,
        "messages": [{"role": "system", "content": system}, user_msg],
        "format": schema.model_json_schema(),  # Ollama constrains output to this schema
        "think": think,  # reasoning pass: slower, but much better at logic
        "stream": False,
        "options": {"temperature": temperature, "num_ctx": settings.llm_context},
    }
    for attempt in range(1, LOAD_RETRIES + 1):
        resp = httpx.post(f"{settings.ollama_url}/api/chat", json=payload, timeout=600)
        # 5xx = the model failed to load (e.g. memory still held by SDXL a moment ago): wait and retry
        if resp.status_code < 500 or attempt == LOAD_RETRIES:
            break
        time.sleep(RETRY_WAIT_SECONDS)
    resp.raise_for_status()
    return schema.model_validate_json(resp.json()["message"]["content"])


def unload(model: str | None = None) -> None:
    """Free the model's memory now (e.g. before SDXL needs it). No model given: every loaded model."""
    models = [model] if model else [m["name"] for m in httpx.get(f"{settings.ollama_url}/api/ps", timeout=30)
                                    .json().get("models", [])]
    for m in models:
        httpx.post(f"{settings.ollama_url}/api/generate", json={"model": m, "keep_alive": 0}, timeout=60)
