"""YouTube via yt-dlp: video info, "most replayed" heatmap, live chat replay and download."""
from dataclasses import dataclass
from pathlib import Path

import yt_dlp


@dataclass
class VideoInfo:
    title: str
    channel: str
    duration: float  # seconds
    was_live: bool
    heatmap: list[dict] | None  # [{start_time, end_time, value 0-1}], None when YouTube has none


def fetch_info(url: str) -> VideoInfo:
    with yt_dlp.YoutubeDL({"quiet": True, "skip_download": True}) as ydl:
        info = ydl.extract_info(url, download=False)
    return VideoInfo(
        title=info.get("title", ""), channel=info.get("channel", ""), duration=float(info.get("duration") or 0),
        was_live=bool(info.get("was_live")), heatmap=info.get("heatmap"),
    )


def download(url: str, folder: Path, max_height: int = 720, live_chat: bool = False) -> Path:
    """Video as folder/video.mp4 (max_height: smaller files, enough for Shorts).
    live_chat: also save the chat replay as folder/video.live_chat.json."""
    opts = {
        "quiet": True, "noprogress": True,
        "format": f"bv*[height<={max_height}][ext=mp4]+ba[ext=m4a]/b[height<={max_height}]",
        "merge_output_format": "mp4",
        "outtmpl": str(folder / "video.%(ext)s"),
    }
    if live_chat:
        opts |= {"writesubtitles": True, "subtitleslangs": ["live_chat"]}
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([url])
    return folder / "video.mp4"
