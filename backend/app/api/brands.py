"""Brands controller: HTTP only, the work is in BrandService."""
from fastapi import APIRouter, Depends

from app.dependencies import brand_service
from app.schemas import BrandOut
from app.services.brand_service import BrandService

router = APIRouter(prefix="/brands", tags=["brands"])


@router.get("", response_model=list[BrandOut])
def list_brands(brands: BrandService = Depends(brand_service)):
    return [BrandOut.of(b) for b in brands.list_brands()]


@router.get("/{slug}", response_model=BrandOut)
def get_brand(slug: str, brands: BrandService = Depends(brand_service)):
    return BrandOut.of(brands.get(slug))
