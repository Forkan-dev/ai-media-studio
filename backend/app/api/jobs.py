"""Jobs controller: HTTP only, the work is in JobService.
Stages take minutes, so they run in the background; the UI polls GET /jobs/{id}."""
from fastapi import APIRouter, BackgroundTasks, Depends, status

from app.dependencies import brand, job_service
from app.schemas import JobCreate, JobOut
from app.services.job_service import JobService

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=list[JobOut])
def list_jobs(brand: str | None = None, jobs: JobService = Depends(job_service)):
    return jobs.list_jobs(brand)


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: int, jobs: JobService = Depends(job_service)):
    return jobs.get(job_id)


@router.post("", response_model=JobOut, status_code=status.HTTP_202_ACCEPTED)
def create_job(body: JobCreate, background: BackgroundTasks, jobs: JobService = Depends(job_service)):
    job = jobs.create(brand(body.brand), body.topic, body.style)
    background.add_task(jobs.run, job.id, body.auto)
    return job


@router.post("/{job_id}/approve", response_model=JobOut, status_code=status.HTTP_202_ACCEPTED)
def approve_job(job_id: int, background: BackgroundTasks, auto: bool = False,
                jobs: JobService = Depends(job_service)):
    """Accept the current result (as is or edited) and start the next stage."""
    job = jobs.check_can_approve(job_id)  # fail now (409), not later in the background
    background.add_task(jobs.approve, job_id, auto)
    return job


@router.post("/{job_id}/redo", response_model=JobOut, status_code=status.HTTP_202_ACCEPTED)
def redo_job(job_id: int, background: BackgroundTasks, jobs: JobService = Depends(job_service)):
    """Run the current stage again (e.g. regenerate all images)."""
    job = jobs.check_can_redo(job_id)
    background.add_task(jobs.redo, job_id)
    return job
