"""Script chain: Writer drafts -> Reviewer (quality) -> fact-check (truth) -> rewrites -> final script."""
from dataclasses import dataclass, field
from typing import Literal

from app.brand import Brand
from app.pipeline.fact_check import check_sentences, sentences
from app.pipeline.reviewer import Review, review_draft
from app.pipeline.writer import WORDS_PER_SECOND, Draft, write_draft

STRUCTURES = ("story", "myth_vs_fact")
MAX_REWRITES = 2
LENGTH_TOLERANCE = 0.15  # script length must be within ±15% of the brand's target


@dataclass
class Candidate:
    structure: str
    draft: Draft
    review: Review
    length_note: str | None  # None = length is fine
    fact_ok: bool | None = None  # None = not checked yet
    good_hooks: list[int] = field(default_factory=list)  # 1-based hooks that do not contradict facts
    wrong_sentences: list[str] = field(default_factory=list)  # hook/body/CTA sentences that contradict

    def hook_number(self) -> int:
        """The reviewer's best hook if it is factually fine, else the first fine one."""
        best = self.review.best_hook
        return best if best in self.good_hooks else self.good_hooks[0]

    def feedback(self) -> list[str]:
        wrong = [f"This sentence contradicts the research, fix or remove it: {s}" for s in self.wrong_sentences]
        length = [self.length_note] if self.length_note else []
        return wrong + length + self.review.fixes

    def passed(self, min_score: float) -> bool:
        """Review passed, length fine, and not failed by the fact-check."""
        return self.review.passed(min_score) and self.length_note is None and self.fact_ok is not False


@dataclass
class ScriptResult:
    status: Literal["passed", "below_quality"]
    best: Candidate
    attempts: list[Candidate]

    def narration(self) -> str:
        """Final spoken text: chosen hook + body + CTA."""
        d = self.best.draft
        hook = d.hooks[self.best.hook_number() - 1] if self.best.good_hooks else d.hooks[0]
        return f"{hook} {d.body} {d.cta}"


def _length_note(brand: Brand, d: Draft) -> str | None:
    """Spoken length = best-case hook + body + CTA. Returns a fix note if outside tolerance."""
    words = len(f"{d.hooks[0]} {d.body} {d.cta}".split())
    target = round(brand.duration * WORDS_PER_SECOND)
    if abs(words - target) <= target * LENGTH_TOLERANCE:
        return None
    side = "short" if words < target else "long"
    return f"Too {side}: {words} words. Write about {target} words (about {brand.duration} seconds)."


def _try(brand: Brand, topic: str, facts: str, structure: str, feedback: list[str] | None) -> Candidate:
    draft = write_draft(brand, topic, facts, structure, feedback)
    return Candidate(structure, draft, review_draft(brand, topic, facts, draft), _length_note(brand, draft))


def _fact_check(brand: Brand, facts: str, c: Candidate) -> bool:
    """One thinking call for all hooks + sentences. OK if a fine hook exists and the body has no errors."""
    body = sentences(f"{c.draft.body} {c.draft.cta}")
    checks = check_sentences(brand, facts, [*c.draft.hooks, *body])
    hook_checks, body_checks = checks[:3], checks[3:]
    c.good_hooks = [i for i, ch in enumerate(hook_checks, 1) if ch.verdict != "contradicted"]
    wrong_hooks = [h for h, ch in zip(c.draft.hooks, hook_checks) if ch.verdict == "contradicted"]
    wrong_body = [s for s, ch in zip(body, body_checks) if ch.verdict == "contradicted"]
    c.wrong_sentences = wrong_hooks + wrong_body
    c.fact_ok = bool(c.good_hooks) and not wrong_body
    return c.fact_ok


def _best(candidates: list[Candidate]) -> Candidate:
    return max(candidates, key=lambda c: c.review.average())


def make_script(brand: Brand, topic: str, facts: str) -> ScriptResult:
    attempts = [_try(brand, topic, facts, s, None) for s in STRUCTURES]
    for rewrite in range(MAX_REWRITES + 1):
        passed = [c for c in attempts if c.passed(brand.min_quality_score)]
        if passed:
            best = _best(passed)  # fact-check only the best passing draft: the check is slow
            if _fact_check(brand, facts, best):
                return ScriptResult("passed", best, attempts)
        else:
            best = _best(attempts)
        if rewrite < MAX_REWRITES:
            attempts.append(_try(brand, topic, facts, best.structure, best.feedback()))
    return ScriptResult("below_quality", _best(attempts), attempts)
