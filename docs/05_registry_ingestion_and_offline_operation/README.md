> **Navigation:** [← 04 Geographic Support and Country Aggregation](../04_geographic_support_and_country_aggregation/README.md) | [Table of Contents](../README.md) | [06 Statistical Contract and Interpretation →](../06_statistical_contract_and_interpretation/README.md)

---


# 5 Registry ingestion and offline operation

Categorize the existing raw datasets through metadata rather than moving files into loosely named temperature or water folders. Preserve original bytes and create explicit bindings from physical parameters to product variables. One dataset can supply several parameters; one parameter can have several scientifically distinct sources.

**Table 5  Registry ingestion and offline operation**

| Registry object | Required fields | Purpose |
| :--- | :--- | :--- |
| ParameterDefinition | id, labels, definition, canonical unit, domain, physical quantity, valid spatial support | Gives the same quantity a stable identity across sources |
| DatasetBinding | collection id, version, DOI or URL, variable, scale, offset, fill values, QA decoder, grid, calendar, observation type | Connects a quantity to a specific source and interpretation |
| AnalysisPolicy | aggregation, eligible record, missingness, baseline, test, dependence settings, slope and band methods | Defines a reproducible scientific question |
| RegionDefinition | stable id, type, parent, geometry version, geometry hash, citation, license | Defines the actual analysis area |
| LayerDefinition | source binding, mode, unit, legend, nodata, native support, tile inventory, attribution | Defines a visual representation without changing the science |
| AcquisitionManifest | files, checksums, retrieved_at, request parameters, granule ids, source URLs, permissions | Makes cached observations traceable and verifiable |

## 5 1 Converting raw files into analysis ready data

Inventory file formats, product versions, time ranges, coordinate systems, calendars, variables, units, and QA fields. Infer possible bindings from metadata, but require a reviewed binding before exposing a scientific result. Quarantine unknown units, duplicate timestamps, unrecognized processing versions, invalid geometries, and undecoded fill values.

Apply the binding's scale and offset once, decode quality flags, normalize units, and keep separate original, decoded, and analysis arrays. Preserve quality masks and reasons for exclusions. Record time bounds for accumulated or composite products, including the final short MODIS composite of a year. Store actual missing values, not zeros or forward-filled source measurements.

Preserve the required POWER daily Parquet files as point data, with one country file and explicit coordinates. Attach a manifest identifying the request time standard, parameter names, source version information available from the provider, and native grid support. Country aggregates from gridded products belong in a separate series collection.

For the first NASA gridded variable, use a pinned MERRA-2 monthly T2M collection such as M2TMNXSLV, with the correct collection citation and documented conversion to Celsius. Its record begins in 1980; the POWER daily interface begins in 1981. Add a separate MODIS day or night LST binding for the user's surface-temperature investigation. The two quantities are never merged into one temperature record. [[27]](../15_references_and_dataset_directory/README.md#ref-27) [[28]](../15_references_and_dataset_directory/README.md#ref-28) [[6]](../15_references_and_dataset_directory/README.md#ref-6)

Store normalized arrays in local Zarr with consolidated metadata where compatible, and regional series in Parquet. Choose chunks for the actual access pattern: time spans over moderate spatial areas for regional extraction, and spatial tiles for map preparation. Profile before choosing chunk sizes. Zarr is a storage format; a Zarr URL can still cause network reads, so local operation requires an explicit local store. [[57]](../15_references_and_dataset_directory/README.md#ref-57)

## 5 2 Offline means a complete declared inventory

Separate the online acquisition command from the API and compute worker. The API may accept a scientific request only against locally available, validated data. OFFLINE=1 must reject remote stores, cloud credentials as a fallback, remote imagery, external MCP calls, and network narration. A missing cache entry produces an actionable missing-data response, never an implicit download.

The local edition includes compiled JavaScript, CSS, fonts, map style JSON, country geometry, required tiles, glyphs, sprites, MapLibre worker files, reference metadata, and English and Bangla templates. Package low-zoom global context plus selected higher-resolution regions. A promise to cache every high-resolution image for every location is neither a practical inventory nor an imagery license.

A cached browser shell can show saved results without internet. New FastAPI calculations need a reachable backend. For genuine offline investigation, run the packaged FastAPI service on the user's computer or a reachable local network. A browser-only edition requires precomputed results or an explicitly implemented in-browser scientific engine; it cannot silently rely on the remote Python API.

**Table 6  Offline means a complete declared inventory**

| Deployment | Works without internet | Limitation to show |
| :--- | :--- | :--- |
| Local frontend and local FastAPI with cached data | New calculations, maps, comparisons, narration, exports | Only installed datasets, regions, and tiles |
| Browser shell with saved results | Existing investigations and cached map areas | New server calculations need a reachable backend |
| Online hosted workspace with cached scientific backend | Normal investigations without upstream data calls | Browser and server connectivity still required |
| Optional licensed imagery mode | Visual context while online | Disable when offline unless the license explicitly permits local storage |

## 5 3 Immutable results and cache keys

Hash the normalized query, dataset versions and input checksums, boundary hash, spatial mask, QA policy, time aggregation, baseline, missingness settings, scientific code version, inference settings, and uncertainty settings. Include the random seed where a bootstrap is used. A change to any of these inputs creates a new result id.

Keep retrieved_at as the actual UTC acquisition timestamp. observation_start and observation_end describe the measurements; analyzed_at describes the computation. Do not substitute the report date or the most recent application launch for data retrieval time. Record provenance as cache for production investigation requests, with original acquisition lineage retained separately.

Write manifests and outputs atomically, verify checksums before use, and reject partial Zarr stores. Retain a lightweight SQLite index of available datasets, regional series, jobs, and result hashes. Mark stale versions visibly. An old validated result can remain reproducible while a new acquisition awaits validation.

## 5 4 NASA Earthdata MCP and acquisition tools

NASA maintains nasa/earthdata-mcp and documents a Streamable HTTP endpoint at https://cmr.earthdata.nasa.gov/mcp/v1. Its current tools cover keywords, collections, granules, services, tools, citations, and variables. Use collection discovery followed by granule verification; collection-level global coverage is not proof that the requested region and dates contain observations. The documented access workflow uses earthaccess for authenticated acquisition. [[3]](../15_references_and_dataset_directory/README.md#ref-3)

**Table 7  NASA Earthdata MCP and acquisition tools**

| Tool or service | Provider status | Use in this project |
| :--- | :--- | :--- |
| NASA Earthdata MCP | Verified NASA organization repository and NASA endpoint | Online discovery, metadata, citation and granule verification before acquisition |
| earthaccess Python library | NASA-supported community library | Explicit ingestion command for download and authentication; local files afterward [58] |
| Direct CMR metadata API | NASA metadata service | Deterministic scripted discovery when no language model is needed |
| datalayer Earthdata MCP server | Third-party project | Optional alternative after capability review; do not label it NASA-maintained [59] |
| Project local scientific tools | Project-owned FastAPI or optional local MCP adapter | Return cached, deterministic scientific results to narration |

Treat discovery suggestions as candidates. An agent may propose a dataset binding, but metadata, granule coverage, QA documentation, and the binding's scientific policy must validate it. Discovery tools do not calculate the approved Mann-Kendall or Theil-Sen result. An API request must never acquire a dataset through MCP to compensate for a missing cache.

Pin the selected MCP implementation or record the remote server tool schema and access time. Store source collection and granule metadata in the acquisition manifest. Keep Earthdata credentials in the ingestion environment; never place them in NEXT_PUBLIC variables or export them in provenance. External service text may help discovery, but it must not override project configuration or execute arbitrary code.



---

> **Navigation:** [← 04 Geographic Support and Country Aggregation](../04_geographic_support_and_country_aggregation/README.md) | [Table of Contents](../README.md) | [06 Statistical Contract and Interpretation →](../06_statistical_contract_and_interpretation/README.md)
