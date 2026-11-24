"""ClipForge endpoints shaped for the UI screens. No business logic: it calls the system backend."""
from fastapi import APIRouter
from pydantic import BaseModel

from app.modules.clipforge import client

router = APIRouter(prefix="/clipforge", tags=["clipforge"])


class SourceCreate(BaseModel):
    url: str | None = None
    file: str | None = None


@router.get("/sources")
async def list_sources():
    return await client.sources()


@router.get("/sources/{source_id}")
async def get_source(source_id: int):
    return await client.source(source_id)


@router.post("/sources", status_code=202)
async def add_source(body: SourceCreate):
    return await client.add_source(body.model_dump())


@router.post("/sources/{source_id}/detect", status_code=202)
async def detect(source_id: int):
    return await client.detect(source_id)
