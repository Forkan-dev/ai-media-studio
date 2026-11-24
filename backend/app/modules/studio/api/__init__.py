from fastapi import APIRouter

from app.modules.studio.api import brands, jobs, topics, voices

router = APIRouter()
for r in (brands.router, topics.router, jobs.router, voices.router):
    router.include_router(r)
