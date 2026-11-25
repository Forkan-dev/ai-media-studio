from app.modules.studio.pipeline.research import research_topic
from app.modules.studio.services.stages.base import Stage, StageContext


class ResearchStage(Stage):
    """Web research -> research.json (editable)."""
    name = "research"
    outputs = ("research.json",)
    gate = True

    def run(self, ctx: StageContext) -> list[str]:
        research = research_topic(ctx.brand, ctx.topic, ctx.report, ctx.notes())
        (ctx.folder / "research.json").write_text(research.model_dump_json(indent=1))
        if research.is_solid():
            return []
        return [f"Research found only {len(research.research.established)} established facts"]
