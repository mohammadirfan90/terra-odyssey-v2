# Earth System Trend Detective — audit 4

Reviewed 2026-10-01. Input: `earth-system-trend-detective(4).zip`, SHA-256 `ae19219217849c6ec1d891f22e1340694bda407369ac97e4b72eee5ef6b328d8`.

**Revision 4 repairs several important failures, but the application still does not satisfy the real-NASA/partner-data requirement. All 30 scientific Parquet files and all five acquisition manifests are unchanged from revision 3. The 26 files previously reproduced exactly from the original synthetic generator retain the same hashes. A normal Bangladesh air-temperature request still publishes a NASA-attributed, statistically supported finding from this cache.**

The new shared aggregation also introduces failures that the supplied tests miss: packaged annual aggregates for daily products become unusable, duplicate or impossible daily dates can qualify as complete years, temperature anomalies receive an incorrect absolute-temperature offset, and truthful confidence-interval narration is rejected. The comparison race repair introduces a stuck loading button.

This is an audit of the uploaded archive and an isolated executable copy, compared with audit 3. The published Claude artifact was not independently revalidated for parity with this archive. No application repairs were made. All 187 extracted source files were checked against the archive and remain identical; audit fixtures changed only the runtime copy and restored scientific files/manifests afterward.

## Verification and scope

| Check | Result |
|---|---|
| Archive | 187 files; 33,334,712 uncompressed bytes |
| Changes from revision 3 | Five additions, 76 byte changes, no removals, 106 unchanged files |
| Meaningful changes | 11 existing text files changed semantically; 62 changes are line-ending conversions; three changed binary files |
| New substantive files | Shared `aggregation.py` and audit-3 regression tests |
| Data continuity | 30/30 scientific Parquets and 5/5 manifests byte-identical to revision 3 |
| Authentic acquisition additions | No scientific provider acquisition adapter or raw scientific NetCDF/HDF/TIFF/Zarr asset added |
| Supplied backend tests | **57 passed**, one Starlette/httpx deprecation warning |
| TypeScript | Fresh `tsc --noEmit` passed |
| Next production build | Passed; Next 15.5.27; root route 287 kB, first-load JavaScript 390 kB |
| Lint | Failed with exit 1: command asks to configure ESLint; no completed noninteractive lint gate |
| Independent checks | 63 main API/kernel checks plus 34 additional scientific/schema checks; separate chart lifecycle/interaction checks |
| Installed wheels | Supplied and clean-built wheels both import and serve tested routes outside the checkout with `DATA_ROOT` configured |
| Browser verification | Actual React components exercised with react-test-renderer; decorative icons stubbed. Full rendered-browser layout, accessibility, and WebGL interaction were not verified |

Independent artificial observations were used only as counterexamples in the audit runtime. They are not genuine NASA observations and were not added to the delivered source. Passing builds/tests establishes the tested behavior, not observation authenticity or statistical calibration.

## Repairs verified in this revision

| Previous failure | Revision 4 result |
|---|---|
| Missing manifest SHA accepted | Typed 422 rejection |
| Omitted QA/coverage declarations allowed missing standard columns | Gridded bindings now require the standard columns if declarations are omitted |
| Declared wrong binding, canonical unit, readiness, filename, row count, or year bounds | Rejected; unit/readiness/inventory fields also tested individually |
| Corrupt Parquet and missing `year` | Typed 422 rejection |
| Twelve rainfall month labels with one NaN counted as complete | Rejected as insufficient observations |
| Fractional month labels | Typed 422 rejection |
| Canonical precision discarded | A reference 0.001 °C/decade trend is preserved |
| Extra undeclared `value` column overrides `value_display` | Display column now takes precedence when canonical values are absent |
| Daily aggregation uses only the first day per month | Full daily calendar now aggregates all valid days; independent annual-mean and slope references match |
| One observation per year qualifies a daily product | Now rejected |
| All daily QA failed causes a 500 | Now returns insufficient-observations 422 |
| Five-year comparison treated as supported climate evidence | Now `insufficient` |
| Comparison with a 25-year missing gap treated as supported | Now `limited`; policy alpha/dependence are passed into inference |
| Monthly layer disappears due to missing pandas import | Monthly fixture survives; MERRA-2 family size remains 10 |
| Unknown map policy ignored | Now 400 `UNKNOWN_POLICY` |
| MODIS 70% policy mishandled | Full daily data at 75% spatial coverage works in trend and map, with both explicit and default MODIS policy |
| Raster endpoint pretends to return scientific tiles | Honest 501 retained; TileJSON now advertises an empty tile list |
| Bengali narration bypasses validation | Both languages validated; injected Bengali invented numbers/causal text trigger fallback |
| Previously tested cross-field slope/coverage substitutions | Rejected |
| Requested interval replaced by retained interval | Request for 1970–2024 preserves that requested interval and receives a distinct identity; returned response matches stored object |
| Installed data root ignored | Both wheel workflows now use configured data, discover 256 regions, and return 200 for the tested trend and MERRA-2 vector layer |
| CLI/proxy port disagreement | CLI default is now 8005, matching the frontend proxy |
| Hovered old index crashes a shorter result | Transition now passes |
| Old comparison survives target change or late response replaces a new primary result | Old cards are cleared and the invalidated response is ignored |

The original hook-order repair, strict-JSON export, Infinity-coverage rejection, and exact spherical triangle-area repair remain effective in the tested cases. Retain these repairs.

## Remaining findings, in priority order

### V4-01 — Critical — Generated data still produces scientific findings

**Audit lineage: R01.** The data problem has not been repaired. All 30 cache files and five manifests are byte-identical to revision 3. The prior generator-match evidence applies to 26 of these exact files; the other four are unverified, rather than independently established as authentic.

The source database now contains six completed results and seven quarantined results. Quarantining a few old results does not quarantine the underlying generated observations. The normal Bangladesh MERRA-2 request returns 200, 45 eligible years, 100% reported area coverage, `supported_increase`, and NASA provenance. No raw granule lineage or scientific acquisition adapter establishes that the records came from the cited provider.

The frontend headline now uses “Investigative Finding” unless `verification_status` is explicitly `verified`. This is a useful wording repair, but it does not authenticate the input or stop unsupported provider attribution. The hash check establishes byte consistency with a self-declared manifest, not NASA origin.

**Fix:** Quarantine the generator-matched inputs and their derived production results. Keep synthetic records in clearly separated tests only. Acquire real provider observations, or ingest an independently verifiable real-data bundle. Record actual source asset identifiers/checksums, product/version/variable, acquisition time, QA interpretation, physical transformations, geometry/mask lineage, and aggregation. Enable a binding/region after this chain is established.

**Acceptance:** A normal production request either derives a reproducible finding from genuine provider records or returns an explicit unavailable state. None of the generator-matched hashes is eligible for production scientific findings.

### V4-02 — High — Manifest/schema validation still has bypasses and untyped failures

**Audit lineage: R02.** The mandatory digest and several mismatch checks are repaired. Other required metadata remains optional, and schema declarations are not consistently used downstream.

Independent counterexamples:

| Fixture | Actual result |
|---|---|
| Remove the entire manifest `metadata` object | `/trend` returns 200 supported; `/coverage` says unavailable |
| Declare the wrong variable, display unit, and temporal cadence | `/trend` still returns 200 |
| Declare `qa_score=False` and `area_coverage=0` as the manifest QA/coverage columns, removing standard columns | Loader accepts the declarations, but aggregation ignores them; supported trend with reported 100% area coverage |
| String-valued years | Untyped HTTP 500 |
| String-valued coverage | Untyped HTTP 500 |

The shared aggregator hard-codes `qa_passed` and `valid_coverage_pct`. The loader accepts alternative declared column names without mapping them to those canonical names. Missing coverage therefore becomes 100% in aggregation even though the manifest's actual declared coverage is zero. `has_series`, `load_series`, registry readiness, and endpoint evidence also disagree about eligibility: a GISTEMP fixture can be analyzed while coverage still reports its binding as catalogued.

**Locations:** [store.py](sandbox:/workspace/scratch/95441b1b3a97/review-v4/source/backend/src/cache/store.py), `has_series` and `load_series`; [aggregation.py](sandbox:/workspace/scratch/95441b1b3a97/review-v4/source/backend/src/compute/aggregation.py), quality/coverage filtering; [coverage.py](sandbox:/workspace/scratch/95441b1b3a97/review-v4/source/backend/src/api/coverage.py).

**Fix:** Use one required, typed acquisition/series contract and one eligibility decision across endpoints. Validate product/variable, units, analysis cadence, column mappings, readiness, inventory, numeric types, and missing-value semantics before computation or cache reuse. Normalize declared columns into a canonical scientific frame. Preserve genuinely unavailable coverage rather than defaulting it to 100%. Convert schema/type failures into typed errors.

**Acceptance:** The cases above are rejected or explicitly unavailable, and coverage, trend, comparisons, and layers agree on eligibility. Every declared QA failure and zero coverage record is excluded regardless of its input column name.

### V4-03 — High — Native product cadence now breaks the packaged annual series

**Audit lineage: R04.** Shared aggregation treats a frame as daily whenever the binding's native cadence is daily. It does not distinguish raw provider cadence from cached analysis cadence. The packaged MODIS day/night, POWER, and OISST files contain one aggregate row per year, so they fail the newly imposed daily row-count requirement.

On the supplied assets, coverage says `analysis_ready`, `has_cached_series=true`, but trend returns 422 with **zero eligible observations** for Bangladesh MODIS day, MODIS night, POWER, and Bay of Bengal OISST. Their four bindings contain 20 packaged files affected by this representation mismatch. This is an observed availability regression, not a reason to restore generated production data.

**Location:** [aggregation.py](sandbox:/workspace/scratch/95441b1b3a97/review-v4/source/backend/src/compute/aggregation.py), cadence determination.

**Fix:** Declare raw cadence and cached/analysis cadence separately, including aggregation method and eligible temporal support. Apply daily completeness only to raw daily records. Accept genuine pre-aggregated annual inputs only when their lineage and completeness contract can be verified. Make readiness reflect usable eligible support.

**Acceptance:** Real daily inputs and verified annual aggregates take appropriate paths; unusable inputs are reported consistently by coverage and analysis. The generated bundle remains quarantined under V4-01.

### V4-04 — High — Daily completeness counts rows instead of real calendar support

**Audit lineage: R04; new counterexamples.** The valid full-calendar aggregation repair works, but its completeness gate is unsafe:

- **365 copies of January 1 per year** qualify as 20 complete years and produce supported evidence, although each year has one distinct observed day.
- Replacing every February date with **February 31** is accepted and produces supported evidence.
- **205 distinct days/year**, roughly **56.2%** of a non-leap year, qualifies under an explicitly selected **80%** spatial/temporal-coverage policy.

The gate computes `int(365 × policy coverage × 0.7)` and tests the number of finite rows. It neither validates actual dates nor deduplicates days, and it does not use leap-year denominators. The response reports spatial coverage but omits distinct temporal completeness, leaving the missing calendar support difficult to inspect.

**Location:** [aggregation.py](sandbox:/workspace/scratch/95441b1b3a97/review-v4/source/backend/src/compute/aggregation.py), calendar validation and daily aggregation.

**Fix:** Validate full timestamps, enforce a documented duplicate-resolution policy, count unique eligible expected intervals, and use correct calendar denominators. Separate temporal completeness from spatial coverage. Remove the unexplained 0.7 relaxation. For precipitation, require the product's valid accumulation intervals and integrate rates before annual depth summation. Weight monthly temperature means by represented duration when the annual estimand requires it.

**Acceptance:** Duplicate January 1 cannot satisfy a year; February 31 is rejected; a 56.2%-complete year cannot satisfy an 80% temporal policy; leap years, exclusions, and valid precipitation intervals are auditable.

### V4-05 — High — Temperature anomaly conversion is physically wrong

**Audit lineage: R04; new regression.** The new canonical-value path subtracts 273.15 whenever canonical units are K and display units are °C. It also does this for GISTEMP's `temperature_anomaly` parameter.

An independent anomaly fixture with first value **0.5 K relative to a baseline** is returned as **−272.65 °C**. The correct anomaly is **0.5 °C**. A temperature difference has the same numerical magnitude in K and °C; the absolute-temperature offset must not be applied. The slope survives the constant offset, which lets slope-only tests miss the corrupted series.

NASA's GISTEMP documentation describes monthly data as anomalies/deviations relative to baseline means, consistent with the parameter's own definition. No GISTEMP asset is supplied here; this counterexample demonstrates the new path's behavior when that binding is ingested.

**Locations:** [aggregation.py](sandbox:/workspace/scratch/95441b1b3a97/review-v4/source/backend/src/compute/aggregation.py), canonical conversion; [parameters.py](sandbox:/workspace/scratch/95441b1b3a97/review-v4/source/backend/src/registry/parameters.py), `surface_temperature_anomaly`.

**Fix:** Resolve conversion by physical quantity and declared transform: absolute temperature, temperature difference/anomaly, rate, accumulation, scale, and offset. Preserve baseline metadata. Test actual values as well as slopes.

**Acceptance:** 298.15 K absolute temperature becomes 25 °C, while 0.5 K anomaly remains 0.5 °C.

### V4-06 — High — Truthful confidence intervals are rejected as invented point slopes

**Audit lineage: R07; new regression.** Both languages are now validated, and the previous malicious substitutions are rejected. However, the slope regex treats every number immediately before `°C/decade` or `°C/দশক` as the point slope, including a confidence interval's upper endpoint.

The application's own truthful templates for **slope 0.30, interval 0.23–0.36 °C/decade** fail in both English and Bangla because 0.36 is compared with 0.30. A fresh computation on the packaged Bangladesh series also triggers this error and falls back to two generic sentences, removing the interval and coverage from narration. Narrow intervals whose endpoints round close to the point slope can still pass.

**Locations:** [validator.py](sandbox:/workspace/scratch/95441b1b3a97/review-v4/source/backend/src/narration/validator.py), slope patterns; [trend.py](sandbox:/workspace/scratch/95441b1b3a97/review-v4/source/backend/src/api/trend.py), bilingual validation/fallback.

**Fix:** Render typed semantic facts and validate quantities by role: point estimate, lower/upper interval endpoint, coverage, p-value, duration, and baseline. Avoid a generic shared number pool and regexes that cannot distinguish those roles. Validate localized fallbacks and preserve material uncertainty/support context.

**Acceptance:** Truthful intervals with endpoints far from the estimate pass in both languages; reusing an endpoint as the point estimate still fails. Fresh normal narration retains truthful uncertainty and support.

### V4-07 — High — Invalidating a comparison leaves its button permanently busy

**Audit lineage: R12; new regression.** The hover crash and stale comparison cards are repaired. A request-identity guard now prevents invalidated responses from replacing current data. Its loading-state handling is incomplete.

Reproduction: start a Bangladesh–USA comparison, deliver a new Kenya primary result before it resolves, then resolve the old request. The old comparison stays cleared, but the button remains disabled and displays **“Contrasting…”**. The reset effect increments the request ID without resetting `isComparing`; the old request's `finally` can clear that flag only if its ID is still current. Target-change invalidation has the same state-handling omission in source.

**Location:** [chart_area.tsx](sandbox:/workspace/scratch/95441b1b3a97/review-v4/source/frontend/components/investigation/chart_area.tsx), reset effect, target handler, and request `finally`.

**Fix:** Reset loading state when invalidating context, with request ownership/abort handling that prevents an old completion from affecting a newer request. Treat primary identity and comparison target as part of the operation's state.

**Acceptance:** Changing primary or target during a pending request clears old data and permits a new comparison; resolving/rejecting the old request cannot unlock or overwrite an unrelated newer one.

### V4-08 — High — Map and primary trend still apply different inference contracts

**Audit lineage: R06.** Shared aggregation, monthly survival, selected-policy alpha, and MODIS coverage are repaired. The map still calls unadjusted Mann–Kendall, while the primary trend applies its selected dependence treatment.

An independent correlated-series fixture returns primary **p=0.68316**, VIF **2.89568**, with dependence adjustment; the map uses **p=0.48734** on the same annual values. On a 15-year increasing fixture, the map sets `is_significant_fdr=true`, while the primary explicitly qualifies evidence as `limited`. A statistically significant short series can exist, but the map lacks the corresponding duration/gap/evidence qualification. Its FDR flag alone is insufficient scientific context.

The layer loop swallows all exceptions and drops affected regions from the testing family. The response has family counts but no frozen family membership, exclusion reasons, per-input hashes, full policy/method context, or immutable layer identity. The frontend map still fetches geographic boundaries only and does not display these scientific endpoints.

**Locations:** [layers.py](sandbox:/workspace/scratch/95441b1b3a97/review-v4/source/backend/src/api/layers.py), regional inference/FDR loop; [map.tsx](sandbox:/workspace/scratch/95441b1b3a97/review-v4/source/frontend/components/ui/map.tsx).

**Fix:** Use one policy-aware inference/support contract for primary, comparison, and layer results. Expose evidence qualification separately from p/q significance. Define the eligible testing family before statistical evaluation, report exclusions/errors, and freeze family/method/input context. Wire scientific layers and inspectable values into the frontend.

**Acceptance:** Identical inputs/policy produce matching raw regional inference; FDR has reproducible membership and exclusions; short/gapped records show their qualifications; the displayed scientific map corresponds to its selected parameter/window/policy.

### V4-09 — High — Result identities still omit changing scientific computation context

**Audit lineage: R05/R08.** Requested-versus-retained interval identity is repaired, and primary cached responses remain frozen. Algorithm identity is not.

The primary hash helper supports geometry and code revision, but its production caller supplies neither. Revision remains `v1.0.0` across aggregation repairs. A normal packaged request reuses its old rounded-value slope **0.2995751342 °C/decade**. A fresh request for 1979–2024, retaining the same actual 1980–2024 years and source data hash, computes **0.2996241369**, matching the new canonical-precision reference. Both claim the same code revision. The difference is small here; the defective invalidation mechanism applies to larger method changes too.

Acquisition time remains the constant `2026-10-01T08:00:00Z`. Geometry/mask, transformations, and schema versions remain absent from scientific identity.

Comparison IDs hash policy ID but omit full policy settings and computation revision. Repeating a comparison changes `created_at` under the same ID. Changing alpha from 0.05 to 0.01 under the same policy ID also keeps that ID while returned provenance changes. Comparisons are not persisted as immutable result objects.

**Locations:** [trend.py](sandbox:/workspace/scratch/95441b1b3a97/review-v4/source/backend/src/api/trend.py), result hash/provenance; [hasher.py](sandbox:/workspace/scratch/95441b1b3a97/review-v4/source/backend/src/cache/hasher.py); [comparisons.py](sandbox:/workspace/scratch/95441b1b3a97/review-v4/source/backend/src/api/comparisons.py), identity construction.

**Fix:** Hash the actual computation revision, full policy, input contracts/transforms, geometry/masks, temporal support, and source identities. Use recorded acquisition timestamps. Issue new identities after method changes, preserving historical results without letting current lookups silently reuse obsolete computation. Freeze comparisons and their testing context as well.

**Acceptance:** Algorithm/geometry/policy changes alter identity; one ID consistently returns one scientific payload and provenance; timestamps trace recorded acquisition.

### V4-10 — High — Dependence-aware uncertainty and real spatial derivation remain incomplete

**Audit lineage: R10.** The geodesic triangle repair remains correct: 63,758,235.12160898 km² matches the independent spherical calculation. The previously validated supplied boundary geometry is unchanged. Do not undo this repair.

The scientific uncertainty kernels have no semantic change in revision 4. Fitted bands independently resample residuals using `rng.choice`; the selected Hamed–Rao dependence treatment is not carried into a calibrated compatible band/slope-interval method. The existing positive-only correction variant is described but not independently calibrated. A VIF flag alone does not establish nominal interval coverage.

Real native-grid QA, masks, physical transformations, cell-area/intersection aggregation, baselines, and actual POWER point coordinates are still not connected to a scientific ingestion pipeline. Correct polygon area alone does not verify the regional observations. Dateline-spanning USA/Fiji bounds still feed naive map bounds. No failure of all supplied country areas is claimed; geometry edge assumptions and genuine scientific derivation are separate issues.

**Locations:** [uncertainty.py](sandbox:/workspace/scratch/95441b1b3a97/review-v4/source/backend/src/compute/uncertainty.py), residual resampling; [serial_corr.py](sandbox:/workspace/scratch/95441b1b3a97/review-v4/source/backend/src/compute/serial_corr.py); [spatial.py](sandbox:/workspace/scratch/95441b1b3a97/review-v4/source/backend/src/compute/spatial.py); [regions.py](sandbox:/workspace/scratch/95441b1b3a97/review-v4/source/backend/src/registry/regions.py); frontend map bounds.

**Fix:** Specify and calibrate the dependence/uncertainty method together, using independent dependent-series references. Connect genuine source grids and point observations to audited QA/physical/spatial derivation. Record masks, geometry versions, baseline support, and sampled coordinates. Handle wrapped geographic bounds.

**Acceptance:** Genuine provider inputs reproduce published regional/point values; dependent-series uncertainty has measured coverage; spatial and dateline behavior are demonstrated.

## Status against audit 3

“Closed” is scoped to the tested defect, not a claim that the entire application or dataset is certified.

| Audit-3 group | Revision-4 status | Assessment |
|---|---|---|
| R01 — Authentic observations | Partial; authenticity blocker open | Headline wording improved; generator-matched inputs and their findings remain eligible |
| R02 — Manifest/schema gate | Partial | Mandatory SHA/default columns/mismatch/corruption repairs work; optional metadata, aliased columns, and typed failures remain |
| R03 — Hook order | Closed, retained | Actual null/result/null/different-result lifecycle passes |
| R04 — Aggregation/completeness | Partial with new regressions | Valid-month, precision, full-calendar mean repaired; native-vs-cache cadence, unique daily support, and anomaly conversion fail |
| R05 — Comparisons | Partial | Duration/gap/alpha/dependence policy applied; immutable context and calibrated uncertainty remain |
| R06 — Scientific layers | Partial | Monthly survival/policy/threshold repaired; inference parity, family context, and scientific frontend wiring remain |
| R07 — Narration | Partial with new regression | Both languages and previous malicious substitutions checked; truthful CI rejected; semantic validation remains incomplete |
| R08 — Frozen identity | Partial | Requested interval identity repaired; algorithm/geometry/acquisition context still incomplete |
| R09 — Infinity/JSON | Closed for tested defects, retained | Invalid coverage rejected and strict export succeeds |
| R10 — Scientific/spatial methods | Partial | Correct area retained; real derivation, compatible uncertainty, baselines/datelines remain |
| R11 — Configured installed workflow | Closed for tested configuration defect | Supplied and fresh wheels work with external `DATA_ROOT`; external bundle authenticity remains R01 |
| R12 — Chart lifecycle/state | Partial with new regression | Hover/stale-card repairs work; invalidation can lock comparison loading |

This gives **three scoped closed groups and nine partial groups**. It is not an overall readiness score.

## Remaining delivery and product requirements

| Area | Remaining action/evidence |
|---|---|
| Single-port delivery | Next still runs at 3005 with a server-side proxy to FastAPI 8005. Add the agreed static export and FastAPI static serving. A “static” prerendered route in build output is not an exported single-port app |
| Framework target | Delivered lock remains Next 15.5.27, Tailwind 3.4.19, raw MapLibre 5.24.0; requested Next 16.3.6+/Tailwind 4/mapcn/shadcn target is incomplete. This is a requirement mismatch, not a vulnerability finding |
| Reproducible dependencies | Python minimum-version ranges remain unlocked. Define supported versions and an installable offline dependency/data bundle |
| Lint/CI | Configure a noninteractive ESLint command with hook rules; current `npm run lint` exits 1 at setup. Add independent semantic cases for this audit's failures |
| Test precision | Existing mismatch tests sometimes change several fields at once, so rejection proves only the first encountered check. Add individual bad-field cases, positive truthful-CI cases, unique-day/impossible-date cases, and pending-request lifecycle cases |
| Typed contracts | Replace important frontend `any` and unstructured backend scientific dictionaries with versioned response schemas. Distinguish unavailable values, point support, area support, temporal completeness, and QA exclusions |
| Scientific interactions | Connect numeric/scientific map modes, observed/anomaly/evidence/coverage inspection, actual seasonal computation, and timeline/playback. The seasonal tab remains explanatory text |
| Date/support selection | Derive selectable windows from verified binding/region support instead of fixed 1980–2024 controls. Expose raw versus retained counts, exclusions, and expected intervals |
| Offline readiness | Health reports an environment-derived flag, and the interface badge is hard-coded. Report actual guard/asset readiness and test the complete installed app with external networking unavailable |
| Accessibility/localization | Verify keyboard operation, labelled controls, drawer focus trapping/restoration, chart/table alternatives, and complete Bangla semantics in a rendered browser. Localized button text and component tests do not close this requirement |
| Performance | Measure large boundary loading/hover/highlighting, computation/caching, and request limits. Current first-load JavaScript is 390 kB; no full browser-performance result is claimed |
| Documentation | Update outdated test counts and unsupported claims about authentic acquisition, wired spatial aggregation, locked dependencies, offline completeness, or implemented views. Record exact supported capabilities and unavailable states |
| Earth-system breadth | The registry remains seven temperature/precipitation parameters; broader vegetation, cryosphere, water, composition, and radiation ingestion/analysis is absent. Enable additional domains after genuine ingestion and validation |

Comparison `equal_rate` still uses a hard-coded near-zero point-estimate threshold. If this label is intended to establish practical equivalence, define the equivalence margin and uncertainty criterion; otherwise label it as an estimate rather than established equality. Likewise, MK direction and Sen slope are different summaries: an audit fixture has MK S=0 and a nonzero Sen slope, while the current primary evidence correctly remains inconclusive.

## Recommended repair order

1. Quarantine the generator-matched data and derived results; establish one genuine provider acquisition/lineage path.
2. Enforce one typed data/manifest/eligibility contract, with explicit cached cadence and quantity-aware physical transformations.
3. Repair real-date/unique-interval completeness and semantic bilingual narration, then align primary/comparison/map inference and identities.
4. Repair comparison loading ownership and connect actual scientific layers to the interface.
5. Finish single-port delivery, target stack, dependency/lint gates, offline readiness, accessibility, and documentation.

The supplied 57 tests should stay, but passing them is insufficient until the independent counterexamples above become acceptance tests with the stated outcomes.

## Evidence and primary references

The companion `Earth_System_Trend_Detective_Revision_4_Evidence.json` contains hashes, status mappings, verification logs, API/kernel outputs, chart results, installed-wheel evidence, source-preservation checks, and executable audit harnesses. Some main probe names retain historical phrases such as “accepted” or “still passes”; **interpret their recorded outcomes**, not those historical names.

- [NASA GISTEMP documentation](https://data.giss.nasa.gov/gistemp/), accessed 2026-10-01: identifies downloaded observations as anomalies/deviations from baseline means. This supports the anomaly interpretation; the faulty conversion was established by the local fixture.
- [SciPy Theil–Sen documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.theilslopes.html), accessed 2026-10-01: defines the pairwise-median slope estimator and slope interval. Independent slope references used the installed SciPy runtime; current online documentation can be a different release.
- Audit-3 evidence establishes the previous exact generator matches and geometry checks. Revision-4 hashes were freshly compared, so inherited conclusions are explicitly tied to unchanged inputs/source.
