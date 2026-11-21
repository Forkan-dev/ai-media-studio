"""Speech-to-text with word timings (mlx-whisper, Apple GPU)."""
from dataclasses import asdict, dataclass
from pathlib import Path

MODEL = "mlx-community/whisper-large-v3-turbo"


@dataclass
class Word:
    text: str
    start: float
    end: float


def transcribe_words(audio_path: Path, language: str | None = None, script: str | None = None) -> list[Word]:
    """Return every spoken word with its start and end time in seconds.
    `script`: the known text, so names and terms are spelled correctly (e.g. "Barry Manilow")."""
    import mlx_whisper

    result = mlx_whisper.transcribe(
        str(audio_path), path_or_hf_repo=MODEL, word_timestamps=True, language=language,
        initial_prompt=script,
    )
    return [
        Word(w["word"].strip(), round(w["start"], 2), round(w["end"], 2))
        for segment in result["segments"]
        for w in segment["words"]
    ]


def to_dicts(words: list[Word]) -> list[dict]:
    return [asdict(w) for w in words]
