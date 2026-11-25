from app.modules.studio.pipeline.produce import make_images
from app.modules.studio.services.stages import scenes
from app.modules.studio.services.stages.base import Stage, StageContext


class ImagesStage(Stage):
    """Scene images -> scene_XX.png (each scene in its own style). Missing images are drawn; a redo draws all.
    No automatic check: the human checks on request at the gate."""
    name = "images"
    outputs = ("scene_*.png", scenes.CHECKS_FILE)
    gate = True
    redo_clean = ("scene_*.png", scenes.CHECKS_FILE)

    def run(self, ctx: StageContext) -> list[str]:
        make_images(ctx.brand, ctx.storyboard(), ctx.folder, ctx.report)
        return []

    def run_action(self, ctx: StageContext, action: dict) -> None:
        if action["type"] == "redraw":
            return scenes.redraw(ctx, action)
        if action["type"] == "check":
            return scenes.check(ctx)
        return super().run_action(ctx, action)
