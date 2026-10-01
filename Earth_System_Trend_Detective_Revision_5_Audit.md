# Earth System Trend Detective — audit 5

Reviewed 2026-10-01. Input: `earth-system-trend-detective(5).zip`, SHA-256 `a941cbf2a76217e06dafe81098a109e0be03cd531d512de8225b4374a1b3a389`.

**Revision 5 repairs many of audit 4's reproducible failures. The backend tests, TypeScript, ESLint, Next 16.3.8 build, and source-tree single-port delivery all pass. The principal blocker remains unchanged: the application still publishes scientific findings from generator-matched observations rather than verified NASA/partner acquisition.**

All 30 scientific Parquet files and all five manifests are byte-identical to revision 4. The same 26 files previously reproduced exactly from the original synthetic generator remain present; the other four remain unverified. Upgrading result revision tags and quarantining older results does not establish authentic observation lineage.

This audit compares the uploaded archive with revision 4, retests prior failures, and exercises additional schema, policy, concurrency, export, and delivery cases. The Claude-published artifact was not revalidated for parity with this archive. No application fixes were made. All 219 extracted source files remain identical to the uploaded archive. Artificial counterexamples were confined to an isolated runtime copy and its scientific files/manifests were restored.

## Verification

| Check | Result |
|---|---|
| Archive | 219 files; 49,412,246 uncompressed bytes |
| Changes from revision 4 | 32 additions, 20 changed files, no removals, 167 unchanged files |
| Existing source changes | 17 semantic text changes, three binary changes; no line-ending-only changes |
| Scientific data | 30/30 Parquets and 5/5 manifests unchanged |
| Provider acquisition additions | No scientific acquisition adapter or raw provider scientific asset added |
| Fresh frontend dependencies | Exact lock installed using `npm ci`; 418 packages |
| Backend tests | **67 passed**, one Starlette/httpx deprecation warning |
| TypeScript | Passed |
| ESLint | Passed, using the new noninteractive command/configuration |
| Production build | Passed: **Next 16.3.8**, static export generated |
| Independent API/kernel checks | 63 prior-case checks, 34 additional checks, 27 new edge checks — **124 recorded checks**, separate from supplied tests |
| React checks | Actual chart component tested for hooks, hover, stale responses, invalidation, and overlapping requests; decorative icons stubbed |
| Real single-port HTTP | Uvicorn with `OFFLINE=1`: HTML, nine referenced JS/CSS assets, `/api/health`, 256 regions, trend, offline style, and primary CSV export returned 200 |
| Wheels | Supplied and fresh-built Python modules match source after line-ending normalization; configured backend routes work outside the checkout |
| Installed wheel frontend | `/` returns 404: frontend export is not in the wheels and no frontend-root setting is provided |
| Scope limit | Full rendered-browser layout, accessibility, WebGL interaction, and statistical interval calibration were not verified |

Source-tree single-port delivery is now a verified repair. This does not certify the scientific inputs or establish a complete browser-level offline workflow.

## Repairs verified

| Audit-4 failure | Revision-5 outcome |
|---|---|
| Entire manifest metadata object absent | Typed 422; coverage does not mark that case ready |
| Explicit wrong variable, display unit, or cadence | Rejected by the analysis loader |
| Declared alternate QA/coverage columns ignored | Actual boolean false/zero coverage now mapped and excluded |
| String-valued numeric years/coverage cause 500 | Numeric strings are normalized; nonnumeric year/coverage values produce typed rejection |
| Packaged annual aggregates for native daily products unusable | Packaged MODIS day/night, POWER, and OISST requests are usable again; authenticity remains unresolved |
| Repeated January 1 qualifies as a complete daily year | Rejected |
| February 31 accepted | Typed 422 |
| About 56% daily coverage qualifies under 80% policy | Rejected; expected-day count now uses the year and configured percentage |
| GISTEMP anomaly offset | Fixed: first values 0.5, 0.51, 0.52 remain those °C anomalies |
| Truthful 0.30 estimate with 0.23–0.36 interval rejected | Both supplied English and Bangla templates pass |
| Fresh ordinary narration falls back because of that interval | Fresh normal narration retains the approved interval; no validation error in the tested case |
| Old rounded-value computation reused | New code tag `v1.4.0` yields the canonical-precision reference **0.2996241369403088 °C/decade** |
| Comparison timestamp changes on repeated sequential query | Same comparison ID and frozen payload/timestamp retained |
| Changing alpha/dependence under the same policy ID leaves comparison ID unchanged | Full policy settings now change comparison identity |
| Map p-value differs from primary dependence-adjusted result | Independent correlated fixture now matches: **p=0.683160224949894** |
| Fifteen-year map record promoted by climate-duration significance gate | FDR flag is now false for that fixture; evidence qualification is also emitted |
| Invalidated comparison stays stuck on “Contrasting…” | Prior reproduction is repaired; a new request can start |
| Missing single-port static delivery | Static export and `/api` aliases work through FastAPI over real HTTP |
| Next 15 / interactive lint setup | Next 16.3.8 and configured ESLint both verified |

The hook lifecycle, shorter-series hover, stale-card removal, late-response suppression, finite-month rainfall rule, fractional-month rejection, daily full-calendar mean, strict JSON export, and spherical triangle-area repairs also remain effective. Keep these changes.

## Remaining findings

### V5-01 — Critical — Production data authenticity is still unresolved

**Prior finding: V4-01.** All scientific assets and manifests retain revision-4 hashes, including 26 exact generator matches established in the earlier audit. No provider acquisition adapter or raw scientific input was added.

The delivered SQLite database contains **14 completed results tagged `v1.4.0` and 16 quarantined results**. A normal Bangladesh air-temperature request still returns 200, 45 eligible years, 100% reported area coverage, NASA provenance, and `supported_increase`. POWER is also again served as a supported finding. These are observations of endpoint behavior, not evidence that the observations came from NASA.

The revised quarantine logic recognizes some legacy result metadata/code tags. It does not quarantine generator-matched cache inputs. Recomputing those inputs under `v1.4.0` simply produces new unverified findings. The improved “Investigative Finding” headline remains preferable, but does not replace source verification.

**Fix:** Quarantine the generator-matched scientific inputs and derived production findings. Keep artificial records in isolated test fixtures. Establish real provider acquisition or an independently verifiable external bundle with source identifiers/checksums, product/version/variable, acquisition time, QA definitions, physical transforms, calendar support, and geometry/mask lineage. Set readiness from that evidence.

**Acceptance:** Every production scientific finding traces to genuine provider records. A missing real dataset yields an explicit unavailable state. None of the generator-matched hashes is eligible as production observations.

### V5-02 — High — QA truthiness and incomplete scientific schemas still fail open

**Prior finding: V4-02; string/missing QA mapping is newly demonstrated in the added conversion path.** Mapping alternative columns repairs the old boolean fixture, but `astype(bool)` is not a scientific QA decoder.

| Counterexample | Actual result |
|---|---|
| Declared alternative QA column contains text `"False"` | Supported result; all records treated as passed |
| Same column contains text `"0"` | Supported result |
| Same column contains missing/NaN values | Supported result |
| Observation value is `"not-a-number"` | Trend and comparison return untyped HTTP 500 |
| Same malformed observation through map endpoint | HTTP 200; Bangladesh silently disappears; FDR family shrinks from 10 to 9 |
| Metadata contains only `availability_state="analysis_ready"` | Supported trend despite missing unit/variable/cadence contract |
| Metadata declares wrong variable | Trend rejects it, but coverage still advertises `analysis_ready` and cached support |

Nonempty strings and NaN become true under this boolean conversion. Numeric value-column conversion is outside the typed exception handling that now covers years/coverage. Required metadata fields are still individually optional; `has_series` still uses a weaker gate than analysis.

**Locations:** [store.py](sandbox:/workspace/scratch/95441b1b3a97/review-v5/source/backend/src/cache/store.py), declared-column mapping and readiness; [aggregation.py](sandbox:/workspace/scratch/95441b1b3a97/review-v5/source/backend/src/compute/aggregation.py), value conversion; [coverage.py](sandbox:/workspace/scratch/95441b1b3a97/review-v5/source/backend/src/api/coverage.py).

**Fix:** Define required typed metadata and a canonical scientific frame. Decode QA according to its actual boolean/enum/bitmask contract, explicitly handling missing values and rejecting unknown encodings. Validate all numeric observation fields with typed errors. Share the full eligibility decision across coverage, trend, comparison, and layers. Preserve the reason when a map input fails.

**Acceptance:** False/zero/missing QA cannot qualify through an alternate column. Malformed values yield typed errors, required scientific fields cannot be omitted, and coverage cannot advertise inputs that analysis rejects.

### V5-03 — High — Absence of calendar columns is accepted as proof of a valid annual aggregate

**Prior findings: V4-03/V4-04.** The native-daily-versus-cached-annual repair restores the packaged series. The new inference is based on column presence: with no `day` or `month`, the frame is treated as annual, without a verified annual-aggregation contract.

Two counterexamples qualify as 20-year supported records:

- A daily POWER binding with **one January 1 timestamp per year** and no split `day`/`month` columns. The timestamp column is ignored. Each year has one distinct observed day.
- An annual precipitation frame explicitly containing **`valid_month_count=1`** for every year. The count is ignored, although annual precipitation requires 12 valid months.

The response still describes the binding's native cadence and reports 100% area coverage, without exposing the missing eligible temporal support. These fixtures do not establish a genuine aggregate merely by having one row per year.

**Location:** [aggregation.py](sandbox:/workspace/scratch/95441b1b3a97/review-v5/source/backend/src/compute/aggregation.py), cadence determination and already-annual branch.

**Fix:** Declare cached cadence/statistic separately from native cadence. For verified aggregates, require expected/eligible intervals, QA exclusions, aggregation method, units, and lineage for each year. Parse the supported timestamp schema explicitly. Apply temporal completeness to aggregate provenance rather than inferring it from absent columns. Retain legitimate annual aggregates; do not restore the revision-4 blanket daily rejection.

**Acceptance:** One observed day cannot stand in for a valid daily year. An annual rainfall record with one valid month is ineligible. Genuine pre-aggregated records pass only with reproducible completeness and derivation.

### V5-04 — High — An incompatible policy changes temperature means into totals

**Newly demonstrated; the policy-dependent aggregation condition already existed in revision 4.** The API accepts `precipitation_total_policy` for `air_temperature_2m`. Aggregation treats that policy ID as a reason to sum observations even though the parameter is temperature and its advertised statistic is annual mean.

Using the same valid monthly temperature fixture:

| Request | First annual value | Slope |
|---|---:|---:|
| Standard temperature policy | 25.0 °C | 1.0 °C/decade |
| Precipitation-total policy | **300.0 °C** | **12.0 °C/decade** |

Both requests return 200 and supported evidence. The parameter/unit/annual-mean descriptions remain temperature descriptions, so this is a mislabeled scientific calculation rather than a requested rainfall statistic.

**Locations:** [trend.py](sandbox:/workspace/scratch/95441b1b3a97/review-v5/source/backend/src/api/trend.py), policy selection; [aggregation.py](sandbox:/workspace/scratch/95441b1b3a97/review-v5/source/backend/src/compute/aggregation.py), `is_precip` decision. Comparison/layer callers share that aggregator.

**Fix:** Validate policy/parameter/binding/statistic compatibility. Determine mean, accumulation, rate integration, and conversion from the declared physical quantity/statistic. Selecting thresholds or inference settings must not silently change the physical estimand.

**Acceptance:** The incompatible request receives a typed rejection, or an explicitly valid temperature policy preserves the temperature mean. No policy silently multiplies annual temperature values/slopes by 12.

### V5-05 — High — Real spatial derivation and calibrated dependent uncertainty remain incomplete

**Prior finding: V4-10.** `uncertainty.py`, `serial_corr.py`, `spatial.py`, `seasonal.py`, Theil–Sen, and Mann–Kendall kernels are byte-identical to revision 4. Map/primary p-value parity is repaired, but parity is separate from scientific calibration.

Fitted bands still independently resample residuals with `rng.choice`. The selected dependence treatment is not carried into a demonstrated compatible slope/band uncertainty method. The existing positive-only correction variant has not been independently calibrated for the claimed inference. No new empirical interval-coverage result is supplied.

There is still no genuine source-grid pipeline connecting product-native QA, masks, cell intersections/areas, units, rate accumulation, and regional time series. Baseline derivation and actual POWER sampled coordinates remain incomplete. Monthly temperature means remain unweighted by represented duration. Dateline-spanning USA/Fiji bounds still feed naive map bounds.

The correct spherical area repair remains intact. This audit does not claim that all supplied country areas are wrong.

**Locations:** [uncertainty.py](sandbox:/workspace/scratch/95441b1b3a97/review-v5/source/backend/src/compute/uncertainty.py); [serial_corr.py](sandbox:/workspace/scratch/95441b1b3a97/review-v5/source/backend/src/compute/serial_corr.py); [spatial.py](sandbox:/workspace/scratch/95441b1b3a97/review-v5/source/backend/src/compute/spatial.py); ingestion/geometry lineage.

**Fix:** Specify and independently validate the inference/uncertainty combination. Connect authentic product data to audited physical and spatial derivation, with interval-duration weighting, baselines, point coordinates, and mask/geometry versions. Handle wrapped map bounds.

**Acceptance:** Real provider observations reproduce regional/point values; dependent-series uncertainty has measured calibration; physical, baseline, spatial, and dateline behavior are demonstrated.

### V5-06 — High — The frontend still does not display the scientific map layers

**Prior finding: V4-08.** The backend now uses the same dependence-adjusted inference as the primary and publishes evidence qualification. Its frontend integration remains absent: the map fetches geographic countries and displays selection/hover overlays, without requesting the parameter's scientific layer endpoint.

The FDR response still lacks a frozen family membership/exclusion record, complete selected policy/method context, source hashes, and layer identity. A malformed observation produces an ordinary 200 response with a smaller family and no explanation of the data error. This does not establish that every smaller family is statistically invalid; it shows that the family and exclusion decision cannot be audited from the response.

**Locations:** [map.tsx](sandbox:/workspace/scratch/95441b1b3a97/review-v5/source/frontend/components/ui/map.tsx); [layers.py](sandbox:/workspace/scratch/95441b1b3a97/review-v5/source/backend/src/api/layers.py).

**Fix:** Wire scientific slope/evidence/coverage layers into the selected parameter/window/policy, with legends and numeric inspection. Preserve unavailable states. Define and record eligible FDR family membership, exclusions, method/policy context, inputs, and identity.

**Acceptance:** A parameter/window change updates actual scientific map values. Users can inspect raw p, adjusted q, evidence qualification, units, coverage, and exclusions; the family is reproducible.

### V5-07 — High — Scientific identity and acquisition provenance remain incomplete

**Prior finding: V4-09.** The code bump fixes the observed stale-precision cache, and full policy/computation tags fix the tested sequential comparison identity. Retain both.

Primary identity still omits geometry/mask/source-transformation/schema context; the hash helper's geometry argument is not supplied by the production caller. Comparison identity likewise does not include those contexts. A fixed release tag must also be advanced when the actual computation changes.

Acquisition time remains the literal `2026-10-01T08:00:00Z`. Metadata is drawn from registry templates rather than recorded provider asset acquisition. Comparison `data_sha256` is a 129-character concatenation of two 64-character hashes; the individual hashes are present and valid-length, but that concatenation is not itself a SHA-256 digest.

**Locations:** [trend.py](sandbox:/workspace/scratch/95441b1b3a97/review-v5/source/backend/src/api/trend.py); [hasher.py](sandbox:/workspace/scratch/95441b1b3a97/review-v5/source/backend/src/cache/hasher.py); [comparisons.py](sandbox:/workspace/scratch/95441b1b3a97/review-v5/source/backend/src/api/comparisons.py).

**Fix:** Record actual acquisition and transformations, and include relevant versioned scientific context in identity. Use an explicit set of input hashes or a canonical combined digest, rather than putting a concatenation into a SHA-256 field. Keep immutable historical objects separate from current eligibility.

**Acceptance:** Changing relevant geometry/mask/transform/schema/computation context changes identity; all provenance quantities trace actual acquisition and satisfy their typed format.

### V5-08 — Medium — The repaired CI parser still accepts a wrong point estimate

**Prior finding: V4-06.** Normal truthful English/Bangla templates now pass. A remaining counterexample exploits the parser's assumption that a number preceded by “to” is a CI upper bound:

> The estimated rate for Temperature in Bangladesh over 1980 to 2024 was equal to 0.36 °C/decade.

With true point estimate **0.30** and true CI upper endpoint **0.36**, this incorrect rate statement passes validation with no errors. The nearby “to” causes it to be validated as an interval endpoint. This was tested directly against the validator; the normal supplied templates are not claimed to produce this wording.

**Location:** [validator.py](sandbox:/workspace/scratch/95441b1b3a97/review-v5/source/backend/src/narration/validator.py), unit-bound role inference.

**Fix:** Render and validate approved typed facts by semantic role rather than a nearby word or shared number pool. Point estimate and interval endpoints must remain distinct in every supported rendering.

**Acceptance:** Truthful intervals pass, while an endpoint used as the rate fails regardless of phrases such as “equal to.”

### V5-09 — Medium — Concurrent cache misses return different payloads under one identity

**Related to V4-09; the newly tested case is concurrency.** Sequential primary/comparison reuse works. Two synchronized real API calls that both observe a cache miss return the same ID but different `created_at` values. One response does not equal the subsequently fetched stored object. This occurs for both primary and comparison results.

The numerical fields matched in both tests. The database already uses `INSERT OR IGNORE`, so the stored winner is preserved; this audit does not claim it is overwritten. The losing caller still returns its locally constructed object rather than the canonical stored winner.

**Locations:** [store.py](sandbox:/workspace/scratch/95441b1b3a97/review-v5/source/backend/src/cache/store.py), `save_result`; primary/comparison save-and-return paths.

**Fix:** Atomically create-or-load a result and return the canonical stored winner, or serialize same-identity computation appropriately. Avoid repeating expensive comparison computation before an available cache lookup where possible.

**Acceptance:** Concurrent requests, sequential repeats, `/results`, and export agree on the complete frozen scientific object, including identity timestamp. No numerical mismatch was observed in this audit's concurrency fixtures.

### V5-10 — Medium — Persisted comparisons break series and CSV export routes

**New regression from comparison persistence.** `/results/{comparison_id}` and default JSON export return 200. The same ID's `/series` and `export?format=csv` return untyped **HTTP 500**, because those handlers assume a primary result with `region`, `parameter`, and `series` fields.

**Location:** [results.py](sandbox:/workspace/scratch/95441b1b3a97/review-v5/source/backend/src/api/results.py); comparison storage contract.

**Fix:** Use a tagged/versioned result union and dispatch series/export by result kind. Export the paired difference/common years and relevant region statistics for comparisons, or return an explicit typed unsupported-operation state.

**Acceptance:** Every result kind has a documented export/series contract; persisted comparison IDs never cause these handlers to crash.

### V5-11 — Medium — An old comparison clears a newer request's busy state

**Related to V4-07; original permanent loading lock is fixed.** Reproduction: start comparison A, change the primary result, start comparison B, then finish A while B remains unresolved. The button changes back to enabled “Compute Contrast” even though B is still running.

The old cards remain suppressed, and B can later display the correct result. The issue is operation ownership: `finally` now clears `isComparing` unconditionally, allowing a stale operation to clear a current operation's state and permit duplicate requests.

**Location:** [chart_area.tsx](sandbox:/workspace/scratch/95441b1b3a97/review-v5/source/frontend/components/investigation/chart_area.tsx), invalidation reset and `finally`.

**Fix:** Keep the new loading reset on invalidation, but let only the owning current request clear its busy state. Abort or ignore invalidated operations consistently.

**Acceptance:** Invalidating A permits B to start; completion of A cannot clear B's loading indicator or enable duplicate submissions while B runs.

## Status against audit 4

“Fixed for the prior case” is scoped to the reproduction, not a certification of the whole subsystem.

| Audit-4 item | Revision-5 status |
|---|---|
| V4-01 — Generated production data | **Unfixed**; same inputs/manifests remain eligible |
| V4-02 — Manifest/schema bypasses | Partial: missing object, explicit mismatches, real boolean mapping, year/coverage coercion repaired; V5-02 remains |
| V4-03 — Packaged daily-product aggregates rejected | Fixed for prior availability cases; verified aggregate contract remains V5-03 |
| V4-04 — Duplicate/impossible dates and 56%-under-80% completeness | Fixed for prior split-calendar cases; undeclared annual/timestamp support remains V5-03 |
| V4-05 — Anomaly offset | Fixed |
| V4-06 — Truthful CI rejected | Fixed for normal supplied templates; semantic bypass remains V5-08 |
| V4-07 — Comparison permanently busy | Fixed for prior case; smaller overlapping-request race remains V5-11 |
| V4-08 — Map inference/qualification/frontend | Raw inference and tested duration qualification repaired; family context/frontend remain V5-06 |
| V4-09 — Stale precision result/full comparison identity | Current code invalidation and sequential comparison freezing repaired; provenance/context/concurrency remain V5-07/V5-09 |
| V4-10 — Uncertainty and real spatial derivation | Unfixed substantive methods/ingestion; correct area repair retained |

The new static export, Next 16, and ESLint changes also close specific delivery items that were pending in audit 4. Tailwind 4/mapcn/shadcn and the remaining product requirements are separate.

## Delivery and product work still needed

| Area | Remaining action |
|---|---|
| Installed frontend packaging | Source ZIP single-port delivery works. Both wheels lack frontend assets; with configured external data, backend routes work but `/` is 404. Package assets deliberately or add/document an external frontend-root setting |
| UI stack | Next 16.3.8 target is met. Tailwind remains 3.4.19, raw MapLibre 5.24.0 remains, and requested mapcn/shadcn composition is not implemented |
| Reproducibility | Python dependencies remain minimum-version ranges without a lock. Provide supported versions and an intentional offline dependency/data bundle |
| Typed API/frontend contracts | Core scientific dictionaries and frontend `any` remain. Tag primary versus comparison results; model nullable support and proper hash/interval/QA formats |
| Point support | POWER results still report 100% area coverage and omit actual sampled coordinates from scientific provenance. Distinguish point support, temporal completeness, and spatial area coverage |
| Seasonal/baseline workflows | Seasonal UI remains explanatory text; baseline and actual seasonal computations are not connected to the investigation workflow |
| Controls | Derive selectable dates from verified dataset/region support; retain raw/eligible counts and exclusion reasons instead of relying on fixed 1980–2024 controls |
| Offline readiness | Health/badge status still comes from environment/hard-coded UI rather than complete guard and asset eligibility. Local HTTP with `OFFLINE=1` passed; a full rendered browser with networking unavailable was not tested |
| Accessibility/localization | Verify drawer focus handling, keyboard chart/table use, labelled controls, and complete English/Bangla semantics in a rendered browser |
| Documentation | README still describes Next 15 and older architecture/counts. Update startup/export/installation instructions, methods, limitations, and data authenticity claims to the actual implementation |
| Scientific breadth/performance | Registry remains seven temperature/precipitation parameters. Additional Earth-system domains, real acquisition breadth, heavy-map behavior, computation/request limits, and browser performance need demonstrated implementations |

Comparison `equal_rate` remains a near-zero point-estimate label. If intended as established practical equivalence, define a margin and an uncertainty-based criterion; otherwise describe it as an estimate. A correct significance calculation does not establish equivalence.

## Repair order

1. Quarantine unverified/generated production observations and establish one complete authentic provider lineage path.
2. Enforce typed QA/value/metadata contracts, explicit cached temporal support, and parameter-policy compatibility.
3. Finish real physical/spatial derivation, calibrated uncertainty, scientific map integration, and reproducible testing-family/provenance context.
4. Complete result-kind exports and canonical concurrent response handling; repair comparison loading ownership.
5. Finish frontend packaging/target UI stack, typed contracts, seasonal/support controls, offline/browser/accessibility verification, and accurate documentation.

Keep the 67 supplied tests, and add the concrete edge cases above as acceptance tests. Several current regression tests check structure or change multiple settings together; passing those tests alone does not establish the full scientific contract.

## Evidence

`Earth_System_Trend_Detective_Revision_5_Evidence.json` contains archive/data hashes, source-preservation checks, old-to-new status mapping, test/build/lint logs, 124 API/kernel records, chart lifecycle/overlap results, wheel content/runtime checks, real single-port HTTP outputs, and executable audit harnesses.

Some retargeted historical probe names retain words such as “accepted,” “ignored,” or “rejected.” Recorded status/body and the audit assessment are authoritative; those names identify the previous reproduction rather than asserting the current outcome. Generator-match conclusions are inherited from exact earlier reproduction and freshly tied to the unchanged revision-5 hashes. Kernel/calibration limitations are tied to unchanged scientific modules; no new empirical calibration study is claimed.
