"""Narration safeguard validator ensuring factual alignment with result JSON Pointers.

Implements Chapter 11.2 and resolves Finding F12:
- Rejects numbers absent from the result or attached to the wrong field
- Strictly blocks causal claims ("caused by", "due to human emissions", "proved")
- Prohibits sensationalized superlatives ("unprecedented", "catastrophic", "worst ever")
- Validates extracted numerical claims against exact claim and result pointers
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple
from .claims import NarrationClaimFrame


FORBIDDEN_CAUSAL_PHRASES = [
    "caused by",
    "causes of",
    "due to greenhouse",
    "due to emissions",
    "due to human",
    "proves climate change",
    "proves global warming",
    "responsible for the warming",
    "unprecedented",
    "catastrophic",
    "worst in history",
    "disastrous",
    "কারণে",
    "প্রমাণ করে",
]


def resolve_json_pointer(doc: Dict[str, Any], pointer: str) -> Any:
    """Resolve an RFC 6901 JSON Pointer against a dictionary."""
    if not pointer or pointer == "/":
        return doc
    parts = pointer.strip("/").split("/")
    cur = doc
    for p in parts:
        p = p.replace("~1", "/").replace("~0", "~")
        if isinstance(cur, dict) and p in cur:
            cur = cur[p]
        elif isinstance(cur, list) and p.isdigit():
            idx = int(p)
            if 0 <= idx < len(cur):
                cur = cur[idx]
            else:
                return None
        else:
            return None
    return cur


def validate_narrative_text(
    sentences: List[str],
    claim: NarrationClaimFrame,
    full_result: Dict[str, Any],
) -> Tuple[bool, List[str]]:
    """Validate that generated narrative sentences adhere strictly to scientific findings.

    Enforces:
    - Zero unverified causal language
    - Exact 2-sentence structure
    - Strict value equality between claim quantities and resolved JSON pointers
    - Field-specific numerical validation preventing cross-field number leakage
    """
    errors: List[str] = []
    combined_text = " ".join(sentences).lower()

    # 1. Check for unverified causal language and unapproved superlatives
    for forbidden in FORBIDDEN_CAUSAL_PHRASES:
        if forbidden in combined_text:
            errors.append(f"Forbidden causal or sensationalized claim detected: '{forbidden}'")

    # 2. Check sentence count constraint (exactly two sentences per language)
    if len(sentences) != 2:
        errors.append(f"Narrative must contain exactly two sentences, got {len(sentences)}")

    # 3. Check JSON pointer integrity and value equality (Resolves Finding F12 / Audit R07)
    for field_name, ptr in claim.json_pointers.items():
        val = resolve_json_pointer(full_result, ptr)
        if val is None:
            errors.append(f"JSON pointer '{ptr}' for {field_name} resolved to None")
            continue

        claim_val = None
        if field_name == "slope":
            claim_val = claim.slope_per_decade
        elif field_name == "coverage":
            claim_val = claim.coverage_pct
        elif field_name == "ci_lower":
            claim_val = claim.ci_95_lower_per_decade
        elif field_name == "ci_upper":
            claim_val = claim.ci_95_upper_per_decade
        elif field_name == "p_value":
            claim_val = claim.p_value

        if claim_val is not None and val is not None:
            try:
                if abs(float(val) - float(claim_val)) > 1e-3:
                    errors.append(
                        f"Claim/Pointer value disagreement for '{field_name}': "
                        f"claim={claim_val} does not match pointer '{ptr}' value={val}"
                    )
            except (ValueError, TypeError):
                if str(val) != str(claim_val):
                    errors.append(
                        f"Claim/Pointer value disagreement for '{field_name}': "
                        f"claim={claim_val} does not match pointer '{ptr}' value={val}"
                    )

    # 4. Check sign consistency if trend is present
    if claim.slope_per_decade is not None:
        if claim.slope_per_decade > 0.05 and "decreased" in combined_text:
            errors.append("Inconsistency: Positive slope described as 'decreased'")
        elif claim.slope_per_decade < -0.05 and "increased" in combined_text:
            errors.append("Inconsistency: Negative slope described as 'increased'")

    # 5. Field-specific numerical fact validation (Resolves Finding F12 / Audit R07)
    # Check rate/slope numbers specifically: they must not borrow from coverage or other fields
    slope_matches = re.findall(
        r"([+-]?\d+(?:\.\d+)?)\s*(?:°c/decade|°c|mm/decade|mm|/decade|দশক প্রতি)",
        combined_text,
    )
    for s_match in slope_matches:
        try:
            s_num = float(s_match)
            allowed_slopes = [claim.slope_per_decade]
            if claim.ci_95_lower_per_decade is not None:
                allowed_slopes.append(claim.ci_95_lower_per_decade)
            if claim.ci_95_upper_per_decade is not None:
                allowed_slopes.append(claim.ci_95_upper_per_decade)

            valid_matches = [v for v in allowed_slopes if v is not None and abs(s_num - v) < 0.05]
            if not valid_matches:
                errors.append(
                    f"Factual mismatch: Extracted slope quantity {s_num} does not match verified slope "
                    f"{claim.slope_per_decade} (cross-field or invented number)."
                )
        except ValueError:
            continue

    # Global number pool for remaining tokens (years, intervals, coverage)
    num_matches = re.findall(r"[-+]?\d+(?:\.\d+)?", " ".join(sentences))
    allowed_numbers = set()
    for val in [
        claim.start_year,
        claim.end_year,
        claim.slope_per_decade,
        claim.p_value,
        claim.ci_95_lower_per_decade,
        claim.ci_95_upper_per_decade,
        claim.coverage_pct,
        claim.end_year - claim.start_year + 1,
        95.0,  # 95% confidence interval
        20.0,  # 20-year climate assessment
        10.0,
    ]:
        if val is not None:
            try:
                allowed_numbers.add(round(float(val), 2))
                allowed_numbers.add(round(float(val), 1))
                allowed_numbers.add(round(float(val), 0))
            except (ValueError, TypeError):
                pass

    # Allow numbers that are part of verified parameter or region metadata (e.g., 2m air temperature)
    for text_source in [claim.parameter_name_en, claim.region_name_en, claim.parameter_name_bn, claim.region_name_bn]:
        if text_source:
            for n in re.findall(r"[-+]?\d+(?:\.\d+)?", text_source):
                try:
                    allowed_numbers.add(round(float(n), 2))
                    allowed_numbers.add(round(float(n), 1))
                    allowed_numbers.add(round(float(n), 0))
                except (ValueError, TypeError):
                    pass

    for tok in num_matches:
        try:
            num = float(tok)
            # Check if this number is within 0.05 of any allowed value
            if not any(abs(num - a) < 0.05 for a in allowed_numbers):
                errors.append(
                    f"Factual mismatch: Extracted number {num} in narration does not match any verified result quantity."
                )
        except ValueError:
            continue

    is_valid = len(errors) == 0
    return is_valid, errors
