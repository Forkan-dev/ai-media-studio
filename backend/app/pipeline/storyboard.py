"""Storyboard: script -> scenes. Code splits scenes and picks motion/transition; the LLM writes image prompts."""
import random
import re

from pydantic import BaseModel, Field, ValidationError, create_model

from app.brand import Brand
from app.pipeline.fact_check import sentences
from app.prompts import render
from app.clients.llm import chat_json

MIN_SCENE_WORDS = 6  # shorter sentences are joined with the next one


class Scene(BaseModel):
    narration: str
    image_prompt: str  # subject only; the brand style is added at image generation
    motion: str
    transition: str  # transition INTO this scene (unused for the first scene)


class Storyboard(BaseModel):
    style: str  # image style name from the brand config; the whole video uses it
    scenes: list[Scene]


MAX_TRIES = 3


def _prompts_schema(count: int) -> type[BaseModel]:
    """Schema that forces exactly `count` prompts (Ollama enforces min/max items)."""
    return create_model("ImagePrompts", image_prompts=(list[str], Field(min_length=count, max_length=count)))


def split_scenes(text: str) -> list[str]:
    """One sentence per scene; very short sentences are joined with the next."""
    scenes, pending = [], ""
    for s in sentences(text):
        pending = f"{pending} {s}".strip()
        if len(pending.split()) >= MIN_SCENE_WORDS:
            scenes.append(pending)
            pending = ""
    if pending:  # leftover short tail joins the last scene
        scenes[-1:] = [f"{scenes[-1]} {pending}"] if scenes else [pending]
    return scenes


CHARACTER_TOKEN = "MAIN_CHARACTER"
# phrases the model sometimes writes instead of the token (only "the ...": "a/small ..." are background figures)
CHARACTER_PHRASES = r"\bthe (?:main character|protagonist)\b"


def insert_character(prompt: str, character: str) -> str:
    """The code, not the LLM, writes the full character description into every prompt."""
    prompt = re.sub(CHARACTER_PHRASES, CHARACTER_TOKEN, prompt, flags=re.IGNORECASE)
    return prompt.replace(CHARACTER_TOKEN, character)


def no_text(prompt: str) -> str:
    """Remove quoted text ('Subscribe', labeled "X"): SDXL cannot draw text."""
    cleaned = re.sub(r"\s*(?:labeled|labelled|reading|that says|saying|with the words?)?\s*['\"][^'\"]+['\"]",
                     "", prompt)
    return re.sub(r"\s{2,}", " ", cleaned).strip()


def _pick_no_repeat(options: list[str], count: int) -> list[str]:
    picks: list[str] = []
    for _ in range(count):
        choices = [o for o in options if not picks or o != picks[-1]] or options
        picks.append(random.choice(choices))
    return picks


def make_storyboard(brand: Brand, topic: str, narration: str, style: str | None = None) -> Storyboard:
    style = style or brand.images.default_style
    lines = split_scenes(narration)
    numbered = "\n".join(f"{i}. {line}" for i, line in enumerate(lines, 1))
    st = brand.images.style(style)
    system = render(brand.prompts, "storyboard", brand_name=brand.name, niche=brand.niche,
                    topic=topic, scenes=numbered, others=st.others)
    schema = _prompts_schema(len(lines))
    for attempt in range(1, MAX_TRIES + 1):
        try:
            prompts = chat_json(system, f"Write all {len(lines)} image descriptions now.", schema,
                                temperature=0.7).image_prompts
            break
        except ValidationError:
            if attempt == MAX_TRIES:
                raise

    motions = _pick_no_repeat(brand.look.motions, len(lines))
    transitions = _pick_no_repeat(brand.look.transitions, len(lines))
    return Storyboard(style=style, scenes=[
        Scene(narration=n, image_prompt=insert_character(no_text(p), st.character), motion=m, transition=t)
        for n, p, m, t in zip(lines, prompts, motions, transitions)
    ])
