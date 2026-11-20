"""Reviewer role: scores a draft. The pass/fail rule is applied in code, not by the LLM."""
from pydantic import BaseModel, Field

from app.brand import Brand
from app.pipeline.writer import Draft
from app.prompts import render
from app.services.llm import chat_json

MIN_ANY = 5  # no criterion may score below this
MIN_ACCURACY = 7


class Score(BaseModel):
    reason: str  # reason first, so the model justifies before it scores
    score: int = Field(ge=1, le=10)


class Review(BaseModel):
    hook: Score
    accuracy: Score
    clarity: Score
    humor: Score
    pacing: Score
    originality: Score
    best_hook: int = Field(ge=1, le=3)
    fixes: list[str]

    def scores(self) -> dict[str, int]:
        return {k: getattr(self, k).score for k in
                ("hook", "accuracy", "clarity", "humor", "pacing", "originality")}

    def average(self) -> float:
        s = self.scores()
        return sum(s.values()) / len(s)

    def passed(self, min_average: float) -> bool:
        s = self.scores()
        return (
            self.average() >= min_average
            and min(s.values()) >= MIN_ANY
            and s["accuracy"] >= MIN_ACCURACY
        )


def _as_text(d: Draft) -> str:
    hooks = "\n".join(f"Hook {i}: {h}" for i, h in enumerate(d.hooks, 1))
    return f"{hooks}\n\nBody: {d.body}\n\nCTA: {d.cta}"


def review_draft(brand: Brand, topic: str, facts: str, draft: Draft) -> Review:
    system = render(
        brand.prompts, "reviewer",
        brand_name=brand.name, niche=brand.niche, tone=brand.tone,
        topic=topic, facts=facts, script=_as_text(draft),
    )
    return chat_json(system, "Review the script now.", Review, temperature=0.2)
