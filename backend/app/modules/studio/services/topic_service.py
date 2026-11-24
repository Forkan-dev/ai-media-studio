"""Topic business logic: discover new ideas, list them, mark them used."""
from pathlib import Path

from app.modules.studio.brand import Brand
from app.modules.studio.models import Topic, TopicStatus
from app.modules.studio.pipeline.topics import find_ideas, is_known, topic_key
from app.modules.studio.repositories import TopicRepository


class TopicService:
    def __init__(self, topics: TopicRepository, videos_dir: Path):
        self._topics = topics
        self._videos_dir = videos_dir

    def list_new(self, brand: Brand) -> list[Topic]:
        """Topics that can be picked, best first."""
        return self._topics.find(brand.slug, TopicStatus.NEW)

    def discover(self, brand: Brand) -> list[Topic]:
        """Find new ideas on the web and save them. Known topics and made videos are skipped."""
        existing = [t.title for t in self._topics.find(brand.slug)]
        known = [topic_key(t) for t in existing] + self._made_videos(brand)
        new: list[Topic] = []
        for idea in find_ideas(brand, existing):
            if is_known(idea.title, known):
                continue
            known.append(topic_key(idea.title))
            new.append(Topic(brand=brand.slug, title=idea.title.strip(), angle=idea.angle.strip(),
                             scores=idea.scores, score=idea.score()))
        self._topics.add_all(new)
        return new

    def mark_used(self, brand: Brand, title: str) -> None:
        """A job was made for it: never suggested again. Added if the title was typed by hand."""
        topic = self._topics.get_by_title(brand.slug, title) or Topic(brand=brand.slug, title=title)
        topic.status = TopicStatus.USED
        self._topics.save(topic)

    def _made_videos(self, brand: Brand) -> list[str]:
        """Topic keys of video folders made before the DB existed: <date>_<topic-slug>_<style>."""
        folder = self._videos_dir / brand.slug
        if not folder.exists():
            return []
        names = [p.name.split("_", 1)[1] for p in folder.glob("*_*_*") if p.is_dir()]
        return [topic_key(n.rsplit("_", 1)[0].replace("-", " ")) for n in names]
