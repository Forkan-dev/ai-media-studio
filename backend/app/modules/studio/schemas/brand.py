from pydantic import BaseModel, Field

from app.modules.studio.brand import Brand


class BrandCreate(BaseModel):
    preset: str
    name: str = Field(min_length=2, max_length=60)
    niche: str = Field(min_length=3, max_length=300)
    tone: str = Field(min_length=3, max_length=500)


class BrandOut(BaseModel):
    slug: str
    name: str
    niche: str
    tone: str
    preset: str
    format: str
    duration: int
    default_style: str
    styles: list[str]

    @classmethod
    def of(cls, b: Brand) -> "BrandOut":
        return cls(slug=b.slug, name=b.name, niche=b.niche, tone=b.tone, preset=b.preset, format=b.format,
                   duration=b.duration, default_style=b.images.default_style, styles=list(b.images.styles))


class PresetOut(BaseModel):
    name: str
    description: str
