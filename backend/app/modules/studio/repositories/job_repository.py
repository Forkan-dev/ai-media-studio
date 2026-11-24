from sqlalchemy import select, update
from sqlalchemy.orm import Session, sessionmaker

from app.modules.studio.models import Job, JobStatus


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

    def claim(self, job_id: int) -> bool:
        """queued -> running, atomically: only one worker (or CLI) gets the job."""
        with self._sessions() as db:
            result = db.execute(update(Job).where(Job.id == job_id, Job.status == JobStatus.QUEUED)
                                .values(status=JobStatus.RUNNING))
            db.commit()
            return result.rowcount == 1

    def oldest_queued(self) -> Job | None:
        with self._sessions() as db:
            return db.scalar(select(Job).where(Job.status == JobStatus.QUEUED).order_by(Job.updated_at))

    def save(self, job: Job) -> Job:
        """Insert or update."""
        with self._sessions() as db:
            job = db.merge(job)
            db.commit()
            return job
