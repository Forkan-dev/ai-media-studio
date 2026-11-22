"""Text-to-speech. Engines: kokoro (fast, 54 preset voices) and chatterbox
(slower, emotion control + voice cloning). Models load lazily on first use."""
from functools import lru_cache
from pathlib import Path

import numpy as np
import soundfile as sf


# ---------- Kokoro ----------
KOKORO_SR = 24000

# Kokoro language codes: a=US English, b=UK English, j=Japanese, z=Chinese,
# e=Spanish, f=French, h=Hindi, i=Italian, p=Portuguese
@lru_cache(maxsize=2)
def _kokoro(lang_code: str):
    from kokoro import KPipeline

    return KPipeline(lang_code=lang_code, repo_id="hexgrad/Kokoro-82M")


def _kokoro_audio(text: str, voice: str, speed: float) -> tuple[np.ndarray, int]:
    lang_code = voice[0]  # Kokoro voice names start with their language code
    chunks = [audio for _, _, audio in _kokoro(lang_code)(text, voice=voice, speed=speed)]
    return np.concatenate(chunks), KOKORO_SR


# ---------- Chatterbox ----------
@lru_cache(maxsize=1)
def _chatterbox():
    import torch
    from chatterbox.tts import ChatterboxTTS

    device = "mps" if torch.backends.mps.is_available() else "cpu"
    return ChatterboxTTS.from_pretrained(device=device)


def _chatterbox_audio(
    text: str, voice_ref: str | None, exaggeration: float, cfg_weight: float
) -> tuple[np.ndarray, int]:
    model = _chatterbox()
    wav = model.generate(
        text,
        audio_prompt_path=voice_ref,  # None = default voice; path = clone that voice
        exaggeration=exaggeration,  # 0.5 neutral, higher = more intense
        cfg_weight=cfg_weight,  # lower = slower, more deliberate pacing
    )
    return wav.squeeze(0).cpu().numpy(), model.sr


# ---------- Public API ----------
def synthesize(
    text: str,
    out_path: Path,
    engine: str = "kokoro",
    voice: str = "af_heart",
    speed: float = 1.0,
    voice_ref: str | None = None,
    exaggeration: float = 0.5,
    cfg_weight: float = 0.5,
) -> float:
    """Write narration to a WAV file. Returns duration in seconds."""
    if engine == "kokoro":
        audio, sr = _kokoro_audio(text, voice, speed)
    elif engine == "chatterbox":
        audio, sr = _chatterbox_audio(text, voice_ref, exaggeration, cfg_weight)
    else:
        raise ValueError(f"Unknown TTS engine: {engine}")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(out_path, audio, sr)
    return len(audio) / sr
