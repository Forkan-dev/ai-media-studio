"""Builds ClipForge services with their dependencies. Used by the API (FastAPI Depends) and the CLI."""
from app.core.config import settings
from app.core.db import SessionLocal
from app.modules.clipforge.repositories import SourceRepository
from app.modules.clipforge.services.source_service import SourceService


def source_service() -> SourceService:
    return SourceService(SourceRepository(SessionLocal), settings.storage_dir / "clipforge")
