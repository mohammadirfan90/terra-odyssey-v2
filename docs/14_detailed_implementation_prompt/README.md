> **Navigation:** [← 13 Completion Gates Licensing and Responsible Product Scope](../13_completion_gates_licensing_and_responsible_product_scope/README.md) | [Table of Contents](../README.md) | [15 References and Dataset Directory →](../15_references_and_dataset_directory/README.md)

---


# 14 Detailed implementation prompt

Use the following specification as the instruction to a coding agent. It is intentionally concrete about scientific and offline behavior. Dataset identifiers and parameter bindings in the attached catalog must be validated before acquisition; the agent must not invent a finished environmental result to make the interface look complete.

## 14 1 Objective and stack

Build Earth System Trend Detective, an offline-first web investigation tool for Earth. The user selects a country or region on a flat 2D map, chooses a physical parameter and time interval, and receives an auditable trend investigation. Follow the research and engineering requirements in this document.

Use Next.js 16.3.8 or a newer verified stable patch satisfying the requested 16.3.6-and-newer family, App Router, strict TypeScript, version-compatible React, Tailwind and shadcn/ui. Use reviewed mapcn components over MapLibre GL JS for the main map. Use Python FastAPI, Pydantic, NumPy, SciPy, xarray, Zarr and Parquet support for the backend. Use a pinned supported runtime and exact lockfiles. Use OpenLayers only for an isolated flat polar view when required.

Inspect an existing repository and its instructions before modifying it. Preserve useful working modules and migrate only the parts that need these contracts. If no repository exists, create the project modules specified in Section 10. Do not pretend that unavailable source code or an inaccessible artifact was inspected.

## 14 2 Nonnegotiable scientific and data rules

1. *No globe, Cesium dependency, terrain or 3D perspective. Lock the primary map to 2D and retain complete scientific coverage through a separate flat polar view where appropriate.*

2. *Categorize every supplied catalog family into ParameterDefinition, DatasetBinding, AnalysisPolicy and LayerDefinition objects. Preserve original raw files and expose binding maturity and installed coverage.*

3. *Keep air temperature, LST day, LST night, SST and blended surface-temperature anomalies distinct. Store units, time bounds, QA, observation type and native measurement support.*

4. *Read pre-cached NASA POWER daily Parquet, one file per country representative point with explicit coordinates. Label it as a point sample. National results require area aggregation of gridded data.*

5. *Start with local NASA MERRA-2 T2M in Zarr and add MODIS LST for the requested surface-temperature investigation. Bind exact source collections, versions and citations. Additional parameters remain unavailable until validated data exist.*

6. *Scientific requests and compute jobs never call an upstream network service. OFFLINE=1 rejects remote stores, imagery, MCP, narration and hidden fallbacks. A cache miss is a typed error.*

7. *Put online discovery and acquisition in a separate command. NASA Earthdata MCP can discover and verify collections and granules; earthaccess can download them during preparation. Neither enters the scientific request path.*

8. *No language model computes, corrects or invents numerical outputs. No fake scientific values, fabricated citations or production fixture fallbacks.*

## 14 3 Numerical implementation

Implement pure functions in src/compute for area-weighted regional series, Mann-Kendall S and tied variance, continuity-corrected Z, two-sided p value, direction, Theil-Sen slope, explicit intercept, 95 percent slope interval, and eligible seasonal decomposition. Use actual elapsed timestamps and preserve missing dates. Define constant-series and insufficient-series behavior separately.

Implement the initial climate workflow with annual or fixed-season observations. Document and implement the selected dependence-aware inference method; use a seasonal method for eligible monthly inference. Return test assumptions, diagnostic settings and primary versus sensitivity outputs. Do not present an independent slope interval as dependence-adjusted merely because the p value was corrected.

Implement a supported fitted-line uncertainty band with uncertainty in both slope and intercept; label pointwise versus simultaneous coverage and the method. Never construct a band by drawing slope bounds through an arbitrary anchor. Return null with a reason when a required uncertainty method or diagnostic is unsupported.

Apply product-specific QA and missingness policies. Keep any decomposition interpolation in a separate diagnostic copy, out of the primary inferential series. Record baselines, time weighting, spatial masks and aggregation settings. Give class changes, events, ocean profiles and short mission records their own estimators instead of applying a generic slope to every field.

For trend maps, define the fixed multiple-testing family and return the declared correction and q values. Country-series inference is separate. For comparison, use compatible bindings and common eligible dates; analyze a paired difference series for the contrast.

## 14 4 API and provenance implementation

Implement GET /trend with region_id, parameter_id, start, end and explicit optional dataset and analysis settings. Preserve a compatibility alias for district only if it resolves unambiguously. Support async jobs for expensive work and immutable GET /results/{id} outputs. Implement coverage, regions, parameters, series, comparison, local layer metadata, local tiles, safe sources and exports.

Use typed result blocks from Section 10. Every result includes dataset_id, source_url, collection/version, actual retrieved_at UTC timestamp, access_mode, checksums, geometry version, method configuration, code revision and exclusions. Production request access_mode is cache; acquisition lineage may separately describe live retrieval. Fixtures are available only in explicit tests.

Hash all scientific inputs and policies into the result id. Validate dates, identifiers, geometry and supported units; return RFC 9457 problem details. Serialize unsupported values as null, never zero, NaN or infinity. Bound compute resources and support cancellation. Keep credentials and private paths out of responses.

## 14 5 Frontend and offline implementation

Provide accessible country search and selection, a parameter selector grouped by physical domain, coverage-aware dates, and an explicit run action. Use a central flat map, a result panel and a linked time-series area. Include custom state, anomaly, slope, evidence, coverage and QA layers with units, nodata, time support, native resolution and source credit.

Replace mapcn's hosted basemap and CDN worker defaults with local assets. Package style JSON, required tiles or local geographic context, glyphs, sprites, fonts, worker modules and scientific layer inventory. Preserve custom layers after style changes. Do not leave remote dependencies in the offline path.

Evaluate the CarbonPlan Zarr display plugin against the local-tile fallback using Section 8. Keep reported calculations in Python and enforce camera-independent scientific values. Treat the Open-Meteo plugin as optional weather context pending maturity, local-asset and license validation. Verify worker and WebAssembly packaging in the actual Next production build instead of assuming that another bundler's example transfers unchanged.

Show observed series, a fitted Theil-Sen line and the supported band. Show explicit gaps. Add two-region comparison, a difference chart, seasonal diagnostics, a data table and a provenance drawer. Bind every displayed quantity to its result JSON Pointer, unit and approved formatter. Inspect clicked values from numerical data, not rendered tile colors.

Keep draft query, committed query and map viewport separate. Ignore stale responses. Maintain the same result id across maps, charts, narration and exports. Preserve scientific settings through English/Bangla switching and shareable URLs. Provide keyboard and non-map alternatives, readable contrast, mobile reflow and reduced motion.

Package a local FastAPI deployment for new offline calculations. A browser-only cached edition can inspect stored results, but must disclose that new calculations need the local service. Optional commercial imagery is an explicitly online context mode unless local rights and assets are established. No Google or commercial tile prefetching contrary to provider terms.

## 14 6 Narration implementation

Produce exactly two sentences per language from approved typed claims. Use deterministic local templates by default. An optional language model receives only the verified result or claim frame and cannot obtain additional numerical facts.

Validate numeric values, signs, units, intervals, regions, evidence status, uncertainty type, localized digits, number words and causal language. A number appearing somewhere in JSON is not enough. Use JSON Pointer bindings and approved phrase identifiers; fall back to deterministic templates when free text fails. Never strengthen inconclusive evidence into a supported trend.

## 14 7 Tests documentation and completion

Add meaningful unit tests for increasing, decreasing, flat, tied, irregular-time and missing-value series, invalid input, seasonal diagnostics, aggregation, direct comparison and uncertainty methods. Verify reference statistical values independently. Add integration tests for blocked-egress operation, missing cache, local map assets, stale results, schema provenance and narration safeguards.

Create an Apache-2.0 source-code license, dependency and dataset notices, a public-ready README listing every catalogued and enabled dataset with its URL, acquisition commands, offline installation, method assumptions and limitations. Use actual input manifests and truthful availability states. Include reproducible example investigations only after their data exist locally.

Report completed release gates, validation results, actual dataset coverage and remaining limitations. Release only working, tested behavior.



---

> **Navigation:** [← 13 Completion Gates Licensing and Responsible Product Scope](../13_completion_gates_licensing_and_responsible_product_scope/README.md) | [Table of Contents](../README.md) | [15 References and Dataset Directory →](../15_references_and_dataset_directory/README.md)
