"""Topic ideas: the LLM finds and scores ideas (from a web search for fact brands). No database here."""
import re
from difflib import SequenceMatcher

from pydantic import BaseModel, Field, create_model

from app.modules.studio.brand import Brand
from app.core.clients.llm import chat_json
from app.core.clients.search import search
from app.core.prompts import render

# generic for every brand: the niche fills the query
QUERY_TEMPLATES = ["surprising {niche}", "{niche} most people don't know", "little known {niche} studies",
                   "weird {niche} explained", "{niche} that changed how we think", "famous {niche} experiments"]
SIMILAR = 0.75  # titles this similar count as the same topic


class Idea(BaseModel):
    title: str
    angle: str
    scores: dict[str, int]

    def score(self) -> float:
        return round(sum(self.scores.values()) / len(self.scores), 1)


def _ideas_schema(criteria: list[str]) -> type[BaseModel]:
    """LLM output schema with one 1-10 score field per brand criterion."""
    scored = {c: (int, Field(ge=1, le=10)) for c in criteria}
    item = create_model("IdeaOut", title=(str, Field(description="short topic name, 2 to 8 words")),
                        angle=(str, Field(description="one sentence: the surprising point of the video")),
                        **scored)
    return create_model("IdeasOut", ideas=(list[item], ...))


def topic_key(title: str) -> str:
    """Normalized title for comparing topics."""
    return re.sub(r"[^a-z0-9]+", " ", title.lower()).replace("the ", "").strip()


def is_known(title: str, known_keys: list[str]) -> bool:
    k = topic_key(title)
    return any(k == o or k in o or o in k or SequenceMatcher(None, k, o).ratio() >= SIMILAR for o in known_keys)


def _web_snippets(brand: Brand) -> str:
    snippets, seen = [], set()
    for template in QUERY_TEMPLATES:
        for r in search(template.format(niche=brand.niche)):
            if r.url not in seen:
                seen.add(r.url)
                snippets.append(f"- {r.title}: {r.snippet}")
    return "\n".join(snippets)


def find_ideas(brand: Brand, known_titles: list[str], count: int = 30) -> list[Idea]:
    """Ideas scored by the LLM on the brand's topic criteria. `known_titles` are given to the LLM to avoid.
    Fact brands get web search results as inspiration; fiction brands brainstorm."""
    snippets = _web_snippets(brand) if brand.pipeline.research else "(none: invent original ideas)"
    system = render(brand.prompt_folders, "topics", brand_name=brand.name, niche=brand.niche, tone=brand.tone,
                    count=str(count), known="\n".join(f"- {t}" for t in known_titles) or "(none)",
                    snippets=snippets)
    # no thinking: tested, it was 3x slower and made evidence scores MORE inflated (research checks evidence)
    out = chat_json(system, "Find and score the topics now.", _ideas_schema(brand.topic_criteria),
                    temperature=0.8)
    return [Idea(title=i.title, angle=i.angle, scores={c: getattr(i, c) for c in brand.topic_criteria})
            for i in out.ideas]
