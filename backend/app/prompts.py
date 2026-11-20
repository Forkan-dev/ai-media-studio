"""Prompt templates live in backend/prompts/<brand>/<role>.md and use $placeholders."""
from string import Template

from app.config import settings


def render(folder: str, name: str, **values) -> str:
    path = settings.prompts_dir / folder / f"{name}.md"
    return Template(path.read_text()).substitute(values)
