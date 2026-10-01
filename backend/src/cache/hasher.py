"""Deterministic canonical result hashing for immutable audit trails.

Implements Section 5.3 and resolves Finding F05:
- Canonical JSON serialization of normalized query parameters, full analysis policy, and input data SHA-256
- Any change to input data values, policy options, or code revision creates a distinct result ID
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, Optional


def compute_result_hash(
    region_id: str,
    parameter_id: str,
    binding_id: str,
    start_date: str,
    end_date: str,
    policy_id: str,
    data_sha256: str = "",
    geometry_sha256: str = "",
    code_revision: str = "v1.0.0",
    policy_settings: Optional[Dict[str, Any]] = None,
    extra_settings: Optional[Dict[str, Any]] = None,
) -> str:
    """Generate canonical SHA-256 hex digest for an immutable scientific investigation result."""
    payload = {
        "region_id": str(region_id).strip().upper(),
        "parameter_id": str(parameter_id).strip().lower(),
        "binding_id": str(binding_id).strip(),
        "start_date": str(start_date).strip(),
        "end_date": str(end_date).strip(),
        "policy_id": str(policy_id).strip(),
        "data_sha256": str(data_sha256).strip(),
        "geometry_sha256": str(geometry_sha256).strip(),
        "code_revision": str(code_revision).strip(),
        "policy": policy_settings or {},
        "extra": extra_settings or {},
    }
    canonical_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
