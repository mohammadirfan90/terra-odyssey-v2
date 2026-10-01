"""Pydantic schemas and RFC 9457 Problem Details for FastAPI API."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class ProblemDetail(BaseModel):
    """RFC 9457 Problem Details for HTTP APIs."""
    type: str = Field(..., description="URI reference identifying the error type")
    title: str = Field(..., description="Short, human-readable summary of problem")
    status: int = Field(..., description="HTTP status code")
    detail: str = Field(..., description="Human-readable explanation specific to this occurrence")
    code: str = Field(..., description="Stable machine-readable error code")
    instance: Optional[str] = Field(None, description="URI reference identifying specific occurrence")
    invalid_params: Optional[List[Dict[str, Any]]] = None


class TrendRequestQuery(BaseModel):
    region_id: str
    parameter_id: str
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    binding_id: Optional[str] = None
    policy_id: Optional[str] = None
    district: Optional[str] = Field(None, description="Deprecated compatibility alias for region_id")


class ComparisonRequest(BaseModel):
    region_id_a: str
    region_id_b: str
    parameter_id: str
    binding_id: Optional[str] = None
    policy_id: Optional[str] = None
    start_year: Optional[int] = None
    end_year: Optional[int] = None


class SeriesPoint(BaseModel):
    year: int
    month: Optional[int] = None
    value: float
    value_display: float
    unit: str
    qa_passed: bool
    is_imputed: bool = False


class ExportBundle(BaseModel):
    result_id: str
    result: Dict[str, Any]
    csv_data: str
    reproducibility_manifest: Dict[str, Any]
