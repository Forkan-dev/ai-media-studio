from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api import jobs, topics
from app.health import check_services
from app.services.errors import InvalidStateError, NotFoundError

app = FastAPI(title="AI Media Studio")
app.include_router(topics.router)
app.include_router(jobs.router)


@app.exception_handler(NotFoundError)
def not_found(_: Request, e: NotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(e)})


@app.exception_handler(InvalidStateError)
def invalid_state(_: Request, e: InvalidStateError):
    return JSONResponse(status_code=409, content={"detail": str(e)})


@app.get("/health")
def health():
    return check_services()
