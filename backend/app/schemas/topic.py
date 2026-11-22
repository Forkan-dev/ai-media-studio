from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TopicOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    brand: str
    title: str
    angle: str
    scores: dict[str, int]
    score: float
    status: str
    created_at: datetime
