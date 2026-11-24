from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class SourceStatus(StrEnum):
    PREPARING = "preparing"  # downloading + extracting audio
    READY = "ready"
    FAILED = "failed"


class Source(Base):
    """ClipForge: one long video (stream / gameplay) that clips are cut from. Files are in `folder`."""
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    url: Mapped[str] = mapped_column(String(500), default="")  # YouTube URL, or ""
    file: Mapped[str] = mapped_column(String(500), default="")  # local video path, or ""
    title: Mapped[str] = mapped_column(String(300), default="")
    channel: Mapped[str] = mapped_column(String(200), default="")
    duration: Mapped[float] = mapped_column(Float, default=0)  # seconds
    folder: Mapped[str] = mapped_column(String(500), default="")
    status: Mapped[str] = mapped_column(String(16), default=SourceStatus.PREPARING)
    error: Mapped[str] = mapped_column(String(2000), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
