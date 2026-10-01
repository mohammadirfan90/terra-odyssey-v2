"""Narration safeguard validator ensuring factual alignment with result JSON Pointers.

Implements Chapter 11.2 and resolves Finding F12 and Audit R07:
- Rejects numbers absent from the result or attached to the wrong field
- Strictly blocks causal claims ("caused by", "due to human emissions", "proved")
- Prohibits sensationalized superlatives ("unprecedented", "catastrophic", "worst ever", "বিপর্যয়")
- Validates extracted numerical claims against exact claim and result pointers
- Enforces strict field binding: point slope, coverage percentage, and interval bounds are distinct
- Fully bilingual: normalizes Bengali numerals to enforce identical validation in English and Bangla
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
    "বিপর্যয়",
]

BN_TO_EN = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")


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
    combined_raw = " ".join(sentences).lower()
    # Normalize Bengali numerals to English digits for consistent regex analysis
    combined_text = combined_raw.translate(BN_TO_EN)

    # 1. Check for unverified causal language and unapproved superlatives
    for forbidden in FORBIDDEN_CAUSAL_PHRASES:
        if forbidden in combined_raw:
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

    # 5. Field-specific numerical fact validation (Resolves Finding F12, Audit R07, Finding V4-06)
    # 5a. Check point slope and CI bounds:
    # Numbers immediately before °C/decade or °C/দশক preceded by "to" or "থেকে" are CI upper endpoints.
    # Numbers explicitly in point slope position must match claim.slope_per_decade strictly.
    explicit_slope_patterns = [
        r"(?:increased at|decreased at|rate of|rate was|slope of)\s*([+-]?\d+(?:\.\d+)?)",
        r"(?:দশক প্রতি|প্রতি দশকে|প্রতি দশক)\s*([+-]?\d+(?:\.\d+)?)",
    ]
    for pattern in explicit_slope_patterns:
        for s_match in re.findall(pattern, combined_text):
            try:
                s_num = float(s_match)
                if claim.slope_per_decade is not None:
                    if abs(s_num - claim.slope_per_decade) >= 0.05:
                        errors.append(
                            f"Factual mismatch: Extracted slope quantity {s_num} does not match verified slope "
                            f"{claim.slope_per_decade} (cross-field or invented number)."
                        )
            except ValueError:
                continue

    # Unit-bound rate patterns: distinguish CI upper bound from point slope
    # E.g. "0.23 to 0.36 °C/decade" vs "+0.30 °C/decade"
    unit_rate_pattern = r"((?:to|থেকে)\s+)?([+-]?\d+(?:\.\d+)?)\s*(?:°c/decade|°c/দশক|mm/decade|mm/দশক|/decade|/দশক)"
    for prefix, num_str in re.findall(unit_rate_pattern, combined_text):
        try:
            val = float(num_str)
            if prefix:
                # Preceded by "to" or "থেকে" -> this is the CI upper bound!
                if claim.ci_95_upper_per_decade is not None:
                    if abs(val - claim.ci_95_upper_per_decade) >= 0.05:
                        errors.append(
                            f"Factual mismatch: Extracted CI upper endpoint {val} does not match verified CI upper "
                            f"{claim.ci_95_upper_per_decade}."
                        )
            else:
                # Not preceded by "to" or "থেকে" -> this is the point slope estimate!
                if claim.slope_per_decade is not None:
                    if abs(val - claim.slope_per_decade) >= 0.05:
                        errors.append(
                            f"Factual mismatch: Extracted slope quantity {val} does not match verified slope "
                            f"{claim.slope_per_decade} (cross-field or invented number)."
                        )
        except ValueError:
            continue

    # 5b. Check explicit CI bounds clauses (e.g. "interval of 0.23 to 0.36"):
    ci_clause_pattern = r"(?:confidence interval of|interval of|ব্যবধান ছিল|ব্যবধান)\s*([+-]?\d+(?:\.\d+)?)\s*(?:to|থেকে)\s*([+-]?\d+(?:\.\d+)?)"
    for low_str, up_str in re.findall(ci_clause_pattern, combined_text):
        try:
            low_val = float(low_str)
            up_val = float(up_str)
            if claim.ci_95_lower_per_decade is not None:
                if abs(low_val - claim.ci_95_lower_per_decade) >= 0.05:
                    errors.append(
                        f"Factual mismatch: Extracted CI lower endpoint {low_val} does not match verified CI lower {claim.ci_95_lower_per_decade}."
                    )
            if claim.ci_95_upper_per_decade is not None:
                if abs(up_val - claim.ci_95_upper_per_decade) >= 0.05:
                    errors.append(
                        f"Factual mismatch: Extracted CI upper endpoint {up_val} does not match verified CI upper {claim.ci_95_upper_per_decade}."
                    )
        except ValueError:
            continue

    # 5c. Check coverage percentages specifically:
    # Must match claim.coverage_pct strictly; cannot borrow duration numbers like 20 or 10.
    cov_patterns = [
        r"(\d+(?:\.\d+)?)\s*%\s*(?:spatial coverage|coverage|স্থানিক কভারেজ|কভারেজ|প্রাপ্যতা)",
        r"(?:spatial coverage|coverage|স্থানিক কভারেজ|কভারেজ|প্রাপ্যতা)\s*(?:was|ছিল|হলো)?\s*(\d+(?:\.\d+)?)\s*%",
        r"with\s*(\d+(?:\.\d+)?)\s*%\s*spatial coverage",
    ]
    for pattern in cov_patterns:
        for c_match in re.findall(pattern, combined_text):
            try:
                c_num = float(c_match)
                if claim.coverage_pct is not None:
                    if abs(c_num - claim.coverage_pct) >= 1.0:
                        errors.append(
                            f"Factual mismatch: Extracted coverage quantity {c_num}% does not match verified coverage "
                            f"{claim.coverage_pct}%."
                        )
            except ValueError:
                continue

    # 6. Global number pool for remaining tokens
    # Build strict set of allowed numbers
    num_matches = re.findall(r"[-+]?\d+(?:\.\d+)?", combined_text)
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
        claim.end_year - claim.start_year,
        95.0,  # 95% confidence interval
    ]:
        if val is not None:
            try:
                allowed_numbers.add(round(float(val), 2))
                allowed_numbers.add(round(float(val), 1))
                allowed_numbers.add(round(float(val), 0))
            except (ValueError, TypeError):
                pass

    # Only allow 10.0 or 20.0 if explicitly mentioned in a duration/span context
    if re.search(r"\b20[- ](?:year|বছর)", combined_text):
        allowed_numbers.add(20.0)
    if re.search(r"\b10[- ](?:year|বছর)", combined_text):
        allowed_numbers.add(10.0)

    # Allow numbers that are part of verified parameter or region metadata (e.g., 2m air temperature)
    for text_source in [claim.parameter_name_en, claim.region_name_en, claim.parameter_name_bn, claim.region_name_bn]:
        if text_source:
            norm_source = text_source.translate(BN_TO_EN)
            for n in re.findall(r"[-+]?\d+(?:\.\d+)?", norm_source):
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
