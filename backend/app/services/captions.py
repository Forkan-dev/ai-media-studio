"""Word-by-word animated captions as an ASS subtitle file (burned in by FFmpeg)."""
from pathlib import Path

from app.services.whisper import Word

HIGHLIGHT = r"{\c&H00E5FF&}"  # ASS colours are BGR: this is yellow
RESET = r"{\c&HFFFFFF&}"  # back to white only; a full style reset shifted the line
BOTTOM_MARGIN = 0.2  # captions sit 20% above the bottom edge, clear of YouTube/Reels buttons

HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: {w}
PlayResY: {h}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, Alignment, Outline, Shadow, MarginL, MarginR, MarginV
Style: Word,Arial,{size},&H00FFFFFF,&H00000000,&H80000000,-1,2,6,2,60,60,{margin_v}

[Events]
Format: Layer, Start, End, Style, Text
"""


def _ts(seconds: float) -> str:
    h, rem = divmod(max(seconds, 0), 3600)
    m, s = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def _chunks(words: list[Word], max_words: int) -> list[list[Word]]:
    """Group words into short phrases; a sentence end always closes a phrase."""
    chunks, current = [], []
    for w in words:
        current.append(w)
        if len(current) == max_words or w.text[-1:] in ".?!,":
            chunks.append(current)
            current = []
    if current:
        chunks.append(current)
    return chunks


def write_ass(
    words: list[Word], out_path: Path, size: tuple[int, int] = (1080, 1920),
    font_size: int = 96, max_words: int = 3,
) -> Path:
    """Show each phrase while it is spoken, bottom middle, with the current word highlighted."""
    margin_v = int(size[1] * BOTTOM_MARGIN)
    lines = [HEADER.format(w=size[0], h=size[1], size=font_size, margin_v=margin_v)]
    for chunk in _chunks(words, max_words):
        for i, word in enumerate(chunk):
            end = chunk[i + 1].start if i + 1 < len(chunk) else word.end
            text = " ".join(
                f"{HIGHLIGHT}{w.text}{RESET}" if j == i else w.text for j, w in enumerate(chunk)
            )
            lines.append(f"Dialogue: 0,{_ts(word.start)},{_ts(end)},Word,{text}")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n")
    return out_path
