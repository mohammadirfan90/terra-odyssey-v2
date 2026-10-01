# Earth System Trend Detective — revision 2 verification

Reviewed: `earth-system-trend-detective(2).zip`, 1 October 2026.

**Several specific defects are corrected, but this revision still does not meet the real-data requirement. All 30 scientific Parquet files are byte-identical to the previous package, including the 26 records previously reproduced exactly from its synthetic generator. The added manifests describe those same files. A new chart hook-order regression also breaks the transition from no result to the first result.**

This review compares the delivered archive against the previous 29-finding audit. It verifies changes rather than relying on comments saying a finding is resolved. Application source and uploaded archives were preserved. Mutating probes used an isolated runtime copy and restored modified Parquet files. Artificial probe inputs were audit fixtures only.

Code references below are relative to the delivered project root. The accompanying `Earth_System_Trend_Detective_Revision_2_Evidence.json` contains the archive comparison, probe results, component error, packaging checks, and numerical counterexample.

## Verification summary

| Item | Observed result |
|---|---|
| Updated archive | 134 files; 32,509,157 uncompressed bytes. |
| SHA-256 | `a8d5032c670bb94c23fe893695a9944c37464a4e71933d4a6fb6690a3ecaee0f` |
| Archive changes | 23 changed files; 9 added files; 102 unchanged files; no removals. |
| Scientific Parquet files | All 30 unchanged, byte for byte. |
| Added scientific manifests | 5 JSON inventory/checksum manifests. |
| Raw scientific assets / Zarr | None supplied. |
| Ingestion | Still only a boundary-fetch script; no scientific provider acquisition adapter. |
| Original updated SQLite | 30 indexed series; 9 completed results. |
| Delivered backend tests | **35 passed**, 2 environment/deprecation warnings. README claims 37. |
| TypeScript | `tsc --noEmit` passed. |
| Next production build | Passed; Next 15.5.27; root route about 287 kB; first-load JavaScript about 389 kB. |
| Chart component transition | **Failed:** `Rendered more hooks than during the previous render.` |
| Installed wheel | Builds, but `src.main`, `main`, and `api.trend` imports fail outside the checkout. |
| Targeted API/data probes | 34 recorded checks, including both repaired and still-failing behavior. |
| Full browser visual/accessibility audit | Not completed; the available Playwright runtime lacked a Chromium executable. Component behavior was tested with the actual React component through a renderer. |

The test environment used Python 3.12 and the same isolated dependencies used for the earlier audit. Node dependencies were reused because `package.json` and `package-lock.json` are unchanged. The React component probe used React 19.3.0 and stubbed decorative icons; its hook logic was the supplied component's actual code.

## Improvements verified

| Attempted correction | Verification |
|---|---|
| Remove production record generation | Both generation routines are gone. Missing Nepal series, IMERG, GISTEMP, and Indian Ocean SST now return 404 rather than manufacturing data or crashing. |
| Validate trend binding and policy | Temperature-as-precipitation and an unknown trend policy return 400. |
| Confine cache paths | The previous comparison traversal request returns 400; the store checks allowed identifiers and resolved paths. |
| Enforce basic QA and coverage | An entirely failed-QA record and zero-coverage record each return 422 on `/trend`. |
| Fix row-count-as-years case | Four years of ordinary monthly input now aggregate to four annual observations and receive `insufficient`, not a supported climate badge. |
| Include source bytes and policy in identity | Changing Parquet contents changes the result ID; full policy settings are included. |
| Preserve an existing saved ID | SQLite now uses `INSERT OR IGNORE` rather than replacing stored results. |
| Handle 15-year evidence | The previously crashing request now returns 200 with `limited`. |
| Detect later-lag dependence | The lag-2/lag-4 fixture now reports significant lags and autocorrelation. |
| Filter missing scientific values | A missing first observation is excluded; support is now 44 values beginning in 1981, and that new export has no literal NaN. |
| Correct MERRA-2 citation | The binding and new manifest use `10.5067/AP1B0BA5PD2K`. The unverified GISTEMP DOI was removed. |
| Improve geographic metadata | USA/Fiji areas and representative points are plausible; the old bbox-derived values are gone. |
| Improve interface state | Stable map callback/ref, form synchronization, primary-request cancellation, and comparison error text were added. |
| Remove external font request | Google Fonts links were removed. Dynamic document language, drawer label, Escape handling, and initial focus were added. |

These are useful, testable changes. They do not establish authenticity of the inherited cache or complete the wider scientific contracts.

## Remaining blockers and required fixes

### R01 — Critical — The inherited generated data is still enabled

**Evidence:** All 30 delivered Parquet files match the earlier ZIP byte for byte. The earlier generator-matched set of 26 also matches its recorded SHA-256 hashes in this revision. No real scientific downloads, granule lineage, raw assets, or acquisition adapters were added. The normal Bangladesh request still returns a supported NASA-labelled finding from the same generated series.

**Location:** `data/cache/`, `data/manifests/`, `backend/src/registry/bindings.py`, `backend/src/api/trend.py`.

**Fix:** Quarantine these records and their generated results. Keep the generator removal. Acquire a genuine provider dataset and preserve exact raw-file/granule identifiers, original values, source checksums, timestamps, units, QA, and transformation history. Enable scientific results only after acquisition and validation complete. Hashing a file establishes its byte identity; provider provenance requires traceable source assets.

**Acceptance:** One region's displayed values can be reproduced independently from a named NASA/NOAA asset, and inherited generated records cannot appear as verified findings.

### R02 — Critical — Manifests are indexed but never enforced

**Evidence:** Changing Bangladesh values made the actual file checksum disagree with the manifest, but `/trend` returned 200 and `supported_increase`. A Nepal Parquet file with no manifest entry was also accepted. Removing QA/coverage columns still returned supported evidence with an invented 100% coverage summary.

`LocalDataStore._sync_manifest_index()` trusts JSON entries and inserts them into SQLite. `load_series()` reads any nonempty matching filename without checking manifest membership, expected checksum, schema, units, source identity, readiness, QA requirements, or row inventory. Broad exception handling silently skips malformed manifests; stale index rows are not removed.

**Location:** `backend/src/cache/store.py:91`, `:147`, `:155`; `backend/src/api/trend.py:176`.

**Fix:** Make a validated manifest the gate to loading. Verify its schema and binding/region association, file hash, required columns/types/units/cadence, finite/range constraints, and readiness. Reject mismatches and unknown assets with typed errors. Treat QA/coverage absence according to an explicit source contract rather than assuming complete support. Load/hash from one consistent asset snapshot and refresh the index transactionally.

**Acceptance:** Missing manifest, mismatched checksum, corrupt Parquet, missing required QA, wrong units, or inconsistent inventory are rejected before scientific inference.

### R03 — Critical — Chart hooks break the first-result transition

**Evidence:** `ChartArea` calls five state hooks, returns early for a null result at line 34, then calls another `useState` at line 91 and `useEffect` at line 94 for a populated result. The parent mounts `ChartArea` even while `currentResult` is null. The actual component's null-to-result update produced **“Rendered more hooks than during the previous render.”** Type checking and the production build did not catch this.

**Location:** `frontend/components/investigation/chart_area.tsx:34`, `:91`, `:94`; `frontend/app/page.tsx:191`.

**Fix:** Put every hook before conditional returns and make effects null-safe, or split the populated chart into a child component mounted only when a result exists. Configure the React hook lint rules. Preserve comparison-reset behavior after fixing hook ordering.

**Acceptance:** Render null → result → null → different result on the same mounted component without errors. Test this interaction in addition to building the application. React's official rules explicitly require hooks before early returns. [1]

### R04 — High — Annual eligibility still accepts incomplete or duplicated months

**Evidence:** The aggregation accepts `len(grp) >= 10`. Ten copies of January in each of 20 years produced 20 eligible annual observations and a supported trend. A 20-year precipitation fixture containing only January–October was accepted as annual totals even under `precipitation_total_policy`. A record with a 25-year gap also received supported evidence despite the declared missing-gap limit.

Daily records without a `month` column are reduced through `drop_duplicates(year)`, which can keep one day and label it an annual value. Monthly means are unweighted arithmetic means; rate-to-depth conversion and actual calendar/time-bound integration remain absent. Inference still uses rounded `value_display`, and every unspecified policy defaults to temperature policy.

**Location:** `backend/src/api/trend.py:145`, `:185`, `:203`; unchanged `registry/policies.py` and scientific ingestion boundary.

**Fix:** Validate unique timestamps and month numbers, reject/conflict-resolve duplicates explicitly, aggregate source cadence correctly, count actual eligible intervals, and compute temporal completeness. Apply the requested 12-valid-month precipitation rule. Weight means/integrate rates using actual bounds and calendars. Enforce gaps, select the correct default product policy, and use full-precision normalized scientific values.

**Acceptance:** Duplicate January rows never become a complete year; ten-month precipitation is withheld; daily input is genuinely aggregated; gap violations have an explicit evidence reason.

### R05 — High — Comparison joins multiply observations and bypass policy

**Evidence:** Four monthly rows from one year in each region produced a 16-row many-to-many merge. The endpoint reported `common_years_count=16`, interval `[2000,2000]`, a null contrast slope, `equal_rate`, and `supported_increase` with p approximately 0.00000917. It also accepts a comparison with 0% coverage or an unknown policy.

Binding/ocean checks and neutral labels are improved, but `pd.merge(..., on='year')` does not enforce unique annual keys. The endpoint still requires only three merged rows, ignores coverage thresholds and policy settings, lacks dependence handling, and returns an unfrozen contrast. The frontend now sends dates and binding, but omits policy; target changes and in-flight comparison requests can still leave stale contrasts.

**Location:** `backend/src/api/comparisons.py:159`, `:166`, `:180`, `:200`; `frontend/components/investigation/chart_area.tsx:94`, `:107`.

**Fix:** Reuse one eligibility/aggregation pipeline, enforce unique time keys with a one-to-one validated join, and apply the contrast's actual policy, duration, coverage, gaps, dependence and uncertainty. Require coherent slope/evidence states. Freeze the result and its support. Send policy, cancel obsolete requests, and clear comparison state when either the result or target changes.

**Acceptance:** One calendar year cannot become 16 eligible years. Invalid support cannot receive contrast evidence, and contrast context matches the displayed investigation.

### R06 — High — Tile responses are placeholders and scientific layers are disconnected

**Evidence:** The tile route returns the same 67 bytes for different XYZ locations. Its PNG header declares 1×1 pixels, and Pillow could not decode it as an image. There are no numerical pixels or pre-rendered 256×256 products. The README claims scientific 256×256 tiles; `verify_e2e.py` prints that claim after checking only a PNG signature and content type.

The new regional GeoJSON does calculate slopes/p/q values, but it recomputes from the inherited generated caches, bypasses QA/coverage/dependence/record gates, ignores requested time windows, and has no frozen analysis identity. A failed-QA, zero-coverage Bangladesh record was still marked as data-bearing and FDR-significant. Changing 1980–2024 to 2010–2024 returned an identical layer payload. The frontend does not fetch or add these scientific sources at all.

**Location:** `backend/src/api/layers.py:21`, `:58`, `:99`; `frontend/components/ui/map.tsx`; `README.md:137`; `verify_e2e.py:56`.

**Fix:** Return an honest unavailable state until a real numerical display asset exists. Build layers from the same verified dataset/window/policy and eligibility pipeline as the investigation. Define the fixed FDR family/mask, freeze the layer identity, and connect it to frontend sources, legends, numeric inspection, and controls. A regional choropleth can be a valid initial product if labelled as regional support; it is not a gridded raster trend product.

**Acceptance:** Decode the actual image and validate dimensions and data-derived pixels, or test the actual regional values. Check that map source, chart, result and export share their scientific context. Endpoint success alone is insufficient.

### R07 — High — Narration can still publish incorrect facts

**Evidence:** The new validator rejects some invented numbers, but uses one pool of all allowed numbers rather than verifying each fact's field. A false **100 °C/decade** slope passed because coverage was 100. A claim of **9.99 °C/decade** also passed against a result whose slope was 0.30 because pointer validation checks presence rather than equality.

With an audit-only injected renderer returning forbidden causal and 999-degree claims, `/trend` still published them with HTTP 200. The validation-failure branch only prints a warning; its comment claims a fallback which is not implemented. Bangla is not validated. Normal names containing “2m” can produce numerical false positives. POWER still gets country wording and assumed 100% spatial coverage; flat/inconclusive wording and the frontend flat badge remain incomplete.

**Location:** `backend/src/narration/validator.py:71`, `:85`; `backend/src/api/trend.py:436`; `narration/templates_en.py`; `frontend/components/investigation/result_panel.tsx:34`.

**Fix:** Generate claims from the frozen result and compare each field, unit, formatter, date and support type with its own pointer. Enforce validation failure through a validated fallback or explicit narration-unavailable response. Validate both languages. Keep point support, annual totals, estimated direction and statistical evidence separate. Replace verification guarantees with truthful status.

**Acceptance:** Cross-field number swaps and claim/result disagreements fail. A failed validator cannot publish the rejected text. Both languages describe the actual support and evidence.

### R08 — High — Identity improvements do not complete the frozen-result contract

**Evidence:** Data-byte hashing and insert-ignore are genuine improvements. However, requesting 1980–2024 and then 1970–2024 produced the same ID with different `requested_interval` and `created_at` values. The latest `/trend` response differed from `/results/{id}`. The endpoint recomputes before insertion and returns the newly constructed object, while SQLite preserves the older one.

`geometry_sha256` exists as a helper parameter but is not supplied. Actual code revision, binding metadata/version/conversions, source manifest and environment are not fully included. Code revision remains `v1.0.0`; retrieval time was changed to another constant. Six saved legacy records with the old wrong MERRA-2 DOI and no data checksum remain publicly retrievable through the API in the delivered package.

**Location:** `backend/src/cache/hasher.py`; `backend/src/api/trend.py:284`, `:425`, `:429`, `:443`; `backend/src/cache/store.py:192`; `data/cache/index.db`.

**Fix:** Define which query fields belong to scientific identity versus request support, then keep frozen payloads consistent. Return the stored result on a verified cache hit, or return a separate request envelope around it. Include real scientific inputs/configuration and actual revision identifiers. Use acquisition timestamps from manifests. Quarantine legacy generated results and migrate schema/version explicitly.

**Acceptance:** The same result ID returns the same frozen payload through all endpoints. Different scientific inputs create a new ID. Requests outside support receive their own clear retained/requested explanation without altering a frozen result.

### R09 — High — Strict numeric/JSON validation is still incomplete

**Evidence:** Missing observation values are now filtered correctly. But infinite coverage passes the threshold, receives supported evidence, appears as null in the tested HTTP response, and is exported as literal **Infinity**, invalid standard JSON. Missing QA/coverage columns produce assumed 100% support. Store/export serializers still use default permissive `json.dumps`.

**Location:** `backend/src/api/trend.py:181`, `:276`; `backend/src/narration/claims.py:44`; `backend/src/cache/store.py:205`; `backend/src/api/results.py:86`.

**Fix:** Validate all numerical fields, with finite values and appropriate ranges, at cache load and result save. Require source-specific fields. Use strict JSON serialization and nullable unavailable quantities. Preserve exclusion reasons and raw-versus-eligible counts instead of silently dropping all context.

**Acceptance:** Invalid percentage/Infinity/NaN values are rejected or explicitly withheld; exports pass a strict parser and match API support summaries.

### R10 — High — Uncertainty, spatial aggregation, and geography remain incomplete

**Evidence:** Later-lag detection is repaired, but the correction now sums only positive significant correlations; its precise variant and calibration still need validation. The unchanged fitted-band code independently resamples residuals, while slope intervals remain disconnected from dependence treatment. Maximum-gap handling and baselines remain unwired. `compute/spatial.py` is still unused by production acquisition/analysis.

Geographic metadata is greatly improved, but the area routine is an approximation rather than an exact geodesic-edge calculation. On a spherical triangle bounded by the equator and two meridians with three right angles, it returns 31,879,117.56 km² versus the exact 63,758,235.12 km². This is a kernel counterexample, not a claim that real country areas are all wrong by 50%. Dateline bounding boxes remain nearly global; the map still fits naive coordinate bounds. Geometry source/version and actual POWER sample coordinates remain unverified.

**Location:** `compute/serial_corr.py:93`, unchanged `compute/uncertainty.py`, `compute/spatial.py`, `registry/regions.py:75`, `frontend/components/ui/map.tsx:199`.

**Fix:** Specify and independently validate the statistical variants and dependence-aware uncertainty. Wire product-native grid/mask/area aggregation from actual provider assets. Use a trusted area algorithm consistent with the chosen boundary-edge model, and validate against an independent reference. Record geometry/mask versions, handle datelines, and expose actual point coordinates.

**Acceptance:** Real-grid fixtures reproduce regional values; dependence/uncertainty coverage tests pass; geographic counterexamples and dateline cases have documented correct behavior.

### R11 — High — Packaging still fails after the attempted repair

**Evidence:** The new `packages.find` with `where=["src"]` builds a wheel containing top-level `api`, `cache`, `compute`, `registry`, and other packages, but neither `src` nor `main.py`. Outside the checkout, `src.main` and `main` raise `ModuleNotFoundError`, and `api.trend` fails with a relative-import error.

**Location:** `backend/pyproject.toml`.

**Fix:** Package the actual named application namespace, include its entry module, and use explicit data-root configuration rather than repository-parent assumptions. Test installation and startup from a wheel in a fresh environment outside the source tree.

**Acceptance:** A clean install launches the documented API command without the repository on `PYTHONPATH` and locates its configured verified data.

### R12 — Remaining interface, delivery, and scope work

The stable map lifecycle, synchronized form, cancellation and dialog improvements should be retained. The following remain:

- The old trend stays visible during a new request. An aborted earlier request's `finally` can also clear the newer request's loading state. Add request identity and explicitly labelled stale/loading content.
- Comparison cancellation/target reset/policy forwarding remain incomplete; the chart hook regression must be fixed first.
- Time limits remain hard-coded to 1980–2024. Seasonal diagnostics are explanatory text rather than connected computation. Scientific playback, layer controls and numeric inspection are absent.
- The drawer lacks a complete focus trap and focus restoration. Accessible chart/table and keyboard workflows need rendered validation.
- Fonts are now local/system-resolved, but offline badges/health still reflect a setting rather than verified guard/assets. The network guard is unchanged and covers a narrow Python connection path.
- Static export and single-port FastAPI serving remain absent. CORS ports were corrected, but the deployment remains two services.
- The frontend remains Next 15.5.27, Tailwind 3.4.19 and raw MapLibre; the agreed Next 16/Tailwind 4/mapcn migration is pending. The issue is target alignment, not a newly established security finding.
- Python dependencies remain unbounded minimum ranges without a lock. Lint is still unconfigured and uses `next lint`. Core API dictionaries/frontend `any` types remain.
- Large geographic assets, hover updates, asynchronous highlight races and analysis-size limits still need measurement.
- README/docstrings claim verified acquisition, geodesic aggregation, real raster tiles and 37 passing tests without supporting implementation. The wider Earth-system catalogue remains seven parameters.

## Status against the original 29 findings

“Fixed” below closes the original specific defect based on source verification. “Partial” means useful changes landed but the finding's acceptance criteria remain unmet. “Unfixed” means the core issue remains. These are not percentage-complete estimates.

| ID | Original finding | Status | Current assessment |
|---|---|---|---|
| F01 | Synthetic scientific records | Partial | Runtime generation removed; previously generated caches/results remain enabled. |
| F02 | Acquisition/lineage/readiness | Partial | Five inventory manifests added; acquisition and manifest enforcement absent. |
| F03 | Binding/path validation | Partial | Trend/comparison paths and bindings repaired; coverage still accepts a mismatched binding. |
| F04 | QA/temporal eligibility | Partial | Basic filters and aggregation added; duplicate months, incomplete totals, gaps and source contracts fail. |
| F05 | Immutable identity/provenance | Partial | Data/full-policy hash and insert-ignore added; frozen response consistency and full provenance fail. |
| F06 | Short-record/evidence states | Partial | 15-year request repaired; flat/insufficient semantics and UI mapping incomplete. |
| F07 | Later-lag dependence | Partial | Later lags detected; positive-only correction variant/calibration and gap handling still need validation. |
| F08 | Dependence-aware uncertainty | Unfixed | Independent residual bootstrap and disconnected slope intervals unchanged. |
| F09 | Nonfinite support/exports | Partial | NaN observations filtered; infinite metadata and permissive JSON still fail. |
| F10 | Comparison science | Partial | Validation/labels improved; many-to-many joins, coverage, policy and evidence fail. |
| F11 | Comparison context/UI | Partial | Dates/binding/errors added; policy/stale requests remain, and a hook-order regression was introduced. |
| F12 | Numerical narration safeguards | Partial | Some number checks added; cross-field facts, pointer equality, enforcement and Bangla checks fail. |
| F13 | Totals/points/flatness narration | Partial | Annual-total label and null CI wording improved; point/coverage and flatness issues remain. |
| F14 | Geographic metadata | Partial | Plausible areas/interior points; exact area method, datelines and source/mask identity remain incomplete. |
| F15 | Real spatial aggregation | Unfixed | Production still does not derive region values from real provider grids. |
| F16 | Scientific map products | Partial | Routes/regional GeoJSON added; tiles are placeholders and scientific sources are not connected to the map. |
| F17 | Spatial FDR | Partial | Regional BH q-values added; invalid support, time context and frozen testing family remain unaddressed. |
| F18 | Map recreation on parent renders | Fixed | Map construction effect is stable; callback is maintained through a ref. Full browser verification pending. |
| F19 | Map/form region divergence | Fixed | Draft state now synchronizes with committed query changes. Dirty-draft behavior remains a design choice to test. |
| F20 | Request races/stale display | Partial | AbortController added; loading ownership and stale result/context handling remain incomplete. |
| F21 | Seasonal/timeline implementation | Unfixed | Explanatory seasonal tab and hard-coded windows remain. |
| F22 | Verified offline operation | Partial | External fonts removed; status/guard/end-to-end offline contract remains unverified. |
| F23 | Installed backend packaging | Unfixed | Wheel still cannot import/launch the application; entry module now omitted. |
| F24 | Deployment contract | Unfixed | CORS improved; static export/single-port package still absent. |
| F25 | Framework/locks/lint/tests | Partial | Ten regression tests added; framework alignment, locking, lint and semantic acceptance coverage remain. |
| F26 | Performance/scaling | Partial | Highlight GeoJSON is cached; large assets, async races and compute limits remain. |
| F27 | Accessibility/language | Partial | Dialog semantics/Escape/focus and document language improved; complete accessible workflow unverified. |
| F28 | Honest documentation/types | Unfixed | Overstated scientific/tile/test claims and loose API/frontend types remain. |
| F29 | Multi-domain catalogue | Unfixed | Seven-parameter scope unchanged; no new real scientific adapters. |

## Next implementation order

1. **Restore usable and truthful behavior:** move chart hooks before returns; quarantine generated data/results; mark scientific tiles unavailable; correct readiness and verification labels.
2. **Make loading trustworthy:** enforce manifest/source/region/schema/checksum gates; implement one real provider acquisition/aggregation workflow; record exact acquisition provenance.
3. **Unify scientific eligibility:** valid unique intervals, 12-month precipitation totals, calendar weighting, gaps, full precision and correct default policies. Share this pipeline across trend, comparison and layers.
4. **Finish reproducibility and evidence:** consistent frozen responses, full hashes/revisions, dependence-aware uncertainty, coherent states and enforced bilingual narration.
5. **Connect actual products to the interface:** same result/window/policy for map/chart/comparison/export, working layers, data-driven dates, supported seasonal modes, request identity and accessibility.
6. **Verify delivery:** installed wheel launch, documented single/two-service deployment, locks/lint, offline asset checks, and rendered interaction tests.

## Regression cases to add now

| Case | Required passing behavior |
|---|---|
| Chart null → result → null | No hook-order error; comparison reset still works. |
| Previously generated cache | Rejected/quarantined, never labelled as provider-verified data. |
| Missing/mismatched manifest | Typed failure before inference; no silent acceptance. |
| Missing QA/coverage or infinite percentage | Required source contract/range checks; strict valid export. |
| Duplicate January / invalid month number | Not counted as multiple valid months. |
| Ten-month precipitation year | Withheld under the complete-year accumulation policy. |
| Declared maximum-gap violation | Explicit unsupported/limited evidence reason. |
| One-year duplicated comparison | No many-to-many inflation; insufficient support. |
| Unknown contrast policy / zero coverage | Correct validation and scientific gates. |
| Same ID through trend/results/export | One consistent frozen payload. |
| Wrong number in another fact field | Rejected, even if its value is present elsewhere in the result. |
| Validation failure in either language | Rejected text not published. |
| Tile response | Decode dimensions/pixels and source identity; no signature-only pass. |
| Layer QA/window/FDR | Same validated scientific context; invalid observations excluded; fixed declared family. |
| Wheel installed outside checkout | Documented entrypoint launches and configured data loads. |
| Aborted/out-of-order requests | Newest query controls loading, map, chart and result. |

The existing 35 tests should remain. Tests should be expanded around these failures rather than weakened to make endpoint availability stand in for scientific correctness.

## Reference

[1] React, [Rules of Hooks](https://react.dev/reference/rules/rules-of-hooks) and [rules-of-hooks lint](https://react.dev/reference/eslint-plugin-react-hooks/lints/rules-of-hooks): hooks must execute consistently before early returns.
