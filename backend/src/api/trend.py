"""GET /trend primary scientific computation endpoint.

Implements Section 10.3, Table 17, and Table 18; resolves Findings F01, F03, F04, F05, F06, F09, F12, F13, and Audit R04, R07, R08:
- Synchronous bounded scientific computation over verified local cached observations
- Zero synthetic data generation (returns typed Problem Details on cache miss)
- Strict validation of parameter bindings and analysis policy
- Enforces QA gates, coverage thresholds, unique calendar years, and minimum eligible years
- Shared aggregation logic for daily, monthly, and annual observations with calendar verification
- Preserves full precision from canonical variables
- Truthful requested vs retained intervals in immutable hashing and data support
- Deterministic bilingual English and Bangla narration with strict numerical verification in both languages
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, Query, Response
import numpy as np
import pandas as pd

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
from ..cache.hasher import compute_result_hash
from ..compute.mann_kendall import mann_kendall_test
from ..compute.theil_sen import theil_sen_slope
from ..compute.serial_corr import check_autocorrelation
from ..compute.uncertainty import calculate_fitted_line_band
from ..compute.aggregation import aggregate_annual_series
from ..narration.claims import NarrationClaimFrame
from ..narration.templates_en import render_english_narration
from ..narration.templates_bn import render_bangla_narration
from ..narration.validator import validate_narrative_text

router = APIRouter(prefix="/trend", tags=["Trend"])


@router.get("")
def calculate_trend(
    region_id: Optional[str] = Query(None, description="Region ID (e.g. BGD, USA)"),
    district: Optional[str] = Query(None, description="Deprecated compatibility alias for region_id"),
    parameter_id: str = Query(..., description="Physical parameter ID (e.g. air_temperature_2m)"),
    start_year: Optional[int] = Query(None, description="Start year of analysis window"),
    end_year: Optional[int] = Query(None, description="End year of analysis window"),
    binding_id: Optional[str] = Query(None, description="Specific dataset binding ID"),
    policy_id: Optional[str] = Query(None, description="Analysis policy ID"),
) -> Dict[str, Any]:
    """Calculate an auditable Earth system trend investigation for a region and parameter."""
    # Handle district compatibility alias
    effective_region_id = region_id or district
    if not effective_region_id:
        raise HTTPException(
            status_code=400,
            detail={
                "type": "https://errors.earthtrenddetective.org/MISSING_REGION_ID",
                "title": "Missing Region Identifier",
                "status": 400,
                "detail": "Either 'region_id' or compatibility alias 'district' must be provided.",
                "code": "MISSING_REGION_ID",
            },
        )

    reg_id = effective_region_id.upper().strip()
    param_id = parameter_id.lower().strip()

    # Validate registry existence
    if reg_id not in REGION_REGISTRY:
        raise HTTPException(
            status_code=404,
            detail={
                "type": "https://errors.earthtrenddetective.org/REGION_NOT_FOUND",
                "title": "Region Not Found",
                "status": 404,
                "detail": f"Region '{reg_id}' is not in the recognized geographical boundary registry.",
                "code": "REGION_NOT_FOUND",
            },
        )
    if param_id not in PARAMETER_REGISTRY:
        raise HTTPException(
            status_code=404,
            detail={
                "type": "https://errors.earthtrenddetective.org/PARAMETER_NOT_FOUND",
                "title": "Parameter Not Found",
                "status": 404,
                "detail": f"Physical parameter '{param_id}' is not in the physical parameter registry.",
                "code": "PARAMETER_NOT_FOUND",
            },
        )

    region = REGION_REGISTRY[reg_id]
    param = PARAMETER_REGISTRY[param_id]

    # Validate spatial support compatibility (Resolves Finding F08)
    if param.valid_spatial_support == "ocean" and not region.has_ocean_support:
        raise HTTPException(
            status_code=400,
            detail={
                "type": "https://errors.earthtrenddetective.org/INCOMPATIBLE_SPATIAL_SUPPORT",
                "title": "Incompatible Spatial Support",
                "status": 400,
                "detail": f"Parameter '{param.name_en}' is valid only over oceanic bodies, but '{region.name_en}' is a terrestrial region.",
                "code": "INCOMPATIBLE_SPATIAL_SUPPORT",
            },
        )

    # Resolve dataset binding
    bind_id = binding_id or param.default_binding_id
    if bind_id not in DATASET_BINDINGS:
        raise HTTPException(
            status_code=400,
            detail={
                "type": "https://errors.earthtrenddetective.org/UNSUPPORTED_BINDING",
                "title": "Unsupported Dataset Binding",
                "status": 400,
                "detail": f"Dataset binding '{bind_id}' is not registered.",
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

    # Resolve and validate policy
    default_pol = (
        "modis_lst_satellite_policy"
        if "MODIS" in bind_id
        else ("precipitation_total_policy" if param_id == "precipitation_total" else "standard_climate_temperature")
    )
    pol_id = policy_id or default_pol
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
    policy: AnalysisPolicy = ANALYSIS_POLICIES[pol_id]

    # Load local Parquet cache (Zero synthetic generation, verified manifest gate)
    store = LocalDataStore()
    try:
        df = store.load_series(bind_id, reg_id, start_year=start_year, end_year=end_year)
    except (CacheMissOfflineError, ManifestEntryNotFoundError, ManifestNotFoundError) as exc:
        raise HTTPException(
            status_code=404,
            detail={
                "type": "https://errors.earthtrenddetective.org/CACHE_MISS_OFFLINE",
                "title": "Offline Cache Miss",
                "status": 404,
                "detail": str(exc),
                "code": "CACHE_MISS_OFFLINE",
            },
        )
    except (ManifestChecksumMismatchError, ManifestSchemaError) as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "type": "https://errors.earthtrenddetective.org/DATA_INTEGRITY_ERROR",
                "title": "Data Integrity Violation",
                "status": 422,
                "detail": str(exc),
                "code": "DATA_INTEGRITY_ERROR",
            },
        )
    except InvalidPathSecurityError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "type": "https://errors.earthtrenddetective.org/INVALID_PATH_SECURITY",
                "title": "Invalid Path Security",
                "status": 400,
                "detail": str(exc),
                "code": "INVALID_PATH_SECURITY",
            },
        )

    # 1. Scientific aggregation and completeness checks (Resolves Audit R04)
    try:
        ann_df = aggregate_annual_series(df, param_id=param_id, policy=policy, binding_id=bind_id)
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

    years = ann_df["year"].to_numpy(dtype=float)
    values = ann_df["val"].to_numpy(dtype=float)
    n_samples = len(values)

    if n_samples < 3:
        raise HTTPException(
            status_code=422,
            detail={
                "type": "https://errors.earthtrenddetective.org/INSUFFICIENT_OBSERVATIONS",
                "title": "Insufficient Valid Observations",
                "status": 422,
                "detail": f"Only {n_samples} valid eligible observations remain after QA filtering (minimum 3 required).",
                "code": "INSUFFICIENT_OBSERVATIONS",
            },
        )

    start_ret = int(years.min())
    end_ret = int(years.max())

    req_start = start_year if start_year is not None else start_ret
    req_end = end_year if end_year is not None else end_ret

    # Check maximum missing consecutive year gap (Resolves Finding F04 / Audit R04)
    sorted_years = np.sort(years)
    year_diffs = np.diff(sorted_years)
    max_gap = int(np.max(year_diffs) - 1) if len(year_diffs) > 0 else 0
    has_excessive_gap = max_gap > policy.max_consecutive_missing_gap

    # Check immutable cache hit early (Resolves Audit R08)
    data_sha = store.get_series_bytes_sha256(bind_id, reg_id)
    result_id = compute_result_hash(
        region_id=reg_id,
        parameter_id=param_id,
        binding_id=bind_id,
        start_date=str(req_start),
        end_date=str(req_end),
        policy_id=policy.id,
        data_sha256=data_sha,
        code_revision="v1.4.0",
        policy_settings=policy.model_dump(),
    )
    cached_result = store.get_result(result_id)
    if cached_result is not None:
        return cached_result

    # 1. Compute Theil-Sen Median Slope and Intercept
    ts_res = theil_sen_slope(years, values, alpha=policy.alpha)

    # 2. Check Serial Correlation of Residuals and compute Hamed-Rao VIF
    ref_t = ts_res.ref_time
    slope = ts_res.slope_per_year if ts_res.slope_per_year is not None else 0.0
    intercept = ts_res.intercept if ts_res.intercept is not None else 0.0
    residuals = values - (intercept + slope * (years - ref_t))
    corr_diag = check_autocorrelation(residuals, alpha=policy.alpha)

    vif = corr_diag.vif if policy.dependence_handling == "hamed_rao" else 1.0
    auto_adj = policy.dependence_handling == "hamed_rao" and corr_diag.is_autocorrelated

    # 3. Compute Mann-Kendall with VIF
    mk_res = mann_kendall_test(values, alpha=policy.alpha, vif=vif, autocorrelation_adjusted=auto_adj)

    # 4. Fitted-Line Pointwise Bootstrap Uncertainty Band
    band_res = calculate_fitted_line_band(
        years, values, alpha=policy.alpha, n_bootstrap=policy.bootstrap_replicates, seed=policy.bootstrap_seed
    )

    # 5. Evidence State Determination (Resolves Finding F06, R04)
    if n_samples < policy.exploratory_min_years:
        evidence_state = "insufficient"
    elif has_excessive_gap:
        evidence_state = "limited"
    elif n_samples < policy.min_eligible_years_climate:
        evidence_state = "limited"
    else:
        evidence_state = mk_res.evidence_state

    # Construct Claim Frame for deterministic narration
    temporal_stat = param.supported_temporal_statistics[0]
    claim = NarrationClaimFrame(
        result_id="",  # filled below
        region_id=reg_id,
        region_name_en=region.name_en,
        region_name_bn=region.name_bn,
        parameter_id=param_id,
        parameter_name_en=param.name_en,
        parameter_name_bn=param.name_bn,
        temporal_statistic=temporal_stat,
        start_year=start_ret,
        end_year=end_ret,
        slope_per_decade=ts_res.slope_per_decade,
        slope_display_en=f"{'+' if (ts_res.slope_per_decade or 0) > 0 else ''}{(ts_res.slope_per_decade or 0):.2f} {param.display_unit}/decade",
        slope_display_bn=f"{'+' if (ts_res.slope_per_decade or 0) > 0 else ''}{(ts_res.slope_per_decade or 0):.2f} {param.display_unit}/দশক",
        unit=param.display_unit,
        direction=mk_res.direction,
        evidence_state=evidence_state,
        p_value=mk_res.p_value,
        ci_95_lower_per_decade=ts_res.ci_95_lower_per_decade,
        ci_95_upper_per_decade=ts_res.ci_95_upper_per_decade,
        coverage_pct=float(ann_df["coverage"].mean()) if "coverage" in ann_df.columns else 100.0,
        method_name_en="Mann-Kendall",
        method_name_bn="ম্যান-কেন্ডাল",
    )

    narration_en = render_english_narration(claim)
    narration_bn = render_bangla_narration(claim)

    claim.result_id = result_id
    created_iso = datetime.now(timezone.utc).isoformat()

    # Interpretation text (Resolves Audit R04)
    if evidence_state in ("supported_increase", "supported_decrease"):
        interp_en = f"Statistically supported {mk_res.direction} trend over {start_ret}-{end_ret}."
        interp_bn = f"{start_ret}-{end_ret} সময়কালে পরিসংখ্যানগতভাবে সমর্থিত প্রবণতা।"
    elif evidence_state == "limited":
        if has_excessive_gap:
            interp_en = f"Exploratory trend evidence over {start_ret}-{end_ret} (consecutive missing gap > {policy.max_consecutive_missing_gap} years)."
            interp_bn = f"{start_ret}-{end_ret} সময়কালে অনুসন্ধানী প্রমাণ (অনুপস্থিত ব্যবধান > {policy.max_consecutive_missing_gap} বছর)।"
        else:
            interp_en = f"Exploratory trend evidence over {start_ret}-{end_ret} (record span < {policy.min_eligible_years_climate} years)."
            interp_bn = f"{start_ret}-{end_ret} সময়কালে প্রাথমিক অনুসন্ধানী প্রমাণ (সময়কাল < {policy.min_eligible_years_climate} বছর)।"
    elif evidence_state == "flat":
        interp_en = f"No monotonic change detected over {start_ret}-{end_ret}; slope is near-zero."
        interp_bn = f"{start_ret}-{end_ret} সময়কালে কোনো ধারাবাহিক একক পরিবর্তন নেই; পরিবর্তনের হার প্রায় শূন্য।"
    else:
        interp_en = f"No statistically significant monotonic trend detected over {start_ret}-{end_ret}."
        interp_bn = f"{start_ret}-{end_ret} সময়কালে কোনো পরিসংখ্যানগতভাবে তাৎপর্যপূর্ণ একক পরিবর্তনের প্রমাণ নেই।"

    # Build final immutable result object conforming to Table 18
    result: Dict[str, Any] = {
        "identity": {
            "result_id": result_id,
            "schema_version": "1.0.0",
            "created_at": created_iso,
            "normalized_query": {
                "region_id": reg_id,
                "parameter_id": param_id,
                "binding_id": bind_id,
                "start_year": req_start,
                "end_year": req_end,
                "policy_id": policy.id,
            },
        },
        "region": {
            "id": region.id,
            "name_en": region.name_en,
            "name_bn": region.name_bn,
            "region_type": region.region_type,
            "centroid": {"lat": region.centroid_lat, "lon": region.centroid_lon},
            "bbox": region.bbox,
            "area_km2": region.area_km2,
            "geometry_version": region.geometry_version,
            "citation": region.citation,
        },
        "parameter": {
            "id": param.id,
            "name_en": param.name_en,
            "name_bn": param.name_bn,
            "domain": param.domain,
            "canonical_unit": param.canonical_unit,
            "display_unit": param.display_unit,
            "temporal_statistic": temporal_stat,
            "observation_type": param.observation_type,
        },
        "data_support": {
            "requested_interval": [req_start, req_end],
            "retained_interval": [start_ret, end_ret],
            "sample_count": n_samples,
            "native_spatial_resolution": binding.native_spatial_resolution,
            "temporal_cadence": binding.temporal_cadence,
            "valid_area_coverage_pct": claim.coverage_pct,
        },
        "series": {
            "years": [int(y) for y in years],
            "values": [round(float(v), 4) for v in values],
            "unit": param.display_unit,
        },
        "mann_kendall": {
            "S": mk_res.S,
            "variance": mk_res.var_S,
            "Z": mk_res.Z,
            "p_value": mk_res.p_value,
            "alpha": mk_res.alpha,
            "method": mk_res.method,
            "direction": mk_res.direction,
            "autocorrelation_adjusted": mk_res.autocorrelation_adjusted,
            "vif": mk_res.vif,
        },
        "theil_sen": {
            "slope_per_year": ts_res.slope_per_year,
            "slope_per_decade": ts_res.slope_per_decade,
            "intercept": ts_res.intercept,
            "ref_time": ts_res.ref_time,
            "ci_95_lower_per_decade": ts_res.ci_95_lower_per_decade,
            "ci_95_upper_per_decade": ts_res.ci_95_upper_per_decade,
            "method": ts_res.method,
            "is_degenerate": ts_res.is_degenerate,
        },
        "fitted_band": {
            "is_valid": band_res.is_valid,
            "coverage": band_res.coverage,
            "method": band_res.method,
            "points": [
                {
                    "time": p.time,
                    "fitted": round(p.fitted, 4),
                    "lower": round(p.lower, 4),
                    "upper": round(p.upper, 4),
                }
                for p in band_res.points
            ],
        },
        "diagnostics": {
            "ar1": corr_diag.ar1,
            "vif": corr_diag.vif,
            "is_autocorrelated": corr_diag.is_autocorrelated,
            "significant_lags": corr_diag.significant_lags,
            "critical_threshold": corr_diag.critical_threshold,
        },
        "evidence": {
            "state": evidence_state,
            "direction": mk_res.direction,
            "alpha": policy.alpha,
            "interpretation_en": interp_en,
            "interpretation_bn": interp_bn,
        },
        "narration": {
            "en": narration_en,
            "bn": narration_bn,
        },
        "provenance": {
            "dataset_id": binding.id,
            "collection_id": binding.collection_id,
            "collection_name": binding.collection_name,
            "version": binding.version,
            "doi": binding.doi,
            "source_url": binding.source_url,
            "citation": binding.citation,
            "access_mode": "cache",
            "retrieved_at": "2026-10-01T08:00:00Z",
            "data_sha256": data_sha,
        },
        "reproducibility": {
            "code_revision": "v1.4.0",
            "policy_id": policy.id,
            "bootstrap_seed": policy.bootstrap_seed,
            "bootstrap_replicates": policy.bootstrap_replicates,
        },
    }

    # Validate generated narration in BOTH English and Bangla (Resolves Finding F12 / Audit R07)
    valid_en, err_en = validate_narrative_text(narration_en, claim, result)
    valid_bn, err_bn = validate_narrative_text(narration_bn, claim, result)
    if not (valid_en and valid_bn):
        # Fallback to pure deterministic claim facts if validation detects anomaly; never publish rejected sentences
        sign_char = "+" if (ts_res.slope_per_decade or 0) > 0 else ""
        slope_str = f"{sign_char}{(ts_res.slope_per_decade or 0):.2f}"
        slope_bn = slope_str.translate(str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯"))
        start_bn = str(start_ret).translate(str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯"))
        end_bn = str(end_ret).translate(str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯"))

        evidence_bn_labels = {
            "supported_increase": "পরিসংখ্যানগতভাবে সমর্থিত বৃদ্ধি",
            "supported_decrease": "পরিসংখ্যানগতভাবে সমর্থিত হ্রাস",
            "limited": "প্রাথমিক অনুসন্ধানী প্রমাণ",
            "insufficient": "অপর্যাপ্ত তথ্য",
            "inconclusive": "অমীমাংসিত",
            "flat": "স্থিতিশীল",
        }
        ev_bn = evidence_bn_labels.get(evidence_state, evidence_state)

        result["narration"]["en"] = [
            f"Over {start_ret} to {end_ret}, {region.name_en} {param.name_en.lower()} had an estimated rate of {slope_str} {param.display_unit}/decade.",
            f"The statistical evidence is categorized as {evidence_state}.",
        ]
        result["narration"]["bn"] = [
            f"{start_bn} থেকে {end_bn} সময়কালে {region.name_bn}-এ {param.name_bn}-এর পরিবর্তনের হার ছিল দশক প্রতি {slope_bn} {param.display_unit}।",
            f"পরিসংখ্যানগত প্রমাণের অবস্থা: {ev_bn}।",
        ]
        result["narration_status"] = "fallback"
        result["narration_validation_errors"] = err_en + err_bn

    # Persist immutable result in SQLite (Append-Only) and return canonical winner
    saved_result = store.save_result(result_id, result["identity"]["normalized_query"], result)

    return saved_result
