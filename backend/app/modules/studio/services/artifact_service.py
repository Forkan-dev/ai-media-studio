"""A job's step outputs (files in its folder): read them for the UI and let the human edit them at the gates.
Each edit is allowed only while that step is waiting for approval; stages read these files, so edits are used."""
import json
from pathlib import Path

import soundfile as sf
from typing import Any

from app.core.config import settings
from app.core.errors import InvalidInputError, InvalidStateError
from app.modules.studio.models import Job, JobStatus
from app.modules.studio.pipeline.research import ResearchResult
from app.modules.studio.pipeline.storyboard import Scene, Storyboard
from app.modules.studio.pipeline.thumbnail import FINAL_SIZE, render_text
from app.modules.studio.services.job_service import JobService


MAX_RESEARCH_CHARS = 60_000  # an edited research.json; the writer prompt must stay small


def media_url(path: Path) -> str | None:
    """URL of a generated file (served under /media); the version changes when the file is rewritten."""
    if not path.exists():
        return None
    return f"/media/{path.relative_to(settings.storage_dir)}?v={int(path.stat().st_mtime)}"


def _json(path: Path) -> Any:
    return json.loads(path.read_text()) if path.exists() else None


class JobArtifactService:
    def __init__(self, jobs: JobService):
        self._jobs = jobs

    def view(self, job_id: int) -> dict:
        job = self._jobs.get(job_id)
        folder = Path(job.folder)
        sb_path = folder / "storyboard.json"
        sb = Storyboard.model_validate_json(sb_path.read_text()) if sb_path.exists() else None
        checks = _json(folder / "checks.json") or {}
        return {
            "stages": [{"name": s.name, "gate": s.gate} for s in self._jobs.stages(job)],
            "research": _json(folder / "research.json"),
            "script": {"text": (folder / "script.txt").read_text(), "review": _json(folder / "script.json")}
            if (folder / "script.txt").exists() else None,
            "scenes": [self._scene(folder, sb, i, s, checks.get(str(i)))
                       for i, s in enumerate(sb.scenes, 1)] if sb else [],
            "thumbnail": {"plan": _json(folder / "thumbnail.json"), "image": media_url(folder / "thumbnail.png")}
            if (folder / "thumbnail.json").exists() else None,
            "metadata": _json(folder / "metadata.json"),
            "video": media_url(folder / "final.mp4"),
        }

    @staticmethod
    def _scene(folder: Path, sb: Storyboard, i: int, scene: Scene, check: dict | None) -> dict:
        image, audio = folder / f"scene_{i:02d}.png", folder / f"scene_{i:02d}.wav"
        return {"narration": scene.narration, "image_prompt": scene.image_prompt, "style": sb.style_of(scene),
                "image": media_url(image), "outdated": image.exists() and sb.is_outdated(scene), "check": check,
                "audio": media_url(audio),
                "seconds": round(sf.info(str(audio)).duration, 1) if audio.exists() else None}

    # ---------- edits at the gates ----------

    def save_research(self, job_id: int, research: ResearchResult) -> None:
        job = self._at_gate(job_id, "research")
        if len(research.model_dump_json()) > MAX_RESEARCH_CHARS:
            raise InvalidInputError("The research is too long; remove some facts")
        (Path(job.folder) / "research.json").write_text(research.model_dump_json(indent=1))

    def save_script(self, job_id: int, text: str) -> None:
        job = self._at_gate(job_id, "script")
        (Path(job.folder) / "script.txt").write_text(text.strip())

    def redraw_image(self, job_id: int, scene: int, prompt: str | None = None, style: str | None = None) -> Job:
        """Queue one scene's image (optionally with an edited prompt / another style); the worker draws it.
        At the storyboard gate this is a test image before drawing all; at the images gate a redraw."""
        job = self._jobs.get(job_id)
        stage = job.stage if job.stage in ("storyboard", "images") else "images"
        self._check_scene(self._at_gate(job_id, stage), scene)
        return self._jobs.queue_action(job_id, stage, {"type": "redraw", "scene": scene,
                                                       "prompt": (prompt or "").strip(), "style": style})

    def save_scene(self, job_id: int, scene: int, prompt: str | None, style: str | None) -> None:
        """Change a scene's prompt / style without drawing (kept for the next drawing; the card shows that its
        image is out of date)."""
        job = self._jobs.get(job_id)
        if job.stage not in ("storyboard", "images"):
            raise InvalidStateError("Scenes can be edited at the storyboard or images step")
        self._at_gate(job_id, job.stage)
        self._check_scene(job, scene)
        if style:
            self._jobs.brand_of(job).images.style(style)  # unknown style -> error
        path = Path(job.folder) / "storyboard.json"
        sb = Storyboard.model_validate_json(path.read_text())
        sb.edit_scene(scene - 1, prompt, style)
        path.write_text(sb.model_dump_json(indent=1))

    def check_images(self, job_id: int) -> Job:
        """Queue the vision check of every image (on request; results show on the image cards)."""
        self._at_gate(job_id, "images")
        return self._jobs.queue_action(job_id, "images", {"type": "check"})

    def rerecord_voice(self, job_id: int, scene: int, text: str | None = None) -> Job:
        """Queue one scene's narration again (optionally with edited words); the worker records it."""
        self._check_scene(self._at_gate(job_id, "voice"), scene)
        return self._jobs.queue_action(job_id, "voice",
                                       {"type": "rerecord", "scene": scene, "text": (text or "").strip()})

    @staticmethod
    def _check_scene(job: Job, scene: int) -> None:
        sb = Storyboard.model_validate_json((Path(job.folder) / "storyboard.json").read_text())
        if not 1 <= scene <= len(sb.scenes):
            raise InvalidStateError(f"No scene {scene}")

    def set_thumbnail_text(self, job_id: int, text: str) -> None:
        """Put another text on the thumbnail image (seconds, no new image)."""
        job = self._at_gate(job_id, "thumbnail")
        folder = Path(job.folder)
        plan = _json(folder / "thumbnail.json") or {}
        plan["text"] = text.strip().upper()
        (folder / "thumbnail.json").write_text(json.dumps(plan, indent=1))
        render_text(folder, plan["text"], FINAL_SIZE[self._jobs.brand_of(job).format])

    def _at_gate(self, job_id: int, stage: str) -> Job:
        job = self._jobs.get(job_id)
        if job.stage != stage or job.status != JobStatus.WAITING:
            raise InvalidStateError(f"The {stage} step can be edited only while it waits for approval")
        return job
