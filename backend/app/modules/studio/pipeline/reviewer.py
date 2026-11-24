"""Reviewer role: scores a draft. The pass/fail rule is applied in code, not by the LLM."""
from functools import cache

from pydantic import BaseModel, Field, PrivateAttr, create_model

from app.modules.studio.brand import Brand
from app.modules.studio.pipeline.writer import Draft
from app.core.prompts import render
from app.core.clients.llm import chat_json

MIN_ANY = 5  # no criterion may score below this
MIN_ACCURACY = 7
WEAKNESS_CAP = 7  # a criterion with a listed weakness scores at most this

# criteria a brand can pick (review_criteria); the brand's reviewer prompt explains each one it uses
CRITERIA: tuple[str, ...] = ("hook", "accuracy", "clarity", "logic", "relatability", "humor", "pacing",
                             "originality", "laugh", "story", "punchline", "enjoyable")


class Score(BaseModel):
    reason: str  # reason first, so the model justifies before it scores
    score: int = Field(ge=1, le=10)


class Weakness(BaseModel):
    criterion: str  # one of the brand's review_criteria
    quote: str  # one exact sentence from the script
    problem: str
    real_problem: bool  # False for remarks like "no issues" or "good pacing"


class Review(BaseModel):
    """Base review; the score fields (one per brand criterion) are added by _review_schema."""
    weaknesses: list[Weakness]  # first: find problems before scoring, so scores are not inflated
    _criteria: tuple[str, ...] = PrivateAttr(default=())  # set from the brand config

    def scores(self) -> dict[str, int]:
        """Final scores for the brand's criteria: the model's score, capped where a real weakness was listed."""
        weak = {w.criterion for w in self.real_weaknesses()}
        return {
            k: min(getattr(self, k).score, WEAKNESS_CAP) if k in weak else getattr(self, k).score
            for k in self._criteria
        }

    def real_weaknesses(self) -> list[Weakness]:
        """Real problems on criteria this brand cares about."""
        return [w for w in self.weaknesses if w.real_problem and w.criterion in self._criteria]

    def average(self) -> float:
        s = self.scores()
        return sum(s.values()) / len(s)

    def fail_reasons(self, min_average: float) -> list[str]:
        """Why the review fails the pass rule (empty = passed)."""
        s, reasons = self.scores(), []
        if self.average() < min_average:
            reasons.append(f"average {self.average():.1f} is below {min_average}")
        reasons += [f"{k} {v} is below {MIN_ANY}" for k, v in s.items() if v < MIN_ANY]
        if "accuracy" in s and MIN_ANY <= s["accuracy"] < MIN_ACCURACY:
            reasons.append(f"accuracy {s['accuracy']} is below {MIN_ACCURACY}")
        return reasons

    def passed(self, min_average: float) -> bool:
        return not self.fail_reasons(min_average)


def _as_text(d: Draft) -> str:
    hooks = "\n".join(f"Hook {i}: {h}" for i, h in enumerate(d.hooks, 1))
    return f"{hooks}\n\nBody: {d.body}\n\nCTA: {d.cta}"


@cache
def _review_schema(criteria: tuple[str, ...]) -> type[Review]:
    """Review with one Score per brand criterion, in order: weaknesses -> scores -> best hook -> fixes."""
    scores = {c: (Score, ...) for c in criteria}
    return create_model("Review", __base__=Review, **scores,
                        best_hook=(int, Field(ge=1, le=3)), fixes=(list[str], ...))


def review_draft(brand: Brand, topic: str, facts: str, draft: Draft) -> Review:
    system = render(
        brand.prompt_folders, "reviewer",
        brand_name=brand.name, niche=brand.niche, tone=brand.tone,
        topic=topic, facts=facts, script=_as_text(draft),
    )
    criteria = tuple(brand.review_criteria)
    review = chat_json(system, "Review the script now.", _review_schema(criteria), temperature=0,
                       model=brand.review_model)
    review._criteria = tuple(brand.review_criteria)
    return review
