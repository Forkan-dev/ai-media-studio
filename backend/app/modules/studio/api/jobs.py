"""Jobs controller: HTTP only, the work is in JobService.
Stages take minutes: the API only queues them, the worker (app.worker) runs them; the UI polls GET /jobs/{id}."""
from fastapi import APIRouter, Depends, status

from app.modules.studio.dependencies import artifact_service, brand, job_service
from app.modules.studio.pipeline.research import ResearchResult
from app.modules.studio.schemas import ImageRedo, JobCreate, JobOut, RedoRequest, ScriptEdit, ThumbnailText, VoiceRedo
from app.modules.studio.services.artifact_service import JobArtifactService
from app.modules.studio.services.job_service import JobService

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=list[JobOut])
def list_jobs(brand: str | None = None, jobs: JobService = Depends(job_service)):
    return jobs.list_jobs(brand)


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: int, jobs: JobService = Depends(job_service)):
    return jobs.get(job_id)


@router.post("", response_model=JobOut, status_code=status.HTTP_202_ACCEPTED)
def create_job(body: JobCreate, jobs: JobService = Depends(job_service)):
    """Queue a new video; the worker runs it."""
    return jobs.create(brand(body.brand), body.topic, body.style, body.auto)


@router.post("/{job_id}/approve", response_model=JobOut, status_code=status.HTTP_202_ACCEPTED)
def approve_job(job_id: int, auto: bool = False, jobs: JobService = Depends(job_service)):
    """Accept the current result (as is or edited) and queue the next stage. auto: no more pauses."""
    return jobs.advance(job_id, auto)


@router.post("/{job_id}/redo", response_model=JobOut, status_code=status.HTTP_202_ACCEPTED)
def redo_job(job_id: int, body: RedoRequest | None = None, jobs: JobService = Depends(job_service)):
    """Queue the current stage again (e.g. regenerate all images), optionally with instructions."""
    return jobs.prepare_redo(job_id, body.notes if body else "")


# ---------- step outputs: view and edit at the gates ----------

@router.get("/{job_id}/artifacts")
def get_artifacts(job_id: int, artifacts: JobArtifactService = Depends(artifact_service)):
    """Everything the steps produced so far: research, script + review, scenes, thumbnail, video."""
    return artifacts.view(job_id)


@router.put("/{job_id}/research", status_code=status.HTTP_204_NO_CONTENT)
def save_research(job_id: int, body: ResearchResult, artifacts: JobArtifactService = Depends(artifact_service)):
    artifacts.save_research(job_id, body)


@router.put("/{job_id}/script", status_code=status.HTTP_204_NO_CONTENT)
def save_script(job_id: int, body: ScriptEdit, artifacts: JobArtifactService = Depends(artifact_service)):
    artifacts.save_script(job_id, body.text)


@router.post("/{job_id}/scenes/{scene}/image", response_model=JobOut, status_code=status.HTTP_202_ACCEPTED)
def redraw_image(job_id: int, scene: int, body: ImageRedo, artifacts: JobArtifactService = Depends(artifact_service)):
    """Queue one scene's image again; the worker draws it, then the job waits at the images gate again."""
    return artifacts.redraw_image(job_id, scene, body.prompt, body.style)


@router.post("/{job_id}/images/check", response_model=JobOut, status_code=status.HTTP_202_ACCEPTED)
def check_images(job_id: int, artifacts: JobArtifactService = Depends(artifact_service)):
    """Queue the vision check of every image; results appear on the image cards."""
    return artifacts.check_images(job_id)


@router.post("/{job_id}/scenes/{scene}/voice", response_model=JobOut, status_code=status.HTTP_202_ACCEPTED)
def rerecord_voice(job_id: int, scene: int, body: VoiceRedo, artifacts: JobArtifactService = Depends(artifact_service)):
    """Queue one scene's narration again (optionally with edited words)."""
    return artifacts.rerecord_voice(job_id, scene, body.text)


@router.put("/{job_id}/thumbnail", status_code=status.HTTP_204_NO_CONTENT)
def set_thumbnail_text(job_id: int, body: ThumbnailText,
                       artifacts: JobArtifactService = Depends(artifact_service)):
    artifacts.set_thumbnail_text(job_id, body.text)
