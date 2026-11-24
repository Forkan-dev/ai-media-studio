"""Brands: read from YAML files in brands_dir (moves to the DB when brands are edited in the UI)."""
from pathlib import Path

from app.brand import Brand, load_brand
from app.services.errors import NotFoundError


class BrandService:
    def __init__(self, brands_dir: Path):
        self._dir = brands_dir

    def list_brands(self) -> list[Brand]:
        return [load_brand(p.stem) for p in sorted(self._dir.glob("*.yaml"))]

    def get(self, slug: str) -> Brand:
        try:
            return load_brand(slug)
        except FileNotFoundError as e:
            raise NotFoundError(f"No brand {slug}") from e
