"""Mann-Kendall non-parametric trend test.

Implements Equations 2, 3, and 4 from Chapter 6 of the scientific specification:
- S statistic from ordered pairs (Eq 2)
- Tie-corrected independent variance (Eq 3)
- Continuity-corrected standard Z and two-sided p-value (Eq 4)
- Constant-series and insufficient-sample handling (Table 19)
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal, Optional, Sequence
import numpy as np
from scipy import stats


@dataclass(frozen=True)
class MannKendallResult:
    """Immutable result of a Mann-Kendall trend test."""
    S: Optional[int]
    var_S: Optional[float]
    Z: Optional[float]
    p_value: Optional[float]
    direction: Literal["increasing", "decreasing", "flat", "insufficient"]
    evidence_state: Literal[
        "supported_increase",
        "supported_decrease",
        "inconclusive",
        "insufficient",
        "flat",
    ]
    sample_count: int
    tied_groups_count: int
    alpha: float
    method: str
    autocorrelation_adjusted: bool
    vif: float


def mann_kendall_test(
    y: Sequence[float] | np.ndarray,
    alpha: float = 0.05,
    vif: float = 1.0,
    autocorrelation_adjusted: bool = False,
) -> MannKendallResult:
    """Calculate the Mann-Kendall test statistic and significance.

    Args:
        y: Sequence of observation values. Missing/NaN values are dropped.
        alpha: Significance threshold (default: 0.05).
        vif: Variance inflation factor for serial correlation adjustment (default: 1.0).
        autocorrelation_adjusted: Whether VIF adjustment was applied.

    Returns:
        MannKendallResult with exact statistics and evidence states.
    """
    arr = np.asarray(y, dtype=np.float64)
    valid_mask = np.isfinite(arr)
    clean_y = arr[valid_mask]
    n = int(clean_y.size)

    # Insufficient data check (requires at least 3 valid observations)
    if n < 3:
        return MannKendallResult(
            S=None,
            var_S=None,
            Z=None,
            p_value=None,
            direction="insufficient",
            evidence_state="insufficient",
            sample_count=n,
            tied_groups_count=0,
            alpha=alpha,
            method="insufficient_data",
            autocorrelation_adjusted=autocorrelation_adjusted,
            vif=vif,
        )

    # Check for constant series (all values equal within numerical tolerance)
    y_min, y_max = np.min(clean_y), np.max(clean_y)
    if math.isclose(y_min, y_max, abs_tol=1e-12):
        return MannKendallResult(
            S=0,
            var_S=0.0,
            Z=0.0,
            p_value=1.0,
            direction="flat",
            evidence_state="flat",
            sample_count=n,
            tied_groups_count=1,
            alpha=alpha,
            method="constant_series_convention",
            autocorrelation_adjusted=autocorrelation_adjusted,
            vif=1.0,
        )

    # Equation 2: S = sum_{i=1}^{n-1} sum_{j=i+1}^n sgn(y_j - y_i)
    # Vectorized computation of pairwise differences
    diffs = clean_y[:, np.newaxis] - clean_y[np.newaxis, :]
    # Upper triangular mask (j > i)
    tri_i, tri_j = np.triu_indices(n, k=1)
    pair_diffs = diffs[tri_j, tri_i]
    signs = np.sign(pair_diffs)
    S = int(np.sum(signs))

    # Equation 3: Tie-corrected variance
    # Find ties among values
    _, counts = np.unique(clean_y, return_counts=True)
    tied_counts = counts[counts > 1]
    tie_term = int(np.sum(tied_counts * (tied_counts - 1) * (2 * tied_counts + 5)))

    base_var = (n * (n - 1) * (2 * n + 5) - tie_term) / 18.0
    adjusted_var = base_var * max(1.0, vif)

    # Equation 4: Continuity-corrected Z statistic
    if adjusted_var <= 0.0:
        Z = 0.0
        p_val = 1.0
    else:
        std_S = math.sqrt(adjusted_var)
        if S > 0:
            Z = float((S - 1) / std_S)
        elif S < 0:
            Z = float((S + 1) / std_S)
        else:
            Z = 0.0

        # Two-sided p-value from standard normal distribution
        # p = 2 * (1 - Phi(|Z|))
        p_val = float(2.0 * stats.norm.sf(abs(Z)))

    # Direction from sign of S
    if S > 0:
        direction: Literal["increasing", "decreasing", "flat"] = "increasing"
    elif S < 0:
        direction = "decreasing"
    else:
        direction = "flat"

    # Evidence state: strictly separate slope direction from significance
    if p_val < alpha:
        if direction == "increasing":
            evidence_state: Literal[
                "supported_increase",
                "supported_decrease",
                "inconclusive",
                "insufficient",
                "flat",
            ] = "supported_increase"
        elif direction == "decreasing":
            evidence_state = "supported_decrease"
        else:
            evidence_state = "flat"
    else:
        evidence_state = "inconclusive"

    method_str = "continuity_corrected_normal"
    if autocorrelation_adjusted:
        method_str += "_hamed_rao"

    return MannKendallResult(
        S=S,
        var_S=float(adjusted_var),
        Z=Z,
        p_value=p_val,
        direction=direction,
        evidence_state=evidence_state,
        sample_count=n,
        tied_groups_count=int(tied_counts.size),
        alpha=alpha,
        method=method_str,
        autocorrelation_adjusted=autocorrelation_adjusted,
        vif=vif,
    )
