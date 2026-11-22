"""Topic ideas: web search from the brand niche -> the LLM finds and scores ideas. No database here."""
import re
from difflib import SequenceMatcher

from pydantic import BaseModel, Field

from app.brand import Brand
from app.clients.llm import chat_json
from app.clients.search import search
from app.prompts import render

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

    def scores(self) -> dict[str, int]:
        return {c: getattr(self, c) for c in CRITERIA}

    def score(self) -> float:
        return round(sum(self.scores().values()) / len(CRITERIA), 1)


class Ideas(BaseModel):
    ideas: list[Idea]


def topic_key(title: str) -> str:
    """Normalized title for comparing topics."""
    return re.sub(r"[^a-z0-9]+", " ", title.lower()).replace("the ", "").strip()


def is_known(title: str, known_keys: list[str]) -> bool:
    k = topic_key(title)
    return any(k == o or k in o or o in k or SequenceMatcher(None, k, o).ratio() >= SIMILAR for o in known_keys)


def find_ideas(brand: Brand, known_titles: list[str], count: int = 30) -> list[Idea]:
    """Ideas from the web, scored by the LLM. `known_titles` are given to the LLM to avoid."""
    snippets, seen = [], set()
    for template in QUERY_TEMPLATES:
        for r in search(template.format(niche=brand.niche)):
            if r.url not in seen:
                seen.add(r.url)
                snippets.append(f"- {r.title}: {r.snippet}")
    system = render(brand.prompts, "topics", brand_name=brand.name, niche=brand.niche, tone=brand.tone,
                    count=str(count), known="\n".join(f"- {t}" for t in known_titles) or "(none)",
                    snippets="\n".join(snippets))
    # no thinking: tested, it was 3x slower and made evidence scores MORE inflated (research checks evidence)
    return chat_json(system, "Find and score the topics now.", Ideas, temperature=0.7).ideas
