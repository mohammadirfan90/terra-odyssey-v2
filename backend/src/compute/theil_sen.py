"""Theil-Sen robust median slope estimator and rank-based confidence interval.

Implements Equation 5 from Chapter 6:
- Pairwise slopes using actual elapsed time (Eq 5)
- Joint median intercept centered at reference time (Eq 5)
- Rank-based 95% slope confidence interval (Sen 1968, Gilbert 1987)
- Conversion to decade rate (x10)
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional, Sequence
import numpy as np
from scipy import stats

from .mann_kendall import mann_kendall_test


@dataclass(frozen=True)
class TheilSenResult:
    """Immutable result of Theil-Sen slope and intercept estimation."""
    slope_per_year: Optional[float]
    slope_per_decade: Optional[float]
    intercept: Optional[float]
    ref_time: float
    ci_95_lower_per_decade: Optional[float]
    ci_95_upper_per_decade: Optional[float]
    pairwise_count: int
    retained_sample_count: int
    method: str
    is_degenerate: bool


def theil_sen_slope(
    times: Sequence[float] | np.ndarray,
    values: Sequence[float] | np.ndarray,
    alpha: float = 0.05,
    ref_time: Optional[float] = None,
) -> TheilSenResult:
    """Compute Theil-Sen median slope, joint intercept, and rank-based confidence interval.

    Args:
        times: Monotonically increasing timestamps or elapsed years.
        values: Corresponding numerical values.
        alpha: Significance level for two-sided confidence interval (default 0.05 for 95% CI).
        ref_time: Reference time for centering intercept (default: min(times)).

    Returns:
        TheilSenResult with decade slopes and rank-based interval.
    """
    t_arr = np.asarray(times, dtype=np.float64)
    y_arr = np.asarray(values, dtype=np.float64)

    # Filter invalid/NaN points simultaneously
    valid_mask = np.isfinite(t_arr) & np.isfinite(y_arr)
    t_clean = t_arr[valid_mask]
    y_clean = y_arr[valid_mask]
    n = int(t_clean.size)

    # Need at least 2 points for slope
    if n < 2:
        return TheilSenResult(
            slope_per_year=None,
            slope_per_decade=None,
            intercept=None,
            ref_time=float(t_clean[0]) if n == 1 else 0.0,
            ci_95_lower_per_decade=None,
            ci_95_upper_per_decade=None,
            pairwise_count=0,
            retained_sample_count=n,
            method="insufficient_data",
            is_degenerate=False,
        )

    # Ensure times are sorted
    sort_idx = np.argsort(t_clean)
    t_sorted = t_clean[sort_idx]
    y_sorted = y_clean[sort_idx]

    if ref_time is None:
        ref_time = float(t_sorted[0])

    # Check for constant series
    if math.isclose(np.min(y_sorted), np.max(y_sorted), abs_tol=1e-12):
        return TheilSenResult(
            slope_per_year=0.0,
            slope_per_decade=0.0,
            intercept=float(y_sorted[0]),
            ref_time=ref_time,
            ci_95_lower_per_decade=0.0,
            ci_95_upper_per_decade=0.0,
            pairwise_count=n * (n - 1) // 2,
            retained_sample_count=n,
            method="constant_series_convention",
            is_degenerate=True,
        )

    # Compute all pairwise slopes: (y_j - y_i) / (t_j - t_i) for j > i
    tri_i, tri_j = np.triu_indices(n, k=1)
    dt = t_sorted[tri_j] - t_sorted[tri_i]

    # Ignore pairs with identical timestamps to avoid division by zero
    valid_dt = dt > 1e-9
    if not np.any(valid_dt):
        return TheilSenResult(
            slope_per_year=None,
            slope_per_decade=None,
            intercept=None,
            ref_time=ref_time,
            ci_95_lower_per_decade=None,
            ci_95_upper_per_decade=None,
            pairwise_count=0,
            retained_sample_count=n,
            method="zero_elapsed_time",
            is_degenerate=False,
        )

    dy = y_sorted[tri_j] - y_sorted[tri_i]
    pairwise_slopes = dy[valid_dt] / dt[valid_dt]
    n_pairs = int(pairwise_slopes.size)

    # Equation 5: Median pairwise slope
    median_slope_year = float(np.median(pairwise_slopes))
    slope_decade = median_slope_year * 10.0

    # Equation 5: Joint median intercept centered at ref_time
    # b = median_i [ y_i - beta * (t_i - ref_time) ]
    intercepts = y_sorted - median_slope_year * (t_sorted - ref_time)
    median_intercept = float(np.median(intercepts))

    # Check if all pairwise slopes are essentially identical (perfect linear relationship)
    slope_min = float(np.min(pairwise_slopes))
    slope_max = float(np.max(pairwise_slopes))
    is_degenerate = math.isclose(slope_min, slope_max, abs_tol=1e-9)

    # Rank-based 95% slope confidence interval (Sen 1968, Gilbert 1987)
    if is_degenerate:
        ci_lower_decade = slope_decade
        ci_upper_decade = slope_decade
    else:
        # Use tie-corrected variance of Mann-Kendall S
        mk_res = mann_kendall_test(y_sorted, alpha=alpha)
        var_s = mk_res.var_S if mk_res.var_S is not None and mk_res.var_S > 0 else (n * (n - 1) * (2 * n + 5) / 18.0)
        z_crit = float(stats.norm.ppf(1.0 - alpha / 2.0))
        c_alpha = z_crit * math.sqrt(var_s)

        # 1-based ranks
        k1 = int(round((n_pairs - c_alpha) / 2.0))
        if k1 < 1:
            k1 = 1
        k2 = n_pairs - k1 + 1
        if k2 > n_pairs:
            k2 = n_pairs

        # 0-based indices for sorted slopes
        sorted_slopes = np.sort(pairwise_slopes)
        idx_lower = max(0, min(k1 - 1, n_pairs - 1))
        idx_upper = max(0, min(k2 - 1, n_pairs - 1))

        ci_lower_year = float(sorted_slopes[idx_lower])
        ci_upper_year = float(sorted_slopes[idx_upper])
        ci_lower_decade = ci_lower_year * 10.0
        ci_upper_decade = ci_upper_year * 10.0

    return TheilSenResult(
        slope_per_year=median_slope_year,
        slope_per_decade=slope_decade,
        intercept=median_intercept,
        ref_time=ref_time,
        ci_95_lower_per_decade=ci_lower_decade,
        ci_95_upper_per_decade=ci_upper_decade,
        pairwise_count=n_pairs,
        retained_sample_count=n,
        method="theil_sen_sen_rank_ci",
        is_degenerate=is_degenerate,
    )
