"""Prompt templates use $placeholders. A brand's own file (prompts/<brand>/<role>.md) wins;
otherwise the shared prompts/default/<role>.md is used, so a new brand works without prompt files."""
from string import Template

from app.config import settings


def render(folder: str, name: str, **values) -> str:
    path = settings.prompts_dir / folder / f"{name}.md"
    if not path.exists():
        path = settings.prompts_dir / "default" / f"{name}.md"
    return Template(path.read_text()).substitute(values)
