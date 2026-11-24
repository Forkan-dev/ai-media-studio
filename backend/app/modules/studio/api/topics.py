"""Topics controller: HTTP only, the work is in TopicService."""
from fastapi import APIRouter, Depends

from app.modules.studio.dependencies import brand, topic_service
from app.modules.studio.schemas import TopicOut
from app.modules.studio.services.topic_service import TopicService

router = APIRouter(prefix="/brands/{slug}/topics", tags=["topics"])


@router.get("", response_model=list[TopicOut])
def list_topics(slug: str, topics: TopicService = Depends(topic_service)):
    """Topics that can be picked, best first (used topics are hidden)."""
    return topics.list_new(brand(slug))


@router.post("/discover", response_model=list[TopicOut])
def discover_topics(slug: str, topics: TopicService = Depends(topic_service)):
    """'Get topics' button: search the web for new ideas (takes ~3 min). Returns the new ones."""
    return topics.discover(brand(slug))
