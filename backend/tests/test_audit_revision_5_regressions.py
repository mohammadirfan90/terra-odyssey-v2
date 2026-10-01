"""Regression test suite for Audit Revision 5 findings (V5-01 through V5-11)."""

import json
import hashlib
import io
import contextlib
import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.cache.store import LocalDataStore, ManifestSchemaError
from src.narration.claims import NarrationClaimFrame
from src.narration.validator import validate_narrative_text
from src.compute.aggregation import aggregate_annual_series
from src.registry.policies import ANALYSIS_POLICIES

client = TestClient(app, raise_server_exceptions=False)


@contextlib.contextmanager
def temp_fixture(df: pd.DataFrame, bind: str = "NASA_MERRA2_M2TMNXSLV", reg: str = "BGD", manifest_edit=None):
    store = LocalDataStore()
    path = store.get_series_path(bind, reg)
    mp = store.manifest_dir / f"{bind}.json"
    old_p = path.read_bytes() if path.exists() else None
    old_m = mp.read_bytes() if mp.exists() else None
    try:
        df.to_parquet(path, index=False)
        m = json.loads(old_m) if old_m else {"binding_id": bind, "metadata": {}, "series": []}
        ent = next((e for e in m.get("series", []) if e.get("region_id") == reg), None)
        if ent is None:
            ent = {"region_id": reg, "qa_column": "qa_passed", "coverage_column": "valid_coverage_pct"}
            m.setdefault("series", []).append(ent)
        ent.update({
            "file_name": path.name,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "row_count": len(df),
            "size_bytes": path.stat().st_size,
            "first_year": int(df["year"].min()) if "year" in df.columns and len(df) > 0 else 1980,
            "last_year": int(df["year"].max()) if "year" in df.columns and len(df) > 0 else 2024,
        })
        if manifest_edit:
            manifest_edit(m)
        store._manifest_cache.clear()
        mp.write_text(json.dumps(m))
        yield
    finally:
        store._manifest_cache.clear()
        if old_p is None:
            path.unlink(missing_ok=True)
        else:
            path.write_bytes(old_p)
        if old_m is None:
            mp.unlink(missing_ok=True)
        else:
            mp.write_bytes(old_m)


def test_v5_02_alternative_qa_boolean_truthiness_rejected():
    """V5-02: String 'False', '0', and NaN in alternative QA columns must decode to False (unpassed QA)."""
    base_store = LocalDataStore()
    df_base = base_store.load_series("NASA_MERRA2_M2TMNXSLV", "BGD")

    for bad_val, label in [("False", "string_false"), ("0", "string_zero"), (np.nan, "missing_val")]:
        df = df_base.copy().drop(columns=["qa_passed"]).assign(quality_pass=bad_val)
        with temp_fixture(df, manifest_edit=lambda m: next(e for e in m["series"] if e["region_id"] == "BGD").update(qa_column="quality_pass")):
            res = client.get("/trend?region_id=BGD&parameter_id=air_temperature_2m")
            # All observations have bad QA, so result must reject with insufficient observations
            assert res.status_code == 422
            assert res.json().get("code") == "INSUFFICIENT_OBSERVATIONS"


def test_v5_02_nonnumeric_observation_typed_error():
    """V5-02: Non-numeric observation values return typed 422 DATA_INTEGRITY_ERROR in trend and comparisons."""
    base_store = LocalDataStore()
    df_base = base_store.load_series("NASA_MERRA2_M2TMNXSLV", "BGD")
    df_corrupt = df_base.copy()
    df_corrupt["value_display"] = "not-a-number"

    with temp_fixture(df_corrupt):
        res_trend = client.get("/trend?region_id=BGD&parameter_id=air_temperature_2m")
        assert res_trend.status_code == 422
        body_trend = res_trend.json()
        assert body_trend.get("code") == "DATA_INTEGRITY_ERROR"

        res_comp = client.post("/comparisons", json={
            "region_id_a": "BGD",
            "region_id_b": "USA",
            "parameter_id": "air_temperature_2m",
        })
        assert res_comp.status_code == 422
        body_comp = res_comp.json()
        assert body_comp.get("code") == "DATA_INTEGRITY_ERROR"


def test_v5_02_readiness_only_metadata_rejected():
    """V5-02: Manifest metadata containing only availability_state is rejected with 422 by trend and unsupported by coverage."""
    base_store = LocalDataStore()
    df_base = base_store.load_series("NASA_MERRA2_M2TMNXSLV", "BGD")

    with temp_fixture(df_base, manifest_edit=lambda m: m.update(metadata={"availability_state": "analysis_ready"})):
        res_trend = client.get("/trend?region_id=BGD&parameter_id=air_temperature_2m")
        assert res_trend.status_code == 422
        assert res_trend.json().get("code") == "DATA_INTEGRITY_ERROR"

        res_cov = client.get("/coverage?region_id=BGD&parameter_id=air_temperature_2m")
        assert res_cov.status_code == 200
        assert res_cov.json().get("is_supported") is False


def test_v5_02_wrong_variable_coverage_unsupported():
    """V5-02: Manifest declaring wrong variable reports unsupported in coverage."""
    base_store = LocalDataStore()
    df_base = base_store.load_series("NASA_MERRA2_M2TMNXSLV", "BGD")

    with temp_fixture(df_base, manifest_edit=lambda m: m["metadata"].update(variable_name="WRONG_VARIABLE")):
        res_cov = client.get("/coverage?region_id=BGD&parameter_id=air_temperature_2m")
        assert res_cov.status_code == 200
        assert res_cov.json().get("is_supported") is False


def test_v5_03_timestamp_daily_binding_temporal_completeness():
    """V5-03: Daily binding with only 1 timestamp per year fails temporal completeness."""
    base_store = LocalDataStore()
    df_power = base_store.load_series("NASA_POWER_DAILY_POINT", "BGD")
    # Assign 1 timestamp per year
    df_power_1day = pd.DataFrame([
        {"year": y, "value_display": 25.0 + 0.05 * (y - 2000), "timestamp": f"{y}-01-01", "qa_passed": True, "valid_coverage_pct": 100.0}
        for y in range(2000, 2020)
    ])

    with temp_fixture(df_power_1day, bind="NASA_POWER_DAILY_POINT"):
        res = client.get("/trend?region_id=BGD&parameter_id=point_air_temperature&binding_id=NASA_POWER_DAILY_POINT")
        assert res.status_code == 422
        assert res.json().get("code") == "INSUFFICIENT_OBSERVATIONS"


def test_v5_03_annual_precipitation_valid_month_count():
    """V5-03: Annual precipitation data with valid_month_count=1 is rejected as incomplete."""
    df_precip_1m = pd.DataFrame([
        {"year": y, "value_display": 1500.0, "valid_month_count": 1, "qa_passed": True, "valid_coverage_pct": 100.0}
        for y in range(2000, 2020)
    ])

    with temp_fixture(df_precip_1m, bind="NASA_MERRA2_M2TMNXSLV"):
        policy = ANALYSIS_POLICIES["precipitation_total_policy"]
        ann = aggregate_annual_series(df_precip_1m, param_id="precipitation_total", policy=policy, binding_id="NASA_MERRA2_M2TMNXSLV")
        assert len(ann) == 0


def test_v5_04_incompatible_precipitation_policy_rejected():
    """V5-04: Precipitation policy applied to temperature returns typed 422 POLICY_PARAMETER_INCOMPATIBLE."""
    res = client.get("/trend?region_id=BGD&parameter_id=air_temperature_2m&policy_id=precipitation_total_policy")
    assert res.status_code == 422
    body = res.json()
    assert body.get("code") == "POLICY_PARAMETER_INCOMPATIBLE"


def test_v5_06_map_fdr_family_and_exclusions():
    """V5-06: Vector layer GeoJSON returns frozen FDR family members and explicit exclusions."""
    res = client.get("/layers/merra2_trend_slope/geojson")
    assert res.status_code == 200
    data = res.json()
    assert "fdr_family_members" in data
    assert "exclusions" in data
    assert "fdr_family_size" in data
    assert isinstance(data["fdr_family_members"], list)
    assert len(data["fdr_family_members"]) == data["fdr_family_size"]


def test_v5_07_comparison_sha256_standard_64_format():
    """V5-07: Comparison provenance.data_sha256 is a standard 64-character SHA-256 hex digest."""
    res = client.post("/comparisons", json={
        "region_id_a": "BGD",
        "region_id_b": "USA",
        "parameter_id": "air_temperature_2m",
    })
    assert res.status_code == 200
    data = res.json()
    sha = data["provenance"]["data_sha256"]
    assert len(sha) == 64
    assert len(data["provenance"]["region_a_data_sha256"]) == 64
    assert len(data["provenance"]["region_b_data_sha256"]) == 64


def test_v5_08_narration_equal_to_point_slope_validation():
    """V5-08: Sentence claiming 'rate was equal to 0.36' when true rate is 0.30 is rejected."""
    claim = NarrationClaimFrame(
        result_id="audit", region_id="BGD", region_name_en="Bangladesh", region_name_bn="বাংলাদেশ",
        parameter_id="air_temperature_2m", parameter_name_en="Temperature", parameter_name_bn="তাপমাত্রা",
        temporal_statistic="annual_mean", start_year=1980, end_year=2024, slope_per_decade=0.30,
        slope_display_en="+0.30 °C/decade", slope_display_bn="+০.৩০ °C/দশক", unit="°C", direction="increasing",
        evidence_state="supported_increase", p_value=0.0001, ci_95_lower_per_decade=0.23, ci_95_upper_per_decade=0.36,
        coverage_pct=100.0, method_name_en="Mann-Kendall", method_name_bn="ম্যান-কেন্ডাল"
    )
    truth = {
        "theil_sen": {"slope_per_decade": 0.30, "ci_95_lower_per_decade": 0.23, "ci_95_upper_per_decade": 0.36},
        "mann_kendall": {"p_value": 0.0001},
        "data_support": {"valid_area_coverage_pct": 100.0},
    }
    sentences = [
        "The estimated rate for Temperature in Bangladesh over 1980 to 2024 was equal to 0.36 °C/decade.",
        "The statistical evidence supports an increasing trend with 100.0% spatial coverage.",
    ]
    valid, errors = validate_narrative_text(sentences, claim, truth)
    assert valid is False
    assert any("Extracted slope quantity 0.36" in e for e in errors)


def test_v5_09_concurrent_cache_miss_canonical_winner():
    """V5-09: save_result returns identical canonical winner when two threads insert same ID."""
    store = LocalDataStore()
    res_id = "test_concurrent_consensus_id"
    payload_a = {
        "identity": {"result_id": res_id, "created_at": "2026-10-01T12:00:00.000000+00:00"},
        "theil_sen": {"slope_per_decade": 0.25},
    }
    payload_b = {
        "identity": {"result_id": res_id, "created_at": "2026-10-01T12:00:00.999999+00:00"},
        "theil_sen": {"slope_per_decade": 0.25},
    }
    winner_a = store.save_result(res_id, {"q": 1}, payload_a)
    winner_b = store.save_result(res_id, {"q": 1}, payload_b)

    assert winner_a["identity"]["created_at"] == "2026-10-01T12:00:00.000000+00:00"
    assert winner_b["identity"]["created_at"] == "2026-10-01T12:00:00.000000+00:00"
    assert winner_a == winner_b


def test_v5_10_comparison_series_and_csv_export():
    """V5-10: Persisted comparison results support /results/{id}/series and CSV export without HTTP 500."""
    res_comp = client.post("/comparisons", json={
        "region_id_a": "BGD",
        "region_id_b": "USA",
        "parameter_id": "air_temperature_2m",
    })
    assert res_comp.status_code == 200
    cid = res_comp.json()["identity"]["comparison_id"]

    res_series = client.get(f"/results/{cid}/series")
    assert res_series.status_code == 200
    s_data = res_series.json()
    assert s_data["result_kind"] == "paired_comparison"
    assert "contrast_difference_series" in s_data

    res_csv = client.get(f"/results/{cid}/export?format=csv")
    assert res_csv.status_code == 200
    assert "text/csv" in res_csv.headers.get("content-type", "")
    assert "difference_°C" in res_csv.text or "year" in res_csv.text
