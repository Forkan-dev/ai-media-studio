"""Database (SQLite via SQLAlchemy). Tables are created on first use."""
from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, String, UniqueConstraint, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from app.config import settings

settings.storage_dir.mkdir(parents=True, exist_ok=True)
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class Topic(Base):
    """A video idea for one brand. status: new (can be picked) | used (a video was made)."""
    __tablename__ = "topics"
    __table_args__ = (UniqueConstraint("brand", "title"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    brand: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(200))
    angle: Mapped[str] = mapped_column(String(500), default="")
    scores: Mapped[dict] = mapped_column(JSON, default=dict)
    score: Mapped[float] = mapped_column(Float, default=0)
    status: Mapped[str] = mapped_column(String(16), default="new")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


def session() -> Session:
    Base.metadata.create_all(engine)  # no-op when the tables exist
    return SessionLocal()


def get_db():
    """FastAPI dependency."""
    with session() as db:
        yield db
