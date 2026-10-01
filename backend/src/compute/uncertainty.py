"""Fitted-line uncertainty band computation via residual bootstrap.

Implements Section 6.4:
- Evaluates joint uncertainty in both slope and intercept simultaneously
- Avoids arbitrary fixed-anchor slope bounds
- Provides pointwise empirical quantiles (default 95% coverage)
- Discloses method, calibration seed, and sample count
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence
import numpy as np

from .theil_sen import theil_sen_slope


@dataclass(frozen=True)
class BandPoint:
    """Evaluated point along the fitted trajectory with uncertainty bounds."""
    time: float
    fitted: float
    lower: float
    upper: float


@dataclass(frozen=True)
class FittedBandResult:
    """Immutable result for the fitted-line uncertainty band."""
    points: List[BandPoint]
    coverage: float
    method: str
    replicates: int
    seed: Optional[int]
    is_valid: bool


def calculate_fitted_line_band(
    times: Sequence[float] | np.ndarray,
    values: Sequence[float] | np.ndarray,
    eval_times: Optional[Sequence[float] | np.ndarray] = None,
    alpha: float = 0.05,
    n_bootstrap: int = 500,
    seed: int = 42,
) -> FittedBandResult:
    """Compute pointwise fitted-line uncertainty band using residual bootstrap.

    Args:
        times: Observation time coordinates.
        values: Observation values.
        eval_times: Target times to evaluate band (defaults to sorted observation times).
        alpha: Two-sided error rate (default: 0.05 -> 95% band).
        n_bootstrap: Number of bootstrap replications (default: 500).
        seed: Random seed for exact reproducibility.

    Returns:
        FittedBandResult with pointwise fitted, lower, and upper bounds.
    """
    t_arr = np.asarray(times, dtype=np.float64)
    y_arr = np.asarray(values, dtype=np.float64)

    valid_mask = np.isfinite(t_arr) & np.isfinite(y_arr)
    t_clean = t_arr[valid_mask]
    y_clean = y_arr[valid_mask]
    n = int(t_clean.size)

    if n < 3:
        return FittedBandResult(
            points=[],
            coverage=1.0 - alpha,
            method="insufficient_data",
            replicates=0,
            seed=seed,
            is_valid=False,
        )

    # Sort by time
    sort_idx = np.argsort(t_clean)
    t_sorted = t_clean[sort_idx]
    y_sorted = y_clean[sort_idx]

    if eval_times is None:
        t_eval = t_sorted
    else:
        t_eval = np.sort(np.asarray(eval_times, dtype=np.float64))

    ref_time = float(t_sorted[0])
    base_ts = theil_sen_slope(t_sorted, y_sorted, alpha=alpha, ref_time=ref_time)
    if base_ts.slope_per_year is None or base_ts.intercept is None:
        return FittedBandResult(
            points=[],
            coverage=1.0 - alpha,
            method="unsupported_fit",
            replicates=0,
            seed=seed,
            is_valid=False,
        )

    slope = base_ts.slope_per_year
    intercept = base_ts.intercept

    # Handle degenerate case: all points on a perfect line or constant
    if base_ts.is_degenerate:
        points = [
            BandPoint(
                time=float(tk),
                fitted=float(intercept + slope * (tk - ref_time)),
                lower=float(intercept + slope * (tk - ref_time)),
                upper=float(intercept + slope * (tk - ref_time)),
            )
            for tk in t_eval
        ]
        return FittedBandResult(
            points=points,
            coverage=1.0 - alpha,
            method="degenerate_exact_line",
            replicates=0,
            seed=seed,
            is_valid=True,
        )

    # Detrended residuals
    residuals = y_sorted - (intercept + slope * (t_sorted - ref_time))

    rng = np.random.default_rng(seed)
    eval_trajectories = np.empty((n_bootstrap, t_eval.size), dtype=np.float64)

    # Residual bootstrap loop
    successful_reps = 0
    for b in range(n_bootstrap):
        resampled_residuals = rng.choice(residuals, size=n, replace=True)
        y_boot = (intercept + slope * (t_sorted - ref_time)) + resampled_residuals
        boot_ts = theil_sen_slope(t_sorted, y_boot, alpha=alpha, ref_time=ref_time)

        if boot_ts.slope_per_year is not None and boot_ts.intercept is not None:
            eval_trajectories[successful_reps, :] = (
                boot_ts.intercept + boot_ts.slope_per_year * (t_eval - ref_time)
            )
            successful_reps += 1

    if successful_reps < 50:
        return FittedBandResult(
            points=[],
            coverage=1.0 - alpha,
            method="bootstrap_convergence_failure",
            replicates=successful_reps,
            seed=seed,
            is_valid=False,
        )

    valid_trajectories = eval_trajectories[:successful_reps, :]
    q_lower = float(alpha / 2.0 * 100.0)
    q_upper = float((1.0 - alpha / 2.0) * 100.0)

    lower_bounds = np.percentile(valid_trajectories, q_lower, axis=0)
    upper_bounds = np.percentile(valid_trajectories, q_upper, axis=0)
    baseline_fitted = intercept + slope * (t_eval - ref_time)

    points = [
        BandPoint(
            time=float(t_eval[k]),
            fitted=float(baseline_fitted[k]),
            lower=float(lower_bounds[k]),
            upper=float(upper_bounds[k]),
        )
        for k in range(t_eval.size)
    ]

    return FittedBandResult(
        points=points,
        coverage=1.0 - alpha,
        method="pointwise_residual_bootstrap",
        replicates=successful_reps,
        seed=seed,
        is_valid=True,
    )
