"""Produce: storyboard -> images + voice + captions -> final MP4.
Finished temp files are reused on rerun; they are deleted after a successful render."""
import re
from datetime import date
from pathlib import Path

import numpy as np
import soundfile as sf

from app.brand import Brand
from app.config import settings
from app.pipeline.image_check import check_image
from app.pipeline.storyboard import Storyboard
from app.services import render
from app.services.captions import write_ass
from app.services.comfy import ImageSpec, free_memory, generate_image
from app.services.llm import unload
from app.services.tts import synthesize
from app.services.whisper import transcribe_words

SCENE_GAP = 0.15  # seconds of silence after each scene's narration
TEMP_PATTERNS = ("scene_*.png", "scene_*.wav", "narration.wav", "captions.ass")
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


def _generate(brand: Brand, sb: Storyboard, prompt: str, path: Path) -> None:
    im, st = brand.images, brand.images.style(sb.style)
    w, h = (832, 1216) if brand.format == "short" else (1216, 832)
    generate_image(ImageSpec(
        f"{st.style}, {prompt}",  # style first: SDXL weights early words more
        st.negative, checkpoint=im.checkpoint, lora=im.lora, lora_weight=st.lora_weight,
        width=w, height=h, steps=im.steps, cfg=im.cfg, sampler=im.sampler, scheduler=im.scheduler,
    ), path)


def _images(brand: Brand, sb: Storyboard, out: Path) -> list[Path]:
    """Generate missing images, then let the vision model check them; redo failed ones."""
    paths = [out / f"scene_{i:02d}.png" for i in range(1, len(sb.scenes) + 1)]
    todo = [i for i, p in enumerate(paths) if not p.exists()]
    for round_no in range(MAX_IMAGE_RETRIES + 1):
        for i in todo:
            _generate(brand, sb, sb.scenes[i].image_prompt, paths[i])
        free_memory()  # SDXL out, vision model in
        checks = {i: check_image(brand, sb.style, sb.scenes[i].image_prompt, paths[i])
                  for i in (range(len(paths)) if round_no == 0 else todo)}
        unload()  # vision model out, SDXL in
        todo = [i for i, c in checks.items() if not c.ok]
        for i in todo:
            print(f"image check failed, scene {i + 1}: {checks[i].reason}", flush=True)
        if not todo:
            break
    return paths  # images still failing after the retries stay; the human review screen catches them


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


def produce_video(brand: Brand, sb: Storyboard, out: Path) -> Path:
    out.mkdir(parents=True, exist_ok=True)
    (out / "storyboard.json").write_text(sb.model_dump_json(indent=1))
    (out / "script.txt").write_text(" ".join(s.narration for s in sb.scenes))
    images = _images(brand, sb, out)
    audio, durations = _voice(brand, sb, out)
    captions = write_ass(
        transcribe_words(audio, language=brand.language, script=" ".join(s.narration for s in sb.scenes)),
        out / "captions.ass", size=brand.size,
        font_size=brand.look.caption_font_size, max_words=brand.look.caption_max_words,
    )
    scenes = [render.Scene(img, dur, s.motion, s.transition)
              for img, dur, s in zip(images, durations, sb.scenes)]
    final = render.render_video(scenes, audio, out / "final.mp4", captions=captions,
                                size=brand.size, transition=brand.look.transition_seconds)
    cleanup(out)  # only reached when the render succeeded
    return final
