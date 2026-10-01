"""GET /results endpoints for immutable results, series, and exports."""

from __future__ import annotations

import io
from typing import Any, Dict
from fastapi import APIRouter, HTTPException, Response
import pandas as pd

from ..cache.store import LocalDataStore

router = APIRouter(prefix="/results", tags=["Results"])


@router.get("/{result_id}")
def get_result_by_id(result_id: str) -> Dict[str, Any]:
    """Retrieve an exact, immutable scientific result object by its SHA-256 hash."""
    store = LocalDataStore()
    res = store.get_result(result_id)
    if not res:
        raise HTTPException(
            status_code=404,
            detail={
                "type": "https://errors.earthtrenddetective.org/RESULT_NOT_FOUND",
                "title": "Result Not Found",
                "status": 404,
                "detail": f"No result found matching hash '{result_id}'.",
                "code": "RESULT_NOT_FOUND",
            },
        )
    return res


@router.get("/{result_id}/series")
def get_result_series(result_id: str) -> Dict[str, Any]:
    """Retrieve observation series and QA flags associated with a frozen result."""
    store = LocalDataStore()
    res = store.get_result(result_id)
    if not res:
        raise HTTPException(status_code=404, detail="Result not found.")

    return {
        "result_id": result_id,
        "region_id": res["region"]["id"],
        "parameter_id": res["parameter"]["id"],
        "unit": res["parameter"]["display_unit"],
        "series": res["series"],
        "fitted_band": res.get("fitted_band", {}),
    }


@router.get("/{result_id}/export")
def export_result(result_id: str, format: str = "json") -> Response:
    """Export complete audit package, JSON, or CSV for reproducible publication."""
    import json
    store = LocalDataStore()
    res = store.get_result(result_id)
    if not res:
        raise HTTPException(status_code=404, detail="Result not found.")

    if format.lower() == "csv":
        years = res["series"]["years"]
        vals = res["series"]["values"]
        unit = res["parameter"]["display_unit"]
        df = pd.DataFrame({"year": years, f"value_{unit}": vals})
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        return Response(
            content=csv_buffer.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=trend_{result_id[:8]}.csv"},
        )

    # Default: Full JSON reproducibility bundle
    export_bundle = {
        "result_id": result_id,
        "exported_at": res["identity"]["created_at"],
        "investigation_result": res,
        "reproducibility_notice": (
            "This export contains the immutable scientific outputs, source collection metadata, "
            "and model parameters from Earth System Trend Detective. All calculations are pure, "
            "deterministic, and verified offline."
        ),
    }
    from ..cache.store import _sanitize_floats
    clean_bundle = _sanitize_floats(export_bundle)
    return Response(
        content=json.dumps(clean_bundle, indent=2, allow_nan=False),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=investigation_{result_id[:8]}.json"},
    )

