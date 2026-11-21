"""Fact-check: all sentences of a script in ONE reasoning call (thinking is slow, so it runs once)."""
import re
from typing import Literal

from pydantic import BaseModel

from app.brand import Brand
from app.prompts import render
from app.services.llm import chat_json


class ClaimCheck(BaseModel):
    reason: str  # reason first, so the model compares before it decides
    verdict: Literal["supported", "contradicted", "not_in_facts"]


class FactCheck(BaseModel):
    results: list[ClaimCheck]


def sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def check_sentences(brand: Brand, facts: str, items: list[str]) -> list[ClaimCheck]:
    numbered = "\n".join(f"{i}. {s}" for i, s in enumerate(items, 1))
    system = render(brand.prompts, "claim_check", facts=facts, sentences=numbered)
    results = chat_json(system, "Check all sentences now.", FactCheck, temperature=0, think=True).results
    if len(results) != len(items):
        raise ValueError(f"fact-check returned {len(results)} results for {len(items)} sentences")
    return results


def contradictions(brand: Brand, facts: str, items: list[str]) -> list[str]:
    """Sentences that contradict the facts."""
    return [s for s, c in zip(items, check_sentences(brand, facts, items)) if c.verdict == "contradicted"]
