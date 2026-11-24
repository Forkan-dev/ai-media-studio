from fastapi import APIRouter

from app.modules.clipforge.api import sources

router = APIRouter()
router.include_router(sources.router)
