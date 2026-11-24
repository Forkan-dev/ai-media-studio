"""System backend API: all business logic, internal only. The UI talks to the BFF (../bff), which calls this.
Long jobs are only queued here; the worker process (app.worker) runs them.

Modules are mounted under their own prefix and never import each other; they share only app.core."""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.errors import InvalidStateError, NotFoundError
from app.core.health import check_services
from app.modules import clipforge, studio

app = FastAPI(title="Framewise System")
app.mount("/media", StaticFiles(directory=settings.storage_dir), name="media")  # generated files
app.include_router(studio.router, prefix="/studio")
app.include_router(clipforge.router, prefix="/clipforge")


@app.exception_handler(NotFoundError)
def not_found(_: Request, e: NotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(e)})


@app.exception_handler(InvalidStateError)
def invalid_state(_: Request, e: InvalidStateError):
    return JSONResponse(status_code=409, content={"detail": str(e)})


@app.get("/health")
def health():
    return check_services()
