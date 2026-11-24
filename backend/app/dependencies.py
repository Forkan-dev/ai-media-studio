"""Builds the services with their dependencies. Used by the API (FastAPI Depends) and the CLI."""
from app.brand import Brand
from app.config import settings
from app.db import SessionLocal
from app.repositories import JobRepository, SourceRepository, TopicRepository
from app.services.brand_service import BrandService
from app.services.job_service import JobService
from app.services.source_service import SourceService
from app.services.stages import video_stages
from app.services.topic_service import TopicService


def brand_service() -> BrandService:
    return BrandService(settings.brands_dir)


def brand(slug: str) -> Brand:
    """One brand (NotFoundError -> 404)."""
    return brand_service().get(slug)


def topic_service() -> TopicService:
    return TopicService(TopicRepository(SessionLocal), settings.storage_dir / "videos")


def job_service() -> JobService:
    return JobService(JobRepository(SessionLocal), topic_service(), video_stages)


def source_service() -> SourceService:
    return SourceService(SourceRepository(SessionLocal), settings.storage_dir / "clipforge")
