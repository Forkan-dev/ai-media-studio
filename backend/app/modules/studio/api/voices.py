"""Voice controller: preview a voice config, upload a sample to clone. HTTP only, work in VoiceService."""
from fastapi import APIRouter, Depends, UploadFile
from pydantic import BaseModel

from app.modules.studio.brand import Voice
from app.modules.studio.dependencies import brand, voice_service
from app.modules.studio.services.artifact_service import media_url
from app.modules.studio.services.voice_service import VoiceService

router = APIRouter(tags=["voices"])


class PreviewRequest(BaseModel):
    voice: Voice
    text: str | None = None


@router.post("/voice-preview")
def preview(body: PreviewRequest, voices: VoiceService = Depends(voice_service)) -> dict:
    """Short clip with these settings (a few seconds; Chatterbox loads its model the first time)."""
    return {"url": media_url(voices.preview(body.voice, body.text))}


@router.post("/brands/{slug}/voice-sample")
async def upload_sample(slug: str, file: UploadFile, voices: VoiceService = Depends(voice_service)) -> dict:
    """Store a voice clip for Chatterbox to clone; returns the path for voice.voice_ref."""
    brand(slug)  # 404 for an unknown brand
    path = voices.save_sample(slug, file.filename or "voice.wav", await file.read())
    return {"path": str(path), "url": media_url(path)}
