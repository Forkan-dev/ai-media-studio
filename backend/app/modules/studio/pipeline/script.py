"""Script chain: always produces a script; problems become flags for the human review.

2 drafts -> review -> at most 1 sentence-repair round -> fact-check once -> wrong body sentences
are removed by code -> status "passed" (no flags) or "needs_attention" (flags listed).
"""
import re
from dataclasses import dataclass, field
from typing import Literal

from app.core.progress import Report, noop
from app.modules.studio.brand import Brand
from app.modules.studio.pipeline.fact_check import check_sentences, sentences
from app.modules.studio.pipeline.reviewer import Review, review_draft
from app.modules.studio.pipeline.writer import (WORDS_PER_SECOND, Draft, plan_story, remove_duplicates, rewrite_sentence,
                                 write_draft)

MAX_REPAIRS = 1
LENGTH_TOLERANCE = 0.15  # script length must be within ±15% of the brand's target
HOOKS = 3  # units 0..2 are the hooks, then body sentences, then the CTA


@dataclass
class Candidate:
    structure: str
    draft: Draft
    review: Review
    length_note: str | None  # None = length is fine
    fact_ok: bool | None = None  # None = not checked yet
    good_hooks: list[int] = field(default_factory=list)  # 1-based hooks that do not contradict facts
    wrong_sentences: list[str] = field(default_factory=list)  # hook/body/CTA sentences that contradict

    def text(self) -> str:
        """This version as spoken: the reviewer's best hook + body + CTA (for the versions list)."""
        d = self.draft
        return " ".join([d.hooks[self.review.best_hook - 1], d.body, d.cta])

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
    status: Literal["passed", "needs_attention"]
    best: Candidate
    attempts: list[Candidate]
    flags: list[str] = field(default_factory=list)  # what the human should check
    removed: list[str] = field(default_factory=list)  # wrong sentences removed by code

    def narration(self) -> str:
        """Final spoken text: an accurate hook (if any) + body + CTA."""
        d = self.best.draft
        hook = d.hooks[self.best.hook_number() - 1] if self.best.good_hooks else ""
        return " ".join(p for p in (hook, d.body, d.cta) if p)


def _length_note(brand: Brand, d: Draft) -> str | None:
    """Spoken length = best-case hook + body + CTA. Returns a fix note if outside tolerance."""
    words = len(f"{d.hooks[0]} {d.body} {d.cta}".split())
    target = round(brand.duration * WORDS_PER_SECOND)
    if abs(words - target) <= target * LENGTH_TOLERANCE:
        return None
    side = "short" if words < target else "long"
    return f"Too {side}: {words} words. Write about {target} words (about {brand.duration} seconds)."


def _try(brand: Brand, topic: str, facts: str, structure: str, feedback: list[str] | None = None,
         previous: Draft | None = None, report: Report = noop) -> Candidate:
    label = structure.replace("_", " ")
    # story mode: a new draft is written from a plan; an edit keeps the previous draft's story
    outline = None
    if brand.script_mode == "story" and not previous:
        report(f"Planning the story · {label}")
        outline = plan_story(brand, topic, structure)
    report(f"Editing the draft · {label}" if previous else f"Writing a draft · {label}")
    draft = write_draft(brand, topic, facts, structure, feedback, previous, outline)
    return _reviewed(brand, topic, facts, structure, draft, report)


def _reviewed(brand: Brand, topic: str, facts: str, structure: str, draft: Draft, report: Report) -> Candidate:
    report(f"Reviewing · {len(f'{draft.body} {draft.cta}'.split())} words")
    c = Candidate(structure, draft, review_draft(brand, topic, facts, draft), _length_note(brand, draft))
    report(f"Review score {c.review.average():.1f} · {structure.replace('_', ' ')}")
    return c


def _fact_check(brand: Brand, facts: str, c: Candidate) -> bool:
    """One thinking call for all hooks + sentences. OK if a fine hook exists and the body has no errors."""
    body = sentences(f"{c.draft.body} {c.draft.cta}")
    checks = check_sentences(brand, facts, [*c.draft.hooks, *body])
    hook_checks, body_checks = checks[:HOOKS], checks[HOOKS:]
    c.good_hooks = [i for i, ch in enumerate(hook_checks, 1) if ch.verdict != "contradicted"]
    wrong_hooks = [h for h, ch in zip(c.draft.hooks, hook_checks) if ch.verdict == "contradicted"]
    wrong_body = [s for s, ch in zip(body, body_checks) if ch.verdict == "contradicted"]
    c.wrong_sentences = wrong_hooks + wrong_body
    c.fact_ok = bool(c.good_hooks) and not wrong_body
    return c.fact_ok


def _best(candidates: list[Candidate]) -> Candidate:
    return max(candidates, key=lambda c: c.review.average())


# ---------- sentence repair ----------

def _units(d: Draft) -> list[str]:
    return [*d.hooks, *sentences(d.body), d.cta]


def _draft(units: list[str]) -> Draft:
    return Draft(hooks=units[:HOOKS], body=" ".join(units[HOOKS:-1]), cta=units[-1])


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", text.lower()).strip()


def _find(units: list[str], text: str) -> int | None:
    """Index of the unit that contains `text` (or is contained in it)."""
    t = _norm(text)
    for i, u in enumerate(units):
        n = _norm(u)
        if t and n and (t in n or n in t):
            return i
    return None


def _context(units: list[str], i: int) -> tuple[str, str]:
    """Sentence before and after unit i. Hooks are alternatives: they lead into the first body sentence."""
    if i < HOOKS:
        return "", units[HOOKS]
    before = units[i - 1] if i > HOOKS else units[0]
    after = units[i + 1] if i + 1 < len(units) else ""
    return before, after


def _repair(brand: Brand, topic: str, facts: str, c: Candidate, report: Report = noop) -> Candidate:
    """Rewrite only the sentences the Reviewer named; fall back to a whole-draft edit for length."""
    units = _units(c.draft)
    problems: dict[int, list[str]] = {}
    for w in c.review.real_weaknesses():
        i = _find(units, w.quote)
        if i is not None:
            problems.setdefault(i, []).append(w.problem)

    if c.length_note or not problems:  # nothing to point at: one whole-draft edit
        return _try(brand, topic, facts, c.structure, c.feedback(), previous=c.draft, report=report)

    report(f"Rewriting {len(problems)} weak sentence(s)")
    new_units = list(units)
    for i, notes in problems.items():
        before, after = _context(units, i)
        new_units[i] = rewrite_sentence(brand, topic, facts, before, units[i], after, notes)
    # a rewritten sentence can repeat its neighbour
    draft = remove_duplicates(_draft(new_units), strict=brand.script_mode == "story")
    return _reviewed(brand, topic, facts, c.structure, draft, report)


def _remove_wrong(c: Candidate) -> list[str]:
    """Remove body/CTA sentences that contradict the research. Returns the removed sentences."""
    removed, units = [], _units(c.draft)
    for s in c.wrong_sentences:
        if s in c.draft.hooks:
            continue  # hooks are handled by choosing another accurate hook
        for i in range(HOOKS, len(units)):
            if _norm(s) and _norm(s) in _norm(units[i]):
                units[i] = units[i].replace(s, "").strip()
                removed.append(s)
                break
    if removed:
        body = [u for u in units[HOOKS:-1] if u]
        c.draft = Draft(hooks=units[:HOOKS], body=" ".join(body), cta=units[-1])
    return removed


def make_script(brand: Brand, topic: str, facts: str, report: Report = noop, notes: str = "",
                previous: Draft | None = None, structure: str | None = None) -> ScriptResult:
    """`facts` is empty for brands without research (fiction).
    `notes`: the human's instructions for a redo. With a `previous` draft, that draft is edited to follow them
    (keeps what was good); without one, new drafts are written with the notes as guidance."""
    guide = [f"The creator asks: {line.strip()}" for line in notes.splitlines() if line.strip()]
    if previous is not None and guide:
        report("Revising the script with your notes")
        attempts = [_try(brand, topic, facts, structure or brand.script_structures[0], guide, previous, report)]
    else:
        attempts = [_try(brand, topic, facts, s, guide or None, report=report) for s in brand.script_structures[:2]]
    best = _best(attempts)
    report(f"Best so far: {best.review.average():.1f} · {best.structure.replace('_', ' ')}")
    for _ in range(MAX_REPAIRS):
        reasons = best.review.fail_reasons(brand.min_quality_score) + ([best.length_note] if best.length_note else [])
        if not reasons:
            break
        report(f"Improving it because {'; '.join(reasons)}")
        repaired = _repair(brand, topic, facts, best, report)
        attempts.append(repaired)
        if repaired.review.average() < best.review.average():  # worse: keep the best and stop trying
            report(f"Kept the {best.review.average():.1f} version (the rewrite scored {repaired.review.average():.1f})")
            break
        best = repaired

    removed: list[str] = []
    if brand.pipeline.fact_check:
        report("Fact-checking every sentence")
        _fact_check(brand, facts, best)  # one thinking call
        removed = _remove_wrong(best)
        if removed:
            report(f"Removed {len(removed)} sentence(s) that contradict the research")
    else:
        best.good_hooks = list(range(1, HOOKS + 1))  # fiction: every hook is allowed

    flags = []
    if reasons := best.review.fail_reasons(brand.min_quality_score):
        flags.append(f"Review failed ({', '.join(reasons)}): "
                     + "; ".join(w.problem for w in best.review.real_weaknesses()[:3]))
    if best.length_note:
        flags.append(best.length_note)
    if removed:
        flags.append(f"{len(removed)} sentence(s) removed because they contradicted the research")
    if not best.good_hooks:
        flags.append("No accurate hook: the video starts with the first body sentence")
    return ScriptResult("needs_attention" if flags else "passed", best, attempts, flags, removed)
