from datetime import datetime
from enum import StrEnum

from sqlalchemy import JSON, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class JobStatus(StrEnum):
    RUNNING = "running"
    WAITING = "waiting"  # paused at a gate for human approval
    FAILED = "failed"
    DONE = "done"


class Job(Base):
    """One video being made. `stage` is the step running now or waiting for approval.
    Step outputs are files in `folder`."""
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    brand: Mapped[str] = mapped_column(String(64), index=True)
    topic: Mapped[str] = mapped_column(String(200))
    style: Mapped[str] = mapped_column(String(64))
    folder: Mapped[str] = mapped_column(String(500))
    stage: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(16), default=JobStatus.RUNNING)
    flags: Mapped[dict] = mapped_column(JSON, default=dict)  # stage -> problems for the human to check
    error: Mapped[str] = mapped_column(String(2000), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
