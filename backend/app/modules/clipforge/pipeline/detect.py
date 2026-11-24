"""Step 2: find hot moments in a long video.

Cheap signals over the WHOLE video (per second): loudness spikes, scene changes, heatmap, chat.
Then Whisper only on the top windows (minutes of audio, not hours)."""
import json
import re
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf
from pydantic import BaseModel

from app.core.clients.whisper import transcribe_words
from app.core.config import settings

WINDOW_BEFORE = 35  # seconds of setup before the peak
WINDOW_AFTER = 25  # seconds of reaction after it
MIN_GAP = 90  # candidates at least this far apart (one per moment)
MAX_CANDIDATES = 40
BASELINE_SECONDS = 120  # "loud" means loud compared with the last/next 2 minutes, not the whole video
SMOOTH_SECONDS = 5
# weight per signal; signals a video does not have are left out and the rest re-weighted
WEIGHTS = {"chat": 0.35, "heatmap": 0.3, "loudness": 0.25, "scene": 0.1}


class Word(BaseModel):
    text: str
    start: float  # seconds in the source video
    end: float


class Candidate(BaseModel):
    start: float
    end: float
    peak: float
    score: float  # 0-1, from the signals
    signals: dict[str, float]  # each signal's value at the peak, for the ranking step and the UI
    text: str = ""
    words: list[Word] = []


# ---------- signals (one value per second) ----------

def loudness(audio: Path) -> np.ndarray:
    """RMS loudness in dB per second."""
    sr = sf.info(str(audio)).samplerate
    rms = [np.sqrt(np.mean(b ** 2) + 1e-12) for b in sf.blocks(str(audio), blocksize=sr, dtype="float32")]
    return 20 * np.log10(np.array(rms))


def scene_changes(video: Path, seconds: int) -> np.ndarray:
    """Max scene-change score (0-1) per second. Only keyframes are decoded (every few seconds), on a tiny
    frame: ~10x faster than decoding every frame, and enough to see action vs calm."""
    out = subprocess.run(
        [settings.ffmpeg_bin, "-hide_banner", "-skip_frame", "nokey", "-i", str(video), "-an",
         "-vf", "scale=160:-2,select='gte(scene,0)',metadata=print:key=lavfi.scene_score:file=-",
         "-fps_mode", "passthrough", "-f", "null", "-"], capture_output=True, text=True, check=True).stdout
    scores = np.zeros(seconds)
    t = 0.0
    for line in out.splitlines():
        if m := re.search(r"pts_time:([\d.]+)", line):
            t = float(m.group(1))
        elif m := re.search(r"lavfi\.scene_score=([\d.]+)", line):
            i = int(t)
            if i < seconds:
                scores[i] = max(scores[i], float(m.group(1)))
    return scores


def heatmap(points: list[dict] | None, seconds: int) -> np.ndarray | None:
    """YouTube "most replayed" (0-1) spread over seconds."""
    if not points:
        return None
    values = np.zeros(seconds)
    for p in points:
        values[int(p["start_time"]):int(p["end_time"]) + 1] = p["value"]
    return values


def chat_rate(chat_file: Path, seconds: int) -> np.ndarray | None:
    """Chat messages per second from a yt-dlp live_chat.json (one JSON object per line)."""
    if not chat_file.exists():
        return None
    counts = np.zeros(seconds)
    for line in chat_file.read_text().splitlines():
        try:
            ms = int(json.loads(line)["replayChatItemAction"]["videoOffsetTimeMsec"])
        except (KeyError, ValueError, json.JSONDecodeError):
            continue
        if 0 <= ms // 1000 < seconds:
            counts[ms // 1000] += 1
    return counts


# ---------- scoring ----------

def _rolling(x: np.ndarray, size: int, fn) -> np.ndarray:
    pad = size // 2
    padded = np.pad(x, pad, mode="edge")
    windows = np.lib.stride_tricks.sliding_window_view(padded, size)[: len(x)]
    return fn(windows, axis=1)


def _spikes(x: np.ndarray) -> np.ndarray:
    """How far above its local baseline each second is, scaled 0-1."""
    excess = np.clip(x - _rolling(x, BASELINE_SECONDS, np.median), 0, None)
    top = np.percentile(excess, 99.5) or 1.0
    return np.clip(excess / top, 0, 1)


def combine(signals: dict[str, np.ndarray]) -> np.ndarray:
    """Weighted sum of the available signals, smoothed."""
    total = sum(WEIGHTS[k] for k in signals)
    score = sum(WEIGHTS[k] / total * v for k, v in signals.items())
    return _rolling(score, SMOOTH_SECONDS, np.mean)


def pick_windows(score: np.ndarray, signals: dict[str, np.ndarray]) -> list[Candidate]:
    """Highest peaks first, one per moment (MIN_GAP apart), each a setup + reaction window."""
    order = np.argsort(score)[::-1]
    peaks: list[int] = []
    for i in order:
        if len(peaks) == MAX_CANDIDATES:
            break
        if all(abs(i - p) >= MIN_GAP for p in peaks):
            peaks.append(int(i))
    n = len(score)
    return [Candidate(start=max(0, p - WINDOW_BEFORE), end=min(n, p + WINDOW_AFTER), peak=p,
                      score=round(float(score[p]), 3),
                      signals={k: round(float(v[p]), 3) for k, v in signals.items()})
            for p in sorted(peaks)]


# ---------- transcript of the windows ----------

def transcribe_window(audio: Path, c: Candidate, tmp: Path) -> Candidate:
    subprocess.run([settings.ffmpeg_bin, "-y", "-loglevel", "error", "-ss", str(c.start), "-to", str(c.end),
                    "-i", str(audio), str(tmp)], check=True)
    words = [Word(text=w.text, start=round(c.start + w.start, 2), end=round(c.start + w.end, 2))
             for w in transcribe_words(tmp, language="en")]
    return c.model_copy(update={"words": words, "text": " ".join(w.text for w in words)})


def detect(folder: Path) -> list[Candidate]:
    """folder has video.mp4, audio.wav, info.json (step 1). Writes candidates.json."""
    info = json.loads((folder / "info.json").read_text())
    loud = loudness(folder / "audio.wav")
    n = len(loud)
    raw = {"loudness": loud, "scene": scene_changes(folder / "video.mp4", n),
           "heatmap": heatmap(info.get("heatmap"), n), "chat": chat_rate(folder / "video.live_chat.json", n)}
    # loudness/chat/scene: spikes vs local baseline; heatmap is already "how replayed" (0-1)
    signals = {k: (v if k == "heatmap" else _spikes(v)) for k, v in raw.items() if v is not None}
    candidates = pick_windows(combine(signals), signals)
    tmp = folder / "window.wav"
    candidates = [transcribe_window(folder / "audio.wav", c, tmp) for c in candidates]
    tmp.unlink(missing_ok=True)
    (folder / "candidates.json").write_text(json.dumps([c.model_dump() for c in candidates], indent=1))
    return candidates
