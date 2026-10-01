"""Deterministic English narration generator from verified claim frames.

Implements Chapter 11.1 and resolves Findings F06 & F13:
- Exactly two plain-language sentences
- Separate sentences for supported, limited, inconclusive, flat, and insufficient states
- Accurate observation type and temporal statistic distinction (annual mean vs annual total)
- Strictly bound to verified values with zero LLM hallucination
"""

from __future__ import annotations

from typing import List
from .claims import NarrationClaimFrame


def render_english_narration(claim: NarrationClaimFrame) -> List[str]:
    """Generate exactly two deterministic English sentences describing the investigation."""
    # Insufficient state
    if claim.evidence_state in ("insufficient", "degenerate") or claim.slope_per_decade is None:
        s1 = (
            f"Over the period {claim.start_year} to {claim.end_year}, there are insufficient eligible "
            f"observations to calculate a reliable {claim.parameter_name_en} trend for {claim.region_name_en}."
        )
        s2 = "Available observations do not meet the minimum spatial coverage or duration requirements for climate inference."
        return [s1, s2]

    # Sentence 1: Rate and direction
    sign = "+" if claim.slope_per_decade > 0 else ""
    slope_str = f"{sign}{claim.slope_per_decade:.2f} {claim.unit}/decade"

    stat_label = "annual total" if claim.temporal_statistic in ("annual_total", "total") else "annual mean"
    loc_phrase = f"in {claim.region_name_en}"

    if claim.direction == "increasing":
        verb = "increased"
    elif claim.direction == "decreasing":
        verb = "decreased"
    else:
        verb = "remained essentially unchanged"

    s1 = (
        f"The estimated {stat_label} {claim.parameter_name_en} {loc_phrase} {verb} "
        f"at a rate of {slope_str} over {claim.start_year} to {claim.end_year}."
    )

    # Sentence 2: Statistical evidence and uncertainty
    if claim.ci_95_lower_per_decade is not None and claim.ci_95_upper_per_decade is not None:
        ci_str = f"a 95% confidence interval of {claim.ci_95_lower_per_decade:.2f} to {claim.ci_95_upper_per_decade:.2f} {claim.unit}/decade"
    else:
        ci_str = "uncalibrated slope uncertainty"

    cov_str = f"{claim.coverage_pct:.1f}% spatial coverage"

    if claim.evidence_state in ("supported_increase", "supported_decrease"):
        s2 = (
            f"The {claim.method_name_en} supports this direction under the stated assumptions, "
            f"with {ci_str} and {cov_str}."
        )
    elif claim.evidence_state == "limited":
        years_span = claim.end_year - claim.start_year + 1
        s2 = (
            f"This observation record spans {years_span} years, providing exploratory evidence "
            f"rather than a standard 20-year climate assessment, with {ci_str} and {cov_str}."
        )
    elif claim.evidence_state == "flat":
        s2 = (
            f"The estimated rate of change is zero or near-zero, and the Mann-Kendall test indicates no monotonic change, "
            f"with {ci_str} and {cov_str}."
        )
    else:  # inconclusive
        s2 = (
            f"The available data do not provide clear statistical evidence of a monotonic trend in this interval, "
            f"with {ci_str} and {cov_str}."
        )

    return [s1, s2]
