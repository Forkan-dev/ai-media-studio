"""LLM calls through Ollama. Every call returns a validated Pydantic object."""
from typing import TypeVar

import httpx
from pydantic import BaseModel

from app.config import settings

T = TypeVar("T", bound=BaseModel)


def chat_json(
    system: str, user: str, schema: type[T], temperature: float = 0.7, model: str | None = None
) -> T:
    """Ask the model for JSON that matches `schema` and return it parsed."""
    resp = httpx.post(
        f"{settings.ollama_url}/api/chat",
        json={
            "model": model or settings.llm_model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "format": schema.model_json_schema(),  # Ollama constrains output to this schema
            "think": False,  # Qwen3: skip the hidden reasoning pass, faster
            "stream": False,
            "options": {"temperature": temperature},
        },
        timeout=600,
    )
    resp.raise_for_status()
    return schema.model_validate_json(resp.json()["message"]["content"])
