from app.pipeline.produce import make_images
from app.services.stages.base import Stage, StageContext


class ImagesStage(Stage):
    """Scene images with the vision check -> scene_XX.png. Missing images are made; a redo makes all new."""
    name = "images"
    gate = True
    redo_clean = ("scene_*.png",)

    def run(self, ctx: StageContext) -> list[str]:
        failed = make_images(ctx.brand, ctx.storyboard(), ctx.folder)
        return [f"Images may not match the style or prompt: scenes {failed}"] if failed else []
