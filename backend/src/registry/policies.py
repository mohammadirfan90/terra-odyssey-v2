"""Analysis policies governing missingness, temporal aggregation, baselines, and inference.

Implements Section 6.6 and Table 8:
- Minimum valid coverage thresholds
- Missing gap limits
- Standard climatology baseline intervals (WMO 1991-2020, MODIS 2001-2020, GISTEMP 1951-1980)
- Climate duration gates (>=20 years standard, 10-19 exploratory, <10 recent change)
"""

from __future__ import annotations

from typing import Dict, Literal, Optional, Tuple
from pydantic import BaseModel, Field


class AnalysisPolicy(BaseModel):
    """Reproducible scientific analysis policy."""
    id: str = Field(..., description="Unique policy identifier")
    name: str
    min_annual_coverage_pct: float = Field(default=80.0, description="Minimum spatial/temporal coverage %")
    min_eligible_years_climate: int = Field(default=20, description="Minimum years for primary climate trend badge")
    exploratory_min_years: int = Field(default=10, description="Minimum years for exploratory trend")
    max_consecutive_missing_gap: int = Field(default=3, description="Maximum consecutive missing intervals")
    climatology_baseline: Optional[Tuple[int, int]] = Field(default=(1991, 2020), description="Baseline window (start_year, end_year)")
    alpha: float = Field(default=0.05, description="Significance level")
    dependence_handling: Literal["none", "hamed_rao", "seasonal_kendall"] = "hamed_rao"
    slope_method: Literal["theil_sen_median"] = "theil_sen_median"
    band_method: Literal["residual_bootstrap_pointwise"] = "residual_bootstrap_pointwise"
    bootstrap_replicates: int = 500
    bootstrap_seed: int = 42


ANALYSIS_POLICIES: Dict[str, AnalysisPolicy] = {
    "standard_climate_temperature": AnalysisPolicy(
        id="standard_climate_temperature",
        name="Standard Climate Temperature Trend Policy",
        min_annual_coverage_pct=80.0,
        min_eligible_years_climate=20,
        exploratory_min_years=10,
        max_consecutive_missing_gap=3,
        climatology_baseline=(1991, 2020),
        alpha=0.05,
        dependence_handling="hamed_rao",
        slope_method="theil_sen_median",
        band_method="residual_bootstrap_pointwise",
    ),
    "modis_lst_satellite_policy": AnalysisPolicy(
        id="modis_lst_satellite_policy",
        name="MODIS Thermal Satellite Retrieval Policy",
        min_annual_coverage_pct=70.0,
        min_eligible_years_climate=20,
        exploratory_min_years=10,
        max_consecutive_missing_gap=3,
        climatology_baseline=(2001, 2020),
        alpha=0.05,
        dependence_handling="hamed_rao",
        slope_method="theil_sen_median",
        band_method="residual_bootstrap_pointwise",
    ),
    "precipitation_total_policy": AnalysisPolicy(
        id="precipitation_total_policy",
        name="Precipitation Depth Accumulation Policy",
        min_annual_coverage_pct=95.0,  # Requires nearly complete year for totals
        min_eligible_years_climate=20,
        exploratory_min_years=10,
        max_consecutive_missing_gap=0,
        climatology_baseline=(2001, 2020),
        alpha=0.05,
        dependence_handling="hamed_rao",
        slope_method="theil_sen_median",
        band_method="residual_bootstrap_pointwise",
    ),
    "point_meteorology_policy": AnalysisPolicy(
        id="point_meteorology_policy",
        name="Single-Point Centroid Meteorology Policy",
        min_annual_coverage_pct=85.0,
        min_eligible_years_climate=20,
        exploratory_min_years=10,
        max_consecutive_missing_gap=5,
        climatology_baseline=(1991, 2020),
        alpha=0.05,
        dependence_handling="hamed_rao",
        slope_method="theil_sen_median",
        band_method="residual_bootstrap_pointwise",
    ),
}
