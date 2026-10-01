"""Approved typed claim frames for deterministic bilingual narration.

Implements Chapter 11:
- Typed claim frame derived directly from the verified result object
- JSON pointer mappings for all quantitative facts
- Explicit evidence state and direction constraints
"""

from __future__ import annotations

from typing import Dict, Literal, Optional
from pydantic import BaseModel, Field


class NarrationClaimFrame(BaseModel):
    """Immutable verified claim frame used to synthesize and validate narration."""
    result_id: str
    region_id: str
    region_name_en: str
    region_name_bn: str
    parameter_id: str
    parameter_name_en: str
    parameter_name_bn: str
    temporal_statistic: str
    start_year: int
    end_year: int
    slope_per_decade: Optional[float]
    slope_display_en: Optional[str]
    slope_display_bn: Optional[str]
    unit: str
    direction: Literal["increasing", "decreasing", "flat", "insufficient", "inconclusive", "degenerate"]
    evidence_state: Literal[
        "supported_increase",
        "supported_decrease",
        "inconclusive",
        "limited",
        "insufficient",
        "flat",
        "degenerate",
    ]
    p_value: Optional[float]
    ci_95_lower_per_decade: Optional[float]
    ci_95_upper_per_decade: Optional[float]
    coverage_pct: float
    method_name_en: str
    method_name_bn: str
    json_pointers: Dict[str, str] = Field(
        default_factory=lambda: {
            "slope": "/theil_sen/slope_per_decade",
            "p_value": "/mann_kendall/p_value",
            "ci_lower": "/theil_sen/ci_95_lower_per_decade",
            "ci_upper": "/theil_sen/ci_95_upper_per_decade",
            "coverage": "/data_support/valid_area_coverage_pct",
        }
    )
