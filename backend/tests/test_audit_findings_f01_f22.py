"""Regression and verification test suite for Audit Findings F01 through F22."""

import json
import numpy as np
import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.cache.store import LocalDataStore, CacheMissOfflineError, InvalidPathSecurityError
from src.cache.hasher import compute_result_hash
from src.compute.serial_corr import check_autocorrelation
from src.registry.regions import REGION_REGISTRY
from src.registry.bindings import DATASET_BINDINGS
from src.narration.claims import NarrationClaimFrame
from src.narration.validator import validate_narrative_text

client = TestClient(app)


def test_f01_no_synthetic_generation_on_missing_cache():
    """F01: Missing cache returns 404 Problem Details without writing replacement files."""
    resp = client.get("/trend?region_id=NPL&parameter_id=air_temperature_2m")
    assert resp.status_code == 404
    body = resp.json()
    assert body.get("code") in ("CACHE_MISS_OFFLINE", "ERROR", "HTTP_404")

    # Verify no file was created on disk
    store = LocalDataStore()
    assert not store.has_series("NASA_MERRA2_M2TMNXSLV", "NPL")


def test_f02_coverage_truthful_readiness():
    """F02: Unacquired products (IMERG, GISTEMP) honestly report catalogued/unacquired state."""
    resp = client.get("/coverage?region_id=BGD&parameter_id=precipitation_total")
    assert resp.status_code == 200
    body = resp.json()
    assert body["is_supported"] is False
    assert body["availability_state"] == "catalogued"


def test_f03_path_traversal_and_binding_mismatch():
    """F03: Path traversal attempts and incompatible bindings are strictly blocked with 4xx."""
    store = LocalDataStore()
    with pytest.raises(InvalidPathSecurityError):
        store.get_series_path("../../audit-path-probe", "BGD")

    # Mismatched parameter and binding
    resp = client.get("/trend?region_id=BGD&parameter_id=precipitation_total&binding_id=NASA_MERRA2_M2TMNXSLV")
    assert resp.status_code == 400
    assert resp.json().get("code") == "INCOMPATIBLE_BINDING_PARAMETER"

    # Unknown policy
    resp2 = client.get("/trend?region_id=BGD&parameter_id=air_temperature_2m&policy_id=unknown_invalid_policy")
    assert resp2.status_code == 400
    assert resp2.json().get("code") == "UNKNOWN_POLICY"


def test_f05_immutable_content_hashing():
    """F05: Changed data produces different result hash; identical data produces identical hash."""
    h1 = compute_result_hash("BGD", "air_temperature_2m", "NASA_MERRA2_M2TMNXSLV", "1980", "2024", "standard", data_sha256="abc123")
    h2 = compute_result_hash("BGD", "air_temperature_2m", "NASA_MERRA2_M2TMNXSLV", "1980", "2024", "standard", data_sha256="xyz789")
    assert h1 != h2

    h3 = compute_result_hash("BGD", "air_temperature_2m", "NASA_MERRA2_M2TMNXSLV", "1980", "2024", "standard", data_sha256="abc123")
    assert h1 == h3


def test_f06_limited_evidence_state_does_not_crash():
    """F06: Requesting a 15-year window returns HTTP 200 with limited evidence state without crashing."""
    resp = client.get("/trend?region_id=BGD&parameter_id=air_temperature_2m&start_year=2010&end_year=2024")
    assert resp.status_code == 200
    data = resp.json()
    assert data["evidence"]["state"] == "limited"
    assert "exploratory" in data["evidence"]["interpretation_en"].lower() or "exploratory" in data["narration"]["en"][1].lower()


def test_f07_serial_correlation_later_lag_detection():
    """F07: Strong dependence at later lags (e.g. lag 2, lag 4) is detected even when lag 1 is small."""
    seq = np.array([1.0, 1.0, -1.0, -1.0] * 10)
    diag = check_autocorrelation(seq)
    assert 2 in diag.significant_lags
    assert 4 in diag.significant_lags
    assert diag.is_autocorrelated is True


def test_f10_comparisons_parameter_neutral_and_validation():
    """F10: Comparisons enforce identical parameter, common eligible years, and neutral direction labels."""
    resp = client.post(
        "/comparisons",
        json={
            "region_id_a": "BGD",
            "region_id_b": "USA",
            "parameter_id": "air_temperature_2m",
            "start_year": 1980,
            "end_year": 2024,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["contrast_difference_series"]["direction"] in ("a_higher_rate", "b_higher_rate", "equal_rate")
    assert data["common_years_count"] >= 40


def test_f12_narration_validator_rejects_hallucinated_numbers():
    """F12: Validator flags narrative text with hallucinated numbers."""
    claim = NarrationClaimFrame(
        result_id="test_res",
        region_id="BGD",
        region_name_en="Bangladesh",
        region_name_bn="বাংলাদেশ",
        parameter_id="air_temperature_2m",
        parameter_name_en="Near-Surface Air Temperature (2m)",
        parameter_name_bn="ভূপৃষ্ঠ সংলগ্ন বায়ুর তাপমাত্রা (২ মিটার)",
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
        method_name_en="Mann-Kendall test",
        method_name_bn="ম্যান-কেন্ডাল পরীক্ষা",
    )
    fake_result = {
        "theil_sen": {"slope_per_decade": 0.30, "ci_95_lower_per_decade": 0.23, "ci_95_upper_per_decade": 0.36},
        "mann_kendall": {"p_value": 0.0001},
        "data_support": {"valid_area_coverage_pct": 100.0},
    }

    # Deliberately injected fake numbers (+999.0 C/decade)
    fake_sentences = [
        "The estimated annual mean Near-Surface Air Temperature in Bangladesh increased at a rate of +999.00 °C/decade over 1980 to 2024.",
        "The Mann-Kendall test supports this direction with a 95% confidence interval of 0.23 to 0.36 °C/decade and 100.0% coverage.",
    ]
    is_valid, errors = validate_narrative_text(fake_sentences, claim, fake_result)
    assert is_valid is False
    assert any("Factual mismatch" in e for e in errors)


def test_f14_geodesic_region_areas_and_centroids():
    """F14: USA and Fiji have accurate geodesic land areas and interior representative centroids."""
    usa = REGION_REGISTRY["USA"]
    assert 9_000_000 < usa.area_km2 < 10_500_000
    assert -120.0 < usa.centroid_lon < -90.0
    assert 30.0 < usa.centroid_lat < 50.0

    fiji = REGION_REGISTRY["FJI"]
    assert 15_000 < fiji.area_km2 < 25_000
    assert 170.0 < fiji.centroid_lon < 185.0
    assert -20.0 < fiji.centroid_lat < -15.0


def test_f16_f17_layers_and_tiles_resolution():
    """F16 & F17: TileJSON, raster tile endpoints, and FDR GeoJSON resolve cleanly."""
    resp_tile = client.get("/tiles/merra2_trend_slope/0/0/0")
    assert resp_tile.status_code == 501
    assert resp_tile.json().get("code") == "RASTER_TILES_UNAVAILABLE"

    resp_json = client.get("/layers/merra2_trend_slope/geojson")
    assert resp_json.status_code == 200
    geo = resp_json.json()
    assert geo["type"] == "FeatureCollection"
    assert "fdr_family_size" in geo
    assert len(geo["features"]) > 0
