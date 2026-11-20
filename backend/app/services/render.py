"""Render still images + narration into a video with motion, transitions and captions."""
import subprocess
from dataclasses import dataclass
from pathlib import Path

from app.config import settings

ZOOM = 0.15  # how far the camera moves during one scene

# zoompan expressions: `on` = output frame number, N = frames in the scene
MOTIONS = {
    "zoom_in": ("1+{z}*on/{n}", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),
    "zoom_out": ("1+{z}-{z}*on/{n}", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),
    "pan_right": ("1+{z}", "(iw-iw/zoom)*on/{n}", "ih/2-(ih/zoom/2)"),
    "pan_left": ("1+{z}", "(iw-iw/zoom)*(1-on/{n})", "ih/2-(ih/zoom/2)"),
}


@dataclass
class Scene:
    image: Path
    duration: float  # seconds this scene is on screen
    motion: str = "zoom_in"


def _scene_filter(i: int, frames: int, motion: str, w: int, h: int, fps: int) -> str:
    z, x, y = (e.format(z=ZOOM, n=frames) for e in MOTIONS[motion])
    return (
        f"[{i}:v]crop='min(iw,ih*{w}/{h})':'min(ih,iw*{h}/{w})',"  # centre-crop to target ratio
        f"scale={w * 2}:{h * 2},"  # upscale first so the zoom is smooth, not jittery
        f"zoompan=z='{z}':x='{x}':y='{y}':d={frames}:s={w}x{h}:fps={fps},"
        f"setsar=1[v{i}]"
    )


def render_video(
    scenes: list[Scene], audio: Path, out_path: Path, captions: Path | None = None,
    size: tuple[int, int] = (1080, 1920), fps: int = 30, transition: float = 0.4,
) -> Path:
    w, h = size
    last = len(scenes) - 1
    filters, inputs = [], []
    for i, s in enumerate(scenes):
        # every scene except the last is extended so the crossfade does not shorten the video
        seconds = s.duration + (transition if i < last else 0)
        inputs += ["-i", str(s.image)]
        filters.append(_scene_filter(i, round(seconds * fps), s.motion, w, h, fps))

    prev, offset = "v0", 0.0
    for i in range(1, len(scenes)):
        offset += scenes[i - 1].duration
        filters.append(
            f"[{prev}][v{i}]xfade=transition=fade:duration={transition}:offset={offset:.3f}[x{i}]"
        )
        prev = f"x{i}"

    if captions:
        filters.append(f"[{prev}]ass='{captions}'[out]")
        prev = "out"

    total = sum(s.duration for s in scenes)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        settings.ffmpeg_bin, "-y", "-loglevel", "error", *inputs, "-i", str(audio),
        "-filter_complex", ";".join(filters),
        "-map", f"[{prev}]", "-map", f"{len(scenes)}:a",
        "-t", f"{total:.3f}", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k", str(out_path),
    ]
    subprocess.run(cmd, check=True)
    return out_path
