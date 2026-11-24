"""Brand config: load and validate a brand YAML file."""
from typing import Literal

from pathlib import Path

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.config import settings
from app.core.clients.render import MOTIONS


class Voice(BaseModel):
    engine: Literal["kokoro", "chatterbox"] = "kokoro"
    voice: str = "af_heart"  # kokoro voice name
    speed: float = 1.0
    voice_ref: str | None = None  # chatterbox: reference clip to clone
    exaggeration: float = 0.5  # chatterbox: emotion intensity when a scene has no emotion
    cfg_weight: float = 0.5  # chatterbox: pace; lower = slower, more deliberate
    scene_emotions: bool = False  # chatterbox: each scene's emotion sets the intensity


class ImageStyle(BaseModel):
    """A selectable look. Add a new block in the brand YAML to add a style: no code change."""
    lora_weight: float = 1.0
    character: str  # main character; the code inserts it into every scene prompt
    others: str = "simple background figures in the same style"  # other people in scenes
    style: str  # added to every image prompt
    negative: str = ""


class Images(BaseModel):
    checkpoint: str
    lora: str | None = None
    default_style: str
    styles: dict[str, ImageStyle]
    steps: int = 30
    cfg: float = 4.5
    sampler: str = "dpmpp_2m"
    scheduler: str = "karras"

    @model_validator(mode="after")
    def default_exists(self):
        if self.default_style not in self.styles:
            raise ValueError(f"default_style '{self.default_style}' not in styles {sorted(self.styles)}")
        return self

    def style(self, name: str | None = None) -> ImageStyle:
        name = name or self.default_style
        if name not in self.styles:
            raise ValueError(f"unknown image style '{name}'; available: {sorted(self.styles)}")
        return self.styles[name]


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


class Pipeline(BaseModel):
    """Which steps this brand uses. Fact brands research and fact-check; fiction brands do neither."""
    research: bool = True  # web research per video (and web search for topic ideas)
    fact_check: bool = True  # check every sentence against the research


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
    pipeline: Pipeline = Pipeline()
    # facts: research + fact-check; story: fiction. Picks the preset prompts (prompts/presets/<preset>/)
    preset: Literal["facts", "story"] = "facts"
    prompts: str | None = None  # optional folder in backend/prompts/ that overrides single preset prompts
    min_quality_score: float = Field(7, ge=1, le=10)
    # Reviewer criteria that count for this brand. A comedy brand adds "humor".
    review_criteria: list[str] = Field(default_factory=lambda: [
        "hook", "accuracy", "clarity", "logic", "relatability", "pacing", "originality"])
    review_model: str | None = None  # Ollama model for the Reviewer; None = the default LLM
    script_structures: list[str] = Field(default_factory=lambda: ["story", "myth_vs_fact"], min_length=1)
    # facts: write from research. story: plan the story first (rule, beats, punchline), stricter repeat removal
    script_mode: Literal["facts", "story"] = "facts"
    # how topic ideas are scored (1-10 each); the topics prompt explains each one
    topic_criteria: list[str] = Field(default_factory=lambda: ["curiosity", "relatable", "evidence", "visual"],
                                      min_length=1)

    @model_validator(mode="after")
    def known_criteria(self):
        from app.modules.studio.pipeline.reviewer import CRITERIA  # local import: reviewer imports Brand
        unknown = set(self.review_criteria) - set(CRITERIA)
        if unknown:
            raise ValueError(f"unknown review_criteria {sorted(unknown)}; allowed: {list(CRITERIA)}")
        if self.pipeline.fact_check and "accuracy" not in self.review_criteria:
            raise ValueError("a brand with fact_check must include 'accuracy' in review_criteria")
        return self

    @property
    def prompt_folders(self) -> list[str]:
        """Where prompt files are looked up, in order: own overrides, preset, shared default."""
        return [*([self.prompts] if self.prompts else []), f"presets/{self.preset}", "default"]

    @property
    def size(self) -> tuple[int, int]:
        return (1080, 1920) if self.format == "short" else (1920, 1080)


def read_brand_yaml(path: Path) -> Brand:
    """A brand from a YAML file (import only; brands live in the DB, see BrandService)."""
    return Brand.model_validate(yaml.safe_load(path.read_text()))


def load_brand(slug: str) -> Brand:
    """Scripts/tests only: the YAML file brands/<slug>.yaml. The app uses BrandService (DB)."""
    path = settings.brands_dir / f"{slug}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Brand config not found: {path}")
    return read_brand_yaml(path)
