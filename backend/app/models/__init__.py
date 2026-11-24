"""SQLAlchemy tables. Import all here so Alembic sees them."""
from app.models.base import Base
from app.models.job import Job, JobStatus
from app.models.source import Source, SourceStatus
from app.models.topic import Topic, TopicStatus

__all__ = ["Base", "Job", "JobStatus", "Source", "SourceStatus", "Topic", "TopicStatus"]
