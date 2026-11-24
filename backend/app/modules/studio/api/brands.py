"""Brands controller: HTTP only, the work is in BrandService."""
from fastapi import APIRouter, Depends, status

from app.core.errors import InvalidStateError
from app.modules.studio.brand import Brand
from app.modules.studio.dependencies import brand_service
from app.modules.studio.schemas import BrandCreate, BrandOut, PresetOut
from app.modules.studio.services.brand_service import BrandService

router = APIRouter(tags=["brands"])


@router.get("/presets", response_model=list[PresetOut])
def list_presets(brands: BrandService = Depends(brand_service)):
    return brands.list_presets()


@router.get("/brands", response_model=list[BrandOut])
def list_brands(brands: BrandService = Depends(brand_service)):
    return [BrandOut.of(b) for b in brands.list_brands()]


@router.post("/brands", response_model=BrandOut, status_code=status.HTTP_201_CREATED)
def create_brand(body: BrandCreate, brands: BrandService = Depends(brand_service)):
    return BrandOut.of(brands.create(body.preset, body.name, body.niche, body.tone))


@router.get("/brand-options")
def brand_options(brands: BrandService = Depends(brand_service)) -> dict[str, list[str]]:
    """Allowed values for the settings form (criteria, motions, transitions, ...)."""
    return brands.options()


@router.get("/brands/{slug}", response_model=BrandOut)
def get_brand(slug: str, brands: BrandService = Depends(brand_service)):
    return BrandOut.of(brands.get(slug))


@router.get("/brands/{slug}/config", response_model=Brand)
def get_config(slug: str, brands: BrandService = Depends(brand_service)):
    """The full config: every parameter, for the settings form."""
    return brands.get(slug)


@router.put("/brands/{slug}", response_model=Brand)
def update_brand(slug: str, body: Brand, brands: BrandService = Depends(brand_service)):
    """Save the full config (validated by the Brand model -> 422 with the reason when invalid)."""
    if body.slug != slug:
        raise InvalidStateError("The brand slug cannot be changed")
    return brands.update(body)
