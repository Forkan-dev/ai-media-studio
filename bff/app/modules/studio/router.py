"""Studio endpoints shaped for the UI screens. No business logic: it combines system calls."""
import asyncio
from typing import Any

from fastapi import APIRouter, UploadFile
from pydantic import BaseModel

from app.modules.studio import client

router = APIRouter(prefix="/studio", tags=["studio"])
MAX_UPLOAD_BYTES = 20 * 1024 * 1024  # same as the system's voice sample limit


class BrandCreate(BaseModel):
    preset: str
    name: str
    niche: str
    tone: str


class JobCreate(BaseModel):
    brand: str
    topic: str
    style: str | None = None
    auto: bool = False


@router.get("/presets")
async def list_presets():
    return await client.presets()


@router.get("/brands")
async def list_brands():
    return await client.brands()


@router.post("/brands", status_code=201)
async def create_brand(body: BrandCreate):
    return await client.create_brand(body.model_dump())


@router.get("/brands/{slug}")
async def brand_page(slug: str):
    """Brand screen in one call: the brand, its topics (best first) and its recent jobs."""
    brand, topics, jobs = await asyncio.gather(client.brand(slug), client.topics(slug), client.jobs(slug))
    return {"brand": brand, "topics": topics, "jobs": jobs[:10]}


@router.get("/brands/{slug}/settings")
async def brand_settings(slug: str):
    """Settings screen in one call: the full config and the allowed values for the form."""
    config, options = await asyncio.gather(client.brand_config(slug), client.brand_options())
    return {"config": config, "options": options}


@router.put("/brands/{slug}")
async def update_brand(slug: str, config: dict[str, Any]):
    return await client.update_brand(slug, config)


@router.post("/brands/{slug}/topics/discover")
async def discover_topics(slug: str):
    return await client.discover_topics(slug)


@router.get("/jobs")
async def list_jobs(brand: str | None = None):
    return await client.jobs(brand)


@router.get("/jobs/{job_id}")
async def job_page(job_id: int):
    """Job screen in one call: the job (stage, status, flags) and everything its steps produced."""
    job, artifacts = await asyncio.gather(client.job(job_id), client.artifacts(job_id))
    brand = await client.brand(job["brand"])
    return {"job": job, "format": brand["format"], "styles": brand["styles"], **artifacts}


class ScriptEdit(BaseModel):
    text: str


class ImageRedo(BaseModel):
    prompt: str | None = None
    style: str | None = None


class VoiceRedo(BaseModel):
    text: str | None = None


class ThumbnailText(BaseModel):
    text: str


@router.put("/jobs/{job_id}/research", status_code=204)
async def save_research(job_id: int, research: dict[str, Any]):
    await client.save_research(job_id, research)


@router.put("/jobs/{job_id}/script", status_code=204)
async def save_script(job_id: int, body: ScriptEdit):
    await client.save_script(job_id, body.text)


@router.post("/jobs/{job_id}/scenes/{scene}/image", status_code=202)
async def redraw_image(job_id: int, scene: int, body: ImageRedo):
    return await client.redraw_image(job_id, scene, body.prompt, body.style)


@router.post("/jobs/{job_id}/images/check", status_code=202)
async def check_images(job_id: int):
    return await client.check_images(job_id)


@router.post("/jobs/{job_id}/scenes/{scene}/voice", status_code=202)
async def rerecord_voice(job_id: int, scene: int, body: VoiceRedo):
    return await client.rerecord_voice(job_id, scene, body.text)


@router.post("/voice-preview")
async def voice_preview(body: dict[str, Any]):
    return await client.voice_preview(body)


@router.post("/brands/{slug}/voice-sample")
async def upload_voice_sample(slug: str, file: UploadFile):
    data = await file.read(MAX_UPLOAD_BYTES + 1)  # the system rejects anything over its limit
    return await client.upload_voice_sample(slug, file.filename or "voice.wav", data,
                                            file.content_type or "application/octet-stream")


@router.put("/jobs/{job_id}/thumbnail", status_code=204)
async def set_thumbnail_text(job_id: int, body: ThumbnailText):
    await client.set_thumbnail_text(job_id, body.text)


@router.post("/jobs", status_code=202)
async def create_job(body: JobCreate):
    return await client.create_job(body.model_dump())


@router.post("/jobs/{job_id}/approve", status_code=202)
async def approve_job(job_id: int, auto: bool = False):
    return await client.approve_job(job_id, auto)


class RedoRequest(BaseModel):
    notes: str = ""


@router.post("/jobs/{job_id}/redo", status_code=202)
async def redo_job(job_id: int, body: RedoRequest | None = None):
    return await client.redo_job(job_id, body.notes if body else "")


@router.post("/jobs/{job_id}/reopen/{stage}")
async def reopen_job(job_id: int, stage: str):
    return await client.reopen_job(job_id, stage)


@router.put("/jobs/{job_id}/scenes/{scene}", status_code=204)
async def save_scene(job_id: int, scene: int, body: ImageRedo):
    await client.save_scene(job_id, scene, body.prompt, body.style)
