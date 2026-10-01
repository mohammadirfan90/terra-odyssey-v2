"""Serial correlation diagnostics and Hamed-Rao modified variance.

Implements Section 6.5:
- Pre-declared lag evaluation of detrended residual rank autocorrelation
- Hamed-Rao (1998) variance inflation factor (VIF)
- Strict non-negative adjustment constraint (VIF >= 1.0)
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Sequence
import numpy as np
from scipy import stats


@dataclass(frozen=True)
class SerialCorrelationResult:
    """Immutable result of serial correlation check and variance correction."""
    ar1: float
    vif: float
    significant_lags: List[int]
    is_autocorrelated: bool
    lag_correlations: List[float]
    critical_threshold: float


def check_autocorrelation(
    residuals: Sequence[float] | np.ndarray,
    alpha: float = 0.05,
    max_lag: int | None = None,
) -> SerialCorrelationResult:
    """Check serial correlation of residuals and compute Hamed-Rao VIF.

    Args:
        residuals: Detrended residuals.
        alpha: Two-sided significance level for lag significance (default: 0.05).
        max_lag: Maximum lag to evaluate (default: min(n // 2, 10)).

    Returns:
        SerialCorrelationResult with AR(1), VIF, and significant lags.
    """
    res = np.asarray(residuals, dtype=np.float64)
    res = res[np.isfinite(res)]
    n = int(res.size)

    if n < 6:
        return SerialCorrelationResult(
            ar1=0.0,
            vif=1.0,
            significant_lags=[],
            is_autocorrelated=False,
            lag_correlations=[],
            critical_threshold=0.0,
        )

    # Compute ranks of residuals
    ranks = stats.rankdata(res)
    mean_rank = np.mean(ranks)
    centered_ranks = ranks - mean_rank
    var_ranks = np.sum(centered_ranks**2) / float(n)

    if var_ranks <= 1e-12:
        return SerialCorrelationResult(
            ar1=0.0,
            vif=1.0,
            significant_lags=[],
            is_autocorrelated=False,
            lag_correlations=[],
            critical_threshold=0.0,
        )

    if max_lag is None:
        max_lag = min(n // 2, 10)

    z_crit = float(stats.norm.ppf(1.0 - alpha / 2.0))
    threshold = z_crit / math.sqrt(n)

    rho_s_list: List[float] = []
    significant_lags: List[int] = []

    sum_vif = 0.0
    # Evaluate all lags up to max_lag to capture later-lag dependence (e.g. lag-2, lag-4)
    for k in range(1, max_lag + 1):
        cov_k = np.sum(centered_ranks[: n - k] * centered_ranks[k:]) / float(n - k)
        rho_k = float(cov_k / var_ranks)
        rho_s_list.append(rho_k)

        # Include all statistically significant lags in significant_lags
        if abs(rho_k) > threshold:
            significant_lags.append(k)
            # Positive-only correction variant: only positive autocorrelations inflate variance
            if rho_k > 0:
                weight = (n - k) * (n - k - 1) * (n - k - 2)
                sum_vif += weight * rho_k

    ar1 = rho_s_list[0] if rho_s_list else 0.0

    # Hamed-Rao VIF formula
    vif = 1.0 + (2.0 / (n * (n - 1) * (n - 2))) * sum_vif
    # Floor VIF at 1.0 to ensure conservative variance inflation
    vif = max(1.0, float(vif))

    is_autocorrelated = len(significant_lags) > 0 or vif > 1.05 or abs(ar1) > threshold

    return SerialCorrelationResult(
        ar1=ar1,
        vif=vif,
        significant_lags=significant_lags,
        is_autocorrelated=is_autocorrelated,
        lag_correlations=rho_s_list,
        critical_threshold=threshold,
    )


def hamed_rao_variance_correction(
    y: Sequence[float] | np.ndarray,
    slope: float,
    intercept: float,
    times: Sequence[float] | np.ndarray,
    ref_time: float = 0.0,
    alpha: float = 0.05,
) -> float:
    """Calculate the Hamed-Rao VIF given a series and its Theil-Sen fit."""
    t_arr = np.asarray(times, dtype=np.float64)
    y_arr = np.asarray(y, dtype=np.float64)
    valid = np.isfinite(t_arr) & np.isfinite(y_arr)
    t_clean = t_arr[valid]
    y_clean = y_arr[valid]

    fitted = intercept + slope * (t_clean - ref_time)
    residuals = y_clean - fitted
    diag = check_autocorrelation(residuals, alpha=alpha)
    return diag.vif
