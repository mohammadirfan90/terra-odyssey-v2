"""Shared scientific aggregation and calendar completeness module.

Implements rigorous temporal aggregation conforming to Table 8, Section 6.6:
- Daily-to-annual aggregation across all valid days (retaining >200 days/year)
- Monthly-to-annual aggregation requiring valid, finite observations across calendar intervals (12 for precip, 10 for temp)
- Calendar validation rejecting fractional or out-of-range months
- Precision preservation from declared canonical values (e.g. Kelvin -> Celsius)
- Explicit exclusion of non-finite/NaN months from completeness counts
"""

from __future__ import annotations

from typing import Optional, Tuple
import numpy as np
import pandas as pd

from ..registry.policies import AnalysisPolicy
from ..registry.parameters import PARAMETER_REGISTRY
from ..registry.bindings import DATASET_BINDINGS, DatasetBinding
from ..cache.store import ManifestSchemaError


def aggregate_annual_series(
    df: pd.DataFrame,
    param_id: str,
    policy: AnalysisPolicy,
    binding_id: Optional[str] = None,
) -> pd.DataFrame:
    """Aggregate a raw multi-cadence DataFrame into a validated annual time series.

    Returns:
        pd.DataFrame with columns: ["year", "val", "coverage"]
    Raises:
        ManifestSchemaError: If calendar values or required schema columns are invalid.
    """
    if df is None or df.empty:
        return pd.DataFrame(columns=["year", "val", "coverage"])

    if "year" not in df.columns:
        raise ManifestSchemaError("Missing required column 'year'.")

    # Validate integer years
    year_vals = df["year"].to_numpy()
    if not np.all(np.isfinite(year_vals)):
        raise ManifestSchemaError("Column 'year' contains non-finite values.")
    if not np.all(np.equal(np.mod(year_vals, 1), 0)):
        raise ManifestSchemaError("Column 'year' must contain integer values.")

    # Resolve parameter and binding
    param = PARAMETER_REGISTRY.get(param_id)
    binding: Optional[DatasetBinding] = DATASET_BINDINGS.get(binding_id) if binding_id else None

    # 1. Resolve scientific value with canonical precision
    if "value_canonical" in df.columns:
        can_vals = df["value_canonical"].to_numpy(dtype=float)
        # Transform canonical Kelvin to display Celsius if appropriate
        if param and param.canonical_unit == "K" and param.display_unit == "°C":
            raw_vals = can_vals - 273.15
        elif binding and binding.canonical_unit == "K" and param and param.display_unit == "°C":
            raw_vals = can_vals - 273.15
        else:
            raw_vals = can_vals
    elif "value_display" in df.columns:
        raw_vals = df["value_display"].to_numpy(dtype=float)
    elif "value" in df.columns:
        raw_vals = df["value"].to_numpy(dtype=float)
    else:
        raise ManifestSchemaError("DataFrame missing recognized value column ('value_canonical', 'value_display', 'value').")

    working_df = df.copy()
    working_df["_val_sci"] = raw_vals

    # 2. Quality and coverage filtering
    if "qa_passed" in working_df.columns:
        working_df = working_df[working_df["qa_passed"] == True]

    has_cov = "valid_coverage_pct" in working_df.columns
    if has_cov:
        working_df = working_df[np.isfinite(working_df["valid_coverage_pct"].to_numpy(dtype=float))]
        working_df = working_df[
            (working_df["valid_coverage_pct"] >= 0.0) & (working_df["valid_coverage_pct"] <= 100.0)
        ]
        working_df = working_df[working_df["valid_coverage_pct"] >= policy.min_annual_coverage_pct]

    if working_df.empty:
        return pd.DataFrame(columns=["year", "val", "coverage"])

    # 3. Calendar validation
    if "month" in working_df.columns:
        month_vals = working_df["month"].to_numpy()
        if not np.all(np.isfinite(month_vals)):
            raise ManifestSchemaError("Invalid calendar month: non-finite month values found.")
        if not np.all(np.equal(np.mod(month_vals, 1), 0)):
            raise ManifestSchemaError("Invalid calendar month: month values must be integers between 1 and 12.")
        if np.any(month_vals < 1) or np.any(month_vals > 12):
            raise ManifestSchemaError("Invalid calendar month: month values must be between 1 and 12.")

    if "day" in working_df.columns:
        day_vals = working_df["day"].to_numpy()
        if not np.all(np.isfinite(day_vals)):
            raise ManifestSchemaError("Invalid calendar day: non-finite day values found.")
        if not np.all(np.equal(np.mod(day_vals, 1), 0)):
            raise ManifestSchemaError("Invalid calendar day: day values must be integers between 1 and 31.")
        if np.any(day_vals < 1) or np.any(day_vals > 31):
            raise ManifestSchemaError("Invalid calendar day: day values must be between 1 and 31.")

    is_precip = (param_id == "precipitation_total") or (policy.id == "precipitation_total_policy")
    if param and param.supported_temporal_statistics and param.supported_temporal_statistics[0] in ("annual_total", "total"):
        is_precip = True

    # 4. Cadence determination
    is_daily = (binding is not None and binding.temporal_cadence == "daily") or ("day" in working_df.columns)

    annual_rows = []
    if is_daily:
        # Daily aggregation: compute mean/sum across ALL valid daily observations in each year
        min_required_days = max(10, int(365 * (policy.min_annual_coverage_pct / 100.0) * 0.7))
        # For standard 80% coverage policy, min_required_days is ~204 days; for MODIS 70%, ~178 days.
        # A fixture with only 1 day per year must not satisfy annual completeness.
        for yr, grp in working_df.groupby("year"):
            finite_grp = grp[np.isfinite(grp["_val_sci"].to_numpy(dtype=float))]
            if len(finite_grp) >= min_required_days:
                stat_val = float(finite_grp["_val_sci"].sum()) if is_precip else float(finite_grp["_val_sci"].mean())
                cov_val = float(finite_grp["valid_coverage_pct"].mean()) if has_cov else 100.0
                annual_rows.append({
                    "year": int(yr),
                    "val": stat_val,
                    "coverage": cov_val,
                })
    elif "month" in working_df.columns:
        # Monthly aggregation: require valid, FINITE observations for all required months
        min_months = 12 if is_precip else 10
        for yr, grp in working_df.groupby("year"):
            finite_grp = grp[np.isfinite(grp["_val_sci"].to_numpy(dtype=float))]
            # Deduplicate by month strictly on finite observations
            unique_months = finite_grp.drop_duplicates(subset=["month"])
            if len(unique_months) >= min_months:
                stat_val = float(unique_months["_val_sci"].sum()) if is_precip else float(unique_months["_val_sci"].mean())
                cov_val = float(unique_months["valid_coverage_pct"].mean()) if has_cov else 100.0
                annual_rows.append({
                    "year": int(yr),
                    "val": stat_val,
                    "coverage": cov_val,
                })
    else:
        # Already annual
        for yr, grp in working_df.groupby("year"):
            finite_grp = grp[np.isfinite(grp["_val_sci"].to_numpy(dtype=float))]
            if not finite_grp.empty:
                val = float(finite_grp["_val_sci"].iloc[0])
                cov = float(finite_grp["valid_coverage_pct"].iloc[0]) if has_cov else 100.0
                annual_rows.append({
                    "year": int(yr),
                    "val": val,
                    "coverage": cov,
                })

    res = pd.DataFrame(annual_rows)
    if res.empty:
        return pd.DataFrame(columns=["year", "val", "coverage"])

    res = res.drop_duplicates(subset=["year"]).dropna(subset=["val"])
    res = res[np.isfinite(res["val"].to_numpy(dtype=float))]
    return res.sort_values("year").reset_index(drop=True)
