import json

from app.modules.studio.pipeline.script import make_script
from app.modules.studio.pipeline.writer import Draft
from app.modules.studio.services.stages.base import Stage, StageContext


class ScriptStage(Stage):
    """Write, review, fact-check -> script.txt (editable narration) + script.json (rating for the gate).
    A redo with notes edits the previous draft to follow them."""
    name = "script"
    gate = True

    def run(self, ctx: StageContext) -> list[str]:
        previous, structure = self._previous(ctx)
        script = make_script(ctx.brand, ctx.topic, ctx.facts(), ctx.report, ctx.notes(), previous, structure)
        review = script.best.review
        (ctx.folder / "script.txt").write_text(script.narration())
        (ctx.folder / "script.json").write_text(json.dumps({
            "status": script.status,
            "review_scores": review.scores(),
            "review_average": round(review.average(), 1),
            "weaknesses": [w.model_dump() for w in review.real_weaknesses()],
            "removed_sentences": script.removed,
            "attempts": len(script.attempts),
            # every version, so the human can compare and copy one (the best is in script.txt)
            "versions": [{"structure": a.structure, "score": round(a.review.average(), 1), "text": a.text(),
                          "best": a is script.best} for a in script.attempts],
            "structure": script.best.structure,
            "draft": script.best.draft.model_dump(),  # the next redo with notes edits this
        }, indent=1))
        return script.flags

    @staticmethod
    def _previous(ctx: StageContext) -> tuple[Draft | None, str | None]:
        path = ctx.folder / "script.json"
        data = json.loads(path.read_text()) if path.exists() else {}
        if "draft" not in data:
            return None, None
        return Draft.model_validate(data["draft"]), data.get("structure")
