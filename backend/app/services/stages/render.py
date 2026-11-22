from app.pipeline.produce import render_final
from app.services.stages.base import Stage, StageContext


class RenderStage(Stage):
    """Voice + captions + scene images -> final.mp4."""
    name = "render"

    def run(self, ctx: StageContext) -> list[str]:
        render_final(ctx.brand, ctx.storyboard(), ctx.folder)
        return []
