"""Integration tests for FastAPI endpoints and RFC 9457 problem contracts."""

import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_health_check():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["offline_enforced"] is True


def test_list_and_search_regions():
    res = client.get("/regions")
    assert res.status_code == 200
    regions = res.json()
    assert len(regions) >= 8

    # Search for Bangladesh
    res_bgd = client.get("/regions?q=bangladesh")
    assert res_bgd.status_code == 200
    found = res_bgd.json()
    assert len(found) == 1
    assert found[0]["id"] == "BGD"
    assert found[0]["name_bn"] == "বাংলাদেশ"


def test_list_parameters_and_bindings():
    res = client.get("/parameters")
    assert res.status_code == 200
    params = res.json()
    param_ids = [p["id"] for p in params]
    assert "air_temperature_2m" in param_ids
    assert "land_surface_temperature_day" in param_ids
    assert "sea_surface_temperature" in param_ids


def test_coverage_ocean_vs_land_validation():
    # Inland country asking for SST should report unsupported with action
    res = client.get("/coverage?region_id=BGD&parameter_id=sea_surface_temperature")
    assert res.status_code == 200
    data = res.json()
    assert data["is_supported"] is False
    assert "ocean region" in data["reason"]

    # Ocean basin asking for SST should be supported
    res_ocean = client.get("/coverage?region_id=BAY_OF_BENGAL&parameter_id=sea_surface_temperature")
    assert res_ocean.status_code == 200
    data_ocean = res_ocean.json()
    assert data_ocean["is_supported"] is True


def test_get_trend_bangladesh_air_temperature():
    res = client.get("/trend?region_id=BGD&parameter_id=air_temperature_2m")
    assert res.status_code == 200
    data = res.json()

    # Identity block
    assert "identity" in data
    assert len(data["identity"]["result_id"]) == 64  # SHA-256 hash
    assert data["region"]["id"] == "BGD"
    assert data["parameter"]["id"] == "air_temperature_2m"

    # Theil-Sen & Mann-Kendall statistics
    assert data["theil_sen"]["slope_per_decade"] is not None
    assert data["theil_sen"]["slope_per_decade"] > 0.1  # Significant warming in MERRA-2
    assert data["mann_kendall"]["p_value"] < 0.05
    assert data["evidence"]["state"] == "supported_increase"

    # Narration (2 sentences each)
    assert len(data["narration"]["en"]) == 2
    assert len(data["narration"]["bn"]) == 2
    assert "বাংলাদেশ" in data["narration"]["bn"][0]
    assert "Bangladesh" in data["narration"]["en"][0]

    # Provenance
    assert data["provenance"]["dataset_id"] == "NASA_MERRA2_M2TMNXSLV"
    assert data["provenance"]["access_mode"] == "cache"

    # Test retrieval by result_id
    res_id = data["identity"]["result_id"]
    res_saved = client.get(f"/results/{res_id}")
    assert res_saved.status_code == 200
    assert res_saved.json()["identity"]["result_id"] == res_id

    # Test export as CSV
    res_csv = client.get(f"/results/{res_id}/export?format=csv")
    assert res_csv.status_code == 200
    assert "year,value_°C" in res_csv.text


def test_get_trend_district_compatibility_alias():
    res = client.get("/trend?district=BGD&parameter_id=air_temperature_2m")
    assert res.status_code == 200
    assert res.json()["region"]["id"] == "BGD"


def test_rfc9457_problem_details_error_handling():
    # 1. Unknown region
    res = client.get("/trend?region_id=NONEXISTENT&parameter_id=air_temperature_2m")
    assert res.status_code == 404
    assert res.headers["content-type"] == "application/problem+json"
    data = res.json()
    assert data["code"] == "REGION_NOT_FOUND"

    # 2. Incompatible spatial support (SST on land country)
    res_sst = client.get("/trend?region_id=BGD&parameter_id=sea_surface_temperature")
    assert res_sst.status_code == 400
    assert res_sst.headers["content-type"] == "application/problem+json"
    data_sst = res_sst.json()
    assert data_sst["code"] == "INCOMPATIBLE_SPATIAL_SUPPORT"


def test_paired_regional_comparison():
    payload = {
        "region_id_a": "BGD",
        "region_id_b": "USA",
        "parameter_id": "air_temperature_2m",
    }
    res = client.post("/comparisons", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "contrast_difference_series" in data
    assert data["common_years_count"] > 20
    assert "slope_per_decade" in data["contrast_difference_series"]
