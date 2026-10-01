"""GET /coverage endpoint with truthful availability reporting."""

from __future__ import annotations

from typing import Any, Dict
from fastapi import APIRouter, HTTPException, Query
from ..registry.parameters import PARAMETER_REGISTRY
from ..registry.regions import REGION_REGISTRY
from ..registry.bindings import DATASET_BINDINGS
from ..cache.store import LocalDataStore

router = APIRouter(prefix="/coverage", tags=["Coverage"])


@router.get("")
def get_coverage(
    region_id: str = Query(..., description="Region ID (e.g. BGD, USA)"),
    parameter_id: str = Query(..., description="Parameter ID (e.g. air_temperature_2m)"),
    binding_id: str | None = Query(None, description="Optional specific dataset binding"),
) -> Dict[str, Any]:
    """Retrieve temporal and spatial coverage for a given region and parameter."""
    reg_id = region_id.upper().strip()
    param_id = parameter_id.lower().strip()

    if reg_id not in REGION_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Region '{region_id}' not found.")
    if param_id not in PARAMETER_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Parameter '{parameter_id}' not found.")

    param_def = PARAMETER_REGISTRY[param_id]
    bind_id = binding_id or param_def.default_binding_id
    if bind_id not in DATASET_BINDINGS:
        raise HTTPException(status_code=400, detail=f"Binding '{bind_id}' not found.")

    binding = DATASET_BINDINGS[bind_id]
    if binding.parameter_id != param_id:
        raise HTTPException(
            status_code=400,
            detail={
                "type": "https://errors.earthtrenddetective.org/INCOMPATIBLE_BINDING_PARAMETER",
                "title": "Incompatible Binding for Parameter",
                "status": 400,
                "detail": f"Binding '{bind_id}' provides '{binding.parameter_id}', not requested parameter '{param_id}'.",
                "code": "INCOMPATIBLE_BINDING_PARAMETER",
            },
        )

    region = REGION_REGISTRY[reg_id]

    # Check ocean compatibility
    if param_def.valid_spatial_support == "ocean" and not region.has_ocean_support:
        return {
            "is_supported": False,
            "region_id": reg_id,
            "parameter_id": param_id,
            "binding_id": bind_id,
            "reason": f"Parameter '{param_id}' requires an ocean region or marine basin, but '{region.name_en}' is an inland/terrestrial boundary.",
            "action": "Choose an ocean region (e.g. BAY_OF_BENGAL, NORTH_ATLANTIC).",
            "availability_state": "unavailable",
        }

    # Check dataset readiness state
    if binding.availability_state == "catalogued":
        return {
            "is_supported": False,
            "region_id": reg_id,
            "parameter_id": param_id,
            "binding_id": bind_id,
            "reason": binding.unavailability_reason or f"Dataset '{binding.id}' is catalogued but local granules have not been ingested.",
            "action": "Select an analysis-ready parameter (e.g. Near-Surface Air Temperature).",
            "availability_state": "catalogued",
        }

    store = LocalDataStore()
    has_cached = store.has_series(bind_id, reg_id)

    if not has_cached:
        return {
            "is_supported": False,
            "region_id": reg_id,
            "region_name": region.name_en,
            "parameter_id": param_id,
            "binding_id": bind_id,
            "reason": f"Region '{region.name_en}' ({reg_id}) is not present in local offline cache for '{binding.id}'.",
            "action": "Select a region with packaged observations (e.g. BGD, USA, KEN, BRA, DEU, MDV).",
            "availability_state": "unavailable",
            "has_cached_series": False,
            "access_mode": "unavailable",
        }

    return {
        "is_supported": True,
        "region_id": reg_id,
        "region_name": region.name_en,
        "parameter_id": param_id,
        "binding_id": bind_id,
        "record_start_date": binding.record_start_date,
        "record_end_date": binding.record_end_date,
        "native_spatial_resolution": binding.native_spatial_resolution,
        "temporal_cadence": binding.temporal_cadence,
        "has_cached_series": True,
        "access_mode": "cache",
        "availability_state": binding.availability_state,
    }
