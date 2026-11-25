from app.core.clients.llm import unload
from app.modules.studio.pipeline.metadata import make_metadata, save_metadata
from app.modules.studio.pipeline.storyboard import make_storyboard
from app.modules.studio.services.stages import scenes
from app.modules.studio.services.stages.base import Stage, StageContext


class StoryboardStage(Stage):
    """Scenes + image prompts -> storyboard.json; publishing text -> metadata.json/.txt.
    Gate: check each scene's line, prompt and style before drawing; optionally test-draw one scene
    (kept: the images step draws only the missing ones)."""
    name = "storyboard"
    outputs = ("storyboard.json", "metadata.json", "metadata.txt", "scene_*.png")  # test images live here too
    gate = True
    redo_clean = ("scene_*.png", scenes.CHECKS_FILE)  # new prompts: old test images no longer match

    def run(self, ctx: StageContext) -> list[str]:
        narration = ctx.narration()
        ctx.report("Splitting scenes and writing image prompts")
        sb = make_storyboard(ctx.brand, ctx.topic, narration, style=ctx.style)
        (ctx.folder / "storyboard.json").write_text(sb.model_dump_json(indent=1))
        ctx.report("Writing title, description and tags")
        save_metadata(make_metadata(ctx.brand, ctx.topic, narration), ctx.folder)
        unload()  # LLM out, SDXL in
        return []

    def run_action(self, ctx: StageContext, action: dict) -> None:
        if action["type"] == "redraw":
            return scenes.redraw(ctx, action)
        return super().run_action(ctx, action)
