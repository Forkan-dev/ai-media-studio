"""Builds the services with their dependencies. Used by the API (FastAPI Depends) and the CLI."""
from app.modules.studio.brand import Brand
from app.core.config import settings
from app.core.db import SessionLocal
from app.modules.studio.repositories import BrandRepository, JobRepository, TopicRepository
from app.modules.studio.services.artifact_service import JobArtifactService
from app.modules.studio.services.brand_service import BrandService
from app.modules.studio.services.job_service import JobService
from app.modules.studio.services.stages import video_stages
from app.modules.studio.services.topic_service import TopicService
from app.modules.studio.services.voice_service import VoiceService


def brand_service() -> BrandService:
    return BrandService(BrandRepository(SessionLocal), settings.presets_dir)


def brand(slug: str) -> Brand:
    """One brand (NotFoundError -> 404)."""
    return brand_service().get(slug)


def topic_service() -> TopicService:
    return TopicService(TopicRepository(SessionLocal), settings.storage_dir / "videos")


def job_service() -> JobService:
    return JobService(JobRepository(SessionLocal), topic_service(), video_stages, brand)


def artifact_service() -> JobArtifactService:
    return JobArtifactService(job_service())


def voice_service() -> VoiceService:
    return VoiceService(settings.storage_dir)
