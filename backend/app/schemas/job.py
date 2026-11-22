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
    error: str
    created_at: datetime
    updated_at: datetime
