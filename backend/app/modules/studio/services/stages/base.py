from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path

from app.core.progress import Report, noop
from app.modules.studio.brand import Brand
from app.modules.studio.pipeline.research import ResearchResult
from app.modules.studio.pipeline.storyboard import Storyboard


NOTES_FILE = "notes.txt"


@dataclass(frozen=True)
class StageContext:
    """What a stage needs. Inputs are read from files in `folder`, so human edits are used."""
    brand: Brand
    topic: str
    style: str
    folder: Path
    report: Report = field(default=noop)  # live progress lines for the UI

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

    def notes(self) -> str:
        """The human's instructions for this redo ("" if none). The job service deletes the file after the run."""
        path = self.folder / NOTES_FILE
        return path.read_text() if path.exists() else ""

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

    def run_action(self, ctx: StageContext, action: dict) -> None:
        """A small change requested at the gate (e.g. redraw one image). Stages that offer one override this."""
        raise ValueError(f"The {self.name} step has no action {action.get('type')}")
