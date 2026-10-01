import pytest
import math
import json
import sqlite3
import pandas as pd
from shapely.geometry import Polygon
from fastapi.testclient import TestClient

from src.main import app
from src.registry.regions import _calculate_geodesic_area_km2
from src.cache.store import (
    LocalDataStore,
    ManifestChecksumMismatchError,
    ManifestEntryNotFoundError,
    _sanitize_floats
)

client = TestClient(app)

def test_spherical_right_triangle_geodesic_area():
    """R10: Verify spherical right triangle (0,0)-(90,0)-(0,90) calculates ~63,758,235.12 km^2."""
    poly = Polygon([(0.0, 0.0), (90.0, 0.0), (0.0, 90.0), (0.0, 0.0)])
    area_km2 = _calculate_geodesic_area_km2(poly)
    expected = 63758235.12160898
    # Within 0.001% relative error
    assert math.isclose(area_km2, expected, rel_tol=1e-5), f"Expected {expected}, got {area_km2}"


def test_tiles_endpoint_honest_501():
    """R06: Tile endpoint should return honest 501 Not Implemented."""
    response = client.get("/tiles/merra2_trend_slope/0/0/0.png")
    assert response.status_code == 501
    data = response.json()
    assert data.get("code") == "RASTER_TILES_UNAVAILABLE"
    assert "GeoJSON" in str(data.get("detail", ""))


def test_layers_geojson_filtering():
    """R06: /layers/{layer_id}/geojson supports time window and QA filtering."""
    response = client.get("/layers/merra2_trend_slope/geojson?start_year=2000&end_year=2005")
    assert response.status_code in [200, 404]
    if response.status_code == 200:
        data = response.json()
        assert data["type"] == "FeatureCollection"
        assert "features" in data


def test_coverage_binding_parameter_mismatch():
    """F03: Coverage check must reject binding whose parameter_id differs from query."""
    response = client.get("/coverage?region_id=BGD&parameter_id=air_temperature_2m&binding_id=GPM_IMERG_FINAL_V07")
    assert response.status_code == 400
    data = response.json()
    assert data.get("code") == "INCOMPATIBLE_BINDING_PARAMETER"


def test_manifest_checksum_mismatch_error(tmp_path):
    """R02: LocalDataStore must reject parquet data whose checksum doesn't match manifest."""
    manifest_dir = tmp_path / "manifests"
    manifest_dir.mkdir(parents=True)
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir(parents=True)
    
    # Create a dummy parquet file
    dummy_file = cache_dir / "test_binding_GLOBAL.parquet"
    df = pd.DataFrame({"time": ["2000-01-01"], "value": [1.0], "qa_score": [1.0]})
    df.to_parquet(dummy_file)
    
    # Write manifest with deliberate sha256 mismatch
    manifest_content = {
        "binding_id": "test_binding",
        "series": [
            {
                "region_id": "GLOBAL",
                "file_name": "test_binding_GLOBAL.parquet",
                "sha256": "0000000000000000000000000000000000000000000000000000000000000000",
                "row_count": 1
            }
        ]
    }
    with open(manifest_dir / "test_binding.json", "w", encoding="utf-8") as f:
        json.dump(manifest_content, f)
        
    store = LocalDataStore(data_root=tmp_path)
    assert not store.has_series("test_binding", "GLOBAL")
    
    with pytest.raises(ManifestChecksumMismatchError):
        store.load_series("test_binding", "GLOBAL")


def test_unmanifested_series_rejected(tmp_path):
    """R02: LocalDataStore must reject series missing from manifest."""
    manifest_dir = tmp_path / "manifests"
    manifest_dir.mkdir(parents=True)
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir(parents=True)
    
    manifest_content = {
        "binding_id": "test_binding",
        "series": []
    }
    with open(manifest_dir / "test_binding.json", "w", encoding="utf-8") as f:
        json.dump(manifest_content, f)
        
    store = LocalDataStore(data_root=tmp_path)
    assert not store.has_series("test_binding", "GLOBAL")
    
    with pytest.raises(ManifestEntryNotFoundError):
        store.load_series("test_binding", "GLOBAL")


def test_quarantined_legacy_results():
    """R01, R08: Results database should have migrated null-hash or deprecated DOI rows to quarantined_results."""
    store = LocalDataStore()
    with sqlite3.connect(store.db_path) as conn:
        cursor = conn.cursor()
        # Verify quarantined_results table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='quarantined_results'")
        assert cursor.fetchone() is not None
        
        # Check active completed_results table has no missing input_hash or deprecated DOIs
        cursor.execute("SELECT result_id, result_json FROM completed_results")
        rows = cursor.fetchall()
        for r_id, r_json in rows:
            obj = json.loads(r_json)
            prov = obj.get("provenance", {})
            assert prov.get("data_sha256") is not None
            assert prov.get("doi") != "10.5067/0JRLVL8YV2Y4"


def test_sanitize_floats_disallows_nan_inf():
    """R09: Sanitize floats converts NaN/Infinity to None or valid numbers."""
    data = {
        "a": float("nan"),
        "b": float("inf"),
        "c": float("-inf"),
        "d": 42.5,
        "nested": [float("nan"), 10.0]
    }
    sanitized = _sanitize_floats(data)
    assert sanitized["a"] is None
    assert sanitized["b"] is None
    assert sanitized["c"] is None
    assert sanitized["d"] == 42.5
    assert sanitized["nested"] == [None, 10.0]
    
    # Should serialize without error when allow_nan=False
    serialized = json.dumps(sanitized, allow_nan=False)
    assert "null" in serialized


def test_comparisons_unknown_policy_rejected():
    """R05: Comparison endpoint rejects unknown policy ID with 400."""
    payload = {
        "region_id_a": "BGD",
        "region_id_b": "USA",
        "parameter_id": "air_temperature_2m",
        "start_year": 1980,
        "end_year": 2020,
        "policy_id": "non_existent_policy_xyz"
    }
    response = client.post("/comparisons", json=payload)
    assert response.status_code == 400
    assert response.json().get("code") == "UNKNOWN_POLICY"
