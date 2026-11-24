"""ClipForge sources controller: HTTP only, the work is in SourceService.
Preparing (download + audio) takes minutes, so it runs in the background; the UI polls GET /sources/{id}."""
from fastapi import APIRouter, BackgroundTasks, Depends, status

from app.dependencies import source_service
from app.schemas import SourceCreate, SourceOut
from app.services.source_service import SourceService

router = APIRouter(prefix="/sources", tags=["clipforge"])


@router.get("", response_model=list[SourceOut])
def list_sources(sources: SourceService = Depends(source_service)):
    return sources.list_sources()


@router.get("/{source_id}", response_model=SourceOut)
def get_source(source_id: int, sources: SourceService = Depends(source_service)):
    return sources.get(source_id)


@router.post("/{source_id}/detect", response_model=SourceOut, status_code=status.HTTP_202_ACCEPTED)
def detect_moments(source_id: int, background: BackgroundTasks, sources: SourceService = Depends(source_service)):
    """Find hot moments in the background; the result is candidates.json."""
    source = sources.check_can_detect(source_id)  # fail now (409), not later in the background
    background.add_task(sources.detect, source_id)
    return source


@router.post("", response_model=SourceOut, status_code=status.HTTP_202_ACCEPTED)
def add_source(body: SourceCreate, background: BackgroundTasks, sources: SourceService = Depends(source_service)):
    source = sources.add(url=body.url, file=body.file)
    background.add_task(sources.prepare, source.id)
    return source
