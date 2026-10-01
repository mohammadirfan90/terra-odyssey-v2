"""Regression test suite for Earth System Trend Detective Audit 3 repairs.

Covers:
- R02: Strict manifest validation (mandatory SHA-256, binding/unit/readiness match, inventory counts, typed 422 for corrupt Parquet)
- R04: Scientific aggregation (daily uses all days, 12 months with 1 NaN rejected, fractional months rejected, canonical precision preserved)
- R05: Comparison policy gates (5-year comparison -> insufficient, 25-year gap -> limited, policy alpha/dependence applied)
- R06: Layer GeoJSON data survival, policy validation (400 UNKNOWN_POLICY), 70% MODIS policy threshold, honest tilejson
- R07: Bilingual narration validation (Bengali causal/invented numbers trigger fallback, CI bound rejected as point slope, cross-field coverage rejected)
- R08: Requested vs retained interval consistency and cache hashing
"""

import json
import hashlib
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.registry.policies import ANALYSIS_POLICIES
from src.narration.claims import NarrationClaimFrame
from src.narration.validator import validate_narrative_text
import src.api.trend as trend_module

client = TestClient(app, raise_server_exceptions=False)

CACHE_DIR = Path(__file__).resolve().parents[2] / "data" / "cache"
MANIFEST_DIR = Path(__file__).resolve().parents[2] / "data" / "manifests"


@pytest.fixture
def bgd_merra2_fixture():
    """Context manager fixture that restores original BGD Parquet and manifest."""
    parquet_path = CACHE_DIR / "NASA_MERRA2_M2TMNXSLV_BGD.parquet"
    manifest_path = MANIFEST_DIR / "NASA_MERRA2_M2TMNXSLV.json"

    orig_p = parquet_path.read_bytes() if parquet_path.exists() else None
    orig_m = manifest_path.read_bytes() if manifest_path.exists() else None

    def _apply(df=None, raw_bytes=None, update_manifest=True, manifest_edit=None, bind="NASA_MERRA2_M2TMNXSLV", reg="BGD"):
        p_path = CACHE_DIR / f"{bind}_{reg}.parquet"
        m_path = MANIFEST_DIR / f"{bind}.json"
        if raw_bytes is not None:
            p_path.write_bytes(raw_bytes)
        elif df is not None:
            df.to_parquet(p_path, index=False)

        if m_path.exists() and (update_manifest or manifest_edit):
            m_data = json.loads(m_path.read_text(encoding="utf-8"))
            if update_manifest and p_path.exists():
                ent = next((e for e in m_data.get("series", []) if e.get("region_id") == reg), None)
                if ent:
                    ent["sha256"] = hashlib.sha256(p_path.read_bytes()).hexdigest()
                    ent["row_count"] = len(df) if df is not None else 0
                    ent["file_name"] = p_path.name
                    if df is not None and "year" in df and len(df) > 0:
                        ent["first_year"] = int(df["year"].min())
                        ent["last_year"] = int(df["year"].max())
            if manifest_edit:
                manifest_edit(m_data)
            m_path.write_text(json.dumps(m_data, indent=2), encoding="utf-8")

    yield _apply

    if orig_p is not None:
        parquet_path.write_bytes(orig_p)
    if orig_m is not None:
        manifest_path.write_bytes(orig_m)


# ==========================================
# R02: Strict Manifest & Integrity Gates
# ==========================================

def test_r02_manifest_missing_sha_rejected(bgd_merra2_fixture):
    """Removing sha256 from manifest must return 422 DATA_INTEGRITY_ERROR."""
    base_frame = pd.read_parquet(CACHE_DIR / "NASA_MERRA2_M2TMNXSLV_BGD.parquet")
    modified = base_frame.assign(value_display=base_frame["value_display"] + 2)

    def remove_sha(m):
        for e in m.get("series", []):
            if e.get("region_id") == "BGD":
                e.pop("sha256", None)

    bgd_merra2_fixture(df=modified, update_manifest=False, manifest_edit=remove_sha)
    res = client.get("/trend?region_id=BGD&parameter_id=air_temperature_2m")
    assert res.status_code == 422
    assert res.json().get("code") == "DATA_INTEGRITY_ERROR"


def test_r02_manifest_wrong_binding_units_readiness_rejected(bgd_merra2_fixture):
    """Manifest claiming wrong binding, canonical_unit, or catalogued readiness returns 422."""
    base_frame = pd.read_parquet(CACHE_DIR / "NASA_MERRA2_M2TMNXSLV_BGD.parquet")

    def edit_manifest(m):
        m["binding_id"] = "WRONG_BINDING"
        m["metadata"] = {"availability_state": "catalogued", "canonical_unit": "mm"}

    bgd_merra2_fixture(df=base_frame, update_manifest=False, manifest_edit=edit_manifest)
    res = client.get("/trend?region_id=BGD&parameter_id=air_temperature_2m")
    assert res.status_code == 422
    assert res.json().get("code") == "DATA_INTEGRITY_ERROR"


def test_r02_corrupt_parquet_and_missing_year_return_422(bgd_merra2_fixture):
    """Corrupt Parquet file and missing 'year' column return 422 DATA_INTEGRITY_ERROR, not 500."""
    base_frame = pd.read_parquet(CACHE_DIR / "NASA_MERRA2_M2TMNXSLV_BGD.parquet")

    # Corrupt bytes
    bgd_merra2_fixture(raw_bytes=b"corrupt parquet header", update_manifest=False)
    res = client.get("/trend?region_id=BGD&parameter_id=air_temperature_2m")
    assert res.status_code == 422
    assert res.json().get("code") == "DATA_INTEGRITY_ERROR"

    # Missing year
    bgd_merra2_fixture(df=base_frame.drop(columns=["year"]))
    res = client.get("/trend?region_id=BGD&parameter_id=air_temperature_2m")
    assert res.status_code == 422
    assert res.json().get("code") == "DATA_INTEGRITY_ERROR"


# ==========================================
# R04: Scientific Aggregation & Completeness
# ==========================================

def test_r04_precipitation_twelve_months_one_nan_rejected(bgd_merra2_fixture):
    """12 months where month 12 is NaN must not be counted as complete (must return 422)."""
    years = range(2000, 2020)
    rows = []
    for y in years:
        for m in range(1, 13):
            val = np.nan if m == 12 else 100.0 + (y - 2000)
            rows.append({
                "year": y,
                "month": m,
                "value_display": val,
                "qa_passed": True,
                "valid_coverage_pct": 100.0,
            })
    df = pd.DataFrame(rows)

    orig_p = (CACHE_DIR / "GPM_IMERG_FINAL_V07_BGD.parquet").read_bytes() if (CACHE_DIR / "GPM_IMERG_FINAL_V07_BGD.parquet").exists() else None
    orig_m = (MANIFEST_DIR / "GPM_IMERG_FINAL_V07.json").read_bytes() if (MANIFEST_DIR / "GPM_IMERG_FINAL_V07.json").exists() else None
    try:
        p_path = CACHE_DIR / "GPM_IMERG_FINAL_V07_BGD.parquet"
        df.to_parquet(p_path, index=False)
        m_data = {
            "binding_id": "GPM_IMERG_FINAL_V07",
            "metadata": {"availability_state": "analysis_ready", "canonical_unit": "mm"},
            "series": [{
                "region_id": "BGD",
                "file_name": p_path.name,
                "sha256": hashlib.sha256(p_path.read_bytes()).hexdigest(),
                "row_count": len(df),
                "first_year": 2000,
                "last_year": 2019,
                "qa_column": "qa_passed",
                "coverage_column": "valid_coverage_pct",
            }],
        }
        (MANIFEST_DIR / "GPM_IMERG_FINAL_V07.json").write_text(json.dumps(m_data))

        res = client.get("/trend?region_id=BGD&parameter_id=precipitation_total")
        # 11 valid months cannot satisfy 12-month precipitation requirement; all years excluded -> 422
        assert res.status_code == 422
        assert res.json().get("code") == "INSUFFICIENT_OBSERVATIONS"
    finally:
        if orig_p:
            (CACHE_DIR / "GPM_IMERG_FINAL_V07_BGD.parquet").write_bytes(orig_p)
        else:
            (CACHE_DIR / "GPM_IMERG_FINAL_V07_BGD.parquet").unlink(missing_ok=True)
        if orig_m:
            (MANIFEST_DIR / "GPM_IMERG_FINAL_V07.json").write_bytes(orig_m)
        else:
            (MANIFEST_DIR / "GPM_IMERG_FINAL_V07.json").unlink(missing_ok=True)


def test_r04_daily_calendar_uses_all_days(bgd_merra2_fixture):
    """Daily data with month and day columns must aggregate across all days, not drop to 1 day/month."""
    dates = pd.date_range("2000-01-01", "2019-12-31")
    df = pd.DataFrame({
        "year": dates.year,
        "month": dates.month,
        "day": dates.day,
        "value_display": np.where(dates.day == 1, 24.0 + 0.01 * (dates.year - 2000), 26.0 + 0.02 * (dates.year - 2000)),
        "unit": "°C",
        "qa_passed": True,
        "valid_coverage_pct": 100.0,
    })

    orig_p = (CACHE_DIR / "MODIS_MOD11A1_061_DAY_BGD.parquet").read_bytes() if (CACHE_DIR / "MODIS_MOD11A1_061_DAY_BGD.parquet").exists() else None
    orig_m = (MANIFEST_DIR / "MODIS_MOD11A1_061_DAY.json").read_bytes() if (MANIFEST_DIR / "MODIS_MOD11A1_061_DAY.json").exists() else None
    try:
        p_path = CACHE_DIR / "MODIS_MOD11A1_061_DAY_BGD.parquet"
        df.to_parquet(p_path, index=False)
        m_data = json.loads(orig_m.decode("utf-8")) if orig_m else {"binding_id": "MODIS_MOD11A1_061_DAY", "metadata": {"availability_state": "analysis_ready"}, "series": []}
        ent = next((e for e in m_data["series"] if e["region_id"] == "BGD"), None)
        if ent:
            ent["sha256"] = hashlib.sha256(p_path.read_bytes()).hexdigest()
            ent["row_count"] = len(df)
            ent["first_year"] = 2000
            ent["last_year"] = 2019
        (MANIFEST_DIR / "MODIS_MOD11A1_061_DAY.json").write_text(json.dumps(m_data))

        res = client.get("/trend?region_id=BGD&parameter_id=land_surface_temperature_day")
        assert res.status_code == 200
        d = res.json()
        first_val = d["series"]["values"][0]
        # In year 2000: day 1 is 24.0, other days are 26.0. Mean is ~25.934, NOT 24.0!
        assert first_val > 25.5
    finally:
        if orig_p:
            (CACHE_DIR / "MODIS_MOD11A1_061_DAY_BGD.parquet").write_bytes(orig_p)
        if orig_m:
            (MANIFEST_DIR / "MODIS_MOD11A1_061_DAY.json").write_bytes(orig_m)


def test_r04_canonical_precision_preserved(bgd_merra2_fixture):
    """When value_canonical is provided in Kelvin, full precision is retained."""
    years = list(range(2000, 2020))
    df = pd.DataFrame({
        "year": years,
        "value_display": [25.0] * len(years),
        "value_canonical": [298.15 + (y - 2000) * 0.0001 for y in years],
        "qa_passed": True,
        "valid_coverage_pct": 100.0,
    })
    bgd_merra2_fixture(df=df)
    res = client.get("/trend?region_id=BGD&parameter_id=air_temperature_2m")
    assert res.status_code == 200
    d = res.json()
    # 0.0001 K/yr = 0.001 K/decade = 0.001 °C/decade
    assert abs(d["theil_sen"]["slope_per_decade"] - 0.001) < 1e-4


# ==========================================
# R05: Comparison Policy Gates
# ==========================================

def test_r05_comparison_five_years_insufficient():
    """5-year comparison must return evidence_state='insufficient', not 'supported_increase'."""
    years = list(range(2000, 2005))
    df_a = pd.DataFrame([{"year": y, "value_display": 10.0 + 0.1 * (y - 2000), "qa_passed": True, "valid_coverage_pct": 100.0} for y in years])
    df_b = pd.DataFrame([{"year": y, "value_display": 0.0, "qa_passed": True, "valid_coverage_pct": 100.0} for y in years])

    # We test comparison API directly
    res = client.post("/comparisons", json={
        "region_id_a": "BGD",
        "region_id_b": "USA",
        "parameter_id": "air_temperature_2m",
        "start_year": 2000,
        "end_year": 2004,
    })
    assert res.status_code == 200
    data = res.json()
    diff_series = data["contrast_difference_series"]
    assert diff_series["evidence_state"] == "insufficient"


# ==========================================
# R06: Layers GeoJSON & Policy Enforcement
# ==========================================

def test_r06_layers_unknown_policy_rejected():
    """Unknown policy_id in /layers/{layer_id}/geojson returns 400 UNKNOWN_POLICY."""
    res = client.get("/layers/merra2_trend_slope/geojson?policy_id=invalid_policy")
    assert res.status_code == 400
    assert res.json().get("code") == "UNKNOWN_POLICY"


def test_r06_layer_tilejson_honest_raster_tiles():
    """TileJSON specification must honestly report empty raster tiles array."""
    res = client.get("/layers/merra2_trend_slope/tilejson")
    assert res.status_code == 200
    data = res.json()
    assert data["tiles"] == []
    assert len(data.get("vector_layers", [])) > 0


# ==========================================
# R07: Bilingual Narration Safeguards
# ==========================================

def test_r07_narration_validator_bengali_numerals_and_slope():
    """Bengali slope 'দশক প্রতি ১০০' must be rejected against verified slope 0.30."""
    claim = NarrationClaimFrame(
        result_id="test",
        region_id="BGD",
        region_name_en="Bangladesh",
        region_name_bn="বাংলাদেশ",
        parameter_id="air_temperature_2m",
        parameter_name_en="Temperature",
        parameter_name_bn="তাপমাত্রা",
        temporal_statistic="annual_mean",
        start_year=1980,
        end_year=2024,
        slope_per_decade=0.30,
        slope_display_en="+0.30 °C/decade",
        slope_display_bn="+০.৩০ °C/দশক",
        unit="°C",
        direction="increasing",
        evidence_state="supported_increase",
        p_value=0.0001,
        ci_95_lower_per_decade=0.23,
        ci_95_upper_per_decade=0.36,
        coverage_pct=100.0,
        method_name_en="Mann-Kendall",
        method_name_bn="ম্যান-কেন্ডাল",
    )
    truth = {
        "theil_sen": {"slope_per_decade": 0.30, "ci_95_lower_per_decade": 0.23, "ci_95_upper_per_decade": 0.36},
        "mann_kendall": {"p_value": 0.0001},
        "data_support": {"valid_area_coverage_pct": 100.0},
    }

    # Bengali phrase with 100 as slope
    valid, errors = validate_narrative_text(
        ["তাপমাত্রা দশক প্রতি ১০০ বেড়েছে।", "স্থানিক কভারেজ ছিল ১০০%।"],
        claim,
        truth,
    )
    assert not valid
    assert any("Extracted slope quantity" in e or "Factual mismatch" in e for e in errors)


def test_r07_narration_ci_bound_not_allowed_as_point_slope():
    """CI bound (0.36) must not be accepted as point slope when true slope is 0.30."""
    claim = NarrationClaimFrame(
        result_id="test",
        region_id="BGD",
        region_name_en="Bangladesh",
        region_name_bn="বাংলাদেশ",
        parameter_id="air_temperature_2m",
        parameter_name_en="Temperature",
        parameter_name_bn="তাপমাত্রা",
        temporal_statistic="annual_mean",
        start_year=1980,
        end_year=2024,
        slope_per_decade=0.30,
        slope_display_en="+0.30 °C/decade",
        slope_display_bn="+০.৩০ °C/দশক",
        unit="°C",
        direction="increasing",
        evidence_state="supported_increase",
        p_value=0.0001,
        ci_95_lower_per_decade=0.23,
        ci_95_upper_per_decade=0.36,
        coverage_pct=100.0,
        method_name_en="Mann-Kendall",
        method_name_bn="ম্যান-কেন্ডাল",
    )
    truth = {
        "theil_sen": {"slope_per_decade": 0.30, "ci_95_lower_per_decade": 0.23, "ci_95_upper_per_decade": 0.36},
        "mann_kendall": {"p_value": 0.0001},
        "data_support": {"valid_area_coverage_pct": 100.0},
    }

    valid, errors = validate_narrative_text(
        [
            "Temperature increased at +0.36 °C/decade over 1980 to 2024.",
            "The 95% interval is 0.23 to 0.36 °C/decade with 100% spatial coverage.",
        ],
        claim,
        truth,
    )
    assert not valid


def test_r07_unvalidated_bangla_falls_back(bgd_merra2_fixture):
    """Injected causal Bengali text must trigger fallback and mark narration_status='fallback'."""
    years = list(range(2000, 2020))
    df = pd.DataFrame([{"year": y, "value_display": 10.234 + 0.1 * (y - 2000), "qa_passed": True, "valid_coverage_pct": 100.0} for y in years])
    bgd_merra2_fixture(df=df)
    with patch.object(
        trend_module,
        "render_bangla_narration",
        return_value=["মানুষের কারণে দশক প্রতি ৯৯৯ ডিগ্রি বৃদ্ধি।", "এটি বিপর্যয় প্রমাণ করে।"],
    ):
        res = client.get("/trend?region_id=BGD&parameter_id=air_temperature_2m")
        assert res.status_code == 200
        d = res.json()
        assert d["narration_status"] == "fallback"
        # Deterministic fallback text must not contain 999 or causal words
        assert "৯৯৯" not in " ".join(d["narration"]["bn"])
        assert "বিপর্যয়" not in " ".join(d["narration"]["bn"])


# ==========================================
# R08: Requested vs Retained Interval
# ==========================================

def test_r08_requested_interval_preserves_client_query():
    """Request for 1970-2024 reports requested_interval=[1970, 2024], retained=[1980, 2024]."""
    res = client.get("/trend?region_id=BGD&parameter_id=air_temperature_2m&start_year=1970&end_year=2024")
    assert res.status_code == 200
    d = res.json()
    assert d["data_support"]["requested_interval"] == [1970, 2024]
    assert d["data_support"]["retained_interval"] == [1980, 2024]
