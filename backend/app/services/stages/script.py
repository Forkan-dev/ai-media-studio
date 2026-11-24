import json

from app.pipeline.script import make_script
from app.services.stages.base import Stage, StageContext


class ScriptStage(Stage):
    """Write, review, fact-check -> script.txt (editable narration) + script.json (rating for the gate)."""
    name = "script"
    gate = True

    def run(self, ctx: StageContext) -> list[str]:
        script = make_script(ctx.brand, ctx.topic, ctx.facts())
        review = script.best.review
        (ctx.folder / "script.txt").write_text(script.narration())
        (ctx.folder / "script.json").write_text(json.dumps({
            "status": script.status,
            "review_scores": review.scores(),
            "review_average": round(review.average(), 1),
            "weaknesses": [w.model_dump() for w in review.real_weaknesses()],
            "removed_sentences": script.removed,
            "attempts": len(script.attempts),
        }, indent=1))
        return script.flags
