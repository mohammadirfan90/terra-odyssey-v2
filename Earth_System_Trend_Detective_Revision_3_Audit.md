# Earth System Trend Detective — audit 3

Reviewed: `earth-system-trend-detective(3).zip`, 1 October 2026. Compared with revision 2 and its audit.

**This revision fixes several specific failures, but it still does not meet the real-data requirement. All 30 scientific Parquet files and all five manifests are unchanged. The same 26 files previously reproduced exactly from the original synthetic generator are still present, and a normal Bangladesh request still returns a NASA-labelled supported finding from those records.**

The first-result chart hook crash, ordinary checksum bypass, duplicate-January aggregation, ten-month rainfall totals, infinite coverage, and invalid JSON export have been repaired. The new checks also reveal incomplete rainfall being accepted through a different route, incorrect daily aggregation, map data silently disappearing, unsupported comparison evidence, and a separate chart crash.

This is an audit, not an application repair. Uploaded archives and extracted source were preserved. Tests, builds, installation checks, and artificial fixtures ran in an isolated runtime copy. Fixture Parquet files and manifests were restored. The supplied ZIP is the authoritative source for this follow-up; this review does not establish that the published Claude artifact has been updated to match it.

## Verification

| Check | Observed result |
|---|---|
| Archive | 182 files; 33,049,511 uncompressed bytes |
| SHA-256 | `1503a1d274a3534db8d6350cccfa6373ff8665267fd2cc4d5396e91566af314a` |
| Changes against revision 2 | 17 changed; 48 added; 117 unchanged; zero removed |
| Scientific cache | All 30 Parquet files byte-identical to revision 2 |
| Scientific manifests | All five JSON manifests byte-identical to revision 2 |
| Real acquisition | No raw scientific NetCDF/HDF/TIFF/Zarr assets or scientific acquisition adapter added |
| Delivered SQLite database | 30 indexed series; two active completed results; seven quarantined results |
| Supplied backend tests | **44 passed**, one dependency deprecation warning |
| Fresh TypeScript check | Passed, after removing the runtime copy's supplied incremental build cache |
| Next production build | Passed; Next 15.5.27; root route 287 kB; first-load JavaScript 389 kB |
| Lint command | Exits 1 and asks interactively for ESLint configuration; no configured lint gate |
| Chart hook lifecycle | Actual component passes null → result → null → different result |
| Chart interaction checks | Hovered point → shorter result crashes; stale comparison target and late response reproduced |
| Bundled and freshly built wheels | Both import `src.main` and serve health successfully outside the checkout; both fail to find supplied scientific data through configuration |
| Independent checks | 63 main API/numerical/inventory probes and four follow-up checks; separate React component harnesses |
| Full browser validation | Not performed; component tests do not establish visual, keyboard, accessibility, or full browser map correctness |

Python verification used 3.12 with FastAPI 0.142.2, Pydantic 2.13.5, NumPy 2.3.5, SciPy 1.17.0, pandas 2.2.3, PyArrow 25.0.1, statsmodels 0.15.0, pytest 9.1.1, and pyproj 3.8.0. The new pyproj import required installing the already-declared dependency in the audit environment. Initial collection errors before that installation are not counted as application defects. Frontend dependencies were reused because the package and lock files are unchanged: React 19.3.0, Tailwind 3.4.19, MapLibre 5.24.0, TypeScript 5.9.3.

## Repairs verified

| Audit 2 defect | Current verification |
|---|---|
| Tampered Parquet accepted despite checksum mismatch | Now returns 422 `DATA_INTEGRITY_ERROR` when the manifest contains the expected digest |
| File without a manifest entry accepted | Now returns 404; a copied Nepal file cannot bypass membership |
| Declared required QA/coverage columns ignored | Removing declared columns now returns 422 |
| Legacy results with missing hashes or the deprecated DOI remained active | Seven rows are quarantined; requests for those IDs return 404 |
| Chart hook order changed after the early return | All hooks are now before the conditional return; four lifecycle transitions pass |
| Ten January duplicates counted as ten months | Now rejected with 422 |
| Ten-month annual precipitation total accepted | Now rejected with 422; precipitation also selects its own policy by default |
| Twenty-five-year gap received supported primary trend evidence | Primary `/trend` now downgrades it to `limited` |
| Comparison rows multiplied in a many-to-many year join | Series are aggregated first; one-year fixture now returns 422; join is explicitly one-to-one |
| Zero-coverage comparisons accepted; unknown comparison policy ignored | Both are now rejected |
| Infinite/out-of-range coverage accepted | Infinity and 101% are excluded and the all-invalid record returns 422 |
| Permissive JSON save/export | Store and export now sanitize nonfinite floats and use `allow_nan=False`; tested export passes a strict parser |
| Raster placeholder bytes presented as scientific PNGs | Tile endpoint now returns honest 501 `RASTER_TILES_UNAVAILABLE` |
| Layer QA/time-window filters ignored | Failed-QA region is excluded; changing the time window changes its statistics |
| English rejected narration still published | Injected causal/999-degree English text is replaced with a deterministic fallback and marked `narration_status=fallback` |
| Claim/pointer disagreement and 100%-as-slope accepted | These specific validator counterexamples are now rejected |
| Parameter name containing “2m” falsely flagged | Metadata numerals are now allowed |
| Same result ID returned changing frozen bodies | Verified cache hit returns the saved object; repeated responses equal `/results/{id}` and skip recomputation |
| Spherical triangle area was half the exact value | pyproj now gives 63,758,235.12160898 km², matching the independent spherical formula |
| Coverage allowed incompatible parameter/binding | Now returns 400 |
| Comparison failed to forward policy | Actual component forwards the primary result's policy |
| Aborted old trend cleared a newer loading state in `finally` | Source now guards this update with `!controller.signal.aborted` |
| Wheel omitted the application namespace | Bundled and clean-built wheels contain matching `src` modules; installed imports work |

## Remaining findings and required fixes

### R01 — Critical — Generated observations still produce verified scientific findings

The cache and manifests are unchanged, byte for byte. The previous audit's 26 exact generator matches retain the same hashes. No provider assets or granule-level lineage were added. Quarantine moved seven old result rows, but the two active results in the delivered database already reference the same generated Bangladesh input hash. A normal request returns 200, `supported_increase`, 45 samples, and 100% area coverage. The interface labels it a “Verified Finding.”

The result-quarantine condition only checks for a missing data hash or one deprecated DOI. A SHA-256 of generated observations satisfies that condition. It does not establish provider origin.

**Locations:** `data/cache/`, `data/manifests/`, `backend/src/cache/store.py:134`, `backend/src/api/trend.py`, `frontend/components/investigation/result_panel.tsx`.

**Fix:** Quarantine the inherited generated observations and every result derived from them. Keep runtime generation disabled. Acquire a genuine provider asset through a separate ingestion workflow, retain original asset/granule identifiers and checksums, and record variables, units, QA decoding, dates, spatial masks, and transformations. Readiness must depend on that validation. Until then, return truthful unavailable states.

**Acceptance:** A displayed regional value is independently reproducible from a named downloaded provider asset. Known generated records cannot produce an analysis-ready or verified finding, even when their local checksums match a manifest.

### R02 — Critical — The manifest gate still fails open when its contract is incomplete

The normal checksum repair works. However, `if expected_sha and actual_sha != expected_sha` makes the checksum optional. Removing `sha256` from a manifest entry allows a modified file to return 200. Removing the QA/coverage declarations and columns also returns 200 with invented 100% coverage. A manifest claiming a different binding, wrong units/variable, and `catalogued` readiness is still accepted. Wrong row count, date inventory, and filename are accepted as well.

Corrupt Parquet and a missing `year` column produce generic 500 responses rather than typed data-integrity problems. `has_series()` checks membership and an optional digest, but not the full schema, so `/coverage` can announce support that `/trend` cannot use.

**Locations:** `backend/src/cache/store.py:247`, `:288`, `:310`, `:320`; `backend/src/api/coverage.py`.

**Fix:** Validate a typed manifest before indexing or loading. Require a correctly formatted digest and consistent binding, region, filename, readiness, inventory, units, cadence, and source-specific columns/types. Derive QA/coverage requirements from the binding rather than letting an incomplete manifest waive them. Define explicit unavailable coverage for point products. Catch read/schema failures and return typed 422 problems. Read and hash one consistent asset snapshot.

**Acceptance:** Missing/empty digest, wrong binding, wrong unit, inconsistent inventory, missing required fields, invalid calendar values, and corrupt assets are rejected before inference. Coverage and trend agree on usability.

### R03 — Closed for the original hook-order defect

All hooks precede the early return and the actual null/result lifecycle passes. Retain this repair. A different hovered-point crash remains and is listed under R12; closing the hook-order defect does not establish that every chart transition is safe.

### R04 — High — Annual completeness and daily aggregation still give wrong results

The twelve-month rule counts rows before validating monthly scientific values. With all twelve month labels present but December's value missing in every year, the rainfall fixture returns 200 and `supported_increase`, reports 100% coverage, and sums only eleven months. The observed slope is 110 mm/decade; the corresponding complete twelve-month fixture is 120 mm/decade. The missing-month fixture should not yield an eligible annual total.

Daily data containing `month` and `day` take the monthly branch. `drop_duplicates(month)` selects one day per month. A complete **7,305-day** MODIS-binding fixture returns an annual value of 24.0°C and a slope of 0.1000°C/decade; aggregation over every actual day gives 25.9344°C in the first year and 0.1967123°C/decade. Daily records without a month column have no calendar-completeness gate: one day per year can produce a supported twenty-year trend. If all such daily records fail QA, the empty aggregation loses its columns and crashes with 500.

Fractional month labels also pass. The new “full precision” selection prefers `value`, but the supplied files store precision in `value_canonical`. They therefore continue to use rounded `value_display`. A consistent canonical Kelvin series with a 0.001°C/decade slope and display values rounded to 25.00°C is reported with slope zero. An undeclared `value` column overrides the display series without any unit contract.

The excessive-gap downgrade is useful, but its explanation incorrectly says “record span <20 years” for a 1980–2024 record. Monthly means still have no explicit calendar/time-bound weighting; rate-to-depth conversion remains absent from a real acquisition workflow.

**Locations:** `backend/src/api/trend.py:219–265`, `:286`, `:390`; duplicated aggregation in `backend/src/api/comparisons.py:44–92`.

**Fix:** Implement one shared, typed eligibility/aggregation routine. Validate finite source values and real calendar timestamps first. Distinguish source cadence from already-aggregated series; resolve duplicate observations explicitly; count valid unique intervals; enforce daily/monthly temporal coverage separately from spatial coverage. Rainfall totals need twelve valid months and documented integration of source rates over time bounds. Infer from a declared full-precision column after the correct unit transformation, and round only for presentation. Preserve exclusion counts and the actual gap reason.

**Acceptance:** Missing-valued months cannot satisfy completeness; complete daily data use all days; incomplete daily years are withheld; invalid calendar labels fail; canonical/display precision is consistent; empty eligible input returns a typed state.

### R05 — High — Comparison evidence still ignores major policy rules

The join and zero-coverage repairs work, and policy IDs are validated. But policy use stops at aggregation/coverage. A five-year comparison returns `supported_increase` with p=0.027486, while the primary trend endpoint categorizes the same duration as `insufficient`. Twenty eligible years separated by a twenty-five-year missing gap also return supported comparison evidence, while primary trend is now `limited`.

The comparison calls Theil–Sen and Mann–Kendall with their defaults. It does not apply the selected policy's alpha, dependence handling, duration thresholds, or maximum gap to inference. It does not freeze a comparison result with both source hashes and its testing context. The `equal_rate` label still follows a hard-coded near-zero estimate threshold rather than an uncertainty-based equivalence definition.

**Locations:** `backend/src/api/comparisons.py:294`, `:311–314`, `:317`, `:352`.

**Fix:** Run the paired difference series through the same policy-aware inference/evidence pipeline as a primary trend. Apply the common eligible-calendar support and dependence treatment. Separate a point estimate's direction from evidence of differing or equivalent rates. Persist a comparison identity, both input hashes, full policy, overlap/exclusions, uncertainty method, and provenance.

**Acceptance:** Five-year and excessive-gap comparisons cannot receive a supported climate badge under the standard policy. Changing alpha/dependence settings affects inference consistently. Every comparison is independently reproducible.

### R06 — High — Monthly map data disappears; map policies remain inconsistent

The new monthly layer branch calls `pd.DataFrame(...)` but `layers.py` never imports pandas. A valid monthly Bangladesh fixture becomes `has_data=false`, and the FDR family drops from ten to nine. The broad `except Exception: continue` hides the `NameError`. In an audit-only diagnostic, supplying that missing import makes the identical data appear with a slope and q-value. No source repair was applied.

QA and date filters now work, but `policy_id` is accepted and ignored: an unknown policy returns 200. Coverage is hard-coded to 80%. A 75%-coverage MODIS series works under its declared 70% trend policy but is withheld by the corresponding map endpoint. Map inference requires only five values and uses unadjusted default Mann–Kendall rather than the primary evidence contract. Daily inputs without a month are still reduced to one observation per year. The FDR family changes according to which loads happen to survive, with no frozen family/support metadata.

The raster endpoint's honest 501 is a successful correction. `/tilejson` still advertises raster URLs that always return 501, and the frontend map still does not consume the scientific GeoJSON products. The new regression test checks that a FeatureCollection exists, not that eligible observations actually survive or the statistics match.

**Locations:** `backend/src/api/layers.py:90–165`; `backend/src/registry/layers.py`; unchanged `frontend/components/ui/map.tsx`.

**Fix:** Add the missing import, replace blanket exception swallowing with explicit per-region failure reasons, and use the shared aggregation/inference policy. Validate policy IDs and date ranges. Define and freeze the intended FDR family, eligible members, exclusion reasons, method, alpha, and source identities. Expose truthful layer availability in the catalogue/TileJSON and connect supported vector layers to the frontend.

**Acceptance:** A valid monthly record renders rather than silently disappearing; map and primary-result support/statistics agree under the same policy; unavailable raster routes are not advertised as ready; testing-family changes are auditable.

### R07 — High — Bilingual and cross-field narration validation remains incomplete

Pointer equality and the specific 100%-as-slope rejection work, and English validation now triggers a fallback. But only English narration is validated. An audit fixture injected Bengali causal text with “999 degrees” and “proves” language; the response published it unchanged with 200 and no fallback status.

The validator still uses a global number pool for most quantities. A sentence claiming **20% spatial coverage** passes against a verified 100% coverage result because 20 is an allowed policy number. A point slope of 0.36 passes against a true estimate of 0.30 because 0.36 is a CI bound. A Bengali phrase putting “per decade” before a unitless 100 also passes by borrowing the coverage number. The exact explicit-unit Bengali slope counterexample is rejected when the validator is called directly; that improvement does not help when production never calls it for Bengali.

Fallback text exposes internal evidence enums and Western digits in Bangla. Point-product narration still describes a Bangladesh regional mean/100% spatial coverage; the cached POWER coordinates differ from the result's representative point and are not exposed as the actual sample location. Flatness and insufficient-record explanations remain misleading in some states.

**Locations:** `backend/src/narration/validator.py:123–167`, `backend/src/api/trend.py:521–536`; unchanged narration templates and claim semantics.

**Fix:** Validate both languages before publication. Bind each rendered quantity and role to its exact field; keep point estimate, interval bounds, p-value, coverage, and years distinct. Prefer deterministic rendering of approved typed facts over permissive number-pool matching. Build localized fallbacks from the same verified semantic frame and validate them. Describe point samples and unavailable area coverage accurately.

**Acceptance:** Wrong Bengali numbers/causation, 20%-for-100% coverage, and CI-bound-as-point-estimate are rejected. Both languages preserve the same support and evidence facts, including point-versus-area support.

### R08 — High — Frozen results now work, but identity and request context remain incomplete

The immutable response repair is real: cache hits skip computation and return the stored object. However, a request for **1970–2024** returns the same frozen object as 1980–2024, including `requested_interval=[1980,2024]`. The scientific retained interval is reasonable; the claimed requested interval is false for the current request.

The hash helper accepts geometry and code-revision inputs, but the production calls omit them. The revision stays the constant `v1.0.0`, including across algorithm changes, and geometry/mask/source-transformation versions are absent. Acquisition time remains the hard-coded `2026-10-01T08:00:00Z`. Early cache reuse can therefore return older outputs after code or relevant metadata changes. Merely having a data hash still admits generated results, as R01 demonstrates.

**Locations:** `backend/src/api/trend.py:292–306`, `:424–431`, `:510–517`; `backend/src/cache/hasher.py`; `backend/src/cache/store.py:371`.

**Fix:** Preserve the frozen scientific object and put request-specific dates/exclusions in a separate response envelope, or include that context in identity. Hash actual computation revision, geometry/mask, binding transformations, schema, and complete policy. Use actual acquisition records and migrate/invalidate legacy identities when their contracts change.

**Acceptance:** The same ID always returns one scientific payload, while each request accurately reports its own requested support. Changing an algorithm, geometry/mask, or transformation creates a new identity; timestamps trace actual acquisition.

### R09 — Closed for the tested Infinity and invalid-JSON defects

Infinite and >100% coverage are now filtered, all-invalid support returns 422, and tested exports pass strict JSON parsing. Store/export use `allow_nan=False`. Retain those changes. Broader source-schema validation belongs to R02, and nonfinite monthly observations must be fixed under R04 before they count as valid temporal support.

### R10 — High — Dependence-aware uncertainty and real spatial derivation remain incomplete

The geodesic triangle defect is fixed. The calculation now uses pyproj on a sphere of radius 6,371,008.8 m and matches the exact spherical test. All 261 supplied features also matched a check that normalized polygon orientation and summed component areas; no delivered orientation cancellation was observed. pyproj's documented signed-area/orientation assumptions should be normalized or enforced for future geometry inputs. An artificial mixed-orientation MultiPolygon cancels to zero, but that is a kernel limitation, not evidence that the supplied country areas are wrong.

The changed serial-correlation file only labels the existing positive-only correction variant in a comment. Later lags remain detected, but the statistical variant has not been independently calibrated. Fitted bands still independently resample residuals with `rng.choice`; slope intervals remain separate from dependence handling. Baseline policies and production product-native grid/mask aggregation are still unwired. There is no real ingestion path calling the spatial kernel to derive the packaged regional series.

USA/Fiji naive dateline bounds, geometry/mask lineage, and actual POWER coordinates remain unresolved. A correct polygon-area helper does not establish correct scientific regional aggregation.

**Locations:** `backend/src/compute/serial_corr.py`, unchanged `uncertainty.py` and `spatial.py`, `backend/src/registry/regions.py:78`, unchanged map bounds handling.

**Fix:** Specify and validate the precise dependence correction and a compatible uncertainty approach. Calibrate coverage with independent dependent-series fixtures rather than only checking for a VIF flag. Connect real source grids, masks, cell intersections/areas, units, and QA to ingestion. Record geometry/mask versions and actual point coordinates; handle dateline views explicitly.

**Acceptance:** Independently reproducible real-grid regional values and calibrated uncertainty are demonstrated. Geometry edge/orientation assumptions and dateline behavior are documented and tested.

### R11 — High — Wheel imports are repaired; installed data discovery is still broken

Both the supplied wheel and a fresh build contain the actual `src` namespace and entry module. Their source modules match the delivered source. Outside the checkout, each imports successfully and `/health` returns 200.

Their data lookup still walks parents of the installed Python module. Neither includes the needed scientific data/boundaries or accepts an application-wide data-root configuration. Setting `DATA_ROOT` to the supplied runtime data directory has no effect. Installed region discovery falls back to only Bangladesh's hard-coded metadata; a normal Bangladesh trend request returns 404. The CLI also defaults to port 8000, while the frontend proxy expects 8005.

**Locations:** `backend/pyproject.toml`; `backend/src/cache/store.py:75`; `backend/src/registry/regions.py:96`; `backend/src/api/layers.py:107`; `backend/src/main.py:126`.

**Fix:** Introduce one explicit configured data root used by the store, registry, layers, and startup validation. Install verified data as an intentional external bundle or package resource. Validate its availability before announcing readiness. Align/document server and proxy ports.

**Acceptance:** A clean wheel install outside the checkout, pointed at a verified data bundle, launches the documented command and serves countries, coverage, layers, and a real trend without repository-relative assumptions.

### R12 — High — Chart and comparison state still fail during result changes

The original hook-order crash is fixed. Another transition crashes: hover the last point of a five-value series, then deliver a three-value result to the same mounted chart. `hoveredIndex` remains four; the tooltip calls `values[4].toFixed(2)` and throws **`TypeError: Cannot read properties of undefined (reading 'toFixed')`**. This can occur when a pending shorter-window result arrives while an old point is hovered.

A completed USA comparison remains displayed after selecting Kenya in the comparison control. An in-flight Bangladesh–USA comparison is cleared when the primary result changes to Kenya, but its late response repopulates those old comparison cards. The component has no cancellation or request-identity guard. Policy forwarding is now correct.

The primary trend's guarded `finally` fixes the earlier loading-reset defect. Its old finding remains visible while committed query/map/form context changes, without being marked as stale. The result panel still maps `flat` to “Insufficient Data”; an excessive-gap `limited` record is labelled “<20 Yrs” despite its long span.

**Locations:** `frontend/components/investigation/chart_area.tsx:29–38`, `:100–134`, `:317–330`, `:344–350`; `frontend/app/page.tsx:69–77`; `frontend/components/investigation/result_panel.tsx:53–72`.

**Fix:** Reset and bounds-check hover state on series identity changes. Reset comparison state on target/context changes and cancel or ignore responses unless their full request context still matches. Clear or explicitly label the prior primary result during loading. Render every declared evidence state and the actual limitation reason.

**Acceptance:** Hover → shorter series never throws. Comparison target/result changes cannot display a stale result. Loading content accurately reflects the committed query and all evidence badges match the backend state/reason.

## Remaining delivery and product work

These requirements were not completed by this revision; the relevant source is unchanged unless noted above.

| Area | Remaining action |
|---|---|
| Deployment | Add the agreed static Next export and single-port FastAPI serving. Current configuration still requires Next at 3005 and FastAPI at 8005, with a server-side proxy. |
| Framework target | Complete the agreed Next 16/Tailwind 4/mapcn migration. Current locked stack remains Next 15.5.27/Tailwind 3.4.19/raw MapLibre. This is a target mismatch, not a newly established vulnerability. |
| Dependency reproducibility | Add a Python lock and supported version constraints. Minimum-only ranges are not a lock. The new pyproj implementation must be part of installed dependencies, including offline bundles. |
| Quality gates | Configure a noninteractive ESLint command with hook rules. Add semantic regression tests for the failures above; the existing layer test permits 200/404 and checks structure only. README counts still say 37/25 rather than 44. |
| Contracts | Replace core response dictionaries/frontend `any` with versioned typed schemas. Represent unavailable quantities as unavailable rather than inventing 100% support or zero confidence bounds. |
| Scientific interaction | Wire actual scientific map layers, numeric inspection, observed/anomaly/evidence/coverage modes, seasonal computation, and timeline/playback. The seasonal tab is still explanatory text. |
| Temporal support | Derive selectable dates from verified dataset/region support rather than hard-coding 1980–2024. Preserve raw versus eligible counts and exclusions. |
| Offline verification | Derive health/badge status from the installed guard and asset readiness. The current badge is hard-coded; the guard covers a limited Python socket path. Validate the entire local workflow with external networking unavailable. |
| Accessibility/Bangla | Complete drawer focus trapping/restoration, keyboard chart/table workflow, labelled controls, and consistent localization. Validate in a rendered browser; component tests do not close this requirement. |
| Performance | Measure large country GeoJSON loading/hover updates, asynchronous map highlights, expensive scientific computations, cache behavior, and request limits. Current root first-load JavaScript is about 389 kB. |
| Documentation | Remove unsupported claims of real grid aggregation, completed NASA acquisition integration, locked dependencies, zero network activity, complete bilingual verification, and implemented polar views. Keep the corrected raster-unavailability statement. |
| Earth-system scope | The same seven temperature/precipitation parameters remain. Vegetation, cryosphere, terrestrial water, atmospheric composition, and radiation acquisition/analysis are still absent. Enable each domain after real ingestion and validation. |

## Status against audit 2

“Closed” applies to the specific reproduced defect. “Partial” means useful repairs are verified but acceptance remains unmet. These group statuses are not a percentage-complete estimate.

| Audit 2 ID | Status | Assessment |
|---|---|---|
| R01 | Partial | Seven legacy results quarantined; generated observations and hash-bearing findings remain active |
| R02 | Partial | Membership/digest checks added; required manifest/schema/readiness contract remains optional |
| R03 | Closed | Hook-order lifecycle passes; different hover crash remains under R12 |
| R04 | Partial | Duplicate months, ten-month rainfall and gap downgrade repaired; valid-value completeness/daily science still fails |
| R05 | Partial | Annual one-to-one join/coverage/policy validation repaired; comparison inference/evidence policy remains incomplete |
| R06 | Partial | Honest raster 501 and QA/dates repaired; monthly map import, policy, FDR context and frontend integration remain |
| R07 | Partial | English enforcement/pointer checks improved; Bangla and semantic field validation remain unsafe |
| R08 | Partial | Frozen cache hit works; request context and full scientific identity/provenance remain incomplete |
| R09 | Closed for tested defects | Infinity coverage and strict JSON save/export repaired; source completeness remains R02/R04 |
| R10 | Partial | Geodesic triangle repaired; uncertainty, real spatial derivation, datelines and lineage remain |
| R11 | Partial | Installed imports/entry module repaired; configured data discovery and functional installed workflow remain broken |
| R12 | Partial | Loading-finally guard/policy forwarding improved; hover crash, stale comparisons and delivery work remain |

## Order of work

1. Quarantine generated inputs/results and deliver one end-to-end real provider dataset with reproducible lineage.
2. Make the manifest and source schema strict; share calendar-aware aggregation and eligibility across every endpoint.
3. Apply one scientific policy and evidence contract to trend, comparison, and map results; correct dependence/uncertainty and result identities.
4. Repair the monthly map import, hovered-point crash, asynchronous comparison state, and both-language narration enforcement.
5. Finish installed data configuration, static/single-port delivery, framework target, lint/locks/types, and accurately scoped documentation.

## Sources and evidence

The accompanying `Earth_System_Trend_Detective_Revision_3_Evidence.json` includes archive/data hashes, verification logs, API counterexamples, exact React failures, installed-wheel results, geographic checks, and status mappings. Artificial fixtures are clearly identified and are not production observations.

Primary references used to check technical interpretation:

- [pyproj Geod documentation](https://pyproj4.github.io/pyproj/stable/api/geod.html): signed geodesic areas, orientation and geometry limitations.
- [SciPy Theil–Sen documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.theilslopes.html): slope estimate, joint/separate intercepts and slope interval scope.
- [NASA IMERG documentation](https://gpm.nasa.gov/data/imerg): source cadence/precipitation-rate context; ingestion must retain the relevant product's exact units/time bounds.
- [React Rules of Hooks](https://react.dev/reference/rules/rules-of-hooks): hooks before conditional returns.

No complete browser accessibility audit, remote NASA acquisition, installed offline distribution, or published-artifact parity test was performed. The findings above rely on inspected source and explicitly recorded runtime/component checks.
