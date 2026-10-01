"""GET /layers endpoints for map layers, TileJSON metadata, raster tiles, and FDR GeoJSON."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Response
import numpy as np
import pandas as pd

from ..registry.layers import LAYER_REGISTRY, LayerDefinition
from ..registry.parameters import PARAMETER_REGISTRY
from ..registry.policies import ANALYSIS_POLICIES, AnalysisPolicy
from ..registry.regions import REGION_REGISTRY
from ..cache.store import LocalDataStore
from ..compute.theil_sen import theil_sen_slope
from ..compute.mann_kendall import mann_kendall_test
from ..compute.multiple_testing import false_discovery_rate_correction
from ..compute.aggregation import aggregate_annual_series

router = APIRouter(tags=["Layers"])


@router.get("/layers", response_model=List[LayerDefinition])
def list_layers() -> List[LayerDefinition]:
    """List registered scientific map layers and rendering styles."""
    return list(LAYER_REGISTRY.values())


@router.get("/layers/{layer_id}/tilejson")
def get_layer_tilejson(layer_id: str) -> Dict[str, Any]:
    """Retrieve TileJSON 3.0 specification for local layer."""
    if layer_id not in LAYER_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Layer '{layer_id}' not found.")

    layer = LAYER_REGISTRY[layer_id]
    return {
        "tilejson": "3.0.0",
        "id": layer.id,
        "name": layer.name_en,
        "description": f"{layer.layer_mode} layer for {layer.parameter_id}",
        "version": "1.0.0",
        "attribution": layer.attribution,
        "scheme": "xyz",
        "tiles": [],
        "vector_layers": [
            {
                "id": layer.id,
                "description": f"Vector GeoJSON available at /layers/{layer.id}/geojson",
            }
        ],
        "minzoom": 0,
        "maxzoom": 6,
        "bounds": [-180.0, -85.0511, 180.0, 85.0511],
        "legend_stops": [stop.model_dump() for stop in layer.legend_stops],
        "unit": layer.unit,
    }


@router.get("/tiles/{layer_id}/{z}/{x}/{y}")
@router.get("/tiles/{layer_id}/{z}/{x}/{y}.png")
def get_layer_tile(layer_id: str, z: int, x: int, y: int) -> Response:
    """Serve local raster tile for scientific layer.

    Raster XYZ tiles are unavailable in this revision. Regional trend slopes are
    available via GeoJSON vector layer at /layers/{layer_id}/geojson.
    """
    clean_id = layer_id.removesuffix(".png")
    if clean_id not in LAYER_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Layer '{clean_id}' not found.")

    raise HTTPException(
        status_code=501,
        detail={
            "type": "https://errors.earthtrenddetective.org/RASTER_TILES_UNAVAILABLE",
            "title": "Raster Tiles Not Implemented",
            "status": 501,
            "detail": (
                f"Raster XYZ tiles for layer '{clean_id}' are not rendered or available in this revision. "
                "Verified regional trend statistics and FDR corrections are available via the vector "
                f"GeoJSON endpoint at /layers/{clean_id}/geojson."
            ),
            "code": "RASTER_TILES_UNAVAILABLE",
        },
    )


@router.get("/layers/{layer_id}/geojson")
def get_layer_geojson(
    layer_id: str,
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
    policy_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Retrieve regional polygon features enriched with Theil-Sen slopes and Benjamini-Hochberg FDR q-values."""
    if layer_id not in LAYER_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Layer '{layer_id}' not found.")

    layer = LAYER_REGISTRY[layer_id]
    param_id = layer.parameter_id
    param = PARAMETER_REGISTRY.get(param_id)
    if not param:
        raise HTTPException(status_code=404, detail=f"Parameter '{param_id}' not found.")

    bind_id = param.default_binding_id

    # Validate analysis policy
    if policy_id:
        if policy_id not in ANALYSIS_POLICIES:
            raise HTTPException(
                status_code=400,
                detail={
                    "type": "https://errors.earthtrenddetective.org/UNKNOWN_POLICY",
                    "title": "Unknown Analysis Policy",
                    "status": 400,
                    "detail": f"Policy '{policy_id}' is not recognized in the policy registry.",
                    "code": "UNKNOWN_POLICY",
                },
            )
        policy = ANALYSIS_POLICIES[policy_id]
    else:
        default_pol = (
            "modis_lst_satellite_policy"
            if "MODIS" in bind_id
            else ("precipitation_total_policy" if param_id == "precipitation_total" else "standard_climate_temperature")
        )
        policy = ANALYSIS_POLICIES.get(default_pol, ANALYSIS_POLICIES["standard_climate_temperature"])

    store = LocalDataStore()

    # Load countries.geojson (respecting DATA_ROOT if set)
    geojson_path = store.regions_dir / "countries.geojson"
    if not geojson_path.exists():
        geojson_path = Path(__file__).resolve().parents[3] / "data" / "regions" / "countries.geojson"
    if not geojson_path.exists():
        geojson_path = Path(__file__).resolve().parents[2] / "data" / "regions" / "countries.geojson"

    with open(geojson_path, "r", encoding="utf-8") as f:
        geo_data = json.load(f)

    # Compute slopes and p-values across cached regions applying shared aggregation and QA filtering
    region_results: Dict[str, Dict[str, Any]] = {}
    p_values_list = []
    reg_keys = []

    for reg_id in REGION_REGISTRY.keys():
        if store.has_series(bind_id, reg_id):
            try:
                df = store.load_series(bind_id, reg_id, start_year=start_year, end_year=end_year)
                ann_df = aggregate_annual_series(df, param_id=param_id, policy=policy, binding_id=bind_id)
                if len(ann_df) >= 3:
                    years = ann_df["year"].to_numpy(dtype=float)
                    vals = ann_df["val"].to_numpy(dtype=float)
                    ts = theil_sen_slope(years, vals, alpha=policy.alpha)
                    mk = mann_kendall_test(vals, alpha=policy.alpha)
                    region_results[reg_id] = {
                        "slope_per_decade": ts.slope_per_decade,
                        "p_value": mk.p_value,
                        "direction": mk.direction,
                        "year_count": len(ann_df),
                    }
                    p_values_list.append(mk.p_value)
                    reg_keys.append(reg_id)
            except Exception:
                continue

    # Apply FDR correction (Section 6.7)
    if p_values_list:
        fdr_res = false_discovery_rate_correction(p_values_list, method="benjamini_hochberg", fdr_threshold=policy.alpha)
        for i, reg_id in enumerate(reg_keys):
            q_val = fdr_res.q_values[i]
            y_count = region_results[reg_id].get("year_count", 0)
            is_sig = q_val is not None and q_val <= policy.alpha and y_count >= policy.exploratory_min_years
            region_results[reg_id]["q_value"] = q_val
            region_results[reg_id]["is_significant_fdr"] = is_sig

    # Enrich features
    enriched_features = []
    for feat in geo_data.get("features", []):
        props = dict(feat.get("properties", {}))
        reg_id = str(props.get("id") or props.get("ISO3166-1-Alpha-3") or props.get("ISO_A3") or "").upper().strip()
        stats = region_results.get(reg_id)
        if stats:
            props["has_data"] = True
            props["slope_per_decade"] = stats["slope_per_decade"]
            props["p_value"] = stats["p_value"]
            props["q_value"] = stats.get("q_value")
            props["is_significant_fdr"] = stats.get("is_significant_fdr", False)
        else:
            props["has_data"] = False
            props["slope_per_decade"] = None
            props["p_value"] = None
            props["q_value"] = None
            props["is_significant_fdr"] = False

        enriched_features.append({
            "type": "Feature",
            "id": reg_id or feat.get("id"),
            "properties": props,
            "geometry": feat.get("geometry"),
        })

    return {
        "type": "FeatureCollection",
        "layer_id": layer_id,
        "parameter_id": param_id,
        "time_window": {"start_year": start_year, "end_year": end_year},
        "fdr_family_size": len(p_values_list),
        "fdr_significant_count": sum(1 for r in region_results.values() if r.get("is_significant_fdr")),
        "features": enriched_features,
    }
