from datetime import datetime
from enum import StrEnum

from sqlalchemy import JSON, Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import Base


class JobStatus(StrEnum):
    QUEUED = "queued"  # waiting for the worker to pick it up
    RUNNING = "running"  # the worker is running its stage
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
    status: Mapped[str] = mapped_column(String(16), default=JobStatus.QUEUED)
    flags: Mapped[dict] = mapped_column(JSON, default=dict)  # stage -> problems for the human to check
    progress: Mapped[list] = mapped_column(JSON, default=list)  # live lines of the running stage, for the UI
    auto: Mapped[bool] = mapped_column(Boolean, default=False)  # True: no pauses at gates until the end
    action: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # queued change at the gate (one image...)
    error: Mapped[str] = mapped_column(String(2000), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
