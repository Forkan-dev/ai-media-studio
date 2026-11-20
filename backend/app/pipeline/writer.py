"""Writer role: topic -> 3 hooks + script draft."""
from pydantic import BaseModel, Field

from app.brand import Brand
from app.prompts import render
from app.services.llm import chat_json

WORDS_PER_SECOND = 2.5  # typical narration pace


class Draft(BaseModel):
    hooks: list[str] = Field(min_length=3, max_length=3)
    body: str
    cta: str


def write_draft(brand: Brand, topic: str, structure: str = "story") -> Draft:
    system = render(
        brand.prompts, "writer",
        brand_name=brand.name, niche=brand.niche, tone=brand.tone,
        duration=brand.duration, word_count=round(brand.duration * WORDS_PER_SECOND),
        topic=topic, structure=structure,
    )
    return chat_json(system, "Write the script now.", Draft, temperature=0.9)
