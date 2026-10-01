"""Multiple testing correction for spatial trend maps.

Implements Section 6.7:
- Pre-declared fixed family multiple testing
- Benjamini-Hochberg (BH) False Discovery Rate (FDR)
- Benjamini-Yekutieli (BY) under arbitrary spatial dependence
- Return of adjusted q-values preserving original array indexing
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Literal, Optional, Sequence
import numpy as np


@dataclass(frozen=True)
class MultipleTestingResult:
    """Immutable result of multiple testing adjustment across a spatial family."""
    method: Literal["benjamini_hochberg", "benjamini_yekutieli"]
    family_size: int
    retained_tests: int
    q_values: List[Optional[float]]
    significant_count: int
    fdr_threshold: float


def false_discovery_rate_correction(
    p_values: Sequence[float | None] | np.ndarray,
    method: Literal["benjamini_hochberg", "benjamini_yekutieli"] = "benjamini_hochberg",
    fdr_threshold: float = 0.05,
) -> MultipleTestingResult:
    """Apply FDR correction to a family of p-values.

    Args:
        p_values: Sequence of p-values (can contain None/NaN for ineligible cells).
        method: Correction algorithm ("benjamini_hochberg" or "benjamini_yekutieli").
        fdr_threshold: Target False Discovery Rate alpha (default 0.05).

    Returns:
        MultipleTestingResult with aligned q-values.
    """
    raw_p = [float(p) if (p is not None and np.isfinite(p)) else None for p in p_values]
    total_family = len(raw_p)

    valid_indices = [i for i, p in enumerate(raw_p) if p is not None]
    m = len(valid_indices)

    if m == 0:
        return MultipleTestingResult(
            method=method,
            family_size=total_family,
            retained_tests=0,
            q_values=[None] * total_family,
            significant_count=0,
            fdr_threshold=fdr_threshold,
        )

    valid_p = np.array([raw_p[i] for i in valid_indices], dtype=np.float64)

    # Sort p-values ascending
    sort_idx = np.argsort(valid_p)
    sorted_p = valid_p[sort_idx]

    # Rank 1 to m
    ranks = np.arange(1, m + 1, dtype=np.float64)

    if method == "benjamini_yekutieli":
        # Multiplier c(m) = sum_{j=1}^m 1/j
        c_m = float(np.sum(1.0 / ranks))
    else:
        c_m = 1.0

    # Adjusted values: (m * c_m / k) * p_(k)
    raw_q = (float(m) * c_m / ranks) * sorted_p

    # Enforce monotonicity: q_(i) = min_{k >= i} raw_q_(k)
    # Computed via reverse cumulative minimum
    mono_q = np.minimum.accumulate(raw_q[::-1])[::-1]
    mono_q = np.clip(mono_q, 0.0, 1.0)

    # Invert sorting to match original valid_indices order
    inverse_sort = np.empty(m, dtype=int)
    inverse_sort[sort_idx] = np.arange(m)
    reordered_q = mono_q[inverse_sort]

    # Map back to full family size (including None for ineligible cells)
    full_q: List[Optional[float]] = [None] * total_family
    for original_idx, q_val in zip(valid_indices, reordered_q):
        full_q[original_idx] = float(q_val)

    significant_count = int(np.sum(reordered_q <= fdr_threshold))

    return MultipleTestingResult(
        method=method,
        family_size=total_family,
        retained_tests=m,
        q_values=full_q,
        significant_count=significant_count,
        fdr_threshold=fdr_threshold,
    )
