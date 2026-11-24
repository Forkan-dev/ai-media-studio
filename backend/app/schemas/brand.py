from pydantic import BaseModel

from app.brand import Brand


class BrandOut(BaseModel):
    slug: str
    name: str
    niche: str
    format: str
    duration: int
    default_style: str
    styles: list[str]

    @classmethod
    def of(cls, b: Brand) -> "BrandOut":
        return cls(slug=b.slug, name=b.name, niche=b.niche, format=b.format, duration=b.duration,
                   default_style=b.images.default_style, styles=list(b.images.styles))
