from datetime import datetime
from enum import StrEnum

from sqlalchemy import JSON, DateTime, Float, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import Base


class TopicStatus(StrEnum):
    NEW = "new"    # can be picked
    USED = "used"  # a job was made for it


class Topic(Base):
    """A video idea for one brand."""
    __tablename__ = "topics"
    __table_args__ = (UniqueConstraint("brand", "title"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    brand: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(200))
    angle: Mapped[str] = mapped_column(String(500), default="")
    scores: Mapped[dict] = mapped_column(JSON, default=dict)
    score: Mapped[float] = mapped_column(Float, default=0)
    status: Mapped[str] = mapped_column(String(16), default=TopicStatus.NEW)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
