"""Job business logic: make one video step by step, pausing for human approval at gated stages.

run      run the current stage; pause at a gate (or continue when auto)
approve  accept the waiting stage's result (as is or edited) and run the next stage
redo     run the current stage again (rejected result, or after a failure)
"""
import json
import logging
from collections.abc import Callable
from pathlib import Path

from app.brand import Brand, load_brand
from app.models import Job, JobStatus
from app.pipeline.produce import cleanup, video_folder
from app.repositories import JobRepository
from app.services.errors import InvalidStateError, NotFoundError
from app.services.stages import Stage, StageContext
from app.services.topic_service import TopicService

log = logging.getLogger(__name__)


class JobService:
    def __init__(self, jobs: JobRepository, topics: TopicService, stages_for: Callable[[Brand], list[Stage]]):
        """`stages_for(brand)`: the brand's steps in order (fiction brands have no research step)."""
        self._jobs = jobs
        self._topics = topics
        self._stages_for = stages_for

    # ---------- queries ----------

    def get(self, job_id: int) -> Job:
        job = self._jobs.get(job_id)
        if job is None:
            raise NotFoundError(f"No job {job_id}")
        return job

    def list_jobs(self, brand: str | None = None) -> list[Job]:
        return self._jobs.find(brand)

    def check_can_approve(self, job_id: int) -> Job:
        job = self.get(job_id)
        if job.status != JobStatus.WAITING:
            raise InvalidStateError(f"Job {job_id} is {job.status}, not waiting for approval")
        return job

    def check_can_redo(self, job_id: int) -> Job:
        job = self.get(job_id)
        if job.status not in (JobStatus.WAITING, JobStatus.FAILED):
            raise InvalidStateError(f"Job {job_id} is {job.status}; only a waiting or failed stage can be redone")
        return job

    # ---------- commands ----------

    def create(self, brand: Brand, topic: str, style: str | None = None) -> Job:
        style = style or brand.images.default_style
        brand.images.style(style)  # fails early on an unknown style
        folder = video_folder(brand, topic, style)
        folder.mkdir(parents=True, exist_ok=True)
        self._topics.mark_used(brand, topic)
        return self._jobs.save(Job(brand=brand.slug, topic=topic, style=style, folder=str(folder),
                                   stage=self._stages_for(brand)[0].name, status=JobStatus.RUNNING))

    def run(self, job_id: int, auto: bool = False) -> Job:
        """Run stages from the current one. auto=True: no pauses at gates (one-shot video)."""
        job = self.get(job_id)
        brand = load_brand(job.brand)
        while True:
            stage = self._stage(brand, job.stage)
            self._set_status(job, JobStatus.RUNNING)
            log.info("job %s: %s", job.id, stage.name)
            try:
                flags = stage.run(StageContext(brand, job.topic, job.style, Path(job.folder)))
            except Exception as e:  # saved on the job, shown in the UI; the stage can be redone
                job.error = f"{type(e).__name__}: {e}"
                self._set_status(job, JobStatus.FAILED)
                raise
            job.flags = {**job.flags, stage.name: flags}  # a redo replaces this stage's flags
            if stage.gate and not auto:
                return self._set_status(job, JobStatus.WAITING)
            if not self._advance(brand, job):
                return self._jobs.save(job)

    def approve(self, job_id: int, auto: bool = False) -> Job:
        job = self.check_can_approve(job_id)
        if not self._advance(load_brand(job.brand), job):
            return self._jobs.save(job)
        self._jobs.save(job)
        return self.run(job_id, auto)

    def redo(self, job_id: int) -> Job:
        job = self.check_can_redo(job_id)
        for pattern in self._stage(load_brand(job.brand), job.stage).redo_clean:
            for f in Path(job.folder).glob(pattern):
                f.unlink()
        return self.run(job_id)

    # ---------- helpers ----------

    def _set_status(self, job: Job, status: JobStatus) -> Job:
        job.status = status
        if status != JobStatus.FAILED:
            job.error = ""
        return self._jobs.save(job)

    def _stage(self, brand: Brand, name: str) -> Stage:
        return next(s for s in self._stages_for(brand) if s.name == name)

    def _advance(self, brand: Brand, job: Job) -> bool:
        """Move to the next stage. Returns False when there is none (the job is finished)."""
        order = [s.name for s in self._stages_for(brand)]
        i = order.index(job.stage)
        if i + 1 < len(order):
            job.stage = order[i + 1]
            return True
        self._finish(job)
        return False

    def _finish(self, job: Job) -> None:
        """Delete temp files, write the summary into the folder."""
        out = Path(job.folder)
        cleanup(out)
        has_flags = any(job.flags.values())
        (out / "review.json").write_text(json.dumps(
            {"status": "needs_attention" if has_flags else "ready_for_review", "flags": job.flags}, indent=1))
        job.status = JobStatus.DONE
