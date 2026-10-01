# Earth System Trend Detective: Research & Engineering System

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-blue)](backend/pyproject.toml)
[![FastAPI](https://img.shields.io/badge/FastAPI-1.0.0-009688.svg)](backend/src/main.py)
[![Next.js](https://img.shields.io/badge/Next.js-15.5-black)](frontend/package.json)
[![Offline](https://img.shields.io/badge/Mode-OFFLINE=1_Enforced-emerald.svg)](backend/src/cache/guard.py)
[![Tests](https://img.shields.io/badge/Tests-37%20Passed%20(100%25)-brightgreen)](backend/tests/)

Welcome to **Earth System Trend Detective**, an offline-first, scientifically rigorous web investigation platform for Earth observations and climate change detection. Users select administrative countries, territories, or ocean basins on an interactive 2D flat map, choose a physical parameter (such as near-surface air temperature, day/night land-surface temperature, sea-surface temperature, or precipitation) and a temporal window, and receive an auditable, statistically defensible change investigation.

---

## 🌟 Core Scientific Principles & Engineering Guarantees

1. **Strict Offline First Execution (`OFFLINE=1`)**: Complete physical separation between external data discovery/ingestion (via NASA Earthdata MCP and `earthaccess`) and deterministic local computation. The runtime FastAPI service and Next.js frontend execute zero network calls during user requests. Un-cached selections produce actionable RFC 9457 problem responses (`CACHE_MISS_OFFLINE`), never implicit downloads.
2. **Area-Weighted Cell Aggregation ([Equation 1](file:///a:/terra%20odeesy%20detective/docs/04_geographic_support_and_country_aggregation/README.md#16))**: National trends are derived from geodesically area-weighted spatial aggregation over native satellite/reanalysis grid cells. Single-point centroid data (e.g. NASA POWER) are preserved strictly as named point samples.
3. **Rigorous Parameter Separation**: Near-surface air temperature (2m), Land Surface Temperature (LST Day / Night via MODIS clear-sky overpasses), Sea Surface Temperature (NOAA OISST), and blended surface-temperature anomalies (NASA GISTEMP v4) are managed as distinct parameters with dedicated physics, QA decoders, and units.
4. **Statistical Rigor ([Equations 2–5](file:///a:/terra%20odeesy%20detective/docs/06_statistical_contract_and_interpretation/README.md#20))**: Dual reporting of magnitude (Theil-Sen median pairwise slope per decade with joint intercept) and evidence (Mann-Kendall test with tie corrections, Hamed-Rao serial autocorrelation adjustment, and continuity-corrected $Z$/$p$-values). Inconclusive evidence is explicitly decoupled from "flat / no change".
5. **Deterministic Bilingual Narration (English & বাংলা)**: Exactly two plain-language sentences rendered from typed claim frames validated against raw JSON Pointers, eliminating LLM hallucinations.
6. **2D Flat Cartography**: MapLibre GL JS with custom local vector/GeoJSON layers (pitch 0°, no 3D globe or Cesium dependencies), paired with polar views for cryospheric observations.

---

## 📁 Repository Architecture

```text
.
├── backend/
│   ├── pyproject.toml              # Locked dependencies & pytest configuration
│   ├── src/
│   │   ├── main.py                 # FastAPI application & OFFLINE=1 lifespan guard
│   │   ├── api/                    # Endpoints (/trend, /regions, /parameters, /comparisons, /results)
│   │   ├── compute/                # Pure scientific kernels (MK, Theil-Sen, STL, Hamed-Rao, Spatial)
│   │   ├── registry/               # Typed schemas (Parameters, Bindings, Policies, Regions, Layers)
│   │   ├── cache/                  # Parquet/Zarr reader, SQLite index, SHA-256 hasher, egress guard
│   │   └── narration/              # Deterministic English & Bangla claim renderer & validator
│   └── tests/                      # 25 test cases verifying Table 19 criteria & API contracts
├── frontend/
│   ├── app/                        # Next.js 15 App Router shell & responsive workspace
│   ├── components/
│   │   ├── ui/map.tsx              # Reviewed 2D MapLibre GL JS flat map (Pitch 0°)
│   │   └── investigation/          # SelectionRail, ResultPanel, ChartArea, ProvenanceDrawer
│   ├── lib/                        # Formatters and authentic Bengali numeral converters
│   └── public/offline/             # Local styles, GeoJSON country boundaries, offline assets
├── data/
│   ├── cache/                      # Local Parquet series (MERRA-2, MODIS, OISST, POWER)
│   ├── manifests/                  # Dataset provenance metadata, checksums, DOIs
│   └── regions/                    # High-fidelity Natural Earth & Marine Regions GeoJSON
├── docs/                           # Complete 15-chapter documentation library
├── LICENSE                         # Apache-2.0 License
└── README.md                       # This document
```

---

## 🔬 Mathematical Formulations

### 1. Geodesic Area-Weighted Regional Mean (Equation 1)
$$\bar{x}_{R,t} = \frac{\sum_{c \in R} a_c v_{c,t} x_{c,t}}{\sum_{c \in R} a_c v_{c,t}}$$
- $a_c$: Geodesic cell intersection area with region polygon $R$ ($m^2$).
- $v_{c,t}$: Observation validity indicator (cloud/QA filtered).
- Dynamic valid coverage fraction $C_t = \frac{\sum a_c v_{c,t}}{\sum a_c}$ reported alongside the mean.

### 2. Mann-Kendall S Statistic & Tied Variance (Equations 2 & 3)
$$S = \sum_{i=1}^{n-1} \sum_{j=i+1}^n \operatorname{sgn}(y_j - y_i)$$
$$\operatorname{Var}(S) = \frac{n(n-1)(2n+5) - \sum_{k=1}^g t_k(t_k - 1)(2t_k + 5)}{18}$$

### 3. Continuity-Corrected Standardized Z & Two-Sided $p$-Value (Equation 4)
$$Z = \begin{cases} \frac{S - 1}{\sqrt{\operatorname{Var}(S)}} & \text{if } S > 0 \\ 0 & \text{if } S = 0 \\ \frac{S + 1}{\sqrt{\operatorname{Var}(S)}} & \text{if } S < 0 \end{cases}, \qquad p = 2[1 - \Phi(|Z|)]$$

### 4. Theil-Sen Median Pairwise Slope & Joint Intercept (Equation 5)
$$\hat{\beta} = \operatorname{median}_{i < j} \left( \frac{y_j - y_i}{t_j - t_i} \right), \qquad \hat{b} = \operatorname{median}_i [y_i - \hat{\beta}(t_i - t_{\text{ref}})]$$
- $t_j - t_i$: Elapsed time in decimal years ($365.2425$ days/year).
- Reported slope is scaled to **per decade** ($\hat{\beta}_{\text{decade}} = 10 \cdot \hat{\beta}$).
- **Uncertainty Band**: Pointwise bootstrap band resampling residuals and evaluating joint $(\hat{\beta}^*, \hat{b}^*)$ quantiles.

---

## 🛰️ Catalogued & Enabled Datasets

| Dataset Binding ID | Collection / Version | Provider | Parameters | Cadence | Grid Support | Offline Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `NASA_MERRA2_M2TMNXSLV` | M2TMNXSLV v5.12.4 | NASA GMAO | `air_temperature_2m` | Monthly (1980–2024) | 0.5° x 0.625° | **Active Cache** |
| `MODIS_MOD11A1_061_DAY` | MOD11A1 v061 | NASA LP DAAC | `land_surface_temperature_day` | Daily (2000–2024) | 1 km Sinusoidal | **Active Cache** |
| `MODIS_MOD11A1_061_NIGHT`| MOD11A1 v061 | NASA LP DAAC | `land_surface_temperature_night`| Daily (2000–2024) | 1 km Sinusoidal | **Active Cache** |
| `NOAA_OISST_V2_1` | OISST v2.1 | NOAA NCEI | `sea_surface_temperature` | Daily (1981–2024) | 0.25° Ocean Grid | **Active Cache** |
| `NASA_POWER_DAILY_POINT` | POWER Point v2.0 | NASA LaRC | `point_air_temperature` | Daily (1981–2024) | Centroid Point | **Active Cache** |
| `GPM_IMERG_FINAL_V07` | GPM 3IMERGM V07B | NASA GES DISC | `precipitation_total` | Monthly (2000–2024) | 0.1° Regular Grid | Catalogued |
| `NASA_GISTEMP_V4` | GISTEMP v4 | NASA GISS | `surface_temperature_anomaly` | Monthly (1880–2024) | 2.0° Coarse Grid | Catalogued |

---

## 🚀 Quickstart & Offline Installation

### Prerequisites
- Python 3.11, 3.12, or 3.13
- Node.js 20+ or 24+ and npm

### 1. Launch FastAPI Scientific Backend
```bash
cd backend
python -m uvicorn src.main:app --host 127.0.0.1 --port 8005
```
Backend API interactive documentation is available at: `http://127.0.0.1:8005/docs`.

### 2. Launch Next.js Frontend Workspace
```bash
cd frontend
npm install
npm run dev
# Or run production bundle:
# npm run build && npm run start
```
Open `http://localhost:3005` in your browser.

### 3. Run Scientific Verification Test Suite
Execute the full test matrix verifying all 12 Table 19 criteria and API contracts:
```bash
cd backend
python -m pytest tests/ -v
```
*(All backend unit and regression tests execute and pass in offline mode).*

---

## 🌐 API Endpoint Contract

| Endpoint | Method | Purpose |
| :--- | :--- | :--- |
| `GET /regions` | GET | Search supported countries, territories, and ocean basins |
| `GET /parameters` | GET | List physical parameters and associated dataset bindings |
| `GET /coverage` | GET | Inspect temporal and spatial support for region and parameter |
| `GET /trend` | GET | Compute deterministic trend investigation (Theil-Sen, MK, Narration) |
| `POST /comparisons`| POST | Compute paired difference series contrast between two regions |
| `GET /layers/{id}/tilejson` | GET | TileJSON 3.0 metadata for scientific map overlays |
| `GET /tiles/{id}/{z}/{x}/{y}` | GET | Returns 501 (Raster tiles unavailable; vector GeoJSON supported) |
| `GET /layers/{id}/geojson` | GET | Regional summary GeoJSON with Benjamini-Hochberg FDR $q$-values |
| `GET /results/{id}`| GET | Retrieve frozen, immutable result object by SHA-256 hash |
| `GET /results/{id}/export` | GET | Download complete reproducibility bundle (JSON) or raw series (CSV) |
| `GET /health` | GET | Verify offline enforcement status and runtime version |

---

## 📜 Software Licensing

- **Source Code**: Licensed under the [Apache License, Version 2.0](LICENSE).
- **Cartographic Boundaries**: Natural Earth public domain vector data.
- **Scientific Citations & Datasets**: Provided under fair research and educational use adhering to respective NASA, NOAA, and WMO distribution policies. See [`docs/15_references_and_dataset_directory/README.md`](docs/15_references_and_dataset_directory/README.md).