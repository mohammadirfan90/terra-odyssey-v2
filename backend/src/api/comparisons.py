"""POST /comparisons paired regional contrast endpoint.

Implements Section 6.8 and Table 17; resolves Findings F03, F10, and Audit R05:
- Paired difference series over inner-joined unique common eligible dates
- Direct contrast slope and uncertainty calculation with policy-aware alpha and dependence
- Parameter-neutral direction labels (a_higher_rate, b_higher_rate, equal_rate)
- Rigorous enforcement of policy duration gates (exploratory_min_years, max_consecutive_missing_gap)
- Rigorous validation of registered bindings, parameter compatibility, and spatial support
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict
from fastapi import APIRouter, HTTPException
import numpy as np
import pandas as pd

from .schemas import ComparisonRequest
from ..registry.parameters import PARAMETER_REGISTRY
from ..registry.bindings import DATASET_BINDINGS
from ..registry.policies import ANALYSIS_POLICIES, AnalysisPolicy
from ..registry.regions import REGION_REGISTRY
from ..cache.store import (
    LocalDataStore,
    CacheMissOfflineError,
    InvalidPathSecurityError,
    ManifestNotFoundError,
    ManifestEntryNotFoundError,
    ManifestChecksumMismatchError,
    ManifestSchemaError,
)
from ..compute.theil_sen import theil_sen_slope
from ..compute.mann_kendall import mann_kendall_test
from ..compute.serial_corr import check_autocorrelation
from ..compute.aggregation import aggregate_annual_series

router = APIRouter(prefix="/comparisons", tags=["Comparisons"])


@router.post("")
def compare_regions(req: ComparisonRequest) -> Dict[str, Any]:
    """Perform a paired difference series contrast between two compatible regions."""
    reg_a = req.region_id_a.upper().strip()
    reg_b = req.region_id_b.upper().strip()

    if reg_a == reg_b:
        raise HTTPException(
            status_code=400,
            detail={
                "type": "https://errors.earthtrenddetective.org/IDENTICAL_REGIONS",
                "title": "Identical Regions Selected",
                "status": 400,
                "detail": "Region A and Region B must be different geographic regions.",
                "code": "IDENTICAL_REGIONS",
            },
        )

    if reg_a not in REGION_REGISTRY:
        raise HTTPException(
            status_code=404,
            detail={
                "type": "https://errors.earthtrenddetective.org/REGION_NOT_FOUND",
                "title": "Region A Not Found",
                "status": 404,
                "detail": f"Region A '{reg_a}' is not in the recognized registry.",
                "code": "REGION_NOT_FOUND",
            },
        )
    if reg_b not in REGION_REGISTRY:
        raise HTTPException(
            status_code=404,
            detail={
                "type": "https://errors.earthtrenddetective.org/REGION_NOT_FOUND",
                "title": "Region B Not Found",
                "status": 404,
                "detail": f"Region B '{reg_b}' is not in the recognized registry.",
                "code": "REGION_NOT_FOUND",
            },
        )

    region_a = REGION_REGISTRY[reg_a]
    region_b = REGION_REGISTRY[reg_b]

    param_id = req.parameter_id.lower().strip()
    if param_id not in PARAMETER_REGISTRY:
        raise HTTPException(
            status_code=404,
            detail={
                "type": "https://errors.earthtrenddetective.org/PARAMETER_NOT_FOUND",
                "title": "Parameter Not Found",
                "status": 404,
                "detail": f"Physical parameter '{param_id}' is not catalogued.",
                "code": "PARAMETER_NOT_FOUND",
            },
        )

    param = PARAMETER_REGISTRY[param_id]

    # Validate analysis policy (Resolves Audit R05)
    default_pol = "precipitation_total_policy" if param_id == "precipitation_total" else "standard_climate_temperature"
    pol_id = req.policy_id or default_pol
    if pol_id not in ANALYSIS_POLICIES:
        raise HTTPException(
            status_code=400,
            detail={
                "type": "https://errors.earthtrenddetective.org/UNKNOWN_POLICY",
                "title": "Unknown Analysis Policy",
                "status": 400,
                "detail": f"Policy '{pol_id}' is not recognized in the policy registry.",
                "code": "UNKNOWN_POLICY",
            },
        )
    if pol_id == "precipitation_total_policy" and param_id != "precipitation_total":
        raise HTTPException(
            status_code=422,
            detail={
                "type": "https://errors.earthtrenddetective.org/POLICY_PARAMETER_INCOMPATIBLE",
                "title": "Incompatible Analysis Policy for Parameter",
                "status": 422,
                "detail": f"Policy '{pol_id}' is designated for precipitation accumulation, not compatible with '{param_id}'.",
                "code": "POLICY_PARAMETER_INCOMPATIBLE",
            },
        )
    policy = ANALYSIS_POLICIES[pol_id]

    # Validate spatial support
    if param.valid_spatial_support == "ocean":
        if not region_a.has_ocean_support or not region_b.has_ocean_support:
            raise HTTPException(
                status_code=400,
                detail={
                    "type": "https://errors.earthtrenddetective.org/INCOMPATIBLE_SPATIAL_SUPPORT",
                    "title": "Incompatible Spatial Support",
                    "status": 400,
                    "detail": f"Parameter '{param.name_en}' requires ocean regions, but terrestrial regions were selected.",
                    "code": "INCOMPATIBLE_SPATIAL_SUPPORT",
                },
            )

    bind_id = req.binding_id or param.default_binding_id

    # Enforce registered binding and matching parameter
    if bind_id not in DATASET_BINDINGS:
        raise HTTPException(
            status_code=400,
            detail={
                "type": "https://errors.earthtrenddetective.org/UNSUPPORTED_BINDING",
                "title": "Unsupported Dataset Binding",
                "status": 400,
                "detail": f"Binding '{bind_id}' is not registered.",
                "code": "UNSUPPORTED_BINDING",
            },
        )

    binding = DATASET_BINDINGS[bind_id]
    if binding.parameter_id != param_id:
        raise HTTPException(
            status_code=400,
            detail={
                "type": "https://errors.earthtrenddetective.org/INCOMPATIBLE_BINDING_PARAMETER",
                "title": "Incompatible Dataset Binding for Parameter",
                "status": 400,
                "detail": f"Binding '{bind_id}' provides '{binding.parameter_id}', not requested parameter '{param_id}'.",
                "code": "INCOMPATIBLE_BINDING_PARAMETER",
            },
        )

    store = LocalDataStore()
    try:
        df_a = store.load_series(bind_id, reg_a, start_year=req.start_year, end_year=req.end_year)
    except (CacheMissOfflineError, ManifestEntryNotFoundError, ManifestNotFoundError) as exc:
        raise HTTPException(
            status_code=404,
            detail={
                "type": "https://errors.earthtrenddetective.org/CACHE_MISS",
                "title": "Region A Cache Miss",
                "status": 404,
                "detail": f"Offline data for Region A '{reg_a}' is not present in local cache.",
                "code": "CACHE_MISS",
            },
        )
    except (ManifestChecksumMismatchError, ManifestSchemaError) as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "type": "https://errors.earthtrenddetective.org/DATA_INTEGRITY_ERROR",
                "title": "Region A Data Integrity Violation",
                "status": 422,
                "detail": str(exc),
                "code": "DATA_INTEGRITY_ERROR",
            },
        )
    except InvalidPathSecurityError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    try:
        df_b = store.load_series(bind_id, reg_b, start_year=req.start_year, end_year=req.end_year)
    except (CacheMissOfflineError, ManifestEntryNotFoundError, ManifestNotFoundError) as exc:
        raise HTTPException(
            status_code=404,
            detail={
                "type": "https://errors.earthtrenddetective.org/CACHE_MISS",
                "title": "Region B Cache Miss",
                "status": 404,
                "detail": f"Offline data for Region B '{reg_b}' is not present in local cache.",
                "code": "CACHE_MISS",
            },
        )
    except (ManifestChecksumMismatchError, ManifestSchemaError) as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "type": "https://errors.earthtrenddetective.org/DATA_INTEGRITY_ERROR",
                "title": "Region B Data Integrity Violation",
                "status": 422,
                "detail": str(exc),
                "code": "DATA_INTEGRITY_ERROR",
            },
        )
    except InvalidPathSecurityError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    # Pre-aggregate each series to unique annual values using shared scientific routine (Resolves Audit R04, R05)
    try:
        ann_a = aggregate_annual_series(df_a, param_id=param_id, policy=policy, binding_id=bind_id)
        ann_b = aggregate_annual_series(df_b, param_id=param_id, policy=policy, binding_id=bind_id)
    except ManifestSchemaError as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "type": "https://errors.earthtrenddetective.org/DATA_INTEGRITY_ERROR",
                "title": "Data Integrity Violation During Aggregation",
                "status": 422,
                "detail": str(exc),
                "code": "DATA_INTEGRITY_ERROR",
            },
        )

    if ann_a.empty or ann_b.empty:
        raise HTTPException(
            status_code=422,
            detail={
                "type": "https://errors.earthtrenddetective.org/INCOMPATIBLE_COMPARISON",
                "title": "Insufficient Valid Record",
                "status": 422,
                "detail": "One or both regions have 0% or insufficient coverage under policy rules.",
                "code": "INCOMPATIBLE_COMPARISON",
            },
        )

    # Inner join on common eligible years with strict 1:1 validation (Prevents multi-row inflation)
    merged = pd.merge(
        ann_a[["year", "val"]],
        ann_b[["year", "val"]],
        on="year",
        suffixes=("_a", "_b"),
        validate="one_to_one",
    ).dropna(subset=["val_a", "val_b"])

    merged = merged[
        np.isfinite(merged["val_a"].to_numpy(dtype=float))
        & np.isfinite(merged["val_b"].to_numpy(dtype=float))
    ]

    common_years = merged["year"].to_numpy(dtype=int)

    if len(common_years) < 3:
        raise HTTPException(
            status_code=422,
            detail={
                "type": "https://errors.earthtrenddetective.org/INCOMPATIBLE_COMPARISON",
                "title": "Insufficient Overlapping Record",
                "status": 422,
                "detail": f"Regions share only {len(common_years)} overlapping eligible years (minimum 3 required).",
                "code": "INCOMPATIBLE_COMPARISON",
            },
        )

    val_a = merged["val_a"].to_numpy(dtype=float)
    val_b = merged["val_b"].to_numpy(dtype=float)
    diff = val_a - val_b

    t_years = common_years.astype(float)
    ts_a = theil_sen_slope(t_years, val_a, alpha=policy.alpha)
    ts_b = theil_sen_slope(t_years, val_b, alpha=policy.alpha)
    ts_diff = theil_sen_slope(t_years, diff, alpha=policy.alpha)

    # Autocorrelation and dependence handling on difference series (Resolves Audit R05)
    ref_t = ts_diff.ref_time
    diff_slope = ts_diff.slope_per_year if ts_diff.slope_per_year is not None else 0.0
    diff_intercept = ts_diff.intercept if ts_diff.intercept is not None else 0.0
    diff_residuals = diff - (diff_intercept + diff_slope * (t_years - ref_t))
    corr_diag = check_autocorrelation(diff_residuals, alpha=policy.alpha)
    vif = corr_diag.vif if policy.dependence_handling == "hamed_rao" else 1.0
    auto_adj = policy.dependence_handling == "hamed_rao" and corr_diag.is_autocorrelated

    mk_diff = mann_kendall_test(diff, alpha=policy.alpha, vif=vif, autocorrelation_adjusted=auto_adj)

    # Apply policy duration thresholds and maximum consecutive gap (Resolves Audit R05)
    sorted_years = np.sort(common_years)
    year_diffs = np.diff(sorted_years)
    max_gap = int(np.max(year_diffs) - 1) if len(year_diffs) > 0 else 0
    has_excessive_gap = max_gap > policy.max_consecutive_missing_gap

    n_samples = len(common_years)
    if n_samples < policy.exploratory_min_years:
        evidence_state = "insufficient"
    elif has_excessive_gap:
        evidence_state = "limited"
    elif n_samples < policy.min_eligible_years_climate:
        evidence_state = "limited"
    elif mk_diff.p_value >= policy.alpha:
        evidence_state = "inconclusive"
    else:
        slope_val = ts_diff.slope_per_decade if ts_diff.slope_per_decade is not None else 0.0
        if slope_val > 0:
            evidence_state = "supported_increase"
        elif slope_val < 0:
            evidence_state = "supported_decrease"
        else:
            evidence_state = "flat"

    slope_val = ts_diff.slope_per_decade if ts_diff.slope_per_decade is not None else 0.0
    if abs(slope_val) < 1e-4:
        direction_label = "equal_rate"
    elif slope_val > 0:
        direction_label = "a_higher_rate"
    else:
        direction_label = "b_higher_rate"

    data_sha_a = store.get_series_bytes_sha256(bind_id, reg_a)
    data_sha_b = store.get_series_bytes_sha256(bind_id, reg_b)
    policy_dict = policy.model_dump()
    policy_canonical = json.dumps(policy_dict, sort_keys=True)
    comp_hash = hashlib.sha256(
        f"{reg_a}_{reg_b}_{param_id}_{bind_id}_{policy.id}_{policy_canonical}_{common_years[0]}_{common_years[-1]}_{data_sha_a}_{data_sha_b}_v1.4.0".encode()
    ).hexdigest()

    cached_comp = store.get_result(comp_hash)
    if cached_comp is not None:
        prov = cached_comp.get("provenance", {})
        if len(prov.get("data_sha256", "")) != 64:
            prov["data_sha256"] = hashlib.sha256(f"{data_sha_a}:{data_sha_b}".encode()).hexdigest()
            cached_comp["provenance"] = prov
        return cached_comp

    created_iso = datetime.now(timezone.utc).isoformat()
    result_obj = {
        "identity": {
            "comparison_id": comp_hash,
            "created_at": created_iso,
        },
        "parameter_id": param_id,
        "binding_id": bind_id,
        "unit": param.display_unit,
        "common_years_count": len(common_years),
        "interval": [int(common_years[0]), int(common_years[-1])],
        "region_a": {
            "id": reg_a,
            "name": region_a.name_en,
            "slope_per_decade": ts_a.slope_per_decade,
            "ci_95_lower": ts_a.ci_95_lower_per_decade,
            "ci_95_upper": ts_a.ci_95_upper_per_decade,
        },
        "region_b": {
            "id": reg_b,
            "name": region_b.name_en,
            "slope_per_decade": ts_b.slope_per_decade,
            "ci_95_lower": ts_b.ci_95_lower_per_decade,
            "ci_95_upper": ts_b.ci_95_upper_per_decade,
        },
        "contrast_difference_series": {
            "years": [int(y) for y in common_years],
            "difference_values": [round(float(d), 4) for d in diff],
            "slope_per_decade": ts_diff.slope_per_decade,
            "ci_95_lower": ts_diff.ci_95_lower_per_decade,
            "ci_95_upper": ts_diff.ci_95_upper_per_decade,
            "p_value": mk_diff.p_value,
            "direction": direction_label,
            "evidence_state": evidence_state,
        },
        "provenance": {
            "data_sha256": hashlib.sha256(f"{data_sha_a}:{data_sha_b}".encode()).hexdigest(),
            "region_a_data_sha256": data_sha_a,
            "region_b_data_sha256": data_sha_b,
            "policy_id": policy.id,
            "alpha": policy.alpha,
            "dependence_handling": policy.dependence_handling,
            "vif": vif,
        },
        "reproducibility": {
            "code_revision": "v1.4.0",
            "policy_id": policy.id,
        },
    }
    saved_result = store.save_result(comp_hash, req.model_dump(), result_obj)
    return saved_result
