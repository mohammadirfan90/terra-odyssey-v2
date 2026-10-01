"""Seasonal decomposition using robust STL for monthly series.

Implements Section 6.5 and Table 19:
- Robust STL decomposition for regular monthly series (period = 12)
- Minimum 5-year requirement (60 monthly observations)
- Short-gap linear interpolation for diagnostic copy only
- Strict isolation: imputed values are tracked and excluded from primary inference
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence
import numpy as np
import pandas as pd
from statsmodels.tsa.seasonal import STL


@dataclass(frozen=True)
class SeasonalPoint:
    """Decomposed components at a single time step."""
    time: float
    observed: Optional[float]
    trend: float
    seasonal: float
    residual: float
    is_imputed: bool


@dataclass(frozen=True)
class SeasonalResult:
    """Immutable result of seasonal STL decomposition."""
    is_available: bool
    reason: Optional[str]
    points: List[SeasonalPoint]
    period: int
    seasonal_amplitude: Optional[float]
    imputed_count: int
    sample_count: int


def stl_decomposition(
    times: Sequence[float] | np.ndarray,
    values: Sequence[float] | np.ndarray,
    period: int = 12,
    min_years: int = 5,
    max_consecutive_missing: int = 3,
) -> SeasonalResult:
    """Perform robust STL decomposition on a regular monthly time series.

    Args:
        times: Array of evenly spaced timestamps/indices.
        values: Corresponding monthly measurements (may include NaNs).
        period: Seasonal cycle length (default: 12 for monthly data).
        min_years: Minimum duration in years required for climate diagnostics (default: 5).
        max_consecutive_missing: Max consecutive missing months allowed to impute in diagnostic copy.

    Returns:
        SeasonalResult containing trend, seasonal, and residual components.
    """
    t_arr = np.asarray(times, dtype=np.float64)
    y_arr = np.asarray(values, dtype=np.float64)
    n = int(y_arr.size)

    min_samples = min_years * period
    if n < min_samples:
        return SeasonalResult(
            is_available=False,
            reason=f"Insufficient duration: requires at least {min_years} years ({min_samples} months), got {n}.",
            points=[],
            period=period,
            seasonal_amplitude=None,
            imputed_count=0,
            sample_count=n,
        )

    # Check for missing values and evaluate consecutive gap lengths
    is_nan = np.isnan(y_arr)
    imputed_count = int(np.sum(is_nan))

    if imputed_count > 0:
        # Check gap lengths
        series_nan = pd.Series(is_nan)
        # Groups of consecutive True
        gap_lengths = series_nan.groupby((~series_nan).cumsum()).sum()
        max_gap = int(gap_lengths.max()) if not gap_lengths.empty else 0
        if max_gap > max_consecutive_missing:
            return SeasonalResult(
                is_available=False,
                reason=f"Missing gap of {max_gap} consecutive months exceeds allowed threshold ({max_consecutive_missing}).",
                points=[],
                period=period,
                seasonal_amplitude=None,
                imputed_count=imputed_count,
                sample_count=n,
            )

        # Create diagnostic copy with linear interpolation
        diagnostic_series = pd.Series(y_arr).interpolate(method="linear", limit=max_consecutive_missing)
        # Fill ends if needed with nearest or forward/back
        diagnostic_series = diagnostic_series.bfill().ffill()
        diagnostic_y = diagnostic_series.to_numpy(dtype=np.float64)
    else:
        diagnostic_y = y_arr.copy()

    try:
        # Fit robust STL
        stl = STL(diagnostic_y, period=period, robust=True)
        res = stl.fit()

        trend = res.trend
        seasonal = res.seasonal
        resid = res.resid

        seasonal_amplitude = float(np.max(seasonal) - np.min(seasonal))

        points: List[SeasonalPoint] = []
        for i in range(n):
            obs_val = None if is_nan[i] else float(y_arr[i])
            points.append(
                SeasonalPoint(
                    time=float(t_arr[i]),
                    observed=obs_val,
                    trend=float(trend[i]),
                    seasonal=float(seasonal[i]),
                    residual=float(resid[i]),
                    is_imputed=bool(is_nan[i]),
                )
            )

        return SeasonalResult(
            is_available=True,
            reason=None,
            points=points,
            period=period,
            seasonal_amplitude=seasonal_amplitude,
            imputed_count=imputed_count,
            sample_count=n,
        )
    except Exception as exc:
        return SeasonalResult(
            is_available=False,
            reason=f"STL fitting failed: {str(exc)}",
            points=[],
            period=period,
            seasonal_amplitude=None,
            imputed_count=imputed_count,
            sample_count=n,
        )
