"""LLM calls through Ollama. Every call returns a validated Pydantic object."""
import base64
from pathlib import Path
from typing import TypeVar

import httpx
from pydantic import BaseModel

from app.config import settings

T = TypeVar("T", bound=BaseModel)


def chat_json(
    system: str, user: str, schema: type[T], temperature: float = 0.7, model: str | None = None,
    think: bool = False, images: list[Path] | None = None,
) -> T:
    """Ask the model for JSON that matches `schema` and return it parsed. `images`: for vision checks."""
    user_msg = {"role": "user", "content": user}
    if images:
        user_msg["images"] = [base64.b64encode(p.read_bytes()).decode() for p in images]
    resp = httpx.post(
        f"{settings.ollama_url}/api/chat",
        json={
            "model": model or settings.llm_model,
            "messages": [{"role": "system", "content": system}, user_msg],
            "format": schema.model_json_schema(),  # Ollama constrains output to this schema
            "think": think,  # Qwen3 reasoning pass: slower, but much better at logic
            "stream": False,
            "options": {"temperature": temperature, "num_ctx": settings.llm_context},
        },
        timeout=600,
    )
    resp.raise_for_status()
    return schema.model_validate_json(resp.json()["message"]["content"])


def unload(model: str | None = None) -> None:
    """Free the model's memory now (e.g. before SDXL needs it)."""
    httpx.post(f"{settings.ollama_url}/api/generate",
               json={"model": model or settings.llm_model, "keep_alive": 0}, timeout=60)
