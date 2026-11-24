"""Storyboard: script -> scenes. Code splits scenes and picks motion/transition; the LLM writes image prompts."""
import random
import re
from typing import Literal

from pydantic import BaseModel, Field, ValidationError, create_model

from app.modules.studio.brand import Brand
from app.modules.studio.pipeline.fact_check import sentences
from app.core.prompts import render
from app.core.clients.llm import chat_json

MIN_SCENE_WORDS = 6  # shorter sentences are joined with the next one
MAX_CHARACTERS = 4

Emotion = Literal["calm", "curious", "happy", "excited", "confused", "nervous", "panicked", "shocked", "sad"]


class Scene(BaseModel):
    narration: str
    image_prompt: str  # subject only; the brand style is added at image generation
    motion: str
    transition: str  # transition INTO this scene (unused for the first scene)
    emotion: Emotion = "calm"  # how the line is spoken (voice intensity)
    style: str | None = None  # this scene's image style; None = the storyboard's style


class Storyboard(BaseModel):
    style: str  # image style name from the brand config; the default for every scene
    scenes: list[Scene]

    def style_of(self, scene: Scene) -> str:
        return scene.style or self.style


MAX_TRIES = 3


class Character(BaseModel):
    """A story character besides the main one, described once so it looks the same in every scene."""
    name: str = Field(description="one ALL CAPS word used as a token in the prompts, e.g. BOSS")
    look: str = Field(description="what the character looks like: body, face, hair, clothes")


class Shot(BaseModel):
    image_prompt: str
    emotion: Emotion


def _shots_schema(count: int) -> type[BaseModel]:
    """Schema that forces exactly `count` shots (Ollama enforces min/max items)."""
    return create_model(
        "Shots",
        characters=(list[Character], Field(max_length=MAX_CHARACTERS)),
        shots=(list[Shot], Field(min_length=count, max_length=count)),
    )


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


def insert_character(prompt: str, character: str, others: list[Character] | None = None) -> str:
    """The code, not the LLM, writes the full character descriptions into every prompt."""
    prompt = re.sub(CHARACTER_PHRASES, CHARACTER_TOKEN, prompt, flags=re.IGNORECASE)
    for c in others or []:
        if c.name.isupper() and c.name != CHARACTER_TOKEN:
            prompt = re.sub(rf"\b{re.escape(c.name)}\b", c.look, prompt)
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
    system = render(brand.prompt_folders, "storyboard", brand_name=brand.name, niche=brand.niche,
                    topic=topic, scenes=numbered, others=st.others)
    schema = _shots_schema(len(lines))
    for attempt in range(1, MAX_TRIES + 1):
        try:
            result = chat_json(system, f"Write the characters and all {len(lines)} shots now.", schema,
                               temperature=0.7)
            break
        except ValidationError:
            if attempt == MAX_TRIES:
                raise

    motions = _pick_no_repeat(brand.look.motions, len(lines))
    transitions = _pick_no_repeat(brand.look.transitions, len(lines))
    return Storyboard(style=style, scenes=[
        Scene(narration=n, image_prompt=insert_character(no_text(shot.image_prompt), st.character,
                                                         result.characters),
              motion=m, transition=t, emotion=shot.emotion)
        for n, shot, m, t in zip(lines, result.shots, motions, transitions)
    ])
