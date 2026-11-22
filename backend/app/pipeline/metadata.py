"""Metadata role: narration -> YouTube title/description/tags + social caption, saved as txt and json."""
from pathlib import Path

from pydantic import BaseModel, Field

from app.brand import Brand
from app.prompts import render
from app.clients.llm import chat_json

AI_DISCLOSURE = "Visuals and voice are AI-generated."


class Metadata(BaseModel):
    youtube_title: str = Field(max_length=100)
    youtube_description: str
    tags: list[str]
    hashtags: list[str]
    social_caption: str

    def as_text(self) -> str:
        hashtags = " ".join(self.hashtags)
        return (
            f"YOUTUBE TITLE\n{self.youtube_title}\n\n"
            f"YOUTUBE DESCRIPTION\n{self.youtube_description}\n\n{hashtags}\n\n{AI_DISCLOSURE}\n\n"
            f"TAGS\n{', '.join(self.tags)}\n\n"
            f"SOCIAL MEDIA CAPTION (Facebook / Instagram / TikTok)\n{self.social_caption}\n\n{hashtags}\n"
        )


def make_metadata(brand: Brand, topic: str, narration: str) -> Metadata:
    system = render(brand.prompts, "metadata", brand_name=brand.name, niche=brand.niche,
                    tone=brand.tone, topic=topic, narration=narration)
    return chat_json(system, "Write the publishing text now.", Metadata, temperature=0.7)


def save_metadata(meta: Metadata, folder: Path) -> None:
    (folder / "metadata.json").write_text(meta.model_dump_json(indent=1))
    (folder / "metadata.txt").write_text(meta.as_text())
