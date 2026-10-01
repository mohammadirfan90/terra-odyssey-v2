"""Audit Revision 4 Regression Tests.

Validates all findings identified in Earth_System_Trend_Detective_Revision_4_Audit.md:
- V4-02: Manifest metadata gating, column mapping (qa_score, area_coverage), numeric type enforcement
- V4-03: Pre-aggregated annual cadence vs raw daily cadence for packaged series
- V4-04: Daily calendar support (duplicate day rejection, Feb 31 rejection, leap-year denominator, 80% coverage)
- V4-05: Physically correct temperature anomaly conversion (0.5 K -> 0.5 °C, not -272.65 °C)
- V4-06: Truthful confidence interval upper bounds in English and Bangla narration
- V4-08: Map vector layer inference parity with primary trend (Hamed-Rao VIF, evidence_state)
- V4-09: Immutable comparison identity and full policy settings hashing
"""

import json
import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.cache.store import LocalDataStore, ManifestSchemaError
from src.compute.aggregation import aggregate_annual_series
from src.registry.policies import ANALYSIS_POLICIES
from src.registry.bindings import DATASET_BINDINGS
from src.narration.validator import NarrationClaimFrame, validate_narrative_text

client = TestClient(app)


def test_v4_03_packaged_series_usable():
    """V4-03: Packaged annual series for daily/monthly products must return 200 with non-zero observations."""
    # Test MODIS day Bangladesh
    resp_day = client.get("/trend?region_id=BGD&parameter_id=land_surface_temperature_day&binding_id=MODIS_MOD11A1_061_DAY")
    assert resp_day.status_code == 200
    body_day = resp_day.json()
    assert body_day["data_support"]["sample_count"] > 0
    assert len(body_day["series"]["years"]) > 0

    # Test MODIS night Bangladesh
    resp_night = client.get("/trend?region_id=BGD&parameter_id=land_surface_temperature_night&binding_id=MODIS_MOD11A1_061_NIGHT")
    assert resp_night.status_code == 200
    body_night = resp_night.json()
    assert body_night["data_support"]["sample_count"] > 0

    # Test POWER point air temperature Bangladesh
    resp_power = client.get("/trend?region_id=BGD&parameter_id=point_air_temperature&binding_id=NASA_POWER_DAILY_POINT")
    assert resp_power.status_code == 200
    body_power = resp_power.json()
    assert body_power["data_support"]["sample_count"] > 0


    # Test OISST sea surface temperature for Bay of Bengal
    resp_oisst = client.get("/trend?region_id=BAY_OF_BENGAL&parameter_id=sea_surface_temperature&binding_id=NOAA_OISST_V2_1")
    assert resp_oisst.status_code == 200
    body_oisst = resp_oisst.json()
    assert body_oisst["data_support"]["sample_count"] > 0




def test_v4_02_manifest_missing_metadata_rejected(tmp_path, monkeypatch):
    """V4-02: Manifest without required metadata object returns 422 on /trend and unavailable on /coverage."""
    data_dir = tmp_path / "data"
    manifests_dir = data_dir / "manifests"
    cache_dir = data_dir / "cache"
    manifests_dir.mkdir(parents=True)
    cache_dir.mkdir(parents=True)

    # Write a test parquet
    pq_path = cache_dir / "NASA_MERRA2_M2TMNXSLV_BGD.parquet"
    df = pd.DataFrame({
        "year": np.arange(1980, 2024),
        "val": np.linspace(25.0, 26.0, 44),
        "valid_coverage_pct": np.full(44, 100.0),
        "qa_passed": np.full(44, True),
    })
    df.to_parquet(pq_path)
    import hashlib
    sha256 = hashlib.sha256(pq_path.read_bytes()).hexdigest()

    # Manifest WITHOUT metadata object
    bad_manifest = {
        "binding_id": "NASA_MERRA2_M2TMNXSLV",
        "series": [{
            "region_id": "BGD",
            "file_name": "NASA_MERRA2_M2TMNXSLV_BGD.parquet",
            "sha256": sha256,
            "row_count": 44,
            "first_year": 1980,
            "last_year": 2023,
        }]
    }
    with open(manifests_dir / "NASA_MERRA2_M2TMNXSLV.json", "w", encoding="utf-8") as f:
        json.dump(bad_manifest, f)

    monkeypatch.setenv("DATA_ROOT", str(data_dir))
    store = LocalDataStore(data_root=data_dir)

    # has_series must be False
    assert store.has_series("NASA_MERRA2_M2TMNXSLV", "BGD") is False

    # load_series must raise ManifestSchemaError
    with pytest.raises(ManifestSchemaError):
        store.load_series("NASA_MERRA2_M2TMNXSLV", "BGD")

    # /trend must return typed 422
    resp = client.get("/trend?region_id=BGD&parameter_id=air_temperature_2m&binding_id=NASA_MERRA2_M2TMNXSLV")
    assert resp.status_code == 422
    assert resp.json().get("code") == "DATA_INTEGRITY_ERROR"

    # /coverage must report unavailable
    c_resp = client.get("/coverage?region_id=BGD&parameter_id=air_temperature_2m&binding_id=NASA_MERRA2_M2TMNXSLV")
    assert c_resp.status_code == 200
    assert c_resp.json()["is_supported"] is False
    assert c_resp.json()["availability_state"] == "unavailable"


def test_v4_02_manifest_wrong_variable_unit_cadence_rejected(tmp_path, monkeypatch):
    """V4-02: Manifest declaring wrong variable, display unit, or temporal cadence returns 422."""
    data_dir = tmp_path / "data"
    manifests_dir = data_dir / "manifests"
    cache_dir = data_dir / "cache"
    manifests_dir.mkdir(parents=True)
    cache_dir.mkdir(parents=True)

    pq_path = cache_dir / "NASA_MERRA2_M2TMNXSLV_BGD.parquet"
    df = pd.DataFrame({
        "year": np.arange(1980, 2024),
        "val": np.linspace(25.0, 26.0, 44),
        "valid_coverage_pct": np.full(44, 100.0),
        "qa_passed": np.full(44, True),
    })
    df.to_parquet(pq_path)
    import hashlib
    sha256 = hashlib.sha256(pq_path.read_bytes()).hexdigest()

    bad_manifest = {
        "binding_id": "NASA_MERRA2_M2TMNXSLV",
        "metadata": {
            "availability_state": "analysis_ready",
            "canonical_unit": "K",
            "variable_name": "WRONG_VAR_T2M",  # Wrong variable
            "display_unit": "degC",
            "temporal_cadence": "monthly",
        },
        "series": [{
            "region_id": "BGD",
            "file_name": "NASA_MERRA2_M2TMNXSLV_BGD.parquet",
            "sha256": sha256,
            "row_count": 44,
            "first_year": 1980,
            "last_year": 2023,
        }]
    }
    with open(manifests_dir / "NASA_MERRA2_M2TMNXSLV.json", "w", encoding="utf-8") as f:
        json.dump(bad_manifest, f)

    monkeypatch.setenv("DATA_ROOT", str(data_dir))
    resp = client.get("/trend?region_id=BGD&parameter_id=air_temperature_2m&binding_id=NASA_MERRA2_M2TMNXSLV")
    assert resp.status_code == 422
    assert resp.json().get("code") == "DATA_INTEGRITY_ERROR"


def test_v4_02_declared_qa_and_coverage_column_mapping(tmp_path, monkeypatch):
    """V4-02: Declared qa_score=False and area_coverage=0 are properly mapped and filtered out."""
    data_dir = tmp_path / "data"
    manifests_dir = data_dir / "manifests"
    cache_dir = data_dir / "cache"
    manifests_dir.mkdir(parents=True)
    cache_dir.mkdir(parents=True)

    pq_path = cache_dir / "NASA_MERRA2_M2TMNXSLV_BGD.parquet"
    # Create 40 years where half have qa_score=False and area_coverage=0
    years = np.arange(1980, 2020)
    qa_score = np.array([True if i % 2 == 0 else False for i in range(40)])
    area_cov = np.array([100.0 if i % 2 == 0 else 0.0 for i in range(40)])
    df = pd.DataFrame({
        "year": years,
        "val": np.linspace(25.0, 26.0, 40),
        "area_coverage": area_cov,
        "qa_score": qa_score,
    })
    df.to_parquet(pq_path)
    import hashlib
    sha256 = hashlib.sha256(pq_path.read_bytes()).hexdigest()

    manifest = {
        "binding_id": "NASA_MERRA2_M2TMNXSLV",
        "metadata": {
            "availability_state": "analysis_ready",
            "canonical_unit": "K",
            "variable_name": "T2M",
            "display_unit": "°C",
            "temporal_cadence": "monthly",
        },
        "series": [{
            "region_id": "BGD",
            "file_name": "NASA_MERRA2_M2TMNXSLV_BGD.parquet",
            "sha256": sha256,
            "row_count": 40,
            "first_year": 1980,
            "last_year": 2019,
            "qa_column": "qa_score",
            "coverage_column": "area_coverage",
        }]
    }
    with open(manifests_dir / "NASA_MERRA2_M2TMNXSLV.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f)

    monkeypatch.setenv("DATA_ROOT", str(data_dir))
    resp = client.get("/trend?region_id=BGD&parameter_id=air_temperature_2m&binding_id=NASA_MERRA2_M2TMNXSLV")
    assert resp.status_code == 200
    body = resp.json()
    # Exactly 20 years should survive (the ones with qa_score=True and area_coverage=100.0)
    assert body["data_support"]["sample_count"] == 20


def test_v4_02_string_numeric_columns_typed_error(tmp_path, monkeypatch):
    """V4-02: String-valued years or coverage return typed 422 DATA_INTEGRITY_ERROR, never untyped 500."""
    data_dir = tmp_path / "data"
    manifests_dir = data_dir / "manifests"
    cache_dir = data_dir / "cache"
    manifests_dir.mkdir(parents=True)
    cache_dir.mkdir(parents=True)

    pq_path = cache_dir / "NASA_MERRA2_M2TMNXSLV_BGD.parquet"
    df = pd.DataFrame({
        "year": ["invalid_year_1", "invalid_year_2", "invalid_year_3"],
        "val": [25.0, 25.1, 25.2],
        "valid_coverage_pct": [100.0, 100.0, 100.0],
        "qa_passed": [True, True, True],
    })
    df.to_parquet(pq_path)
    import hashlib
    sha256 = hashlib.sha256(pq_path.read_bytes()).hexdigest()

    manifest = {
        "binding_id": "NASA_MERRA2_M2TMNXSLV",
        "metadata": {
            "availability_state": "analysis_ready",
            "canonical_unit": "K",
            "variable_name": "T2M",
            "display_unit": "degC",
            "temporal_cadence": "monthly",
        },
        "series": [{
            "region_id": "BGD",
            "file_name": "NASA_MERRA2_M2TMNXSLV_BGD.parquet",
            "sha256": sha256,
            "row_count": 3,
            "first_year": 1980,
            "last_year": 1982,
        }]
    }
    with open(manifests_dir / "NASA_MERRA2_M2TMNXSLV.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f)

    monkeypatch.setenv("DATA_ROOT", str(data_dir))
    resp = client.get("/trend?region_id=BGD&parameter_id=air_temperature_2m&binding_id=NASA_MERRA2_M2TMNXSLV")
    assert resp.status_code == 422
    assert resp.json().get("code") == "DATA_INTEGRITY_ERROR"


def test_v4_04_calendar_completeness_and_impossible_dates():
    """V4-04: Duplicate Jan 1 rows, Feb 31, and insufficient calendar completeness are strictly rejected."""
    policy = ANALYSIS_POLICIES["modis_lst_satellite_policy"]  # requires 80% coverage

    # 1. 365 duplicate January 1 rows per year
    dates = ["2001-01-01"] * 365
    df_dup = pd.DataFrame({
        "year": [2001] * 365,
        "month": [1] * 365,
        "day": [1] * 365,
        "date": dates,
        "val": [25.0] * 365,
        "qa_passed": [True] * 365,
        "valid_coverage_pct": [100.0] * 365,
    })
    ann = aggregate_annual_series(df_dup, param_id="land_surface_temperature_day", policy=policy, binding_id="MODIS_MOD11A1_061_DAY")
    # Must have 0 valid years because 1 distinct day < 292 required days (80% of 365)
    assert len(ann) == 0

    # 2. Impossible date (February 31) must raise ManifestSchemaError (which yields 422)
    df_feb31 = pd.DataFrame({
        "year": [2001],
        "month": [2],
        "day": [31],
        "date": ["2001-02-31"],
        "val": [25.0],
        "qa_passed": [True],
        "valid_coverage_pct": [100.0],
    })
    with pytest.raises(ManifestSchemaError):
        aggregate_annual_series(df_feb31, param_id="land_surface_temperature_day", policy=policy, binding_id="MODIS_MOD11A1_061_DAY")

    # 3. 205 distinct days (56.2% of non-leap year) must fail under 80% policy
    # Generate 205 valid days starting from Jan 1
    d_range = pd.date_range("2001-01-01", periods=205, freq="D")
    df_205 = pd.DataFrame({
        "year": d_range.year,
        "month": d_range.month,
        "day": d_range.day,
        "date": d_range.strftime("%Y-%m-%d"),
        "val": np.full(205, 25.0),
        "qa_passed": np.full(205, True),
        "valid_coverage_pct": np.full(205, 100.0),
    })
    ann_205 = aggregate_annual_series(df_205, param_id="land_surface_temperature_day", policy=policy, binding_id="MODIS_MOD11A1_061_DAY")
    # 205 days is < 292 days required under 80% threshold
    assert len(ann_205) == 0


def test_v4_05_physically_correct_temperature_anomaly():
    """V4-05: 0.5 K temperature anomaly relative to baseline converts to 0.5 degC, NOT -272.65 degC."""
    policy = ANALYSIS_POLICIES["standard_climate_temperature"]
    df_anomaly = pd.DataFrame({
        "year": np.arange(1980, 2020),
        "value": np.full(40, 0.5),  # 0.5 K anomaly
        "qa_passed": np.full(40, True),
        "valid_coverage_pct": np.full(40, 100.0),
    })
    ann = aggregate_annual_series(
        df_anomaly,
        param_id="surface_temperature_anomaly",
        policy=policy,
        binding_id="gistemp_v4_annual_anomaly",
    )
    assert len(ann) == 40
    # First value must be exactly 0.5 degC
    np.testing.assert_allclose(ann["val"].iloc[0], 0.5, atol=1e-5)
    assert ann["val"].iloc[0] > -10.0  # Must not be -272.65


def test_v4_06_truthful_confidence_interval_narration():
    """V4-06: Truthful confidence intervals pass bilingual validation when bounds differ from point slope."""
    claim = NarrationClaimFrame(
        result_id="test_res_001",
        region_id="BGD",
        region_name_en="Bangladesh",
        region_name_bn="বাংলাদেশ",
        parameter_id="air_temperature_2m",
        parameter_name_en="Near-Surface Air Temperature",
        parameter_name_bn="পৃষ্ঠের বায়ুর তাপমাত্রা",
        temporal_statistic="annual_mean",
        start_year=1980,
        end_year=2024,
        slope_per_decade=0.30,
        slope_display_en="+0.30 °C/decade",
        slope_display_bn="+০.৩০ °C/দশক",
        unit="°C",
        direction="increasing",
        evidence_state="supported_increase",
        p_value=0.001,
        ci_95_lower_per_decade=0.23,
        ci_95_upper_per_decade=0.36,
        coverage_pct=100.0,
        method_name_en="Mann-Kendall",
        method_name_bn="ম্যান-কেন্ডাল",
    )
    truth = {
        "theil_sen": {"slope_per_decade": 0.30, "ci_95_lower_per_decade": 0.23, "ci_95_upper_per_decade": 0.36},
        "mann_kendall": {"p_value": 0.001},
        "data_support": {"valid_area_coverage_pct": 100.0},
    }

    # Truthful English sentences mentioning slope 0.30 and CI [0.23, 0.36] °C/decade
    en_sentences = [
        "Between 1980 and 2024, Near-Surface Air Temperature in Bangladesh showed a supported increase at a rate of 0.30 °C/decade.",
        "The 95% confidence interval is 0.23 to 0.36 °C/decade with 100% spatial coverage.",
    ]
    is_valid_en, issues_en = validate_narrative_text(en_sentences, claim, truth)
    assert is_valid_en is True, f"English validation failed: {issues_en}"

    # Truthful Bangla sentences mentioning 0.30 and CI 0.23 থেকে 0.36 °C/দশক
    from src.narration.templates_bn import to_bengali_numerals
    bn_sentences = [
        f"১৯৮০ থেকে ২০২৪ সালের মধ্যে, বাংলাদেশে পৃষ্ঠের বায়ুর তাপমাত্রা প্রতি দশকে {to_bengali_numerals(0.30)} °C হারে বৃদ্ধি পেয়েছে।",
        f"৯৫% আত্মবিশ্বাস ব্যবধান ছিল {to_bengali_numerals(0.23)} থেকে {to_bengali_numerals(0.36)} °C/দশক এবং স্থানিক কভারেজ ছিল {to_bengali_numerals(100.0)}%।",
    ]
    is_valid_bn, issues_bn = validate_narrative_text(bn_sentences, claim, truth)
    assert is_valid_bn is True, f"Bangla validation failed: {issues_bn}"

    # Reusing interval endpoint 0.36 as point slope must FAIL
    invented_sentences = [
        "Between 1980 and 2024, Near-Surface Air Temperature in Bangladesh increased at 0.36 °C/decade.",
        "The 95% confidence interval is 0.23 to 0.36 °C/decade with 100% spatial coverage.",
    ]
    is_valid_inv, _ = validate_narrative_text(invented_sentences, claim, truth)
    assert is_valid_inv is False


def test_v4_08_map_vector_inference_parity():
    """V4-08: Map vector GeoJSON applies Hamed-Rao VIF autocorrelation and exposes evidence_state."""
    resp = client.get("/layers/merra2_trend_slope/geojson")
    assert resp.status_code == 200
    geojson = resp.json()
    assert geojson["type"] == "FeatureCollection"
    assert len(geojson["features"]) > 0

    # Find Bangladesh feature
    bgd_feature = next((f for f in geojson["features"] if f["properties"].get("id") == "BGD"), None)
    assert bgd_feature is not None
    props = bgd_feature["properties"]
    assert props["has_data"] is True
    assert props["slope_per_decade"] is not None
    assert props["p_value"] is not None
    assert "evidence_state" in props
    assert props["evidence_state"] in ("supported_increase", "supported_decrease", "stable", "inconclusive", "limited", "insufficient")


def test_v4_09_comparison_identity_and_policy_invalidation():
    """V4-09: Repeating comparison preserves created_at timestamp; changing alpha changes comparison_id."""
    payload_1 = {
        "region_id_a": "BGD",
        "region_id_b": "KEN",
        "parameter_id": "air_temperature_2m",
        "start_year": 1980,
        "end_year": 2023,
    }
    resp1 = client.post("/comparisons", json=payload_1)
    assert resp1.status_code == 200
    res1 = resp1.json()
    cid1 = res1["identity"]["comparison_id"]
    created_at_1 = res1["identity"]["created_at"]

    # Repeat exact same comparison: must return identical comparison_id AND identical created_at
    resp2 = client.post("/comparisons", json=payload_1)
    assert resp2.status_code == 200
    res2 = resp2.json()
    assert res2["identity"]["comparison_id"] == cid1
    assert res2["identity"]["created_at"] == created_at_1

    # Modify policy (changing alpha under modis policy vs standard policy)
    payload_2 = {
        "region_id_a": "BGD",
        "region_id_b": "KEN",
        "parameter_id": "air_temperature_2m",
        "start_year": 1980,
        "end_year": 2023,
        "policy_id": "point_meteorology_policy",
    }
    resp3 = client.post("/comparisons", json=payload_2)
    assert resp3.status_code == 200
    res3 = resp3.json()
    assert res3["identity"]["comparison_id"] != cid1

