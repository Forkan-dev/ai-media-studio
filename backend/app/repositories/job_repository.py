from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.models import Job


class JobRepository:
    """Data access for jobs. Each call uses its own short session (stages run for minutes)."""

    def __init__(self, sessions: sessionmaker[Session]):
        self._sessions = sessions

    def get(self, job_id: int) -> Job | None:
        with self._sessions() as db:
            return db.get(Job, job_id)

    def find(self, brand: str | None = None) -> list[Job]:
        """Newest first."""
        query = select(Job).order_by(Job.id.desc())
        if brand:
            query = query.where(Job.brand == brand)
        with self._sessions() as db:
            return list(db.scalars(query))

    def save(self, job: Job) -> Job:
        """Insert or update."""
        with self._sessions() as db:
            job = db.merge(job)
            db.commit()
            return job
