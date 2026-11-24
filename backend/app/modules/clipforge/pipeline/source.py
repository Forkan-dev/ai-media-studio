"""Step 1: a long video -> folder with video.mp4, audio.wav (16 kHz mono) and info.json."""
import json
import subprocess
from pathlib import Path

from app.core.clients.youtube import VideoInfo, download, fetch_info
from app.core.config import settings

AUDIO_RATE = 16000  # Whisper and loudness analysis both work on 16 kHz mono


def probe_duration(video: Path) -> float:
    out = subprocess.run(
        [settings.ffmpeg_bin.replace("ffmpeg", "ffprobe"), "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(video)], capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def extract_audio(video: Path, out: Path) -> Path:
    subprocess.run([settings.ffmpeg_bin, "-y", "-loglevel", "error", "-i", str(video), "-vn",
                    "-ac", "1", "-ar", str(AUDIO_RATE), str(out)], check=True)
    return out


def prepare_url(url: str, folder: Path) -> VideoInfo:
    """Download (720p) + chat replay for past streams + audio. Saves info.json (with the heatmap)."""
    info = fetch_info(url)
    video = download(url, folder, live_chat=info.was_live)
    extract_audio(video, folder / "audio.wav")
    (folder / "info.json").write_text(json.dumps(info.__dict__, indent=1))
    return info


def prepare_file(path: Path, folder: Path) -> VideoInfo:
    """A video on this machine: linked (not copied: streams are many GB) + audio."""
    if not path.exists():
        raise FileNotFoundError(f"No video file at {path}")
    video = folder / f"video{path.suffix.lower()}"
    video.unlink(missing_ok=True)
    video.symlink_to(path.resolve())
    info = VideoInfo(title=path.stem, channel="", duration=probe_duration(video), was_live=False, heatmap=None)
    extract_audio(video, folder / "audio.wav")
    (folder / "info.json").write_text(json.dumps(info.__dict__, indent=1))
    return info
