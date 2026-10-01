"""Deterministic Bangla (বাংলা) narration generator with authentic numeral conversion.

Implements Chapter 11.1 and resolves Findings F06 & F13:
- Exactly two plain-language Bangla sentences
- Converts Latin digits to Bengali digits (০, ১, ২, ৩, ৪, ৫, ৬, ৭, ৮, ৯)
- Separate sentences for supported, limited, inconclusive, flat, and insufficient states
- Accurate observation type and temporal statistic distinction
"""

from __future__ import annotations

from typing import List
from .claims import NarrationClaimFrame


BENGALI_DIGITS = {
    "0": "০", "1": "১", "2": "২", "3": "৩", "4": "৪",
    "5": "৫", "6": "৬", "7": "৭", "8": "৮", "9": "৯"
}


def to_bengali_numerals(text: str | int | float) -> str:
    """Convert ASCII digits in a string or number to authentic Bengali script numerals."""
    s = str(text)
    return "".join(BENGALI_DIGITS.get(ch, ch) for ch in s)


def render_bangla_narration(claim: NarrationClaimFrame) -> List[str]:
    """Generate exactly two deterministic Bangla sentences describing the investigation."""
    start_bn = to_bengali_numerals(claim.start_year)
    end_bn = to_bengali_numerals(claim.end_year)

    # Insufficient state
    if claim.evidence_state in ("insufficient", "degenerate") or claim.slope_per_decade is None:
        s1 = (
            f"{start_bn} থেকে {end_bn} সময়কালে {claim.region_name_bn} অঞ্চলে {claim.parameter_name_bn} "
            f"এর নির্ভরযোগ্য পরিবর্তনের ধারা মূল্যায়নের জন্য পর্যাপ্ত পর্যবেক্ষণ তথ্য নেই।"
        )
        s2 = "বিদ্যমান উপাত্ত জলবায়ু পূর্বাভাসের জন্য প্রয়োজনীয় ন্যূনতম স্থানিক বিস্তার বা সময়কাল পূরণ করে না।"
        return [s1, s2]

    sign_bn = "+" if claim.slope_per_decade > 0 else ""
    slope_num_bn = to_bengali_numerals(f"{claim.slope_per_decade:.2f}")
    slope_str_bn = f"{sign_bn}{slope_num_bn} {claim.unit}/দশক"

    stat_label_bn = "বার্ষিক মোট" if claim.temporal_statistic in ("annual_total", "total") else "বার্ষিক গড়"

    # Sentence 1: Direction and rate
    if claim.direction == "increasing":
        change_word = "বৃদ্ধির"
    elif claim.direction == "decreasing":
        change_word = "হ্রাসের"
    else:
        change_word = "পরিবর্তনের"

    s1 = (
        f"{start_bn} থেকে {end_bn} সময়ে {claim.region_name_bn} অঞ্চলে {stat_label_bn} {claim.parameter_name_bn} "
        f"{change_word} আনুমানিক হার ছিল {slope_str_bn}।"
    )

    # Sentence 2: Evidence and uncertainty
    if claim.ci_95_lower_per_decade is not None and claim.ci_95_upper_per_decade is not None:
        ci_low_bn = to_bengali_numerals(f"{claim.ci_95_lower_per_decade:.2f}")
        ci_high_bn = to_bengali_numerals(f"{claim.ci_95_upper_per_decade:.2f}")
        ci_str_bn = f"৯৫% নির্ভরযোগ্যতার ব্যবধান {ci_low_bn} থেকে {ci_high_bn} {claim.unit}/দশক"
    else:
        ci_str_bn = "অনির্ধারিত অনিশ্চয়তা"

    cov_bn = to_bengali_numerals(f"{claim.coverage_pct:.1f}")
    cov_str_bn = f"তথ্যের প্রাপ্যতা {cov_bn}%"

    if claim.evidence_state in ("supported_increase", "supported_decrease"):
        s2 = (
            f"নির্ধারিত শর্তাবলী অনুযায়ী {claim.method_name_bn} এই প্রবণতার পক্ষে সুস্পষ্ট পরিসংখ্যানগত প্রমাণ দেয়; "
            f"{ci_str_bn} এবং {cov_str_bn}।"
        )
    elif claim.evidence_state == "limited":
        years_span_bn = to_bengali_numerals(claim.end_year - claim.start_year + 1)
        s2 = (
            f"এই পর্যবেক্ষণটি {years_span_bn} বছরব্যাপী বিস্তৃত যা একটি পূর্ণাঙ্গ জলবায়ু মূল্যায়নের পরিবর্তে প্রাথমিক অনুসন্ধানী প্রমাণ নির্দেশ করে; "
            f"{ci_str_bn} এবং {cov_str_bn}।"
        )
    elif claim.evidence_state == "flat":
        s2 = (
            f"আনুমানিক পরিবর্তনের হার প্রায় শূন্য এবং ম্যান-কেন্ডাল পরীক্ষা এই সময়কালে কোনো ধারাবাহিক একক পরিবর্তন নির্দেশ করে না; "
            f"{ci_str_bn} এবং {cov_str_bn}।"
        )
    else:  # inconclusive
        s2 = (
            f"বিদ্যমান তথ্য এই সময়কালে কোনো সুনির্দিষ্ট একক পরিবর্তনের পরিসংখ্যানগত প্রমাণ নিশ্চিত করে না; "
            f"{ci_str_bn} এবং {cov_str_bn}।"
        )

    return [s1, s2]
