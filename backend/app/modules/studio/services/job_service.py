"""Job business logic: make one video step by step, pausing for human approval at gated stages.

Commands only QUEUE work (fast, used by the API); the worker process runs it (app.worker), so restarting
the API never stops a video.
create   new job, queued at its first stage
advance  approve the waiting stage: queue the next one (or finish)
prepare_redo  queue the current stage again (rejected result, or after a failure)
run      (worker / CLI) run stages from the current one until a gate, the end, or a failure
"""
import json
import logging
from collections.abc import Callable
from pathlib import Path

from app.modules.studio.brand import Brand
from app.modules.studio.models import Job, JobStatus
from app.modules.studio.pipeline.produce import cleanup, video_folder
from app.modules.studio.repositories import JobRepository
from app.core.errors import InvalidStateError, NotFoundError
from app.modules.studio.services.stages import Stage, StageContext
from app.modules.studio.services.stages.base import NOTES_FILE
from app.modules.studio.services.topic_service import TopicService

log = logging.getLogger(__name__)


class JobService:
    def __init__(self, jobs: JobRepository, topics: TopicService, stages_for: Callable[[Brand], list[Stage]],
                 brand: Callable[[str], Brand], wake: Callable[[], None] = lambda: None):
        """`stages_for(brand)`: the brand's steps in order (fiction brands have no research step).
        `brand(slug)`: looks up a brand's config."""
        self._jobs = jobs
        self._topics = topics
        self._stages_for = stages_for
        self._brand = brand
        self._wake = wake  # starts the worker when work is queued

    # ---------- queries ----------

    def get(self, job_id: int) -> Job:
        job = self._jobs.get(job_id)
        if job is None:
            raise NotFoundError(f"No job {job_id}")
        return job

    def list_jobs(self, brand: str | None = None) -> list[Job]:
        return self._jobs.find(brand)

    def recover_interrupted(self) -> list[int]:
        """Worker startup: jobs still 'running' were cut off (worker stopped, crash) - mark them failed so they
        can be retried; the stage reuses files it already made. One worker, so nothing else can own them."""
        stuck = [j for j in self._jobs.find() if j.status == JobStatus.RUNNING]
        for job in stuck:
            job.error = "Interrupted: the server stopped during this step. Retry to continue."
            job.status = JobStatus.FAILED
            self._jobs.save(job)
        return [j.id for j in stuck]

    def brand_of(self, job: Job) -> Brand:
        return self._brand(job.brand)

    def stages(self, job: Job) -> list[Stage]:
        """The job's steps in order."""
        return self._stages_for(self.brand_of(job))

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

    def create(self, brand: Brand, topic: str, style: str | None = None, auto: bool = False) -> Job:
        style = style or brand.images.default_style
        brand.images.style(style)  # fails early on an unknown style
        folder = video_folder(brand, topic, style)
        folder.mkdir(parents=True, exist_ok=True)
        self._topics.mark_used(brand, topic)
        job = self._jobs.save(Job(brand=brand.slug, topic=topic, style=style, folder=str(folder),
                                  stage=self._stages_for(brand)[0].name, status=JobStatus.QUEUED, auto=auto))
        self._wake()
        return job

    def next_job(self) -> Job | None:
        """Worker: claim the oldest queued job (None if there is nothing to do)."""
        while job := self._jobs.oldest_queued():
            if self._jobs.claim(job.id):
                return self.get(job.id)
        return None

    def run_now(self, job_id: int) -> Job:
        """CLI: run a queued job in this process instead of the worker (if the worker has not taken it)."""
        return self.run(job_id) if self._jobs.claim(job_id) else self.get(job_id)

    def queue_action(self, job_id: int, stage: str, action: dict) -> Job:
        """A small change at a gate (redraw one image, re-record one line); the worker runs it, then the
        job waits at the same gate again."""
        job = self.check_can_approve(job_id)
        if job.stage != stage:
            raise InvalidStateError(f"Job {job_id} is at {job.stage}, not {stage}")
        job.action = action
        job.progress = []
        return self._set_status(job, JobStatus.QUEUED)

    def run(self, job_id: int) -> Job:
        """Run stages from the current one (the job is already claimed). job.auto: no pauses at gates.
        A queued action runs instead, and the job goes back to waiting at its gate."""
        job = self.get(job_id)
        brand = self._brand(job.brand)

        def report(line: str) -> None:  # live progress for the UI
            job.progress = [*job.progress, line][-20:]
            self._jobs.save(job)

        if job.action:
            ctx = StageContext(brand, job.topic, job.style, Path(job.folder), report)
            try:
                self._stage(brand, job.stage).run_action(ctx, job.action)
            finally:  # a failed action still returns the job to its gate; the item keeps its old version
                job.action = None
                self._set_status(job, JobStatus.WAITING)
            return job

        while True:
            stage = self._stage(brand, job.stage)
            job.progress = []
            self._set_status(job, JobStatus.RUNNING)
            log.info("job %s: %s", job.id, stage.name)
            try:
                flags = stage.run(StageContext(brand, job.topic, job.style, Path(job.folder), report))
            except Exception as e:  # saved on the job, shown in the UI; the stage can be redone
                job.error = f"{type(e).__name__}: {e}"
                self._set_status(job, JobStatus.FAILED)
                raise
            (Path(job.folder) / NOTES_FILE).unlink(missing_ok=True)  # notes are for one run only
            job.flags = {**job.flags, stage.name: flags}  # a redo replaces this stage's flags
            if stage.gate and not job.auto:
                return self._set_status(job, JobStatus.WAITING)
            if not self._advance(brand, job):
                return self._jobs.save(job)

    def advance(self, job_id: int, auto: bool = False) -> Job:
        """Approve the waiting stage: queue the next one (or finish if it was the last).
        auto=True: the rest runs without pausing at gates."""
        job = self.check_can_approve(job_id)
        job.auto = auto
        if not self._advance(self._brand(job.brand), job):
            return self._jobs.save(job)
        return self._set_status(job, JobStatus.QUEUED)

    def reopen(self, job_id: int, stage: str) -> Job:
        """Go back to an earlier step of an unfinished job. Everything the later steps made is deleted (they are
        made again from the changes). A gated step waits for the human (edit, redo or approve); a step without
        a gate runs again."""
        job = self.check_can_redo(job_id)  # waiting or failed: nothing is running
        stages = self.stages(job)
        names = [s.name for s in stages]
        if stage not in names:
            raise InvalidStateError(f"No step {stage}")
        target, current = names.index(stage), names.index(job.stage)
        if target > current:
            raise InvalidStateError(f"The {stage} step has not been reached yet")
        folder = Path(job.folder)
        keep = set(stages[target].outputs)  # files the reopened step also owns stay (e.g. storyboard images)
        for later in stages[target + 1:]:
            for pattern in set(later.outputs) - keep:
                for f in folder.glob(pattern):
                    f.unlink()
            job.flags.pop(later.name, None)
        job.flags = dict(job.flags)
        job.stage, job.auto, job.action, job.progress = stage, False, None, []
        if stages[target].gate and stages[target].has_result(folder):
            return self._set_status(job, JobStatus.WAITING)  # its result is still there: back at its gate
        for pattern in stages[target].outputs:
            for f in folder.glob(pattern):
                f.unlink()
        return self._set_status(job, JobStatus.QUEUED)

    def prepare_redo(self, job_id: int, notes: str = "") -> Job:
        """Queue the current stage again; its old outputs are deleted first.
        `notes`: the human's instructions for this run (stages that use them: research, script)."""
        job = self.check_can_redo(job_id)
        for pattern in self._stage(self._brand(job.brand), job.stage).redo_clean:
            for f in Path(job.folder).glob(pattern):
                f.unlink()
        notes_file = Path(job.folder) / NOTES_FILE
        if notes.strip():
            notes_file.write_text(notes.strip())
        else:
            notes_file.unlink(missing_ok=True)
        job.auto = False
        return self._set_status(job, JobStatus.QUEUED)

    # ---------- helpers ----------

    def _set_status(self, job: Job, status: JobStatus) -> Job:
        job.status = status
        if status != JobStatus.FAILED:
            job.error = ""
        job = self._jobs.save(job)
        if status == JobStatus.QUEUED:
            self._wake()
        return job

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
