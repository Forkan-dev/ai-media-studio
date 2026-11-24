from datetime import datetime

from pydantic import BaseModel, ConfigDict, model_validator


class SourceCreate(BaseModel):
    """Exactly one: a YouTube URL or a path to a video file on this machine."""
    url: str | None = None
    file: str | None = None

    @model_validator(mode="after")
    def one_input(self):
        if bool(self.url) == bool(self.file):
            raise ValueError("give either url or file")
        return self


class SourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    url: str
    file: str
    title: str
    channel: str
    duration: float
    status: str
    error: str
    created_at: datetime
