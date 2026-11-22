"""Produce: storyboard -> images, then voice + captions -> final MP4.
Finished temp files are reused on rerun; they are deleted when the job is done."""
import re
from datetime import date
from pathlib import Path

import numpy as np
import soundfile as sf

from app.brand import Brand
from app.config import settings
from app.pipeline.image_check import check_image
from app.pipeline.storyboard import Storyboard
from app.clients import render
from app.clients.captions import write_ass
from app.clients.comfy import ImageSpec, free_memory, generate_image
from app.clients.llm import unload
from app.clients.tts import synthesize
from app.clients.whisper import transcribe_words

SCENE_GAP = 0.15  # seconds of silence after each scene's narration
TEMP_PATTERNS = ("scene_*.png", "scene_*.wav", "narration.wav", "captions.ass")  # thumbnail files are kept
MAX_IMAGE_RETRIES = 2  # rounds of regenerating images that fail the vision check


def video_folder(brand: Brand, topic: str, style: str, day: date | None = None) -> Path:
    """storage/videos/<brand>/<YYYY-MM-DD>_<topic>_<style>/"""
    slug = re.sub(r"[^a-z0-9]+", "-", topic.lower()).strip("-")[:50]
    return settings.storage_dir / "videos" / brand.slug / f"{(day or date.today()).isoformat()}_{slug}_{style}"


def cleanup(folder: Path) -> None:
    """Delete scene images, audio clips and temp files; keep final.mp4, script, storyboard, metadata."""
    for pattern in TEMP_PATTERNS:
        for f in folder.glob(pattern):
            f.unlink()


def generate_scene_image(brand: Brand, style: str, prompt: str, path: Path) -> None:
    im, st = brand.images, brand.images.style(style)
    w, h = (832, 1216) if brand.format == "short" else (1216, 832)
    generate_image(ImageSpec(
        f"{st.style}, {prompt}",  # style first: SDXL weights early words more
        st.negative, checkpoint=im.checkpoint, lora=im.lora, lora_weight=st.lora_weight,
        width=w, height=h, steps=im.steps, cfg=im.cfg, sampler=im.sampler, scheduler=im.scheduler,
    ), path)


def _images(brand: Brand, sb: Storyboard, out: Path) -> tuple[list[Path], list[int]]:
    """Generate missing images, then let the vision model check them; redo failed ones.
    Returns the image paths and the 1-based scene numbers that still fail (flags for review)."""
    paths = [out / f"scene_{i:02d}.png" for i in range(1, len(sb.scenes) + 1)]
    todo = [i for i, p in enumerate(paths) if not p.exists()]
    for round_no in range(MAX_IMAGE_RETRIES + 1):
        for i in todo:
            generate_scene_image(brand, sb.style, sb.scenes[i].image_prompt, paths[i])
        free_memory()  # SDXL out, vision model in
        checks = {i: check_image(brand, sb.style, sb.scenes[i].image_prompt, paths[i])
                  for i in (range(len(paths)) if round_no == 0 else todo)}
        unload()  # vision model out, SDXL in
        todo = [i for i, c in checks.items() if not c.ok]
        for i in todo:
            print(f"image check failed, scene {i + 1}: {checks[i].reason}", flush=True)
        if not todo:
            break
    return paths, [i + 1 for i in todo]  # still-failing images stay; they are flagged for review


def _voice(brand: Brand, sb: Storyboard, out: Path) -> tuple[Path, list[float]]:
    """Narrate each scene, join with short gaps. Returns the audio file and each scene's duration."""
    v = brand.voice
    chunks, durations, sr = [], [], 24000
    for i, scene in enumerate(sb.scenes, 1):
        path = out / f"scene_{i:02d}.wav"
        if not path.exists():
            synthesize(scene.narration, path, engine=v.engine, voice=v.voice, speed=v.speed,
                       voice_ref=v.voice_ref, exaggeration=v.exaggeration)
        audio, sr = sf.read(path)
        chunks += [audio, np.zeros(int(sr * SCENE_GAP))]
        durations.append(len(audio) / sr + SCENE_GAP)
    narration = out / "narration.wav"
    sf.write(narration, np.concatenate(chunks), sr)
    return narration, durations


def make_images(brand: Brand, sb: Storyboard, out: Path) -> list[int]:
    """Missing scene images are made and checked. Returns the scene numbers that still fail the check."""
    return _images(brand, sb, out)[1]


def render_final(brand: Brand, sb: Storyboard, out: Path) -> Path:
    """Scene images (already made) + voice + captions -> final.mp4."""
    images = [out / f"scene_{i:02d}.png" for i in range(1, len(sb.scenes) + 1)]
    audio, durations = _voice(brand, sb, out)
    captions = write_ass(
        transcribe_words(audio, language=brand.language, script=" ".join(s.narration for s in sb.scenes)),
        out / "captions.ass", size=brand.size,
        font_size=brand.look.caption_font_size, max_words=brand.look.caption_max_words,
    )
    scenes = [render.Scene(img, dur, s.motion, s.transition)
              for img, dur, s in zip(images, durations, sb.scenes)]
    return render.render_video(scenes, audio, out / "final.mp4", captions=captions,
                               size=brand.size, transition=brand.look.transition_seconds)
