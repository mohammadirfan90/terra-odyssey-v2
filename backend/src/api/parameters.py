"""GET /parameters endpoint."""

from __future__ import annotations

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from ..registry.parameters import PARAMETER_REGISTRY, ParameterDefinition
from ..registry.bindings import DATASET_BINDINGS, DatasetBinding

router = APIRouter(prefix="/parameters", tags=["Parameters"])


@router.get("", response_model=List[ParameterDefinition])
def list_parameters(
    domain: Optional[str] = Query(None, description="Filter by physical domain"),
) -> List[ParameterDefinition]:
    """List physical Earth system parameters grouped by domain."""
    params = list(PARAMETER_REGISTRY.values())
    if domain:
        params = [p for p in params if p.domain == domain]
    return params


@router.get("/{parameter_id}", response_model=ParameterDefinition)
def get_parameter(parameter_id: str) -> ParameterDefinition:
    """Get single physical parameter definition."""
    p_id = parameter_id.lower().strip()
    if p_id not in PARAMETER_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Parameter '{parameter_id}' not found.")
    return PARAMETER_REGISTRY[p_id]


@router.get("/{parameter_id}/bindings", response_model=List[DatasetBinding])
def get_parameter_bindings(parameter_id: str) -> List[DatasetBinding]:
    """Get all dataset bindings available for a given parameter."""
    p_id = parameter_id.lower().strip()
    if p_id not in PARAMETER_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Parameter '{parameter_id}' not found.")
    return [b for b in DATASET_BINDINGS.values() if b.parameter_id == p_id]
