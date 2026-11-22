"""Topic discovery + ranking: web search from the brand niche -> LLM finds and scores ideas -> saved in the DB.

Topics that already have a video (DB status 'used' or a video folder) are never suggested again.
"""
import re
from difflib import SequenceMatcher

from pydantic import BaseModel, Field
from sqlalchemy import select

from app.brand import Brand
from app.config import settings
from app.db import Topic, session
from app.prompts import render
from app.services.llm import chat_json
from app.services.search import search

# generic for every brand: the niche fills the query
QUERY_TEMPLATES = ["surprising {niche}", "{niche} most people don't know", "little known {niche} studies",
                   "weird {niche} explained", "{niche} that changed how we think", "famous {niche} experiments"]
SIMILAR = 0.75  # titles this similar count as the same topic
CRITERIA = ("curiosity", "relatable", "evidence", "visual")


class Idea(BaseModel):
    title: str = Field(description="short topic name, 2 to 6 words")
    angle: str = Field(description="one sentence: the surprising point the video makes")
    curiosity: int = Field(ge=1, le=10)
    relatable: int = Field(ge=1, le=10)
    evidence: int = Field(ge=1, le=10)
    visual: int = Field(ge=1, le=10)


class Ideas(BaseModel):
    ideas: list[Idea]


def _key(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", title.lower()).replace("the ", "").strip()


def _is_known(title: str, known: list[str]) -> bool:
    k = _key(title)
    return any(k == o or k in o or o in k or SequenceMatcher(None, k, o).ratio() >= SIMILAR for o in known)


def _made_videos(brand: Brand) -> list[str]:
    """Topics of video folders: <date>_<topic-slug>_<style>."""
    folder = settings.storage_dir / "videos" / brand.slug
    names = [p.name.split("_", 1)[1] for p in folder.glob("*_*_*") if p.is_dir()] if folder.exists() else []
    return [_key(n.rsplit("_", 1)[0].replace("-", " ")) for n in names]


def list_topics(brand: Brand, status: str = "new") -> list[Topic]:
    """Best first. Also used by the UI's brand studio."""
    with session() as db:
        return list(db.scalars(select(Topic).where(Topic.brand == brand.slug, Topic.status == status)
                               .order_by(Topic.score.desc())))


def discover_topics(brand: Brand, count: int = 30) -> list[Topic]:
    """Search the web, let the LLM pick and score new ideas, save them. Returns the newly saved topics."""
    snippets, seen = [], set()
    for template in QUERY_TEMPLATES:
        for r in search(template.format(niche=brand.niche)):
            if r.url not in seen:
                seen.add(r.url)
                snippets.append(f"- {r.title}: {r.snippet}")

    with session() as db:
        existing = list(db.scalars(select(Topic.title).where(Topic.brand == brand.slug)))
    known = [_key(t) for t in existing] + _made_videos(brand)

    system = render(brand.prompts, "topics", brand_name=brand.name, niche=brand.niche, tone=brand.tone,
                    count=str(count), known="\n".join(f"- {t}" for t in existing) or "(none)",
                    snippets="\n".join(snippets))
    ideas = chat_json(system, "Find and score the topics now.", Ideas, temperature=0.7).ideas

    new: list[Topic] = []
    for idea in ideas:
        if _is_known(idea.title, known):
            continue
        known.append(_key(idea.title))
        scores = {c: getattr(idea, c) for c in CRITERIA}
        new.append(Topic(brand=brand.slug, title=idea.title.strip(), angle=idea.angle.strip(), scores=scores,
                         score=round(sum(scores.values()) / len(scores), 1)))
    with session() as db:
        db.add_all(new)
        db.commit()
    return new


def mark_used(brand: Brand, title: str) -> None:
    """Called when a video is made, so the topic is not suggested again (added if typed by hand)."""
    with session() as db:
        topic = db.scalar(select(Topic).where(Topic.brand == brand.slug, Topic.title == title))
        if topic is None:
            topic = Topic(brand=brand.slug, title=title)
            db.add(topic)
        topic.status = "used"
        db.commit()
