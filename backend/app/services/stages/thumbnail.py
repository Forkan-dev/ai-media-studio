from app.clients.llm import unload
from app.pipeline.metadata import Metadata
from app.pipeline.thumbnail import make_thumbnail, plan_thumbnail
from app.services.stages.base import Stage, StageContext


class ThumbnailStage(Stage):
    """Plan (symbol + text options) -> image with the vision check -> thumbnail.png."""
    name = "thumbnail"
    gate = True

    def run(self, ctx: StageContext) -> list[str]:
        meta = Metadata.model_validate_json((ctx.folder / "metadata.json").read_text())
        plan = plan_thumbnail(ctx.brand, ctx.style, meta.youtube_title, ctx.narration(),
                              ctx.research().research.core_fact.text)
        unload()  # LLM out, SDXL in
        _, ok = make_thumbnail(ctx.brand, ctx.style, plan, ctx.folder)
        return [] if ok else ["Thumbnail image may not match the style or prompt"]
