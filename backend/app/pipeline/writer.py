"""Writer role: topic + research -> 3 hooks + script draft."""
import re
from difflib import SequenceMatcher

from pydantic import BaseModel, Field

from app.brand import Brand
from app.config import settings
from app.prompts import render
from app.services.llm import chat_json

WORDS_PER_SECOND = 2.5  # typical narration pace
WORDS_PER_SENTENCE = 13  # measured for Qwen3.5; small models follow a sentence count better than a word count


class Draft(BaseModel):
    hooks: list[str] = Field(min_length=3, max_length=3)
    body: str
    cta: str


DUPLICATE_SIMILARITY = 0.7  # sentences this similar say the same thing


def _strip_repeated_hook(d: Draft) -> Draft:
    """The model sometimes starts the body with a hook again; remove that repeat."""
    for hook in d.hooks:
        if d.body.lower().startswith(hook.lower()):
            return d.model_copy(update={"body": d.body[len(hook):].lstrip()})
    return d


def remove_duplicates(d: Draft) -> Draft:
    """Remove body sentences that repeat an earlier sentence (exact or near-duplicate). Code, no model."""
    from app.pipeline.fact_check import sentences  # local import: fact_check imports nothing from here

    def norm(s: str) -> str:
        return re.sub(r"[^a-z0-9 ]", "", s.lower())

    kept: list[str] = []
    for s in sentences(d.body):
        if not any(SequenceMatcher(None, norm(s), norm(k)).ratio() >= DUPLICATE_SIMILARITY for k in kept):
            kept.append(s)
    return d.model_copy(update={"body": " ".join(kept)})


def _example(brand: Brand, topic: str) -> str:
    """Optional style example (prompts/<brand>/writer_example.md, first line "Topic: ...").
    Skipped when it is about the same topic, so the Writer can never copy it."""
    path = settings.prompts_dir / brand.prompts / "writer_example.md"
    if not path.exists():
        return ""
    text = path.read_text()
    first = text.splitlines()[0]
    example_topic = first.removeprefix("Topic:").strip().lower() if first.startswith("Topic:") else ""
    words = lambda s: set(re.findall(r"[a-z]{4,}", s.lower())) - {"effect", "the"}
    if example_topic and words(example_topic) & words(topic):
        return ""
    return text


def _as_text(d: Draft) -> str:
    hooks = "\n".join(f"Hook {i}: {h}" for i, h in enumerate(d.hooks, 1))
    return f"{hooks}\nBody: {d.body}\nCTA: {d.cta}"


def write_draft(
    brand: Brand, topic: str, facts: str, structure: str = "story",
    feedback: list[str] | None = None, previous: Draft | None = None,
) -> Draft:
    """First draft when `previous` is None; otherwise an EDIT of `previous` that fixes `feedback`."""
    words = round(brand.duration * WORDS_PER_SECOND)
    system = render(
        brand.prompts, "writer",
        brand_name=brand.name, niche=brand.niche, tone=brand.tone,
        duration=brand.duration, word_count=words, body_sentences=round(words / WORDS_PER_SENTENCE) - 2,
        topic=topic, structure=structure, facts=facts,
        feedback="\n".join(f"- {f}" for f in feedback) if feedback else "None, this is the first draft.",
        previous=_as_text(previous) if previous else "None, this is the first draft.",
        example=_example(brand, topic),
    )
    temperature = 0.4 if previous else 0.7  # edits stay close to the draft; first drafts are creative
    task = "Edit the previous draft now." if previous else "Write the script now."
    return remove_duplicates(_strip_repeated_hook(chat_json(system, task, Draft, temperature=temperature)))


class _Sentence(BaseModel):
    sentence: str


def rewrite_sentence(
    brand: Brand, topic: str, facts: str, before: str, sentence: str, after: str, problems: list[str]
) -> str:
    """Replace ONE sentence; the rest of the script stays frozen."""
    system = render(
        brand.prompts, "sentence_fix",
        brand_name=brand.name, niche=brand.niche, tone=brand.tone, topic=topic, facts=facts,
        before=before or "(start of script)", sentence=sentence, after=after or "(end of script)",
        problems="\n".join(f"- {p}" for p in problems),
    )
    return chat_json(system, "Write the new sentence now.", _Sentence, temperature=0.5).sentence.strip()
