"""Prompt templates use $placeholders. `folders` are tried in order, e.g. a brand's own override
folder, then its preset (presets/facts), then the shared default/ - so a new brand needs no prompt files."""
from pathlib import Path
from string import Template

from app.core.config import settings


def find(folders: list[str], name: str) -> Path | None:
    for folder in folders:
        path = settings.prompts_dir / folder / f"{name}.md"
        if path.exists():
            return path
    return None


def render(folders: list[str], name: str, **values) -> str:
    path = find(folders, name)
    if path is None:
        raise FileNotFoundError(f"No prompt '{name}' in {folders}")
    return Template(path.read_text()).substitute(values)
