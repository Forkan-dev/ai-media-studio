"""Brands live in the DB with their FULL config (every parameter, defaults filled in), so all brands
always have the same parameters. New brands start from a preset (presets/<name>.yaml).
YAML brand files are only for import/export."""
import re
from dataclasses import dataclass
from pathlib import Path

import yaml

from app.core.clients.render import MOTIONS, TRANSITIONS
from app.core.clients.tts import KOKORO_VOICES
from app.core.errors import InvalidStateError, NotFoundError
from app.modules.studio.brand import Brand, read_brand_yaml
from app.modules.studio.models import BrandRecord
from app.modules.studio.repositories import BrandRepository


@dataclass
class Preset:
    name: str
    description: str
    config: dict


class BrandService:
    def __init__(self, brands: BrandRepository, presets_dir: Path):
        self._brands = brands
        self._presets_dir = presets_dir

    def list_brands(self) -> list[Brand]:
        return [Brand.model_validate(r.config) for r in self._brands.find()]

    def get(self, slug: str) -> Brand:
        record = self._brands.get(slug)
        if not record:
            raise NotFoundError(f"No brand {slug}")
        return Brand.model_validate(record.config)

    def update(self, brand: Brand) -> Brand:
        """Replace an existing brand's config (the slug cannot change)."""
        self.get(brand.slug)  # 404 if it does not exist
        return self.save(brand)

    @staticmethod
    def options() -> dict[str, list[str]]:
        """Allowed values for the settings form."""
        from app.modules.studio.pipeline.reviewer import CRITERIA  # local import: reviewer imports Brand
        return {"review_criteria": list(CRITERIA), "motions": list(MOTIONS), "transitions": list(TRANSITIONS),
                "engines": ["kokoro", "chatterbox"], "formats": ["short", "long"],
                "script_modes": ["facts", "story"], "kokoro_voices": list(KOKORO_VOICES)}

    def save(self, brand: Brand) -> Brand:
        """Create or update; stores every parameter, not only the ones that differ from the defaults."""
        record = self._brands.get(brand.slug) or BrandRecord(slug=brand.slug)
        record.config = brand.model_dump(mode="json")
        self._brands.save(record)
        return brand

    # ---------- presets / create ----------

    def list_presets(self) -> list[Preset]:
        return [self._preset(p.stem) for p in sorted(self._presets_dir.glob("*.yaml"))]

    def create(self, preset: str, name: str, niche: str, tone: str) -> Brand:
        """A new brand: the preset's full config + the user's name, niche and tone."""
        slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
        if not slug:
            raise InvalidStateError("The brand name needs letters or numbers")
        if self._brands.get(slug):
            raise InvalidStateError(f"A brand named {name} already exists")
        config = {**self._preset(preset).config, "preset": preset,
                  "slug": slug, "name": name, "niche": niche, "tone": tone}
        return self.save(Brand.model_validate(config))

    def _preset(self, name: str) -> Preset:
        path = self._presets_dir / f"{name}.yaml"
        if not path.exists():
            raise NotFoundError(f"No preset {name}")
        text = path.read_text()
        description = text.splitlines()[0].split(":", 1)[-1].strip()  # first line: "# Preset 'x': ..."
        return Preset(name, description, yaml.safe_load(text))

    # ---------- import ----------

    def import_yaml(self, folder: Path) -> list[str]:
        """Add brands from <folder>/*.yaml that are not in the DB yet. Returns the imported slugs."""
        imported = []
        for path in sorted(folder.glob("*.yaml")):
            brand = read_brand_yaml(path)
            if not self._brands.get(brand.slug):
                self.save(brand)
                imported.append(brand.slug)
        return imported
