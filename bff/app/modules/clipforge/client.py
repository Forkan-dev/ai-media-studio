"""Calls to the system backend's ClipForge module."""
from typing import Any

from app.core.system import system

BASE = "/clipforge"


async def sources() -> list[dict]:
    return await system.get(f"{BASE}/sources")


async def source(source_id: int) -> dict:
    return await system.get(f"{BASE}/sources/{source_id}")


async def add_source(body: dict[str, Any]) -> dict:
    return await system.post(f"{BASE}/sources", body)


async def detect(source_id: int) -> dict:
    return await system.post(f"{BASE}/sources/{source_id}/detect")
