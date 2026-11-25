"""Scene image actions shared by the storyboard gate (test one image) and the images gate (redraw)."""
import json

from app.modules.studio.pipeline.produce import check_images, draw_scene
from app.modules.studio.services.stages.base import StageContext

CHECKS_FILE = "checks.json"


def redraw(ctx: StageContext, action: dict) -> None:
    """{"type": "redraw", "scene": n, "prompt": optional, "style": optional} - edits are saved in the storyboard."""
    sb, i = ctx.storyboard(), action["scene"] - 1
    if action.get("style"):
        ctx.brand.images.style(action["style"])  # fails on an unknown style
    sb.edit_scene(i, action.get("prompt"), action.get("style"))
    ctx.report(f"Drawing scene {i + 1}")
    draw_scene(ctx.brand, sb, i, ctx.folder)
    (ctx.folder / "storyboard.json").write_text(sb.model_dump_json(indent=1))
    _forget_check(ctx, i + 1)


def check(ctx: StageContext) -> None:
    """{"type": "check"} - vision check of every image -> checks.json, shown on the image cards."""
    results = check_images(ctx.brand, ctx.storyboard(), ctx.folder, ctx.report)
    (ctx.folder / CHECKS_FILE).write_text(json.dumps(results, indent=1))


def _forget_check(ctx: StageContext, scene: int) -> None:
    """A redrawn image needs a new check."""
    path = ctx.folder / CHECKS_FILE
    if path.exists():
        results = json.loads(path.read_text())
        results.pop(str(scene), None)
        path.write_text(json.dumps(results, indent=1))
