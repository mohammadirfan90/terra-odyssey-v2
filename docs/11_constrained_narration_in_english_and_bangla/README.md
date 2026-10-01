> **Navigation:** [← 10 Architecture API and Implementation Boundaries](../10_architecture_api_and_implementation_boundaries/README.md) | [Table of Contents](../README.md) | [12 Verification and Acceptance Criteria →](../12_verification_and_acceptance_criteria/README.md)

---


# 11 Constrained narration in English and Bangla

The safest default is deterministic local narration. Render exactly two plain-language sentences in English and two in Bangla from the same approved claim frame. An optional language model receives only that frame or the verified result object; it has no scientific tools, acquisition access, or independent numerical role during narration.

## 11 1 Templates and translation

Use templates that contain placeholders bound to exact result fields. For a supported temperature increase, an English template can say: "The estimated annual mean {quantity} in {region} increased by {slope_display} over {start_display} to {end_display}. The {method_display} supports this direction under the stated assumptions, with {uncertainty_display} and {coverage_display}."

Bangla template: "{start_display} থেকে {end_display} সময়ে {region} অঞ্চলে বার্ষিক গড় {quantity} বৃদ্ধির আনুমানিক হার ছিল {slope_display}। নির্ধারিত শর্ত অনুযায়ী {method_display} এই বৃদ্ধির পক্ষে পরিসংখ্যানগত প্রমাণ দেয়; অনিশ্চয়তা {uncertainty_display} এবং তথ্যের প্রাপ্যতা {coverage_display}।"

For an inconclusive result, use a different second sentence stating that the available data do not provide clear statistical evidence in the chosen interval. For insufficient data, both languages explain the missing support; the template must not mention a numerical slope if that field is null. A declining trend uses corresponding decreasing language.

These are template patterns, not measured findings. Have a fluent Bangla reviewer verify terminology, unit order, tone, and the distinction between an estimated rate and a supported direction. Localize the display strings while preserving the canonical quantity and JSON Pointer.

## 11 2 A number membership check is insufficient

A sentence can repeat a number that appears somewhere in JSON but attach it to the wrong unit, region, or method. A year could be falsely described as a slope; a positive slope could be narrated as a decrease. Validate typed claims rather than accepting text merely because its digits occur in the input.

For every quantitative claim, validate the JSON Pointer, value, approved rounding, sign, unit, time basis, region, interval, and uncertainty type. Normalize English and Bengali digits, number words, scientific notation, minus signs, dates, ranges, and percent expressions. Distinguish reported 95 percent coverage from a claimed 95 percent probability that a hypothesis is true.

Also validate nonnumeric claims: direction, evidence state, source type, baseline, causal language, and comparison compatibility. Reject an unsupported cause, an unapproved superlative, or a certainty statement stronger than the result. Prefer a schema in which the model selects approved phrase identifiers and the local renderer fills exact quantities. If free prose fails validation, return the deterministic template.

Store narration with the result id, language, template or model version, approved claim pointers, and validation outcome. A later model change may produce a new narrative version, but cannot mutate the scientific result.



---

> **Navigation:** [← 10 Architecture API and Implementation Boundaries](../10_architecture_api_and_implementation_boundaries/README.md) | [Table of Contents](../README.md) | [12 Verification and Acceptance Criteria →](../12_verification_and_acceptance_criteria/README.md)
