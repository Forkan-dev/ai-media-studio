from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class JobCreate(BaseModel):
    brand: str
    topic: str = Field(min_length=2, max_length=200)
    style: str | None = None  # default: the brand's default style
    auto: bool = False  # True: no pauses at gates


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    brand: str
    topic: str
    style: str
    stage: str
    status: str
    flags: dict[str, list[str]]
    progress: list[str]
    auto: bool
    action: dict | None
    error: str
    created_at: datetime
    updated_at: datetime


class RedoRequest(BaseModel):
    notes: str = ""  # instructions for this run, e.g. "make the hook shorter" (research and script use them)


class ScriptEdit(BaseModel):
    text: str = Field(min_length=20)


class ImageRedo(BaseModel):
    prompt: str | None = None  # edited image prompt; None = draw the same prompt again
    style: str | None = None  # another image style of the brand for this scene; None = keep


class VoiceRedo(BaseModel):
    text: str | None = None  # edited narration; None = record the same words again


class ThumbnailText(BaseModel):
    text: str = Field(min_length=1, max_length=40)
