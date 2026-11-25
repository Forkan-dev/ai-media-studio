from app.core.clients.llm import unload
from app.modules.studio.pipeline.metadata import Metadata
from app.modules.studio.pipeline.thumbnail import make_thumbnail, plan_thumbnail
from app.modules.studio.services.stages.base import Stage, StageContext


class ThumbnailStage(Stage):
    """Plan (symbol + text options) -> image with the vision check -> thumbnail.png."""
    name = "thumbnail"
    outputs = ("thumbnail.json", "thumbnail.png", "thumbnail_raw.png")
    gate = True

    def run(self, ctx: StageContext) -> list[str]:
        meta = Metadata.model_validate_json((ctx.folder / "metadata.json").read_text())
        ctx.report("Planning the picture and the text")
        plan = plan_thumbnail(ctx.brand, ctx.style, meta.youtube_title, ctx.narration(), ctx.core_fact())
        unload()  # LLM out, SDXL in
        ctx.report("Drawing and checking the thumbnail")
        _, ok = make_thumbnail(ctx.brand, ctx.style, plan, ctx.folder)
        return [] if ok else ["Thumbnail image may not match the style or prompt"]
