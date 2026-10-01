> **Navigation:** [← 09 Interface and Interaction Design](../09_interface_and_interaction_design/README.md) | [Table of Contents](../README.md) | [11 Constrained Narration in English and Bangla →](../11_constrained_narration_in_english_and_bangla/README.md)

---


# 10 Architecture API and implementation boundaries

Use a TypeScript frontend and a Python scientific backend with a single shared contract generated from FastAPI's OpenAPI schema. Map and chart state refer to immutable scientific results. Python is responsible for numerical values, eligibility, interpretation states, and approved narrative claims; TypeScript handles interaction, formatting, and visualization.

![Figure 2: Online acquisition is separated from local request and computation paths](figure_2_online_acquisition_architecture.png)

**Figure 2  Online acquisition is separated from local request and computation paths**

## 10 1 Next js and dependency choices

Use Next.js 16.3.8 or a newer verified stable patch rather than an open-ended package specification. The September 30, 2026 official security release identifies 16.3.8 as the active-LTS patched version, following the September 22 release of 16.3.6. Record exact dependency versions in the lockfile and check the official release guidance when implementing. [[1]](../15_references_and_dataset_directory/README.md#ref-1) [[83]](../15_references_and_dataset_directory/README.md#ref-83)

Use TypeScript strict mode and version-matched React types. Next.js 16 documents a Node minimum of 20.9 and TypeScript minimum of 5.1; select a currently supported compatible Node LTS and lock its version. Follow the asynchronous request API requirements and run ESLint separately rather than assuming next lint remains available. [[84]](../15_references_and_dataset_directory/README.md#ref-84)

Keep mapcn and MapLibre in a client component. Render the surrounding controls and explanatory content safely in the chosen App Router architecture; do not access window or construct a map during server rendering. Use a client boundary for any dynamic import with server rendering disabled, and clean up map instances, listeners, workers, and pending requests.

For the local edition, prefer a static export of the frontend served alongside FastAPI, with client-side region and query selection. Static export cannot use features that require a Next server, such as Server Actions or unrestricted request-time dynamic routes. If such features are required, package a local Next server explicitly instead. Local image assets avoid the remote image optimization path. [[85]](../15_references_and_dataset_directory/README.md#ref-85)

Use a controlled form and URL state for the committed investigation, a small client store for map interaction if needed, and a query library or equivalent cache keyed by the full scientific query. Keep dependency additions purposeful. A chart library such as ECharts or a focused SVG chart can render backend values; choose based on keyboard access, gaps, confidence bands, and export behavior, then verify those features.

## 10 2 Suggested project modules

**Table 16  Suggested project modules**

| Path | Responsibility |
| :--- | :--- |
| frontend/app | Next App Router shell, country selection, investigation views |
| frontend/components/ui/map.tsx | Reviewed mapcn component with local assets and 2D settings |
| frontend/components/investigation | Result panel, chart, comparison, diagnostics and provenance |
| frontend/lib/contracts | Generated TypeScript API types and validated display bindings |
| frontend/public/offline | Local styles, fonts, geometry, workers, glyphs and sprites |
| backend/src/api | FastAPI endpoints, validation and problem responses |
| backend/src/compute | Mann-Kendall, Sen, uncertainty, seasonal and spatial routines |
| backend/src/registry | Parameter, dataset, region, layer and policy schemas |
| backend/src/ingest | Explicit online acquisition commands and metadata adapters |
| backend/src/cache | Local inventory, manifests, checksums and result store |
| backend/src/narration | Approved claim frames, bilingual templates and validation |
| backend/tests | Scientific, contract, offline, geometry and integration tests |
| data/manifests | Versioned dataset and acquisition metadata |
| data/cache | Local Parquet and Zarr stores, outside ordinary source commits |
| docs | Methods, dataset inventory, offline guide and release evidence |

Run expensive work in a separate bounded process worker or local task queue, not directly on the FastAPI async event loop. Start with a simple process-based worker and SQLite job tracking; add distributed processing only after profiling justifies it. Local Dask can help with chunked arrays, but no worker may retrieve missing upstream data during computation.

## 10 3 Endpoint contract

Preserve GET /trend as required, with region_id, parameter_id, start and end replacing ambiguous district and variable names. Add dataset_id, aggregation, baseline_id, and policy_id where necessary. A deprecated district alias can resolve to a region id when unambiguous; reject conflicting aliases.

**Table 17  Endpoint contract**

| Endpoint | Behavior |
| :--- | :--- |
| GET /regions | Search supported countries, subregions and ocean regions with geometry versions |
| GET /parameters | Physical definitions, available bindings and scientific capability states |
| GET /coverage | Cached temporal and spatial support for a selected query |
| GET /trend | Cached result or bounded inexpensive local computation under the specified contract |
| POST /investigations | Queue a new expensive local computation and return a job id |
| GET /jobs/{id} | Job state, progress, cancellation state and immutable result reference |
| GET /results/{id} | Exact immutable result object |
| GET /results/{id}/series | Raw and eligible observations with QA and dates |
| POST /comparisons | Compatible paired regional contrast computation |
| GET /layers/{id}/tilejson | Local visual layer metadata and tile inventory |
| GET /tiles/{id}/{z}/{x}/{y} | Locally prepared scientific or context tiles |
| GET /sources/{id} | Source metadata, citations and safe manifest fields |
| GET /results/{id}/export | JSON, CSV and reproducibility manifest for the investigation |

Define a clear asynchronous response for a GET that cannot finish within its budget, or have it return a problem directing the client to create a job. Do not leave an unbounded computation hanging behind a simple query. Return 202 with a status location for accepted jobs; the ready result can later return 200.

Validate supported identifiers, date order, actual coverage, allowed geometry size, parameter binding, and analysis settings. Never accept arbitrary file paths or arbitrary source URLs through scientific query parameters. Use RFC 9457 problem details for failures, with stable error codes such as CACHE_MISS_OFFLINE, UNSUPPORTED_BINDING, INSUFFICIENT_SUPPORT, and INCOMPATIBLE_COMPARISON. [[86]](../15_references_and_dataset_directory/README.md#ref-86)

## 10 4 Result object fields

**Table 18  Result object fields**

| Result block | Required content |
| :--- | :--- |
| identity | result_id, schema_version, normalized query and creation timestamp |
| region | id, display label, region type, geometry version and hash, area and mask definition |
| parameter | id, scientific definition, quantity, canonical unit, display unit and temporal statistic |
| data_support | requested and retained interval, sample count, native support, valid-area coverage and exclusions |
| series | Original and eligible values or immutable series references; QA and imputation masks |
| mann_kendall | S, variance, Z, p value, method and p-value convention; nulls when unsupported |
| theil_sen | slope, unit, intercept, reference time, slope interval and interval method |
| fitted_band | Dates, lower and upper values, pointwise or simultaneous label and method |
| seasonal | Settings, components, diagnostic-only flag and imputed observations |
| diagnostics | Dependence, coverage, sampling, transitions, eligibility and warnings |
| evidence | Direction, status, alpha, applicable q value, correction family and interpretation reason |
| provenance | dataset_id, collection and granule ids, version, source_url, DOI, retrieved_at, cache lineage and checksums |
| reproducibility | Code revision, environment versions, boundary and policy hashes, seed and method settings |
| claims | Approved typed facts and JSON Pointers allowed in narration |

Use null for unsupported numeric outputs, with a reason. Use exact JSON numbers where finite and prohibit NaN or infinity in serialized responses. Include display-ready rounded strings as derivatives of canonical values when needed for bilingual consistency; they do not replace the original values.

Define provenance.access_mode as live, cache, or fixture. This API's production scientific results use cache because requests never acquire upstream data. An acquisition record can independently state that its original retrieval was live. Fixture outputs are restricted to explicit test runs and are never substituted into a user's environmental investigation.

Use source and derived inventories compatible with STAC concepts where helpful: asset identifiers, geometry, dates, checksums, links, and processing lineage. STAC organizes assets and metadata; it does not verify a trend calculation or make a display tile scientifically valid. [[87]](../15_references_and_dataset_directory/README.md#ref-87)



---

> **Navigation:** [← 09 Interface and Interaction Design](../09_interface_and_interaction_design/README.md) | [Table of Contents](../README.md) | [11 Constrained Narration in English and Bangla →](../11_constrained_narration_in_english_and_bangla/README.md)
