# Earth System Trend Detective — code, data, and specification audit

Audit date: 1 October 2026. Reviewed package: `earth-system-trend-detective(1).zip`.

**The principal blocker is data authenticity. The application generates synthetic time series during normal operation and presents them with NASA/NOAA collection metadata, quality flags, scientific evidence, and retrieval dates. This version does not meet the requirement to use real provider data. Its statistical results should not be used as Earth-system findings.**

The project has a useful structure to retain: separate FastAPI and Next.js applications, a flat MapLibre map, explicit parameter/binding/policy registries, basic Mann–Kendall and Theil–Sen kernels, a direct paired-difference comparison concept, and local English/Bangla templates. The main work is making those pieces enforce their scientific contracts and replacing generated data with verified acquisition and aggregation.

## Scope and limits

I inspected the supplied archive, application source, included data, tests, and bundled research/implementation document. I ran the existing backend tests, frontend type check and production build, packaging checks, and targeted API/data probes. Mutating probes ran in an isolated copy. The original uploaded ZIP remains untouched; application source was not repaired during this audit.

The live artifact at <https://claude.ai/artifact/PUnJNpKuEXRbvKafSgU6fA> remained behind a Cloudflare security-verification page. Consequently, I could not verify its exact rendered appearance or establish that the bundled specification is identical to that artifact. The bundled specification was reviewed as a separate supplied document. The local frontend also could not be opened through the browser environment, so UI findings below come from source analysis and build checks, not a completed visual or accessibility audit.

All code references below are relative to the project root inside the ZIP. The accompanying `Earth_System_Trend_Detective_Audit_Evidence.json` records file hashes and reproduced probes. Findings are marked **reproduced**, **source-confirmed**, or **gap** to distinguish measured failures from unimplemented requirements.

## What was actually supplied and verified

| Check | Result | Meaning |
|---|---|---|
| Archive | 125 members; 32,337,334 uncompressed bytes | Audited the supplied package, not a different repository revision. |
| Archive SHA-256 | `640956d5e2388aad0414c968f0de641e54887748b3005f2ee9d93ab4404fbc95` | Identifies the reviewed input. |
| Geographic inventory | 261 GeoJSON features; 256 registered region IDs | Feature count and unique selectable registry count are different. |
| Scientific registry | 7 parameters; 7 bindings | Much narrower than the bundled multi-domain catalogue. |
| Cached time series | 30 Parquet files | 10 MERRA-2; 6 MODIS day; 6 MODIS night; 6 POWER; 2 OISST. |
| Source lineage | No raw scientific assets, manifest files, or Zarr stores in the archive | Provider metadata cannot establish the origin of the cached values. |
| Original SQLite | `cached_series`: 0 rows; `completed_results`: 7 rows | The shipped index does not describe or checksum the 30 series. |
| Generator reproduction | 26 generated files exactly matched packaged DataFrames | Direct evidence that those supplied records came from the bundled synthetic generator. The other 4 were not independently matched by this probe. |
| Backend tests | 25 passed | Passing tests do not establish real-data authenticity or scientific end-to-end correctness. |
| Frontend TypeScript | Passed `tsc --noEmit` | Static compilation succeeded despite extensive `any` use. |
| Frontend production build | Passed `npm run build` | Root route approximately 286 kB; first-load JavaScript approximately 389 kB. |
| Frontend lint | Not operational | `npm run lint` prompted for configuration and exited unsuccessfully. |
| Installed backend wheel | Import/launch contract broken | Wheel builds, but packaged imports do not work outside the source checkout. |

The backend test environment used Python 3.11-compatible dependencies resolved in an isolated environment, including NumPy 2.3.5, SciPy 1.17.0, pandas 2.2.3, PyArrow 25.0.1, FastAPI 0.142.2, Pydantic 2.13.5, and pytest 9.1.1. Tests emitted two environment/deprecation warnings; this was not a clean install from a backend lockfile because no such lockfile was supplied.

## Priority and release decision

**P0** means a blocker to trusting or exposing scientific results. **P1** means a correctness or core-functionality defect that must be addressed before a credible scientific release. **P2** means an engineering, usability, or scope improvement.

| Priority | Finding | Main location | Required outcome |
|---|---|---|---|
| P0 | F01 Synthetic records masquerade as provider data | `backend/src/cache/store.py` | Remove generation from production reads/startup; use verified source assets. |
| P0 | F02 Acquisition and readiness claims lack evidence | `backend/src/ingest/`, `registry/bindings.py`, `api/coverage.py` | Build source adapters and derive readiness from validated manifests. |
| P0 | F03 Binding confusion and cache-path escape | `api/trend.py`, `api/comparisons.py`, `cache/store.py` | Shared compatibility validation and confined, opaque asset paths. |
| P0 | F04 QA, coverage, and eligible-year gates are bypassed | `api/trend.py` | Run inference only on eligible, correctly aggregated observations. |
| P0 | F05 Result identity is mutable and provenance is fabricated | `cache/hasher.py`, `cache/store.py`, `api/trend.py` | Content-based identities and immutable, verifiable results. |
| P1 | F06–F09 Evidence-state crashes, dependence, uncertainty, nonfinite exports | `api/trend.py`, `compute/`, `narration/claims.py` | One coherent statistical and serialization contract. |
| P1 | F10–F13 Comparisons, narration, and geographic support mislead | `api/comparisons.py`, `narration/`, frontend investigation components | Compatible comparisons and statements grounded in the frozen result. |
| P1 | F14–F17 Geometry, spatial aggregation, scientific map, FDR incomplete | `registry/regions.py`, `compute/spatial.py`, `api/layers.py` | Correct spatial support and actual numerical map products. |
| P1 | F18–F25 UI state, missing analysis, offline, packaging, deployment | Frontend application and build/configuration | Reliable interaction and a reproducible operating contract. |
| P2 | F26–F29 Performance, accessibility, documentation, catalogue scope | Frontend and documentation | Measured usability and accurate capability claims. |

## Detailed findings and fixes

### F01 — P0 — Production generates synthetic scientific data

**Reproduced.** `backend/src/cache/store.py:48` invokes `_ensure_calibrated_cache_seeded()` whenever a store is constructed. `load_series()` invokes `_seed_series_for_region()` for missing registered-region data. These routines manufacture baselines, warming rates, Gaussian noise, quality flags, and coverage percentages. They do not retrieve or aggregate NASA/NOAA observations. Calling the seed routine in an empty data root exactly reproduced 26 supplied Parquet DataFrames.

The general fallback also produces temperature-like values for IMERG precipitation and GISTEMP anomalies. Missing precipitation returned HTTP 200 with 1980–2024 values around 15.9, labelled `mm`, although its binding starts in 2000. The generated records are still supplied with collection citations and a supported trend badge. Dynamic generation uses Python's salted `hash(region_id)`, so its advertised determinism also fails across processes.

**Fix:** Delete both generation calls from production. Separate artificial numerical fixtures into tests with unmistakable labels and isolated data roots. Quarantine the supplied generated cache and completed results. A missing or unverified real asset must return a typed unavailable/cache-miss response without writing replacement data. Remove scientific-verification claims until the underlying data is verified.

**Acceptance:** Starting or querying an empty cache creates no scientific series. Missing IMERG/GISTEMP/OISST data returns a documented unavailable state; no random-number generator can be reached from a production analysis request.

### F02 — P0 — Provider acquisition, lineage, and readiness are missing

**Source-confirmed gap.** The only acquisition script is `backend/src/ingest/fetch_world_geojson.py`, which fetches boundaries. There are no scientific product download/normalization adapters, raw granules, acquisition manifests, or implemented Zarr reader. `DatasetBinding.availability_state` defaults to `analysis_ready`; all seven bindings claim this state, including products with no packaged cache. `/coverage` primarily uses static binding metadata and file existence, not verified per-region support.

**Fix:** Implement explicit acquisition jobs for each supported product. Store exact collection/version/variable, granule identifiers, source URLs, actual retrieval times, SHA-256 hashes, units, time bounds/calendar, CRS/grid, QA rules, conversion history, and derived-asset checksums. Maintain separate provider record availability and locally acquired/validated coverage. Promote a binding through `catalogued → acquired → validated → analysis_ready → display_ready` only when its required artifacts pass checks.

NASA Earthdata MCP can support discovery and granule verification; Earthdata-authenticated acquisition should happen in a separate ingestion workflow. It must not silently fetch or fabricate data during an offline trend request. [8]

**Acceptance:** Every exposed series is traceable to named provider assets and repeatable transformations. Manifest tampering or checksum mismatch rejects the asset. Catalogued products stay visible but disabled with an accurate reason.

### F03 — P0 — Parameters can be relabelled, and comparison bindings escape the cache

**Reproduced.** `api/trend.py` checks whether a binding exists but does not require `binding.parameter_id == parameter_id`. Requesting precipitation with `NASA_MERRA2_M2TMNXSLV` returns temperature data labelled as precipitation in millimetres. `api/comparisons.py` does not even require the supplied binding to be registered. An SST comparison over Bangladesh/USA using a MERRA-2 binding returned HTTP 200.

`cache/store.py:get_series_path()` interpolates the binding directly into a filesystem path. A comparison with binding `../../audit-path-probe` created `audit-path-probe_BGD.parquet` and `audit-path-probe_USA.parquet` outside `data/cache` in the isolated audit copy. The demonstrated issue is a filesystem escape within the application's write permissions; arbitrary code execution was not tested or established.

**Fix:** Use one resolver for trend, comparison, coverage, and layers. Require registered bindings, matching parameters, compatible spatial support, supported aggregation/policy, and valid intervals. Reject unknown policy IDs rather than silently selecting the temperature policy. Resolve opaque manifest asset IDs to paths; enforce that resolved paths, including symlinks, remain beneath the configured cache root.

**Acceptance:** Incompatible or unknown bindings/policies return structured 4xx responses before any file operation. Traversal inputs cannot read or create files outside the allowed data root.

### F04 — P0 — Quality and time-support rules are not enforced

**Reproduced.** `api/trend.py:150–197` sends cached `value_display` rows directly into inference and counts rows as eligible years. It does not filter `qa_passed`, enforce annual coverage thresholds, implement maximum missing gaps, or aggregate monthly/daily input. Setting every row to `qa_passed=False` and 0% coverage still produced `supported_increase`. Supplying 48 monthly rows spanning only 2020–2023 produced a supported climate trend with a sample count of 48 and duplicate integer years.

The endpoint defaults every parameter to `standard_climate_temperature`; product-specific policies and declared baselines are largely disconnected. Numerical inference also uses rounded display values rather than full scientific precision.

**Fix:** Apply fill/QA decoding, finite-value checks, spatial support, product-specific temporal aggregation, unique timestamps, annual eligibility, record span, and gap rules before inference. Distinguish valid sample count from calendar-year span. Integrate rates over actual time bounds for accumulation products; weight averages correctly. Preserve full precision and round only for display. Treat minimum-duration thresholds as explicit project policies, not universal provider requirements.

**Acceptance:** All-QA-failed data cannot receive a supported badge. Four years of monthly observations remain a four-year record. The exported eligibility table explains every excluded interval and the policy actually used.

### F05 — P0 — Results are not immutable or fully reproducible

**Reproduced.** `cache/hasher.py` omits source-data content/version, geometry/mask hashes, full policy values, aggregation details, and environment identity. `api/trend.py` stamps a constant retrieval date (`2026-09-15T08:00:00Z`) and code revision (`v1.0.0`). `cache/store.py:save_result()` uses `INSERT OR REPLACE`.

Changing input values changed the estimated slope from **0.299575** to **0.526848 °C/decade**, but the result ID remained identical. Retrieving the old ID then returned the new series. Its creation timestamp was also replaced. This is a direct failure of the frozen-result contract.

**Fix:** Hash the normalized scientific request plus verified input asset digests, geometry/mask, full policy/configuration, actual code revision, units/conversions, aggregation, baseline, and random seed. Persist results append-only. Reuse an existing verified result instead of recomputing it. Save real acquisition timestamps in manifests. Use transactional/atomic writes and an explicit schema migration strategy.

**Acceptance:** Changed scientific inputs create a new identity or are rejected as corrupted. A saved ID never changes its series, statistics, provenance, or creation time. A fresh environment can reproduce the numerical result from its recorded assets and policy.

### F06 — P1 — Valid shorter requests crash, and evidence states disagree

**Reproduced.** A Bangladesh 2010–2024 request returns HTTP 500. The endpoint emits `limited` for 10–19 samples, while `narration/claims.py:32–38` excludes `limited` from its literal enum. Adding the enum alone is insufficient: English/Bangla template fallbacks can describe unhandled states as flat, and the frontend result panel lacks an explicit `flat` case. Generic interpretation text also turns several unsupported/limited conditions into a statement about nonsignificance.

A missing SST region separately returns HTTP 500 because the fake-data branch calls Python `max()` on a NumPy array. Remove that branch rather than repairing it to manufacture more data.

**Fix:** Define a shared evidence-state schema with reason codes and complete mappings in API responses, both narration languages, and UI. Keep record insufficiency, exploratory evidence, nonsignificance, numerical degeneracy, and a supported direction distinct.

**Acceptance:** Short, constant, incomplete, missing, and ordinary records all produce documented responses without 500 errors or invented flatness claims.

### F07 — P1 — Dependence diagnostics miss strong later-lag correlation

**Reproduced.** `compute/serial_corr.py:84–101` stops adjustment at the first nonsignificant lag. For a repeated `[1, 1, -1, -1]` sequence, lag-1 correlation was approximately 0.0127, but lag-2 was −1 and lag-4 was +1. The function nevertheless returned `is_autocorrelated=False`, no significant lags, and VIF 1. Its diagnostics compute later correlations without incorporating them into the reported significant-lag set.

**Fix:** Specify and validate the exact published dependence method and lag-selection rule. Test it against an independently implemented reference and realistic correlated series. Use actual eligible timestamps and documented gap handling. Disclose the current VIF floor and the `>1.05` classification threshold if retained as policy choices; do not present such choices as an unspecified canonical Hamed–Rao implementation.

**Acceptance:** Strong dependence at a later evaluated lag is reported even when lag 1 is weak. Irregular or gapped records do not silently receive a regular-grid adjustment.

### F08 — P1 — Uncertainty methods are inconsistent with dependence handling

**Source-confirmed.** `compute/uncertainty.py:132` resamples residuals independently, even when the endpoint detects autocorrelation. The Sen slope confidence interval is calculated separately before the Mann–Kendall variance adjustment. Adjusting the test statistic does not automatically make the slope interval or fitted-line band valid under dependence.

**Fix:** Declare separate methods and assumptions for the monotonic-trend test, slope interval, and fitted-line band. Implement an appropriate dependence-preserving procedure, with explicit block/lag settings and gap handling, or withhold unsupported uncertainty. Calibrate coverage on realistic independent and correlated fixtures. Identify pointwise confidence bands separately from prediction intervals and simultaneous bands. SciPy explicitly describes its Theil–Sen interval as a slope interval. [5]

**Acceptance:** The result records uncertainty method, settings, success count, and limitations. The UI draws a band only when `is_valid` and its interpretation are supported.

### F09 — P1 — Missing values corrupt support counts and JSON exports

**Reproduced.** With one `NaN` inserted, the trend endpoint reported 45 samples despite only 44 finite values and retained the invalid endpoint year. The HTTP response represented the missing value as null in the tested FastAPI version, while the saved/exported JSON contained literal `NaN`, which is invalid standard JSON. The frontend assumes every value is a number and calls numeric formatting on it.

**Fix:** Use one explicit eligible-data mask across calculations, support summaries, narration, and exports. Represent unavailable points as nullable values with exclusion reasons; preserve raw and eligible series separately. Serialize with strict finite-number validation, such as `allow_nan=False`. Handle null points, chart gaps, invalid intervals, and unavailable statistics in typed frontend models.

**Acceptance:** Exports parse with a strict JSON parser. Counts and retained dates match eligible observations. A missing point never becomes a plotted zero or a runtime formatting error.

### F10 — P1 — Comparisons bypass the main scientific policy

**Source-confirmed and partly reproduced.** `api/comparisons.py` intersects sets of integer years and subtracts sorted arrays rather than joining unique eligible timestamps. Duplicate/monthly rows can therefore misalign or have incompatible lengths. It only requires three shared years, ignores the requested policy, does not enforce product/geometry compatibility, and uses unadjusted Mann–Kendall inference. Its direction label is always “warming faster,” even for precipitation; an exactly zero slope returns numeric `0` instead of a direction enum.

**Fix:** Reuse the validated aggregation and inference pipeline. Inner-join on complete eligible time keys and identical units, product version, temporal statistic, and baseline where relevant. Analyze the paired difference directly; retain this useful existing concept. Apply contrast-specific record/dependence/uncertainty gates and use parameter-neutral direction labels. Freeze/export the contrast with its own provenance and result identity.

**Acceptance:** Both regions and the difference use precisely the same accepted dates. Invalid support or short records cannot receive stronger claims than the primary trend pipeline allows.

### F11 — P1 — The comparison UI silently changes the investigation

**Source-confirmed.** `frontend/components/investigation/chart_area.tsx:94–101` submits region IDs and parameter only. It omits the displayed result's time window, binding, and policy. A selected-window chart can therefore show a full-record/default-binding comparison. Comparison state is not reset when the main result or target changes, and non-2xx errors are not shown.

**Fix:** Submit the frozen normalized context, preferably the source result ID plus validated contrast options. Clear/cancel stale comparison state when any input changes. Show requested versus retained common intervals and actionable failures. Plot both accepted series and their paired difference in addition to numerical summaries.

**Acceptance:** Comparison context matches the displayed investigation, and an earlier contrast cannot remain visible under a new region/parameter/window.

### F12 — P1 — Narrative safeguards do not validate numerical facts

**Reproduced.** `narration/validator.py` primarily checks forbidden English phrases, list length, sign words, and whether a slope pointer is non-null. It does not compare the claim or formatted text with the actual pointed value. A deliberately false narrative containing a 999-degree rate, an invented p-value, and 100% coverage passed validation. `api/trend.py:370` ignores the validator's returned boolean/errors and does not validate Bangla output.

**Fix:** Build approved claims from the completed frozen result. Validate exact field binding, numeric formatting, units, dates, evidence state, geographic support, and both languages. Treat validation failure as a failed narration step, not a publishable sentence. Local templates can remain the default; any optional language model should only render approved claims. Remove “Zero Hallucination Safe” guarantees.

**Acceptance:** Altering any bound fact makes validation fail. Neither language can state support, causation, or completeness that the scientific result does not establish.

### F13 — P1 — Narration confuses totals, points, flatness, and country support

**Source-confirmed.** Templates use “annual mean” for annual-total precipitation. POWER point data is narrated as a value “in Bangladesh,” without making its single-point support prominent; absent area-coverage fields default to 100%. Stored POWER coordinates are not consistently exposed as the analyzed point. A numerical example `[0,3,2,1]` has Sen slope −1/3 per year but Mann–Kendall `S=0`/direction `flat`, so wording based only on the test direction can imply zero physical change despite a nonzero estimate.

**Fix:** Render the actual temporal statistic and observation type. Identify point coordinates explicitly and never claim country-area coverage for a point. Separate estimated slope direction from whether a test supports a monotonic trend. State inconclusiveness without equating it to a zero trend. Use unavailable/null wording rather than default zero confidence limits.

**Acceptance:** Precipitation uses accumulation terminology; POWER names its location; nonsignificance never becomes proof of no change.

### F14 — P1 — Region areas and centroids are incorrect

**Reproduced.** `registry/regions.py:93–130` labels the midpoint of a longitude/latitude bounding box as the centroid and estimates area from rectangle dimensions times a constant. The USA was returned near longitude **+0.3187°** with area **162,539,584.5 km²**. Fiji was returned at longitude 0° with area **28,676,285.7 km²**. These values expose antimeridian and polygon-support errors. Ocean regions also inherit an inappropriate generic country geometry citation/version.

**Fix:** Use a versioned analysis geometry with actual polygon area, an appropriate representative point, and antimeridian-aware bounds. Distinguish display boundaries from analysis masks. Record the precise boundary source/hash, ocean support, islands/holes, and treatment of disputed/overseas features. A point-sampling coordinate should be intentionally selected and recorded, not assumed to be a valid polygon centroid.

**Acceptance:** USA/Fiji dateline cases produce sensible areas, interior representative points where required, and compact map bounds. Returned metadata matches the exact geometry used for analysis.

### F15 — P1 — Country aggregation is declared but not connected to data

**Source-confirmed gap.** `compute/spatial.py` contains an area-weighting kernel, but the production trend route never uses it. Cached region values are manufactured rather than derived from masked provider grids. Polygon intersection fractions in geographic degree coordinates multiplied by spherical full-cell area are an approximation, not exact geodesic intersections, and the current kernel does not cover all native grids such as MODIS sinusoidal tiles.

**Fix:** Implement product-native grid bounds, suitable area calculations/intersections, valid-cell QA, and fixed land/ocean support before regional aggregation. Preserve valid-area denominators and temporal coverage. Define intensive means versus extensive totals by variable; multiplying by area is appropriate for densities, not arbitrary already-per-cell totals. Add dateline, polar, islands, holes, partial-cell, and different-CRS fixtures.

**Acceptance:** A small real provider-grid fixture produces a independently checked regional aggregate, with visible accepted area and a reproducible mask hash.

### F16 — P1 — Scientific map layers do not exist

**Reproduced gap.** `/layers/{id}/tilejson` advertises `/tiles/...` URLs, but there is no corresponding tile route or asset. `/tiles/merra2_trend_slope/0/0/0` returned HTTP 404. The frontend renders geographic outlines and selection highlighting, not scientific numerical layers. There is no connected observed-value/anomaly/slope/evidence/coverage layer, numeric legend, cell inspector, or time-window-dependent map product. A configured nodata value of zero also conflicts with a legitimate zero trend.

**Fix:** Build derived numerical fields from the same verified dataset/window/policy as the regional result. Persist arrays and display pyramids/tiles; provide a working local delivery path. Connect layer selection, units, legend limits, coverage/evidence, dates, and numeric inspection in MapLibre. Use an explicit nodata mask. Keep the existing 2D approach; a globe is unnecessary. mapcn is an optional UI component layer, not a scientific data pipeline.

**Acceptance:** Every advertised layer URL resolves; inspected numbers agree with stored fields; changing the analysis window changes the map product and its identity.

### F17 — P1 — Spatial significance and FDR are not wired up

**Source-confirmed gap.** `compute/multiple_testing.py` exists but is not connected to a scientific p/q field or display layer. A large number of cell tests cannot be presented as ordinary per-cell p<0.05 findings without a defined testing family and interpretation.

**Fix:** Define the tested domain and eligible-cell family in the analysis manifest, compute raw p and adjusted q fields under a documented correction, and store the domain/mask/policy identity. Keep correction independent of current zoom or viewport. Distinguish the trend of an area-mean series from the mean of individual cell trends; these are different calculations.

**Acceptance:** Panning/zooming does not change a cell's q-value or significance. Regional and cell-level findings clearly identify their different support.

### F18 — P1 — Parent renders can destroy and recreate the map

**Source-confirmed.** `frontend/app/page.tsx` recreates the selection callback on each render, and `components/ui/map.tsx` includes that callback in the map-construction effect dependencies. Loading/result/language updates can therefore tear down and rebuild the map. Existing loading and asynchronous highlighting state can refer to a previous map instance.

**Fix:** Give the map a stable lifecycle, keep callbacks stable with `useCallback` or a callback ref, and update sources/selection through dedicated effects. Cancel pending geometry updates on cleanup and maintain accurate loaded/error state. Verify camera and selection persistence in a rendered browser.

**Acceptance:** Completing a query or toggling language does not construct another map or lose the camera position.

### F19 — P1 — Map selection and form selection diverge

**Source-confirmed.** `selection_rail.tsx` initializes draft query state from props once but does not synchronize it. A map click can commit a new region while the form still contains the previous region; pressing Run can undo the visible selection.

**Fix:** Define one explicit state model for draft versus committed investigation. Synchronize map-driven changes, preserve intentional dirty fields, and display which query the current result belongs to. Generate available regions, bindings, and intervals from verified metadata.

**Acceptance:** A map click, keyboard form change, and Run action resolve to the same intended region and window.

### F20 — P1 — Old requests can overwrite new results

**Source-confirmed.** `app/page.tsx` fetches trends without cancellation or request identity. A slower earlier request can replace the response for the latest query. Failed/new queries can leave an old result visible beneath a new map/form context. Some metadata-fetch failures are silently ignored.

**Fix:** Use `AbortController` and monotonically increasing request identity or a query-cache key. Keep displayed results bound to their normalized query/result ID. Clear or visibly mark stale content, and show errors/retry/unavailable-cache actions. Apply the same pattern to comparison and geometry fetches.

**Acceptance:** Intentionally resolving requests in reverse order still leaves the newest requested investigation visible and correctly labelled.

### F21 — P1 — Seasonal and timeline capabilities are placeholders

**Source-confirmed gap.** The seasonal tab displays explanatory text rather than computed diagnostics. `compute/seasonal.py` is not connected to an endpoint/result. Annual-only caches cannot produce a meaningful monthly seasonal decomposition. The selection rail hard-codes 1980–2024 instead of using actual validated availability; it excludes earlier GISTEMP coverage and includes unsupported windows for other products. The map has no scientific playback timeline.

**Fix:** Acquire eligible monthly data and connect seasonal methods with method-specific completeness/length rules. Make annual/monthly/seasonal aggregation explicit where supported. Drive interval controls from actual local support. Implement numerical time playback only when display fields exist; disable unfinished modes with clear reasons.

**Acceptance:** A seasonal view contains computed, traceable components or an honest unavailable state. The UI cannot request a falsely available year.

### F22 — P1 — Offline status is a label, not a verified operating mode

**Source-confirmed.** `app/layout.tsx` loads Google Fonts externally, while the page/drawer display hard-coded offline claims. Backend health reflects an environment setting rather than verified guard/assets. The socket guard only patches a narrow Python connection method; it does not establish DNS/UDP/browser/subprocess-wide network isolation. There is no service worker providing a fully offline hosted-browser application.

**Fix:** Define offline scope precisely: a local application with reachable local services differs from an offline cached hosted page. Self-host fonts, basemap assets, scripts, and workers. Derive status from actual configuration and data readiness. Test the complete application under denied external network access; enforce egress at an appropriate runtime/container layer if this is a required guarantee. If adopting mapcn, its default basemap/worker are external; follow its documented self-hosting instructions, including both worker module files. [6]

**Acceptance:** With outbound access disabled, the intended local workflow renders and computes using verified local assets, and missing data produces a truthful unavailable response.

### F23 — P1 — Backend packaging does not support a clean installed launch

**Reproduced.** The wheel contains top-level `main.py`, `api/`, `cache/`, and other modules, while source code relies on the `src` package and package-relative imports. In an isolated installed layout, `src.main` fails with `ModuleNotFoundError`; importing `main` or `api.trend` fails on relative imports. A successful wheel build is therefore not a working distribution.

**Fix:** Use a named application package and explicit build-system/package-discovery configuration. Resolve data paths through deployment configuration/package resources rather than checkout-specific parent walking. Document an actual install and startup command and test it outside the repository.

**Acceptance:** A fresh virtual environment can install the built wheel, locate configured assets, and launch the API without the source checkout on `PYTHONPATH`.

### F24 — P1 — Deployment architecture does not match the stated target

**Source-confirmed gap.** `frontend/next.config.mjs` proxies API traffic to localhost:8005 and does not configure static export. FastAPI does not serve a compiled frontend. The current application therefore requires separate Node and Python services. This is a valid possible architecture, but it is not the requested single-port static-frontend/FastAPI distribution described in the bundled specification. CORS lists other development ports and needs review if a direct cross-origin API arrangement is chosen; same-origin Next rewrites currently avoid that particular issue.

**Fix:** Select and document one deployable contract. For a unified local/offline package, use a compatible static Next export plus local FastAPI routes/static assets. Otherwise manage both services explicitly and make proxy/base-URL/health configuration environment-driven. Include data provisioning and shutdown/startup behavior.

**Acceptance:** A clean deployment starts through one documented procedure and all frontend/API/static/layer URLs resolve under its intended origin.

### F25 — P1 — Framework target, dependency locking, lint, and test coverage need correction

**Reproduced/source-confirmed.** The frontend lock resolves Next **15.5.27**, React **19.3.0**, Tailwind **3.4.19**, and MapLibre **5.24.0**. It is not a Next 16/Tailwind 4/mapcn implementation. The installed Next version should not be called unpatched: the official 30 September 2026 release lists 15.5.27 as a patched maintenance version and 16.3.8 as the patched active version. A requested Next 16 migration should use a verified patched release rather than assuming 16.3.6 is sufficient. [7]

Backend dependencies use unbounded minimum ranges without a reproducible lock. Lint has no configuration and uses deprecated `next lint`. Existing tests mainly cover kernels and happy paths; they allow a fake-data implementation to pass. Frontend interaction checks and source-authenticity gates are missing.

**Fix:** Lock tested Python/Node environments, migrate deliberately to the agreed framework target, use a noninteractive ESLint command/configuration, and add the targeted regression cases in the checklist below. Preserve the working type/build checks.

**Acceptance:** Clean install/build/lint/test commands run unattended in CI and enforce data authenticity, not a predetermined warming direction.

### F26 — P2 — Geography delivery and analysis scaling need work

**Source-confirmed.** The frontend uses a roughly 13.6 MB country GeoJSON and fetches/parses it again for highlighting. Frequent mouse movement drives state updates; map recreation further magnifies the cost. Pairwise Sen calculations and 500 bootstrap fits also require an explicit size/job policy before raw daily/global analysis is enabled.

**Fix:** Reuse parsed geography or serve appropriate local vector assets, select by stable feature ID, throttle hover, and handle container resize/map errors. Precompute shared scientific fields and cache verified frozen results. Bound synchronous jobs by supported cadence/size; use controlled acquisition/analysis jobs for larger products.

**Acceptance:** Measure network bytes, map lifecycle, interaction latency, and analysis cost on target hardware. Do not claim performance from a successful build alone.

### F27 — P2 — Accessibility and multilingual semantics are incomplete

**Source-confirmed; rendered validation pending.** The provenance drawer lacks a complete modal/focus/Escape contract, some icon controls lack accessible names, charts lack a keyboard-readable alternative, and document language remains English when Bangla is selected. Numeric null fallbacks and evidence text require parallel language review.

**Fix:** Add correct dialog/label semantics, focus management, keyboard map/form alternatives, an accessible data table, status announcements, and dynamic document language. Verify contrast, focus order, reflow, and screen-reader output in a browser.

**Acceptance:** The complete investigation and export workflow works with a keyboard and understandable English/Bangla accessible text. This audit did not establish visual WCAG conformance.

### F28 — P2 — Documentation and API types overstate implemented behavior

**Source-confirmed.** README/docstrings claim rigorous real caches, Zarr access, immutable results, exact scientific safeguards, offline operation, and other behaviors that are absent or contradicted by the implementation. Some documentation uses machine-specific Windows links. Core endpoint dictionaries and frontend `any` types allow evidence-state and nullable-value mismatches to escape compilation. Displayed version labels are not consistently tied to installed software.

**Fix:** Generate typed response models and frontend types from a shared OpenAPI/schema contract. Add strict validation at cache-load and result-save boundaries. Rewrite capability statements from a measured implementation matrix; distinguish implemented, catalogued, and planned features. Repair portable links and collection/dependency attribution notices.

**Acceptance:** Documentation startup/capability claims reproduce on a clean install, and schema generation catches incompatible states/nullability before release.

### F29 — P2 — The Earth-system catalogue remains narrow

**Gap relative to the bundled specification.** Seven parameters cover temperature variants and precipitation, while the document describes a much wider multi-domain catalogue. Vegetation, water storage, cryosphere, atmospheric composition, radiation, and derived indicators are not implemented. This is a scope gap, not justification to enable every product through a generic fallback.

**Fix:** Make a deliberate supported catalogue. Start with a small set of fully authentic and scientifically validated products; list later domains as catalogued with acquisition/readiness reasons. Add each adapter with its own units, support, QA, cadence, inference policy, and display product. Never imply that an unimplemented parameter is analysis-ready.

**Acceptance:** The product accurately states which Earth-system questions it can answer and why each unavailable parameter is unavailable.

## Dataset-specific corrections

The table separates verified provider facts from implementation work. A valid citation attached to a generated series does not make that series real.

| Product | Correction required |
|---|---|
| **MERRA-2 M2TMNXSLV / T2M** | The binding's DOI `10.5067/0JRLVL8YV2Y4` identifies M2TMNXFLX, a different monthly collection. NASA gives **`10.5067/AP1B0BA5PD2K`** for M2TMNXSLV. Correct both DOI and citation. Acquire actual T2M grids, decode source metadata, preserve Kelvin scientific values, apply appropriate monthly-to-annual weighting, and aggregate the versioned region mask. [1] |
| **MODIS MOD11A1 V061 day/night LST** | These are clear-sky land-surface retrievals, not 2 m air temperature. Apply each product's fill/scale metadata and `QC_Day`/`QC_Night` bit rules, account for observation/clear-sky support, handle the native sinusoidal grid, and distinguish partial first-year coverage. A fixed 95% coverage field is unsupported. Keep day and night separate. [2] |
| **GPM IMERG Final V07 precipitation** | Replace the temperature fallback. Verify the chosen Final-run collection/version and granule coverage. Decode each selected format's actual units/scaling; convert rates to accumulated depth using real time bounds where applicable. Require sufficient completeness for annual totals and do not invent pre-product years. NASA documents format-dependent rate/accumulation units. [3] |
| **NOAA OISST v2.1** | Acquire actual daily 0.25° fields and relevant support/error/sea-ice metadata; preserve version transitions and ocean masks. NOAA describes an interpolated, blended analysis, not independent satellite observations at each grid cell. Its record begins 1 September 1981, so a full annual record and provider record start are different concepts. Avoid applying scale factors twice when a library already decodes them. [4] |
| **NASA POWER point T2M** | Preserve the exact requested and returned coordinates, source response/units/time keys, fill handling, and valid-day counts. Mark support as a point sample; do not represent it as a country-area aggregate or 100% national coverage. Replace guessed point histories and bbox-based coordinate selection. |
| **GISTEMP v4 anomaly** | Acquire the actual selected global/zonal/grid product. Preserve NASA's **1951–1980 anomaly baseline** and the product's spatial support. An anomaly is a difference; it must not receive an absolute Kelvin-to-Celsius offset. The binding DOI `10.2797/110915` was not verified through NASA's published citation instructions; remove or replace it only with a verified product citation rather than treating it as authoritative. [9] |

For every source, store **provider availability**, **local acquisition interval**, **eligible analysis interval**, and **display-ready interval** separately. Hard-coded 2024 end dates are acceptable only as an explicitly frozen local snapshot with its own manifest; they should not be labelled as the provider's current complete record.

## Minimum data and result contract

| Object | Required contents |
|---|---|
| Source manifest | Collection and version; variable; provider/granule identifiers; URLs; actual UTC acquisition times; asset hashes; units; fill/scaling metadata; time bounds/calendar; native CRS/grid bounds; QA definition; licence/citation. |
| Normalized observations | Full-precision value; unique timestamp and interval bounds; validity/exclusion reason; retained native-unit/conversion information; point or grid support; spatial and temporal coverage denominators. |
| Analysis asset | Source manifest digest; geometry/mask digest; spatial aggregation; temporal statistic; eligible intervals; complete policy values; baseline; derived checksum. |
| Frozen result | Content-based ID; immutable creation time; actual code/environment revision; raw/eligible support summaries; numerical estimates and tests; separate uncertainty methods; evidence state and reason; traceable narrative fields. |
| Display asset | Dataset/window/policy/mask identity; numeric arrays/tiles; units and range; nodata mask; coverage; raw p and adjusted q where applicable; fixed testing domain. |

## Ordered implementation backlog

1. **Stop scientific misrepresentation.** Remove production seed/fallback paths, quarantine generated records/results, reject unsupported bindings/policies, confine cache paths, and show truthful unavailable states.
2. **Establish one authentic vertical slice.** Acquire a small real MERRA-2 fixture and a separate POWER point fixture, with verified manifests and independently checked aggregation. Keep point and area support explicit. Reproduce the same values offline from the saved assets.
3. **Make eligibility enforceable.** Connect QA/fill decoding, grid masks, time-bound aggregation, unique dates, annual completeness, gaps, and product-specific policies. Fix shorter-record and missing-data schemas before opening more products.
4. **Freeze the science.** Validate dependence/uncertainty, align comparison policy, derive narrative facts from results, and introduce content-based immutable identities and strict exports.
5. **Complete the scientific interface.** Implement real layers, legends, cell inspection, fixed-domain q fields, supported timeline/seasonal modes, synchronized query state, request cancellation, and comparison context.
6. **Make delivery reproducible.** Repair packaging, choose the deployment contract, lock dependencies, configure lint/CI, remove external offline dependencies, and test the complete application in a rendered browser.
7. **Expand the catalogue deliberately.** Add MODIS, IMERG, OISST, GISTEMP and further Earth-system domains only after each has a verified source and product-specific acceptance evidence.

This ordering is dependency-based; it is not a time estimate or a 48-hour implementation plan.

## Acceptance checks before scientific release

| Check | Passing behavior |
|---|---|
| Empty/missing cache | Typed unavailable response; no manufactured record or file writes. |
| Authenticity | A real provider fixture can be traced to exact raw assets and hashes; values match an independent decode/aggregate. |
| Binding validation | Temperature-as-rainfall, SST-on-land, unknown policies/bindings, and traversal inputs fail before I/O. |
| QA/coverage | All-failed QA and zero valid coverage cannot produce supported evidence. |
| Annual eligibility | Four years of monthly rows remain four eligible years; incomplete totals are rejected or explicitly withheld. |
| Evidence states | Short, limited, flat, inconclusive, and unsupported states are coherent in schemas, templates, API, and UI. |
| Dependence/uncertainty | Lag-2/later-lag dependence is detected; tests and intervals use their declared assumptions and calibrated methods. |
| Missing values | Counts/dates reflect valid observations; strict JSON exports contain no NaN/Infinity; charts preserve gaps. |
| Immutable result | Changed input/policy/mask produces a different identity; retrieving an old ID never changes it. |
| Comparison | Unique common eligible dates, identical units/support/context, frozen provenance, and current-window UI payload. |
| Narration | Wrong numeric fields/units/dates/support fail validation in both languages; failure is enforced. |
| Geography | Dateline, polar, island, hole, and partial-cell cases pass independently checked geometry/area tests. |
| Scientific map | Every advertised layer loads; inspector values match stored numbers; q-values do not change with viewport. |
| UI interaction | Map persists; map/form agree; reversed request completion cannot show an older result under a newer query. |
| Packaging/delivery | Clean installed launch succeeds; documented deployment resolves all assets and APIs. |
| Offline | With external access denied, the stated local workflow works and reports actual local data availability. |
| Accessibility | Keyboard, modal focus, chart table, language semantics, and narrow-screen workflow are validated in a browser. |
| Documentation | Capability/readiness statements match observable implemented behavior. |

The existing 25 passing tests should remain, but tests asserting expected warming on generated caches cannot serve as evidence of scientific correctness. Acceptance fixtures should verify actual provider values and the pipeline's behavior even when the result is flat, decreasing, missing, or inconclusive.

## Primary references checked

1. NASA GMAO, [Citing MERRA-2 data](https://gmao.gsfc.nasa.gov/gmao-products/merra-2/citing-merra-2-data_merra-2/) — collection-specific DOI correction.
2. NASA LAADS DAAC, [MOD11A1 product](https://ladsweb.modaps.eosdis.nasa.gov/missions-and-measurements/products/MOD11A1) — daily LST, day/night retrieval and QA/support context.
3. NASA GPM, [IMERG](https://gpm.nasa.gov/data/imerg) — product runs and format-dependent precipitation units.
4. NOAA NCEI, [Optimum Interpolation SST](https://www.ncei.noaa.gov/products/optimum-interpolation-sst) — native cadence/resolution, record start, blended/interpolated support and ancillary fields.
5. SciPy, [theilslopes documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.theilslopes.html) — slope/intercept definitions and slope confidence-interval scope.
6. mapcn, [Installation](https://www.mapcn.dev/docs/installation) — component installation and self-hosted worker requirements.
7. Next.js, [September 2026 security release](https://nextjs.org/blog/september-2026-security-release) — patched 15.5.27 and 16.3.8 versions at audit date.
8. NASA, [earthdata-mcp](https://github.com/nasa/earthdata-mcp) — collection/granule discovery and acquisition workflow boundaries.
9. NASA GISS, [GISTEMP v4](https://data.giss.nasa.gov/gistemp/) — anomaly baseline, selected product support, version and citation instructions.

Provider documentation checks establish product semantics and citation corrections. They do not authenticate the generated files shipped with this application.
