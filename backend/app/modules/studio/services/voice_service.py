"""Voice settings helpers: preview a voice config and store custom voice samples (Chatterbox cloning)."""
import hashlib
import re
from pathlib import Path

from app.core.clients.tts import synthesize
from app.core.errors import InvalidInputError
from app.modules.studio.brand import Voice

PREVIEW_TEXT = "Here is something surprising about your brain. Most people never notice it, but you will."
SAMPLE_TYPES = (".wav", ".mp3", ".m4a", ".flac")
MAX_SAMPLE_BYTES = 20 * 1024 * 1024  # 20 MB: a clone needs only 5-20 seconds of speech


class VoiceService:
    def __init__(self, storage: Path):
        self._previews = storage / "previews"
        self._samples = storage / "voices"

    def preview(self, voice: Voice, text: str | None = None) -> Path:
        """A short clip with these voice settings (cached: the same settings give the same file)."""
        text = (text or PREVIEW_TEXT).strip()[:300]
        key = hashlib.sha1(f"{voice.model_dump_json()}|{text}".encode()).hexdigest()[:16]
        path = self._previews / f"{key}.wav"
        if not path.exists():
            self._previews.mkdir(parents=True, exist_ok=True)
            synthesize(text, path, engine=voice.engine, voice=voice.voice, speed=voice.speed,
                       voice_ref=voice.voice_ref, exaggeration=voice.exaggeration, cfg_weight=voice.cfg_weight)
        return path

    def save_sample(self, brand: str, filename: str, data: bytes) -> Path:
        """A voice clip to clone (Chatterbox). 5-20 seconds of clear speech works best."""
        suffix = Path(filename).suffix.lower()
        if suffix not in SAMPLE_TYPES:
            raise InvalidInputError(f"Use an audio file: {', '.join(SAMPLE_TYPES)}")
        if len(data) > MAX_SAMPLE_BYTES:
            raise InvalidInputError("The file is too large (max 20 MB); 5-20 seconds of speech is enough")
        name = re.sub(r"[^a-z0-9_-]+", "_", Path(filename).stem.lower()).strip("_") or "voice"
        path = self._samples / brand / f"{name}{suffix}"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path
