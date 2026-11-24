"""Calls to the system backend's Studio module."""
from typing import Any

from app.core.system import system

BASE = "/studio"


async def presets() -> list[dict]:
    return await system.get(f"{BASE}/presets")


async def brands() -> list[dict]:
    return await system.get(f"{BASE}/brands")


async def create_brand(body: dict[str, Any]) -> dict:
    return await system.post(f"{BASE}/brands", body)


async def brand(slug: str) -> dict:
    return await system.get(f"{BASE}/brands/{slug}")


async def brand_config(slug: str) -> dict:
    return await system.get(f"{BASE}/brands/{slug}/config")


async def update_brand(slug: str, config: dict[str, Any]) -> dict:
    return await system.put(f"{BASE}/brands/{slug}", config)


async def brand_options() -> dict:
    return await system.get(f"{BASE}/brand-options")


async def topics(slug: str) -> list[dict]:
    return await system.get(f"{BASE}/brands/{slug}/topics")


async def discover_topics(slug: str) -> list[dict]:
    return await system.post(f"{BASE}/brands/{slug}/topics/discover")


async def jobs(brand: str | None = None) -> list[dict]:
    return await system.get(f"{BASE}/jobs", **({"brand": brand} if brand else {}))


async def job(job_id: int) -> dict:
    return await system.get(f"{BASE}/jobs/{job_id}")


async def create_job(body: dict[str, Any]) -> dict:
    return await system.post(f"{BASE}/jobs", body)


async def approve_job(job_id: int, auto: bool) -> dict:
    return await system.post(f"{BASE}/jobs/{job_id}/approve", auto=auto)


async def redo_job(job_id: int, notes: str) -> dict:
    return await system.post(f"{BASE}/jobs/{job_id}/redo", {"notes": notes})


async def artifacts(job_id: int) -> dict:
    return await system.get(f"{BASE}/jobs/{job_id}/artifacts")


async def save_research(job_id: int, research: dict[str, Any]) -> None:
    await system.put_empty(f"{BASE}/jobs/{job_id}/research", research)


async def save_script(job_id: int, text: str) -> None:
    await system.put_empty(f"{BASE}/jobs/{job_id}/script", {"text": text})


async def redraw_image(job_id: int, scene: int, prompt: str | None, style: str | None) -> dict:
    return await system.post(f"{BASE}/jobs/{job_id}/scenes/{scene}/image", {"prompt": prompt, "style": style})


async def check_images(job_id: int) -> dict:
    return await system.post(f"{BASE}/jobs/{job_id}/images/check")


async def rerecord_voice(job_id: int, scene: int, text: str | None) -> dict:
    return await system.post(f"{BASE}/jobs/{job_id}/scenes/{scene}/voice", {"text": text})


async def voice_preview(body: dict[str, Any]) -> dict:
    return await system.post(f"{BASE}/voice-preview", body)


async def upload_voice_sample(slug: str, filename: str, data: bytes, content_type: str) -> dict:
    return await system.post_file(f"{BASE}/brands/{slug}/voice-sample", filename, data, content_type)


async def set_thumbnail_text(job_id: int, text: str) -> None:
    await system.put_empty(f"{BASE}/jobs/{job_id}/thumbnail", {"text": text})
