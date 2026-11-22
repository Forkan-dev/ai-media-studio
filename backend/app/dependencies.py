"""Builds the services with their dependencies. Used by the API (FastAPI Depends) and the CLI."""
from app.brand import Brand, load_brand
from app.config import settings
from app.db import SessionLocal
from app.repositories import JobRepository, TopicRepository
from app.services.errors import NotFoundError
from app.services.job_service import JobService
from app.services.stages import video_stages
from app.services.topic_service import TopicService


def brand(slug: str) -> Brand:
    try:
        return load_brand(slug)
    except FileNotFoundError as e:
        raise NotFoundError(f"No brand {slug}") from e


def topic_service() -> TopicService:
    return TopicService(TopicRepository(SessionLocal), settings.storage_dir / "videos")


def job_service() -> JobService:
    return JobService(JobRepository(SessionLocal), topic_service(), video_stages())
