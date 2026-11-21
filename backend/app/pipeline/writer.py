"""Writer role: topic + research -> 3 hooks + script draft."""
from pydantic import BaseModel, Field

from app.brand import Brand
from app.prompts import render
from app.services.llm import chat_json

WORDS_PER_SECOND = 2.5  # typical narration pace
WORDS_PER_SENTENCE = 10  # small models follow a sentence count better than a word count


class Draft(BaseModel):
    hooks: list[str] = Field(min_length=3, max_length=3)
    body: str
    cta: str


def _strip_repeated_hook(d: Draft) -> Draft:
    """The model sometimes starts the body with a hook again; remove that repeat."""
    for hook in d.hooks:
        if d.body.lower().startswith(hook.lower()):
            return d.model_copy(update={"body": d.body[len(hook):].lstrip()})
    return d


def write_draft(
    brand: Brand, topic: str, facts: str, structure: str = "story", feedback: list[str] | None = None
) -> Draft:
    words = round(brand.duration * WORDS_PER_SECOND)
    system = render(
        brand.prompts, "writer",
        brand_name=brand.name, niche=brand.niche, tone=brand.tone,
        duration=brand.duration, word_count=words, body_sentences=round(words / WORDS_PER_SENTENCE) - 2,
        topic=topic, structure=structure, facts=facts,
        feedback="\n".join(f"- {f}" for f in feedback) if feedback else "None, this is the first draft.",
    )
    return _strip_repeated_hook(chat_json(system, "Write the script now.", Draft, temperature=0.9))
