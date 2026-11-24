from app.modules.studio.pipeline.produce import render_final
from app.modules.studio.services.stages.base import Stage, StageContext


class RenderStage(Stage):
    """Approved voice + captions + scene images -> final.mp4."""
    name = "render"

    def run(self, ctx: StageContext) -> list[str]:
        render_final(ctx.brand, ctx.storyboard(), ctx.folder, ctx.report)
        return []
