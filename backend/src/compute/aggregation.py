"""Shared scientific aggregation and calendar completeness module.

Implements rigorous temporal aggregation conforming to Table 8, Section 6.6:
- Daily-to-annual aggregation across unique valid calendar days (enforcing leap-year completeness without arbitrary relaxation)
- Calendar validation rejecting impossible dates (e.g. Feb 31) and deduplicating calendar days
- Accurate physical quantity conversions (Kelvin to Celsius for absolute temperature; identity preservation for temperature anomalies)
- Monthly-to-annual aggregation requiring valid, finite observations across calendar intervals (12 for precip, 10 for temp)
- Calendar validation rejecting fractional or out-of-range months
- Cadence determination distinguishing raw daily inputs with 'day' column from pre-aggregated annual series
"""

from __future__ import annotations

import calendar
from typing import Optional
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
        ManifestSchemaError: If calendar values, numeric types, or required schema columns are invalid.
    """
    if df is None or df.empty:
        return pd.DataFrame(columns=["year", "val", "coverage"])

    if "year" not in df.columns:
        raise ManifestSchemaError("Missing required column 'year'.")

    # Validate integer years with strict numeric parsing
    try:
        year_vals = pd.to_numeric(df["year"], errors="raise").to_numpy(dtype=float)
    except Exception as e:
        raise ManifestSchemaError(f"Column 'year' must contain numeric integer values: {e}")

    if not np.all(np.isfinite(year_vals)):
        raise ManifestSchemaError("Column 'year' contains non-finite values.")
    if not np.all(np.equal(np.mod(year_vals, 1), 0)):
        raise ManifestSchemaError("Column 'year' must contain integer values.")

    # Resolve parameter and binding
    param = PARAMETER_REGISTRY.get(param_id)
    binding: Optional[DatasetBinding] = DATASET_BINDINGS.get(binding_id) if binding_id else None

    # Determine if parameter is an anomaly (temperature differences: 1 K == 1 °C, NO -273.15 offset)
    is_anomaly = (
        (param is not None and getattr(param, "physical_quantity", "") == "temperature_anomaly")
        or (param_id == "surface_temperature_anomaly")
        or ("anomaly" in str(param_id).lower())
    )

    # 1. Resolve scientific value with canonical precision
    if "value_canonical" in df.columns:
        can_vals = df["value_canonical"].to_numpy(dtype=float)
        # Transform canonical Kelvin to display Celsius ONLY if NOT a temperature anomaly!
        # For temperature anomalies, 1 K delta == 1 °C delta; absolute offset must not be subtracted.
        if not is_anomaly:
            if param and param.canonical_unit == "K" and param.display_unit == "°C":
                raw_vals = can_vals - 273.15
            elif binding and binding.canonical_unit == "K" and param and param.display_unit == "°C":
                raw_vals = can_vals - 273.15
            else:
                raw_vals = can_vals
        else:
            raw_vals = can_vals
    elif "value_display" in df.columns:
        val_series = df["value_display"]
    elif "value" in df.columns:
        val_series = df["value"]
    elif "val" in df.columns:
        val_series = df["val"]
    else:
        raise ManifestSchemaError("DataFrame missing recognized value column ('value_canonical', 'value_display', 'value', 'val').")

    if "value_canonical" not in df.columns:
        try:
            raw_vals = pd.to_numeric(val_series, errors="raise").to_numpy(dtype=float)
        except Exception as e:
            raise ManifestSchemaError(f"Observation values contain non-numeric data: {e}")

    working_df = df.copy()
    working_df["year"] = year_vals.astype(int)
    working_df["_val_sci"] = raw_vals

    # Parse timestamps or dates into calendar columns if present
    date_col = None
    for cand in ["timestamp", "date", "time", "datetime"]:
        if cand in working_df.columns:
            date_col = cand
            break
    if date_col is not None:
        try:
            parsed_dt = pd.to_datetime(working_df[date_col], errors="coerce")
            if not parsed_dt.isna().all():
                if "month" not in working_df.columns:
                    working_df["month"] = parsed_dt.dt.month
                if "day" not in working_df.columns:
                    working_df["day"] = parsed_dt.dt.day
                if "year" not in working_df.columns:
                    working_df["year"] = parsed_dt.dt.year
        except Exception:
            pass

    # 2. Quality and coverage filtering
    if "qa_passed" in working_df.columns:
        working_df = working_df[working_df["qa_passed"] == True]

    has_cov = "valid_coverage_pct" in working_df.columns
    if has_cov:
        try:
            cov_vals = pd.to_numeric(working_df["valid_coverage_pct"], errors="raise").to_numpy(dtype=float)
            working_df["valid_coverage_pct"] = cov_vals
        except Exception as e:
            raise ManifestSchemaError(f"Coverage column contains non-numeric values: {e}")

        working_df = working_df[np.isfinite(working_df["valid_coverage_pct"].to_numpy(dtype=float))]
        working_df = working_df[
            (working_df["valid_coverage_pct"] >= 0.0) & (working_df["valid_coverage_pct"] <= 100.0)
        ]
        working_df = working_df[working_df["valid_coverage_pct"] >= policy.min_annual_coverage_pct]

    if working_df.empty:
        return pd.DataFrame(columns=["year", "val", "coverage"])

    # 3. Calendar validation
    if "month" in working_df.columns:
        try:
            month_vals = pd.to_numeric(working_df["month"], errors="raise").to_numpy(dtype=float)
        except Exception as e:
            raise ManifestSchemaError(f"Column 'month' contains non-numeric values: {e}")

        if not np.all(np.isfinite(month_vals)):
            raise ManifestSchemaError("Invalid calendar month: non-finite month values found.")
        if not np.all(np.equal(np.mod(month_vals, 1), 0)):
            raise ManifestSchemaError("Invalid calendar month: month values must be integers between 1 and 12.")
        if np.any(month_vals < 1) or np.any(month_vals > 12):
            raise ManifestSchemaError("Invalid calendar month: month values must be between 1 and 12.")
        working_df["month"] = month_vals.astype(int)

    if "day" in working_df.columns:
        try:
            day_vals = pd.to_numeric(working_df["day"], errors="raise").to_numpy(dtype=float)
        except Exception as e:
            raise ManifestSchemaError(f"Column 'day' contains non-numeric values: {e}")

        if not np.all(np.isfinite(day_vals)):
            raise ManifestSchemaError("Invalid calendar day: non-finite day values found.")
        if not np.all(np.equal(np.mod(day_vals, 1), 0)):
            raise ManifestSchemaError("Invalid calendar day: day values must be integers between 1 and 31.")
        if np.any(day_vals < 1) or np.any(day_vals > 31):
            raise ManifestSchemaError("Invalid calendar day: day values must be between 1 and 31.")
        working_df["day"] = day_vals.astype(int)

    # Validate that (year, month, day) are real valid calendar dates (reject impossible dates like Feb 31)
    if "month" in working_df.columns and "day" in working_df.columns:
        try:
            date_strings = (
                working_df["year"].astype(str)
                + "-"
                + working_df["month"].astype(str).str.zfill(2)
                + "-"
                + working_df["day"].astype(str).str.zfill(2)
            )
            parsed_dates = pd.to_datetime(date_strings, format="%Y-%m-%d", errors="coerce")
            if parsed_dates.isna().any():
                raise ManifestSchemaError("Invalid calendar date: impossible date found (e.g. Feb 31 or invalid month/day).")
        except ManifestSchemaError:
            raise
        except Exception as e:
            raise ManifestSchemaError(f"Invalid calendar date parsing error: {e}")

    # Enforce verified month counts for pre-aggregated annual records if declared
    if "valid_month_count" in working_df.columns:
        try:
            vmc = pd.to_numeric(working_df["valid_month_count"], errors="coerce")
            # Precipitation requires 12 valid months; temperature requires at least 10
            req_m = 12 if param_id == "precipitation_total" else 10
            working_df = working_df[vmc >= req_m]
        except Exception:
            pass

    # Physical estimand: only precipitation or parameters declaring 'total'/'annual_total' statistic are accumulated!
    # Air temperature and surface temperature are ALWAYS averaged (mean), never summed!
    is_precip = (param_id == "precipitation_total") or (
        param is not None
        and param.supported_temporal_statistics
        and param.supported_temporal_statistics[0] in ("annual_total", "total")
    )

    # 4. Cadence determination
    # Distinguish raw daily inputs with 'day' column from pre-aggregated annual series
    has_day = "day" in working_df.columns
    has_month = "month" in working_df.columns

    annual_rows = []
    if has_day:
        # Daily aggregation: compute mean/sum across valid UNIQUE calendar days in each year
        for yr, grp in working_df.groupby("year"):
            finite_grp = grp[np.isfinite(grp["_val_sci"].to_numpy(dtype=float))]
            # Deduplicate by calendar day (month, day)
            unique_days = (
                finite_grp.drop_duplicates(subset=["month", "day"])
                if "month" in finite_grp.columns
                else finite_grp.drop_duplicates(subset=["day"])
            )
            total_days_in_year = 366 if calendar.isleap(int(yr)) else 365
            required_days = int(np.ceil(total_days_in_year * (policy.min_annual_coverage_pct / 100.0)))
            if len(unique_days) >= required_days:
                stat_val = float(unique_days["_val_sci"].sum()) if is_precip else float(unique_days["_val_sci"].mean())
                cov_val = float(unique_days["valid_coverage_pct"].mean()) if has_cov else 100.0
                annual_rows.append({
                    "year": int(yr),
                    "val": stat_val,
                    "coverage": cov_val,
                })
    elif has_month:
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
