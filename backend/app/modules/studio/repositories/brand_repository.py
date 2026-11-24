from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.modules.studio.models import BrandRecord


class BrandRepository:
    """Data access for brands."""

    def __init__(self, sessions: sessionmaker[Session]):
        self._sessions = sessions

    def get(self, slug: str) -> BrandRecord | None:
        with self._sessions() as db:
            return db.scalar(select(BrandRecord).where(BrandRecord.slug == slug))

    def find(self) -> list[BrandRecord]:
        with self._sessions() as db:
            return list(db.scalars(select(BrandRecord).order_by(BrandRecord.slug)))

    def save(self, record: BrandRecord) -> BrandRecord:
        """Insert or update."""
        with self._sessions() as db:
            record = db.merge(record)
            db.commit()
            return record
