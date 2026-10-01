> **Navigation:** [← 11 Constrained Narration in English and Bangla](../11_constrained_narration_in_english_and_bangla/README.md) | [Table of Contents](../README.md) | [13 Completion Gates Licensing and Responsible Product Scope →](../13_completion_gates_licensing_and_responsible_product_scope/README.md)

---


# 12 Verification and acceptance criteria

Verification must establish that the system measures what it claims, preserves the data, and behaves predictably offline. The following cases are implementation requirements; they are not claims that an existing application has already passed them.

## 12 1 Scientific tests

**Table 19  Scientific tests**

| Test case | Expected property |
| :--- | :--- |
| Increasing values 1 through 10 at unit-spaced times | S=45, tied-corrected variance=125, continuity-corrected Z about 3.93548, two-sided asymptotic p about 0.00008303, slope=1 per time unit |
| Decreasing values 10 through 1 | S and Z reverse sign; two-sided p matches increasing case; slope=-1 |
| Ten identical finite values | Explicit constant-series convention gives S=0, Z=0, p=1, slope=0 and degenerate slope interval |
| Irregular times 2000 2002 2005 2009 with values 1 5 11 19 | Slope=2 per year; timestamps determine slopes |
| Times 0 1 2 3 4 with values 0 missing 4 missing 8 | Retained times 0 2 4 yield slope=2, not slope=4 from compressed positions |
| Ties and missing endpoints | Correct tie variance, retained dates, exclusions and valid null handling |
| Fewer than two eligible values | Typed insufficient state; no misleading p=1 or fabricated band |
| NaNs infinities duplicate times and unsorted dates | Explicit validation or documented sorting; no nonfinite JSON values |
| Known monthly seasonal series | Correct seasonal period and recoverable decomposition behavior; no imputed values enter primary inference |
| Positively dependent no-trend simulations | Check false-positive behavior of the chosen corrected method and uncertainty coverage |
| Spatial masks with known cell areas and values | Correct intensive mean, extensive sum, partial overlap and coverage denominator |
| Paired region series | Direct contrast uses common dates and the difference series |

Check Theil-Sen slope and rank interval against the pinned SciPy convention, including intercept settings, confidence level and degenerate cases. Increasing and decreasing fixtures with a perfect linear relation should have a degenerate slope interval at the known slope. Independent reference values must not come from the same implementation under test. [[61]](../15_references_and_dataset_directory/README.md#ref-61)

Use synthetic data only inside tests and explicit examples. Scientific calibration simulations should evaluate the selected dependence method over a range of realistic record lengths and autocorrelation strengths. They do not validate every product automatically. Publish assumptions and observed calibration limits before enabling the production evidence badge.

## 12 2 Integration offline and interface checks

**Table 20  Integration offline and interface checks**

| Acceptance gate | Evidence to collect |
| :--- | :--- |
| Complete offline request path | Block outbound access and show that cached investigation, tiles, fonts, workers and narration still work |
| Offline cache miss | Confirm a stable missing-data response and zero attempted upstream acquisition |
| Schema and provenance | Validate every ready result and every visible numerical field binding |
| Input preservation | Check scale, offset, units, QA and checksum against source fixtures |
| Geometry and resolution | Test islands, holes, antimeridian, poles, small countries, and native support warnings |
| Stale request behavior | Rapidly change region and parameter; no result is relabeled incorrectly |
| Comparison correctness | Match support, interval and binding; reject incompatible comparisons |
| Narration safeguards | Reject wrong units, signs, certainty, numeric words, absent quantities and causal claims |
| Accessibility | Keyboard-only selection, focus, screen-reader labels, contrast and mobile reflow |
| Reproducibility | Recompute a saved result with the same input hashes and declared tolerances |
| Release package | Fresh installation uses only documented local assets and produces an auditable investigation |

Network testing must cover lazy remote Zarr reads, CDN worker imports, font requests, tile and sprite URLs, service workers, API fallbacks, telemetry if enabled, and external narration. A single monkeypatch of one HTTP client does not prove the entire system is offline. Use runtime egress controls plus request monitoring for the frontend and worker.

## 12 3 Performance and efficient computing

Exact Theil-Sen estimation over forty years of daily values produces roughly one hundred million pairwise slopes; forty annual values produce only 780 pairs. Aggregate to the scientific target before trend estimation, preserve daily data for exploration, and queue expensive analyses. A map drag or uncommitted slider change must not trigger a full trend recomputation.

Initial engineering targets can be a cached national result within two seconds, local tiles within a few hundred milliseconds, and an interactive initial workspace within about three seconds on an ordinary development laptop. These are proposed targets, not measured performance. Publish the test hardware, dataset size, cold and warm conditions, and percentiles when benchmarking.

Prepare common global trend windows and map products offline, but preserve arbitrary supported regional investigations through the local worker. Use tiles and feature simplification for large map geometry; mapcn does not replace MapLibre's data-volume and source design considerations. [[88]](../15_references_and_dataset_directory/README.md#ref-88)



---

> **Navigation:** [← 11 Constrained Narration in English and Bangla](../11_constrained_narration_in_english_and_bangla/README.md) | [Table of Contents](../README.md) | [13 Completion Gates Licensing and Responsible Product Scope →](../13_completion_gates_licensing_and_responsible_product_scope/README.md)
