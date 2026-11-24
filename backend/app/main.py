from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api import brands, jobs, sources, topics
from app.config import settings
from app.health import check_services
from app.services.errors import InvalidStateError, NotFoundError

app = FastAPI(title="AI Media Studio")
# generated files (images, videos, thumbnails) for the UI; no auth yet (local only)
app.mount("/media", StaticFiles(directory=settings.storage_dir), name="media")
app.include_router(brands.router)
app.include_router(topics.router)
app.include_router(jobs.router)
app.include_router(sources.router)


@app.exception_handler(NotFoundError)
def not_found(_: Request, e: NotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(e)})


@app.exception_handler(InvalidStateError)
def invalid_state(_: Request, e: InvalidStateError):
    return JSONResponse(status_code=409, content={"detail": str(e)})


@app.get("/health")
def health():
    return check_services()
