"""Database connection only. Tables: app/models. Table changes: Alembic migrations (alembic/)."""
from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

settings.storage_dir.mkdir(parents=True, exist_ok=True)
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(engine, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    """FastAPI dependency."""
    with SessionLocal() as db:
        yield db
