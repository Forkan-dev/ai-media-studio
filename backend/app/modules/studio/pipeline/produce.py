"""Produce: storyboard -> images, then voice + captions -> final MP4.
Finished temp files are reused on rerun; they are deleted when the job is done."""
import re
from datetime import date
from pathlib import Path

import numpy as np
import soundfile as sf

from app.modules.studio.brand import Brand
from app.core.config import settings
from app.modules.studio.pipeline.image_check import check_image
from app.modules.studio.pipeline.storyboard import Scene, Storyboard
from app.core.clients import render
from app.core.clients.captions import write_ass
from app.core.clients.comfy import ImageSpec, free_memory, generate_image
from app.core.clients.llm import unload
from app.core.clients.tts import synthesize
from app.core.clients.whisper import transcribe_words
from app.core.progress import Report, noop

SCENE_GAP = 0.15  # seconds of silence after each scene's narration
TEMP_PATTERNS = ("scene_*.png", "scene_*.wav", "narration.wav", "captions.ass")  # thumbnail files are kept
MAX_IMAGE_RETRIES = 2  # thumbnail: rounds of regenerating an image that fails the vision check


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


def draw_scene(brand: Brand, sb: Storyboard, i: int, out: Path) -> Path:
    """One scene's image (0-based i) in the scene's own style -> scene_XX.png.
    Records what it was drawn with in the storyboard (saved by the caller)."""
    scene = sb.scenes[i]
    path = out / f"scene_{i + 1:02d}.png"
    generate_scene_image(brand, sb.style_of(scene), scene.image_prompt, path)
    scene.drawn = sb.key(scene)
    return path


def make_images(brand: Brand, sb: Storyboard, out: Path, report: Report = noop) -> None:
    """Draw the scenes that have no image yet (a test image from the storyboard gate is kept)."""
    todo = [i for i in range(len(sb.scenes)) if not (out / f"scene_{i + 1:02d}.png").exists()]
    for k, i in enumerate(todo, 1):
        report(f"Drawing image {k} of {len(todo)} · scene {i + 1}")
        draw_scene(brand, sb, i, out)
        (out / "storyboard.json").write_text(sb.model_dump_json(indent=1))


def check_images(brand: Brand, sb: Storyboard, out: Path, report: Report = noop) -> dict[int, dict]:
    """Vision check of every image against its prompt (on request). {scene: {"ok", "reason"}}"""
    free_memory()  # SDXL out, vision model in
    results = {}
    for i, scene in enumerate(sb.scenes, 1):
        report(f"Checking image {i} of {len(sb.scenes)}")
        c = check_image(brand, sb.style_of(scene), scene.image_prompt, out / f"scene_{i:02d}.png")
        results[i] = {"ok": c.ok, "reason": c.reason}
    unload()  # vision model out, SDXL in
    return results


#  Chatterbox (exaggeration, cfg_weight) per emotion. Higher exaggeration = more intense;
#  lower cfg_weight keeps intense lines from rushing (Chatterbox guidance). Above ~0.9 gets unstable.
EMOTION_VOICE: dict[str, tuple[float, float]] = {
    "calm": (0.4, 0.5), "sad": (0.45, 0.5), "curious": (0.55, 0.5), "happy": (0.6, 0.45),
    "confused": (0.6, 0.45), "nervous": (0.65, 0.4), "excited": (0.75, 0.35),
    "panicked": (0.85, 0.3), "shocked": (0.9, 0.3),
}


def _voice_settings(brand: Brand, scene: Scene) -> tuple[float, float]:
    if brand.voice.scene_emotions:
        return EMOTION_VOICE[scene.emotion]
    return brand.voice.exaggeration, brand.voice.cfg_weight


def record_scene(brand: Brand, scene: Scene, path: Path) -> None:
    """One scene's narration -> path (wav), with the brand's voice and the scene's emotion."""
    v = brand.voice
    exaggeration, cfg_weight = _voice_settings(brand, scene)
    synthesize(scene.narration, path, engine=v.engine, voice=v.voice, speed=v.speed,
               voice_ref=v.voice_ref, exaggeration=exaggeration, cfg_weight=cfg_weight)


def make_voice(brand: Brand, sb: Storyboard, out: Path, report: Report = noop) -> None:
    """Record the scenes that have no audio yet (scene_XX.wav)."""
    for i, scene in enumerate(sb.scenes, 1):
        path = out / f"scene_{i:02d}.wav"
        if not path.exists():
            report(f"Recording voice {i} of {len(sb.scenes)}")
            record_scene(brand, scene, path)


def _voice(brand: Brand, sb: Storyboard, out: Path, report: Report = noop) -> tuple[Path, list[float]]:
    """Scene audio (recorded if missing), joined with short gaps. Returns the file and each scene's duration."""
    make_voice(brand, sb, out, report)
    chunks, durations, sr = [], [], 24000
    for i in range(1, len(sb.scenes) + 1):
        audio, sr = sf.read(out / f"scene_{i:02d}.wav")
        chunks += [audio, np.zeros(int(sr * SCENE_GAP))]
        durations.append(len(audio) / sr + SCENE_GAP)
    narration = out / "narration.wav"
    sf.write(narration, np.concatenate(chunks), sr)
    return narration, durations



def render_final(brand: Brand, sb: Storyboard, out: Path, report: Report = noop) -> Path:
    """Scene images (already made) + voice + captions -> final.mp4."""
    images = [out / f"scene_{i:02d}.png" for i in range(1, len(sb.scenes) + 1)]
    audio, durations = _voice(brand, sb, out, report)
    report("Timing the captions")
    captions = write_ass(
        transcribe_words(audio, language=brand.language, script=" ".join(s.narration for s in sb.scenes)),
        out / "captions.ass", size=brand.size,
        font_size=brand.look.caption_font_size, max_words=brand.look.caption_max_words,
    )
    scenes = [render.Scene(img, dur, s.motion, s.transition)
              for img, dur, s in zip(images, durations, sb.scenes)]
    report("Rendering the video")
    return render.render_video(scenes, audio, out / "final.mp4", captions=captions,
                               size=brand.size, transition=brand.look.transition_seconds)
