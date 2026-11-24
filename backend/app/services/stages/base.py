from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from app.brand import Brand
from app.pipeline.research import ResearchResult
from app.pipeline.storyboard import Storyboard


@dataclass(frozen=True)
class StageContext:
    """What a stage needs. Inputs are read from files in `folder`, so human edits are used."""
    brand: Brand
    topic: str
    style: str
    folder: Path

    def research(self) -> ResearchResult | None:
        """None for brands without research (fiction)."""
        path = self.folder / "research.json"
        return ResearchResult.model_validate_json(path.read_text()) if path.exists() else None

    def facts(self) -> str:
        research = self.research()
        return research.facts_text() if research else ""

    def core_fact(self) -> str:
        research = self.research()
        return research.research.core_fact.text if research else ""

    def narration(self) -> str:
        return (self.folder / "script.txt").read_text()

    def storyboard(self) -> Storyboard:
        return Storyboard.model_validate_json((self.folder / "storyboard.json").read_text())


class Stage(ABC):
    """One step of making a video. Add a step = add a Stage class; the job service does not change."""
    name: str
    gate: bool = False  # pause for human approval after this stage
    redo_clean: tuple[str, ...] = ()  # file patterns deleted before a redo, so they are made again

    @abstractmethod
    def run(self, ctx: StageContext) -> list[str]:
        """Do the work, write the output files. Returns flags for the human (never stops the job)."""
