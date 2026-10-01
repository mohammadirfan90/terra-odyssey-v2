"""Unit tests for bilingual constrained narration and validation safeguards."""

import pytest
from src.narration.claims import NarrationClaimFrame
from src.narration.templates_en import render_english_narration
from src.narration.templates_bn import render_bangla_narration, to_bengali_numerals
from src.narration.validator import validate_narrative_text, resolve_json_pointer


def test_bengali_numerals_conversion():
    assert to_bengali_numerals(1980) == "১৯৮০"
    assert to_bengali_numerals("2024") == "২০২৪"
    assert to_bengali_numerals("+0.28 °C/decade") == "+০.২৮ °C/decade"


def test_english_and_bangla_deterministic_narration():
    claim = NarrationClaimFrame(
        result_id="test_result_123",
        region_id="BGD",
        region_name_en="Bangladesh",
        region_name_bn="বাংলাদেশ",
        parameter_id="air_temperature_2m",
        parameter_name_en="Near-Surface Air Temperature (2m)",
        parameter_name_bn="ভূপৃষ্ঠ সংলগ্ন বায়ুর তাপমাত্রা (২ মিটার)",
        temporal_statistic="annual_mean",
        start_year=1980,
        end_year=2024,
        slope_per_decade=0.284,
        slope_display_en="+0.28 °C/decade",
        slope_display_bn="+০.২৮ °C/দশক",
        unit="°C",
        direction="increasing",
        evidence_state="supported_increase",
        p_value=1.5e-6,
        ci_95_lower_per_decade=0.21,
        ci_95_upper_per_decade=0.36,
        coverage_pct=98.5,
        method_name_en="Mann-Kendall test with autocorrelation adjustment",
        method_name_bn="অটোকরিলেশন সমন্বিত ম্যান-কেন্ডাল পরীক্ষা",
    )

    en_sentences = render_english_narration(claim)
    assert len(en_sentences) == 2
    assert "increased at a rate of +0.28 °C/decade" in en_sentences[0]
    assert "supports this direction" in en_sentences[1]

    bn_sentences = render_bangla_narration(claim)
    assert len(bn_sentences) == 2
    assert "১৯৮০ থেকে ২০২৪" in bn_sentences[0]
    assert "+০.২৮ °C/দশক" in bn_sentences[0]
    assert "পরিসংখ্যানগত প্রমাণ" in bn_sentences[1]


def test_narrative_safeguard_blocks_forbidden_causal_language():
    claim = NarrationClaimFrame(
        result_id="test_result_123",
        region_id="USA",
        region_name_en="United States",
        region_name_bn="মার্কিন যুক্তরাষ্ট্র",
        parameter_id="air_temperature_2m",
        parameter_name_en="Air Temperature",
        parameter_name_bn="বায়ুর তাপমাত্রা",
        temporal_statistic="annual_mean",
        start_year=1980,
        end_year=2024,
        slope_per_decade=0.31,
        slope_display_en="+0.31 °C/decade",
        slope_display_bn="+০.৩১ °C/দশক",
        unit="°C",
        direction="increasing",
        evidence_state="supported_increase",
        p_value=1e-5,
        ci_95_lower_per_decade=0.22,
        ci_95_upper_per_decade=0.40,
        coverage_pct=100.0,
        method_name_en="Mann-Kendall",
        method_name_bn="ম্যান-কেন্ডাল",
    )

    fake_result = {
        "theil_sen": {"slope_per_decade": 0.31, "ci_95_lower_per_decade": 0.22, "ci_95_upper_per_decade": 0.40},
        "mann_kendall": {"p_value": 1e-5},
        "data_support": {"valid_area_coverage_pct": 100.0},
    }

    # Halucinated sentences with causal claims
    bad_sentences = [
        "The temperature increased rapidly caused by greenhouse gas emissions.",
        "This proves climate change is disastrous.",
    ]

    is_valid, errors = validate_narrative_text(bad_sentences, claim, fake_result)
    assert is_valid is False
    assert any("caused by" in err for err in errors)
    assert any("disastrous" in err for err in errors)


def test_resolve_json_pointer():
    doc = {
        "identity": {"result_id": "abc"},
        "theil_sen": {"slope_per_decade": 0.25},
        "points": [{"date": 2000, "val": 10.0}],
    }
    assert resolve_json_pointer(doc, "/identity/result_id") == "abc"
    assert resolve_json_pointer(doc, "/theil_sen/slope_per_decade") == 0.25
    assert resolve_json_pointer(doc, "/points/0/val") == 10.0
    assert resolve_json_pointer(doc, "/nonexistent/path") is None
