"""Backend for frontend: the only API the UI talks to. It shapes data for screens and calls the
system backend (../backend) for all work. Auth and RBAC will live here."""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from starlette.background import BackgroundTask

from app.core.system import system
from app.modules.clipforge.router import router as clipforge_router
from app.modules.studio.router import router as studio_router

# headers passed through for media, so the browser can seek in videos (range requests)
MEDIA_HEADERS = ("content-type", "content-length", "content-range", "accept-ranges", "last-modified", "etag")


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    await system.close()


app = FastAPI(title="Framewise BFF", lifespan=lifespan)
app.include_router(studio_router)
app.include_router(clipforge_router)


@app.get("/health")
async def health():
    return await system.get("/health")


@app.get("/media/{path:path}")
async def media(path: str, request: Request):
    """Generated files (images, videos), streamed from the system backend."""
    headers = {"range": request.headers["range"]} if "range" in request.headers else {}
    req = system.http.build_request("GET", f"/media/{path}", headers=headers)
    resp = await system.http.send(req, stream=True)
    return StreamingResponse(
        resp.aiter_raw(), status_code=resp.status_code,
        headers={k: v for k, v in resp.headers.items() if k in MEDIA_HEADERS},
        background=BackgroundTask(resp.aclose),
    )
