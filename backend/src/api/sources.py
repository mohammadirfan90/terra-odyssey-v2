"""GET /sources endpoint for dataset provenance, DOI, and citations."""

from __future__ import annotations

from typing import Any, Dict
from fastapi import APIRouter, HTTPException
from ..registry.bindings import DATASET_BINDINGS, DatasetBinding

router = APIRouter(prefix="/sources", tags=["Sources"])


@router.get("/{source_id}", response_model=DatasetBinding)
def get_source_manifest(source_id: str) -> DatasetBinding:
    """Retrieve full source collection metadata, DOI, and citation string."""
    if source_id not in DATASET_BINDINGS:
        raise HTTPException(
            status_code=404,
            detail=f"Dataset binding source '{source_id}' not found in registry.",
        )
    return DATASET_BINDINGS[source_id]
