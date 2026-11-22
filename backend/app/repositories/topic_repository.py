from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.models import Topic, TopicStatus


class TopicRepository:
    """Data access for topics. Each call uses its own short session."""

    def __init__(self, sessions: sessionmaker[Session]):
        self._sessions = sessions

    def find(self, brand: str, status: TopicStatus | None = None) -> list[Topic]:
        """Best score first."""
        query = select(Topic).where(Topic.brand == brand).order_by(Topic.score.desc())
        if status:
            query = query.where(Topic.status == status)
        with self._sessions() as db:
            return list(db.scalars(query))

    def get_by_title(self, brand: str, title: str) -> Topic | None:
        with self._sessions() as db:
            return db.scalar(select(Topic).where(Topic.brand == brand, Topic.title == title))

    def add_all(self, topics: list[Topic]) -> None:
        with self._sessions() as db:
            db.add_all(topics)
            db.commit()

    def save(self, topic: Topic) -> Topic:
        with self._sessions() as db:
            topic = db.merge(topic)
            db.commit()
            return topic
