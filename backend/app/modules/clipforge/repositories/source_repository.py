from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.modules.clipforge.models import Source


class SourceRepository:
    """Data access for ClipForge sources. Each call uses its own short session (downloads take minutes)."""

    def __init__(self, sessions: sessionmaker[Session]):
        self._sessions = sessions

    def get(self, source_id: int) -> Source | None:
        with self._sessions() as db:
            return db.get(Source, source_id)

    def find(self) -> list[Source]:
        """Newest first."""
        with self._sessions() as db:
            return list(db.scalars(select(Source).order_by(Source.id.desc())))

    def save(self, source: Source) -> Source:
        """Insert or update."""
        with self._sessions() as db:
            source = db.merge(source)
            db.commit()
            return source
