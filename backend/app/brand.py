"""Brand config: load and validate a brand YAML file."""
from typing import Literal

import yaml
from pydantic import BaseModel, Field, field_validator

from app.config import settings
from app.services.render import MOTIONS


class Voice(BaseModel):
    engine: Literal["kokoro", "chatterbox"] = "kokoro"
    voice: str = "af_heart"  # kokoro voice name
    speed: float = 1.0
    voice_ref: str | None = None  # chatterbox: reference clip to clone
    exaggeration: float = 0.5  # chatterbox: emotion intensity


class Images(BaseModel):
    checkpoint: str
    lora: str | None = None
    lora_weight: float = 1.0
    style: str  # added to every image prompt
    negative: str = ""
    steps: int = 30
    cfg: float = 4.5
    sampler: str = "dpmpp_2m"
    scheduler: str = "karras"


class Look(BaseModel):
    motions: list[str] = Field(default_factory=lambda: list(MOTIONS))
    transitions: list[str] = Field(default_factory=lambda: ["fade"])  # FFmpeg xfade names
    transition_seconds: float = 0.4
    caption_font_size: int = 96
    caption_max_words: int = 3

    @field_validator("motions")
    @classmethod
    def known_motions(cls, v: list[str]) -> list[str]:
        unknown = set(v) - set(MOTIONS)
        if unknown:
            raise ValueError(f"unknown motions {sorted(unknown)}; allowed: {sorted(MOTIONS)}")
        return v


class Brand(BaseModel):
    slug: str
    name: str
    niche: str
    language: str = "en"
    tone: str
    format: Literal["short", "long"] = "short"
    duration: int = Field(60, gt=0)  # seconds
    voice: Voice = Voice()
    images: Images
    look: Look = Look()
    prompts: str  # folder in backend/prompts/
    min_quality_score: float = Field(7, ge=1, le=10)

    @property
    def size(self) -> tuple[int, int]:
        return (1080, 1920) if self.format == "short" else (1920, 1080)


def load_brand(slug: str) -> Brand:
    path = settings.brands_dir / f"{slug}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Brand config not found: {path}")
    return Brand.model_validate(yaml.safe_load(path.read_text()))


def list_brands() -> list[str]:
    return sorted(p.stem for p in settings.brands_dir.glob("*.yaml"))
