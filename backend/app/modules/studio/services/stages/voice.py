from app.modules.studio.pipeline.produce import make_voice, record_scene
from app.modules.studio.services.stages.base import Stage, StageContext


class VoiceStage(Stage):
    """Narration per scene -> scene_XX.wav. Listen at the gate; re-record one line or all."""
    name = "voice"
    outputs = ("scene_*.wav", "narration.wav")
    gate = True
    redo_clean = ("scene_*.wav", "narration.wav")

    def run(self, ctx: StageContext) -> list[str]:
        make_voice(ctx.brand, ctx.storyboard(), ctx.folder, ctx.report)
        return []

    def run_action(self, ctx: StageContext, action: dict) -> None:
        """{"type": "rerecord", "scene": n, "text": optional new narration (saved in the storyboard)}"""
        if action["type"] != "rerecord":
            return super().run_action(ctx, action)
        sb, i = ctx.storyboard(), action["scene"] - 1
        if action.get("text"):
            sb.scenes[i].narration = action["text"]
            (ctx.folder / "storyboard.json").write_text(sb.model_dump_json(indent=1))
        ctx.report(f"Re-recording scene {i + 1}")
        record_scene(ctx.brand, sb.scenes[i], ctx.folder / f"scene_{i + 1:02d}.wav")
