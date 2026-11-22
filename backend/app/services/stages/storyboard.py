from app.clients.llm import unload
from app.pipeline.metadata import make_metadata, save_metadata
from app.pipeline.storyboard import make_storyboard
from app.services.stages.base import Stage, StageContext


class StoryboardStage(Stage):
    """Scenes + image prompts -> storyboard.json; publishing text -> metadata.json/.txt."""
    name = "storyboard"

    def run(self, ctx: StageContext) -> list[str]:
        narration = ctx.narration()
        sb = make_storyboard(ctx.brand, ctx.topic, narration, style=ctx.style)
        (ctx.folder / "storyboard.json").write_text(sb.model_dump_json(indent=1))
        save_metadata(make_metadata(ctx.brand, ctx.topic, narration), ctx.folder)
        unload()  # LLM out, SDXL in
        return []
