"""Research role: topic -> sorted findings (core fact, established, debated) with source links."""
from pydantic import BaseModel

from app.modules.studio.brand import Brand
from app.core.progress import Report, noop
from app.core.prompts import render
from app.core.clients.llm import chat_json
from app.core.clients.search import Result, page_text, search

QUERY_SUFFIXES = ["psychology study", "scientific evidence replication", "examples everyday life",
                  "what research really shows"]
MAX_PAGES = 8
MIN_ESTABLISHED = 3  # fewer established facts = topic is not solid enough for a video
# reliable sources are read first
PREFERRED = ("wikipedia.org", ".edu", "apa.org", "ncbi.nlm.nih.gov", "nature.com", "sciencedirect.com",
             "simplypsychology.org", "britannica.com", "thedecisionlab.com", "verywellmind.com")


class Finding(BaseModel):
    text: str
    sources: list[int]


class Misconception(BaseModel):
    myth: str
    truth: str
    sources: list[int]


class Research(BaseModel):
    core_fact: Finding
    established: list[Finding]
    debated: list[Finding]
    surprising_details: list[Finding]
    misconceptions: list[Misconception]


class ResearchResult(BaseModel):
    research: Research
    urls: list[str]  # index i = source number i+1

    def is_solid(self) -> bool:
        return len(self.research.established) >= MIN_ESTABLISHED

    def facts_text(self) -> str:
        """Facts for the Writer, Reviewer and fact-check, sorted by how safe they are."""
        r = self.research
        lines = ["CORE FACT (build the video on this):", f"- {r.core_fact.text}", "",
                 "ESTABLISHED FACTS:", *[f"- {f.text}" for f in r.established]]
        if r.debated:
            lines += ["", "DEBATED (only say 'some studies suggest', never as the main point):",
                      *[f"- {f.text}" for f in r.debated]]
        lines += ["", "SURPRISING DETAILS:", *[f"- {d.text}" for d in r.surprising_details]]
        lines += ["", "MYTH vs TRUTH:", *[f"- Myth: {m.myth} Truth: {m.truth}" for m in r.misconceptions]]
        return "\n".join(lines)


def _reliable_first(results: list[Result]) -> list[Result]:
    return sorted(results, key=lambda r: not any(d in r.url for d in PREFERRED))


def _collect_sources(topic: str, report: Report = noop) -> tuple[list[str], list[str]]:
    urls, texts = [], []
    for n, suffix in enumerate(QUERY_SUFFIXES, 1):
        report(f"Searching the web ({n} of {len(QUERY_SUFFIXES)}) · {len(urls)} sources read")
        for r in _reliable_first(search(f"{topic} {suffix}")):
            if len(urls) >= MAX_PAGES:
                return urls, texts
            if r.url in urls:
                continue
            text = page_text(r.url)
            if len(text) > 500:  # skip empty or tiny pages
                urls.append(r.url)
                texts.append(text)
    return urls, texts


def research_topic(brand: Brand, topic: str, report: Report = noop, notes: str = "") -> ResearchResult:
    urls, texts = _collect_sources(topic, report)
    if not texts:
        raise RuntimeError(f"No readable sources found for: {topic}")
    sources = "\n\n".join(f"[{i}] {u}\n{t}" for i, (u, t) in enumerate(zip(urls, texts), 1))
    system = render(brand.prompt_folders, "researcher",
                    brand_name=brand.name, niche=brand.niche, topic=topic, sources=sources)
    if notes.strip():
        system += f"\n\nExtra instructions from the creator (follow them):\n{notes.strip()}"
    report(f"Sorting facts from {len(texts)} sources")
    research = chat_json(system, "Extract the research now.", Research, temperature=0.2)
    return ResearchResult(research=research, urls=urls)
