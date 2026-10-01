> **Navigation:** [← 07 Derived Indicators and Special Investigations](../07_derived_indicators_and_special_investigations/README.md) | [Table of Contents](../README.md) | [09 Interface and Interaction Design →](../09_interface_and_interaction_design/README.md)

---


# 8 Flat map components and scientific layers

Use mapcn for the React component shell and MapLibre GL JS for scientific map sources and layers. The interface is a flat 2D map: pitch zero, no terrain, no globe projection, no 3D buildings, and no tilt control. Keep globe-oriented dependencies out of the project. Country outlines, custom raster layers, legends, and selectable regions supply the investigation experience.

**Table 11  Flat map components and scientific layers**

| Option | Role and strengths | Recommendation |
| :--- | :--- | :--- |
| mapcn with MapLibre GL JS | React components, controls, theme integration, access to the underlying map | Preferred main map; retain local ownership of the copied components [68] |
| Direct MapLibre GL JS | Full control over vector, raster, GeoJSON and feature state | Use where a scientific interaction needs access beyond the wrapper [69] [70] |
| OpenLayers | 2D projection support and raster reprojection | Use an isolated polar workspace if needed for complete polar coverage [71] |
| Commercial satellite tile service | Visual geographic context with provider attribution | Optional online mode, after access and permitted caching are established |

## 8 1 mapcn integration for the selected stack

The documented setup uses a Tailwind and shadcn/ui project, then adds the map component through the shadcn registry. Use the official mapcn project and reviewed component source. Pin the imported source revision and dependency versions so future registry changes do not silently alter offline behavior. [[2]](../15_references_and_dataset_directory/README.md#ref-2) [[68]](../15_references_and_dataset_directory/README.md#ref-68)

The current default loads CARTO basemaps and a versioned worker from unpkg. Replace both for the local edition. Copy the installed MapLibre worker and shared module side by side into public assets and configure the worker URL locally. Inspect the selected component revision rather than assuming those filenames will remain unchanged across upgrades. [[2]](../15_references_and_dataset_directory/README.md#ref-2)

Use a local custom style or the documented blank map mode with project-owned geographic layers. Keep light and dark styles local. Integrate selection and committed application state through the map ref and controlled viewport facilities where suitable. Preserve custom layers after a style change or avoid resetting the style during an investigation. [[72]](../15_references_and_dataset_directory/README.md#ref-72)

Do not assume that an open-source map component includes unlimited basemap rights. mapcn's repository identifies separate CARTO terms. For the initial offline world map, locally prepared Natural Earth context avoids dependence on that hosted default. Retain attribution for any additional source. [[68]](../15_references_and_dataset_directory/README.md#ref-68) [[54]](../15_references_and_dataset_directory/README.md#ref-54)

## 8 2 Layer inventory and rendering contract

Build layers from the catalog's scientific arrays and computed results. Ready-made WMTS layers can help during online exploration, but a visually available overlay is not a substitute for a quantitative, QA-aware trend product. A custom scientific layer is usually a server-prepared numerical field plus a rendered raster or vector representation.

**Table 12  Layer inventory and rendering contract**

| Layer mode | Data behind it | Required legend or inspector |
| :--- | :--- | :--- |
| Observed state | Eligible values for the chosen time or composite | Quantity, unit, time support, source, nodata and native support |
| Anomaly | Values minus the declared reference | Reference period, method, zero-centered scale |
| Trend slope | Per-cell or per-region fitted estimate for a fixed window | Per-decade unit, window, aggregation and eligible sample support |
| Evidence | Corrected q values or named regional inference | Adjustment method, family, threshold and ineligible mask |
| Coverage and QA | Valid area, sample count, exclusions or quality class | Thresholds, reasons and denominator |
| Context | Terrain, imagery, land cover or event features | Provider, date, legend and appropriate observational meaning |

Render continuous fields as local raster XYZ tiles prepared from a source or result field. Use vector tiles or small GeoJSON for country selection, region summaries, and event geometry. Store the numerical result separately so clicking a location returns the actual value and QA; never recover science by reading a tile color. MapLibre supports these source types, but the backend must supply the quantitative layer contract. [[69]](../15_references_and_dataset_directory/README.md#ref-69)

Use appropriate reprojection for display while performing scientific aggregation on the native analysis grid. Preserve exact class and quality values with nearest-neighbor display; any smoothing of continuous fields must be declared and must not alter the inspector's source value. Do not imply that extra zoom reveals new scientific detail beyond the native support.

Separate the map's observation-time cursor from the trend analysis interval. A slider showing one monthly state must not quietly change the interval used by the slope layer. Display the committed interval beside the active trend legend, chart, and evidence panel.

Use data-derived or physically chosen limits with a disclosed policy. Keep comparison maps on the same scale. Offer a robust clipped scale only with the clipping limits visible. A positive anomaly is not automatically harmful, and a negative slope is not automatically beneficial; use neutral physical language.

## 8 3 Polar coverage and the meaning of global

Standard Web Mercator tiled maps stop near 85.051 degrees latitude. A sea-ice project must not silently exclude the poles. Keep the principal world map flat and provide a flat polar view using OpenLayers with appropriate northern or southern projections when the selected product needs it. Use the source grid and CRS metadata, rather than assigning EPSG:3413 or EPSG:3031 to every polar product indiscriminately. [[69]](../15_references_and_dataset_directory/README.md#ref-69) [[71]](../15_references_and_dataset_directory/README.md#ref-71)

Share region, parameter, analysis interval, legend, and result id between the world and polar views. A view switch must not rerun a different scientific estimator. Handle wraparound explicitly so an antimeridian-crossing region is neither duplicated in statistics nor visually lost.

## 8 4 Satellite imagery quality and practical choices

High-quality visual imagery and a high-quality trend estimate serve different purposes. Select imagery by native support, acquisition date, cloud conditions, spectral bands, geolocation, seasonal comparability, coverage, and permitted use. A sharp mosaic can contain scenes from different dates; it is geographic context until a repeat-observation analysis establishes a scientific change product.

**Table 13  Satellite imagery quality and practical choices**

| Imagery source | Use and strengths | Constraints for this project |
| :--- | :--- | :--- |
| Landsat Collection 2 | Repeat optical and surface-temperature science products | Surface-temperature output grid size does not equal native thermal support; preserve QA and known gaps [51] |
| NASA HLS | Harmonized 30 m surface reflectance for repeat land observations | Reflectance is not an LST measurement; cloud-free observation availability varies [44] |
| Maxar or Vantor basemaps | Detailed commercial context; documented HD offerings include 30 cm and 15 cm products | Verify native versus enhanced detail, scene dates, AOI coverage, price and storage rights [73] |
| Google Map Tiles API | Familiar 2D satellite context where licensed and available | Attribution required; do not prefetch or cache for an offline edition contrary to the service policy [74] |
| Local open geographic context | Reliable overview and offline region selection | Lower visual detail, but independent of a remote imagery service |

Recommend an open local overview as the default, scientific Landsat or HLS layers for selected investigations, and a clearly labeled optional commercial context switch. Store licensed imagery separately from publicly redistributable scientific data. No single provider can be called universally highest quality without evaluating the requested place, date, bands, and use.

## 8 5 Evaluation of the proposed MapLibre plugins

The two supplied listings lead to CarbonPlan's zarr-layer and Open-Meteo's weather-map-layer. The duplicate weather link identifies the same plugin. Use their maintainers' repositories to verify capabilities and pin releases. [[75]](../15_references_and_dataset_directory/README.md#ref-75) [[76]](../15_references_and_dataset_directory/README.md#ref-76)

**Table 14  Evaluation of the proposed MapLibre plugins**

| Candidate | Verified capabilities | Decision for this application |
| :--- | :--- | :--- |
| CarbonPlan zarr-layer | Zarr v2 and v3, dimension selectors, GPU coloring, custom stores, projection metadata and multiscales | Strong candidate for displaying local numerical climate arrays; prototype beside local raster tiles [77] |
| Open-Meteo weather-map-layer | Custom om protocol for OM weather files, worker and WebAssembly assets; repository warns it is under construction | Optional weather-context experiment; keep outside the default scientific bundle [78] |
| Project local raster tiles | Versioned scientific fields prepared by Python, simple local delivery | Reliable fallback and initial production path; numerical values remain separately queryable |

For zarr-layer, use a local read-only Zarr URL or an explicitly local compatible store, complete metadata and chunks, and tested codecs. The renderer requires multiscales for high-resolution data. Its default queries follow the displayed resolution; the documented finest option removes camera dependence. Debounce selector updates and handle readiness errors. [[77]](../15_references_and_dataset_directory/README.md#ref-77)

Keep the scientific contract in FastAPI. A browser polygon query is not automatically a geodesically area-weighted national estimator, and a display pyramid can change values with zoom. Use backend values for reported national statistics and provenance. A client query can be a labeled inspection aid after parity testing against the selected native analysis level.

Validate CRS, cell edges versus centers, latitude orientation, fill values, scale and offset, QA masks, selector names, and pyramid reduction rules during preparation. Use consistent units and color limits. A class or evidence pyramid cannot use the same averaging rule as temperature. Custom shaders may format or inspect data, but must not become an untracked second scientific estimator.

The inspected zarr-layer package declares MIT licensing and broad map-library peer dependencies. A wildcard peer declaration does not prove compatibility with every mapcn, MapLibre, Next or browser release; verify the chosen versions through a production build and real rendering tests. [[79]](../15_references_and_dataset_directory/README.md#ref-79)

Open-Meteo's demonstration reads model-run data from remote storage, with worker and WebAssembly loading. Its seamless mode can switch between model domains as zoom changes. That is useful context but must not change the dataset used by a frozen climate investigation. Offline use would require locally available OM assets, metadata, decoding modules and verified delivery behavior. A Zarr cache does not become an OM source merely by renaming its URL. [[78]](../15_references_and_dataset_directory/README.md#ref-78)

The weather plugin is labeled GPL-2.0; the project requests Apache-2.0. Apache's compatibility guidance distinguishes GPLv2 from GPLv3. Do not assume that bundling this plugin preserves the intended license; verify the exact release and applicable grant before distribution. The recommended default remains the MIT Zarr candidate or project-rendered tiles. This is a dependency decision to resolve before adoption, not a reason to stop building the map. [[80]](../15_references_and_dataset_directory/README.md#ref-80) [[81]](../15_references_and_dataset_directory/README.md#ref-81)

Prototype one local temperature array, one nodata mask and one backend trend field. Test selection at several zoom levels, scale and offset exactly once, missing chunks, a time change during loading, style reload, unmount cleanup, blocked internet access, and pixel-versus-backend value parity. Choose Zarr display only after these gates pass; keep the simpler tile path available for unsupported codecs, hardware or datasets.



---

> **Navigation:** [← 07 Derived Indicators and Special Investigations](../07_derived_indicators_and_special_investigations/README.md) | [Table of Contents](../README.md) | [09 Interface and Interaction Design →](../09_interface_and_interaction_design/README.md)
