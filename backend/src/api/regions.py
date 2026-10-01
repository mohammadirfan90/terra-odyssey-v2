"""GET /regions endpoint."""

from __future__ import annotations

from typing import List, Optional
from fastapi import APIRouter, Query
from ..registry.regions import REGION_REGISTRY, RegionDefinition

router = APIRouter(prefix="/regions", tags=["Regions"])


@router.get("", response_model=List[RegionDefinition])
def list_regions(
    q: Optional[str] = Query(None, description="Search filter for region name or ISO code"),
    region_type: Optional[str] = Query(None, description="Filter by type (country, ocean_basin)"),
) -> List[RegionDefinition]:
    """List and search supported geographic regions, countries, and ocean basins."""
    results = list(REGION_REGISTRY.values())

    if region_type:
        results = [r for r in results if r.region_type == region_type]

    if q:
        query_str = q.lower().strip()
        results = [
            r for r in results
            if query_str in r.id.lower()
            or query_str in r.name_en.lower()
            or query_str in r.name_bn
            or (r.iso_a2 and query_str in r.iso_a2.lower())
            or (r.iso_a3 and query_str in r.iso_a3.lower())
        ]

    return results


@router.get("/{region_id}", response_model=RegionDefinition)
def get_region(region_id: str) -> RegionDefinition:
    """Retrieve details for a specific region by ID."""
    reg_id = region_id.upper().strip()
    if reg_id in REGION_REGISTRY:
        return REGION_REGISTRY[reg_id]

    # Search by ISO
    for r in REGION_REGISTRY.values():
        if r.iso_a2 == reg_id or r.iso_a3 == reg_id:
            return r

    from fastapi import HTTPException
    raise HTTPException(status_code=404, detail=f"Region '{region_id}' not found in registry.")
