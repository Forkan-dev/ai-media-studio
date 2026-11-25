"""Test setup: a temporary DB + storage folder and fake stages (fast, no AI models, real data untouched)."""
from pathlib import Path

import pytest
import yaml
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.modules.clipforge.models  # noqa: F401  (register tables)
import app.modules.studio.models  # noqa: F401
from app.core.config import ROOT, settings
from app.core.models import Base
from app.modules.studio.brand import Brand
from app.modules.studio.repositories import JobRepository, TopicRepository
from app.modules.studio.services.job_service import JobService
from app.modules.studio.services.stages.base import Stage, StageContext
from app.modules.studio.services.topic_service import TopicService


class FakeStage(Stage):
    """Writes '<name>.out' (its output); can fail on purpose; records actions."""

    def __init__(self, name: str, gate: bool, extra_outputs: tuple[str, ...] = ()):
        self.name, self.gate = name, gate
        self.outputs = (f"{name}.out", *extra_outputs)
        self.redo_clean = (f"{name}.out",)
        self.fail = False
        self.seen_notes: list[str] = []
        self.actions: list[dict] = []

    def run(self, ctx: StageContext) -> list[str]:
        self.seen_notes.append(ctx.notes())
        ctx.report(f"working on {self.name}")
        if self.fail:
            raise RuntimeError("boom")
        (ctx.folder / f"{self.name}.out").write_text("done")
        return [f"flag from {self.name}"]

    def run_action(self, ctx: StageContext, action: dict) -> None:
        self.actions.append(action)
        if action.get("fail"):
            raise RuntimeError("action failed")


@pytest.fixture
def brand() -> Brand:
    config = yaml.safe_load((ROOT / "backend/presets/facts.yaml").read_text())
    return Brand.model_validate({**config, "slug": "test_brand", "name": "Test", "niche": "tests", "tone": "plain"})


@pytest.fixture
def stages() -> list[FakeStage]:
    # 'b' also owns 'shared.png' (like the storyboard owns test images that the images step also makes)
    return [FakeStage("a", gate=True), FakeStage("b", True, ("shared.png",)),
            FakeStage("c", False, ("shared.png",)), FakeStage("d", gate=True)]


@pytest.fixture
def jobs(tmp_path: Path, monkeypatch, brand: Brand, stages: list[FakeStage]) -> JobService:
    monkeypatch.setattr(settings, "storage_dir", tmp_path)
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)
    sessions = sessionmaker(engine, expire_on_commit=False)
    topics = TopicService(TopicRepository(sessions), tmp_path / "videos")
    return JobService(JobRepository(sessions), topics, lambda _: stages, lambda _: brand)
