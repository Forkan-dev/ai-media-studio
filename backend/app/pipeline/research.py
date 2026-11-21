"""Research role: topic -> verified facts with source links."""
from pydantic import BaseModel

from app.brand import Brand
from app.prompts import render
from app.services.llm import chat_json
from app.services.search import page_text, search

QUERY_SUFFIXES = ["psychology study", "experiment results", "examples everyday life", "surprising facts"]
MAX_PAGES = 8


class Finding(BaseModel):
    text: str
    sources: list[int]


class Misconception(BaseModel):
    myth: str
    truth: str
    sources: list[int]


class Research(BaseModel):
    facts: list[Finding]
    surprising_details: list[Finding]
    misconceptions: list[Misconception]


class ResearchResult(BaseModel):
    research: Research
    urls: list[str]  # index i = source number i+1

    def facts_text(self) -> str:
        """Facts formatted for the Writer and Reviewer prompts."""
        lines = [f"- {f.text}" for f in self.research.facts]
        lines += [f"- (detail) {d.text}" for d in self.research.surprising_details]
        lines += [f"- {m.truth} (This corrects the wrong belief: {m.myth})"
                  for m in self.research.misconceptions]
        return "\n".join(lines)


def _collect_sources(topic: str) -> tuple[list[str], list[str]]:
    urls, texts = [], []
    for suffix in QUERY_SUFFIXES:
        for r in search(f"{topic} {suffix}"):
            if len(urls) >= MAX_PAGES:
                return urls, texts
            if r.url in urls:
                continue
            text = page_text(r.url)
            if len(text) > 500:  # skip empty or tiny pages
                urls.append(r.url)
                texts.append(text)
    return urls, texts


def research_topic(brand: Brand, topic: str) -> ResearchResult:
    urls, texts = _collect_sources(topic)
    if not texts:
        raise RuntimeError(f"No readable sources found for: {topic}")
    sources = "\n\n".join(f"[{i}] {u}\n{t}" for i, (u, t) in enumerate(zip(urls, texts), 1))
    system = render(brand.prompts, "researcher",
                    brand_name=brand.name, niche=brand.niche, topic=topic, sources=sources)
    research = chat_json(system, "Extract the research now.", Research, temperature=0.2)
    return ResearchResult(research=research, urls=urls)
