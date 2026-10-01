> **Navigation:** [← 02 Assessment of Supplied Implementation Specification](../02_assessment_of_the_supplied_implementation_specification/README.md) | [Table of Contents](../README.md) | [04 Geographic Support and Country Aggregation →](../04_geographic_support_and_country_aggregation/README.md)

---


# 3 Catalog assessment and corrections

The attached catalog organizes the Earth system into useful domains and correctly emphasizes units, QA, uncertainty, long records, and the distinction between observations and derived indicators. Its repeated domain tables, parameter map, and acquisition list should become one machine-readable registry rather than several separate lists. [[11]](../15_references_and_dataset_directory/README.md#ref-11)

The registry should represent a scientific quantity independently of its sources. A parameter such as land-surface temperature can have several dataset bindings; each binding retains its own measurement definition, version, sampling, and inference policy. Adding a dataset must not automatically create a duplicate parameter in the interface.

**Table 3  Catalog assessment and corrections**

| Catalog item | Research finding | Required correction |
| :--- | :--- | :--- |
| Global surface temperature used alongside LST | GISTEMP is a blended surface-temperature anomaly estimate with a native reference and coarse grid | Name it explicitly; do not present it as satellite LST or a detailed country thermal map [12] |
| Generic NASA SSH link | NASA_SSH_GMSL_INDICATOR is a global mean indicator; NASA_SSH_REF_SIMPLE_GRID_V1 supplies regional anomaly maps | Use the gridded product for regional ocean analysis and the indicator only for global context [13] [14] |
| GRACE fine output grid | JPL mascons can be displayed on a 0.5 degree grid but have much coarser independent support | Preserve mascon identity and leakage uncertainty; do not count display cells as independent measurements [15] |
| Generic SMAP L3 and L4 | L4 root-zone moisture uses assimilation into a land model; L3 is a different observation product | Create separate surface and root-zone parameter bindings and observation labels [16] |
| Sea ice CDR without a pinned release | The inspected official record now documents G02202 Version 6 and an AMSR2 input transition from 2025 | Pin a tested release and retain transition metadata; avoid assuming an older guide describes current inputs [17] |
| NISE near-real-time snow and ice | The official guide states that NISE is not intended for time-series, anomaly or trend analysis | Preserve it as monitoring context, never a substitute for the sea-ice climate record [18] |
| GEDI biomass as a generic trend source | The inspected L4B Version 2 grid is a one-time multi-year biomass estimate | Treat that product as context; require a repeat-observation estimator before enabling a biomass trend [19] |
| OCO 2 described as gridded or Level 3 | Bias-corrected Lite full-physics XCO2 is an explicit Level 2 collection; gridded products require their own identity | Bind the exact collection and estimator; column concentration does not directly measure national emissions [20] [21] |
| CERES SYN1deg for all radiation use | CERES offers products with different climate, synoptic, and energy-budget purposes | Select the product for the question; verify the relevant quality summary rather than imposing one radiation product [22] [23] |
| Land cover and imagery as context only | Class-area transitions and repeat spectral observations can themselves be valid change targets | Keep context mode, but add categorical transition and repeat-image modes rather than applying numeric slopes to class codes |
| NISAR described as mission-era data | ASF documents calibrated, partially validated provisional products and release-specific cautions | Show maturity and composite release identity; use recent change detection rather than a long climate trend [24] |
| All anomalies required before all trends | Removing a constant baseline leaves a linear slope unchanged; seasonal baselines and transformations can alter the question | Preserve raw values and anomalies; record the exact baseline and target series instead of treating anomaly conversion as a universal cure |
| Active fire combined with burned area | NASA cautions that active-fire locations do not directly determine burned area | Analyze detections, radiative power, and burned area as distinct quantities [25] [26] |

## 3 1 Catalog coverage as product capabilities

The following mapping covers the catalog's core, extended, and explanatory families. Combined rows hold related measurements with the same source family; the registry creates a distinct parameter_id for each measurement or component. The mode describes the suitable initial capability, not evidence that every country already has a usable cached record.

**Table 4  Catalog coverage as product capabilities**

| Parameter ids and user labels | Source bindings and native support | Analysis mode and interpretation |
| :--- | :--- | :--- |
| surface_temperature_anomaly  -  blended surface anomaly | GISTEMP v4; monthly, 2 degree grid; retain provider baseline | Long-record anomaly trend; global context and coarse regional support [12] |
| air_temperature_2m; air_temperature_min; air_temperature_max | MERRA-2 T2M for NASA baseline; POWER point daily; ERA5 or ERA5-Land as companion | Area mean or explicitly named point sample; max and min remain separate quantities [27] [28] [29] [30] |
| land_surface_temperature_day; land_surface_temperature_night | MOD11A1 061; daily 1 km; MOD21 family as an alternative binding | Clear-sky overpass LST; keep sensor, algorithm, day and night separate [6] [31] |
| sea_surface_temperature | NOAA OISST v2.1; daily 0.25 degree ocean grid with error information | Ocean polygon trend; retain interpolation and ice-proxy context [7] |
| precipitation_total; precipitation_rate | GPM IMERG Final V07; 0.1 degree; subdaily or monthly product | Convert rates with time bounds; sum depth over time; use a homogeneous Final collection [32] |
| soil_moisture_surface; soil_moisture_rootzone | SMAP L3 retrieval or SPL4SMGP assimilation; example L4 grid 9 km, 3 hourly | Moisture trend over eligible land; sensor support differs from grid spacing [16] |
| terrestrial_water_storage_anomaly | JPL GRACE and GRACE-FO mascon equivalent water thickness; monthly | Large-area storage trend with mission gaps, gain or leakage settings, and uncertainty [15] |
| sea_level_anomaly; global_mean_sea_level | NASA SSH regional grid or GMSL indicator | Regional ocean height versus global mean; distinguish absolute from coastal relative sea level [14] [13] |
| sea_surface_salinity | OISSS multi-mission L4; 0.25 degree; inspected 7-day Version 2 grid | Ocean salinity trend with coastal and product QA limits [33] |
| chlorophyll_a | Aqua MODIS ocean color L3; choose science reprocessing and a mapped monthly product | Ocean biological retrieval; test log transform and valid coverage; not direct total biomass [34] |
| ndvi; evi | MOD13Q1 061; 16-day, 250 m | Greenness trends with vegetation QA and composite sampling [35] |
| leaf_area_index; fpar | MOD15A2H or MCD15A3H 061; product-specific 8-day or 4-day, 500 m | Canopy and absorbed-radiation fractions; retain algorithm quality [36] [11] |
| evapotranspiration; potential_evapotranspiration; latent_heat_flux | MOD16A2GF 061; gap-filled 8-day, 500 m | Model-derived totals or fluxes; use actual interval duration and preserve fill lineage [37] |
| net_primary_production | MOD17A3HGF 061; annual, 500 m | Productivity trend with modeled-product interpretation and appropriate carbon units [38] |
| surface_albedo_blacksky; surface_albedo_whitesky | MCD43A3 061; daily 500 m product; multi-day retrieval support | Reflectance fraction with BRDF QA; daily outputs are not independent daily retrievals [39] |
| land_cover_class; land_cover_area_change | MCD12Q1 061; annual, 500 m | Class fractions and transition matrix; never regress numeric class identifiers [40] |
| snow_cover; snow_season_duration | MOD10A1 or MYD10A1 061; daily 500 m | Snow area or timing from valid observations; preserve clouds and NDSI interpretation [41] |
| sea_ice_concentration; sea_ice_extent; sea_ice_area | NOAA NSIDC CDR G02202; inspected Version 6; daily or monthly 25 km | Polar analysis; concentration, threshold extent, and concentration-weighted area are distinct [17] |
| ice_surface_height_change; ice_motion; ice_deformation | ICESat-2 ATL06 for land-ice heights; NISAR and repeat optical or SAR tracking for appropriate motion products | Separate height change, motion and deformation; retain reference frame, repeat sampling and method [42] [11] |
| active_fire_detections; fire_radiative_power | FIRMS MODIS and VIIRS observations, with sensor and observation effort | Event monitoring or calibrated annual regime indicators; counts are not burned area [25] |
| burned_area | MCD64A1 061; monthly 500 m | Sum valid burned pixel area with unique period accounting [26] |
| aboveground_biomass_density | GEDI L4A footprints and L4B gridded estimates | Context or repeat-sampling analysis; inspected L4B v2 is a multi-year mean, not annual observations [19] |
| surface_deformation_los; surface_displacement_change | NISAR appropriate displacement or interferometric products, pinned release | Recent change with reference frame, geometry, coherence, and maturity; LOS is not automatically vertical motion [24] |
| surface_water_extent; inundation_extent | SWOT, SAR, optical repeat scenes; optional HLS derived water product | Water-area or event change with consistent classification and observation opportunity [43] [44] |
| river_water_level; river_width; river_slope; river_discharge | SWOT RiverSP reach and node data; LakeSP for lake-specific quantities | Feature-based repeated observations; discharge is a derived estimate, not identical to measured height [43] |
| lake_water_level; lake_water_extent | SWOT LakeSP family identified in the catalog | Feature-based recent change; bind an exact collection and its quality guide before release [11] |
| atmospheric_xco2; solar_induced_fluorescence | OCO-2 exact XCO2 or SIF collection; sparse soundings | Column concentration or vegetation fluorescence; separate targets and aggregation policies [20] [21] [11] |
| atmospheric_ch4_column; no2_tropospheric_column; co_column; so2_column; ozone_column; hcho_column | Sentinel-5P TROPOMI species-specific L2 products; optional AIRS or MLS bindings where appropriate | QA-filtered column series; retain retrieval, processor, sampling, and vertical definition [45] |
| aerosol_optical_depth; absorbing_aerosol_index; aerosol_layer_height | MODIS or VIIRS aerosol retrievals and TROPOMI alternatives | Distinct aerosol quantities; AOD is not surface particulate mass concentration [46] [45] |
| cloud_fraction; cloud_optical_thickness; cloud_top_height; cloud_top_pressure | MODIS atmosphere and CERES cloud fields; species-specific TROPOMI fields where supported | Cloud observations and sampling context; cloud fraction is a fraction, not a concentration [47] [22] |
| toa_outgoing_longwave; toa_reflected_shortwave; toa_net_flux | CERES product selected for climate or energy-budget question | Separate radiative components and sign convention; suitable monthly regional support [22] [23] |
| surface_shortwave_down; surface_shortwave_up; surface_longwave_down; surface_longwave_up | CERES surface flux products; POWER radiation for point workflows | Keep mean power density and integrated energy separate [22] [28] |
| station_air_temperature; station_precipitation; station_snow_depth; station_visibility; station_wind | NOAA GHCN-Daily and ISD station observations | Validation and local investigation with station metadata, instrument changes and record completeness [48] [49] |
| ocean_temperature_profile; ocean_salinity_profile; ocean_oxygen; ocean_nutrients | NOAA World Ocean Database and appropriate Argo records | Profile and depth-bin analysis; changing sample locations require a sampling-aware estimator [50] |
| wind_u_10m; wind_v_10m; wind_speed_10m | ERA5 or NASA MERRA-2; scatterometer binding where selected | Vector components and speed differ; mean speed is not speed of the mean vector [29] [27] |
| surface_pressure; mean_sea_level_pressure; dewpoint_2m; relative_humidity | ERA5, MERRA-2, POWER or appropriate AIRS products | Separate levels and definitions; humidity derivation must be recorded [29] [28] |
| significant_wave_height; wave_period; wave_direction | ERA5 wave fields or selected altimetry products | Ocean-region analysis; directional data require circular statistics [29] |
| ground_elevation; surface_reflectance | SRTM, ASTER, Copernicus DEM; Landsat C2 and HLS | Static terrain context; repeat reflectance and classified transitions are change-capable [11] [51] [44] |
| earthquake_events; cyclone_tracks; nighttime_lights_context | USGS catalog, NOAA IBTrACS; night lights named as context in the catalog | Event overlays or context; establish catalog completeness before event-frequency trends [52] [53] [11] |

## 3 2 Units and parameter distinctions

Use canonical scientific units in storage and record every display conversion. Temperature can be stored in kelvin and displayed in degrees Celsius; temperature differences retain the same numeric size under that conversion. Precipitation rates require duration integration before being called precipitation totals. Volumetric soil moisture uses a volume fraction, while equivalent water thickness uses a length unit.

Use carbon mass per area per interval for NPP, a dimensionless value for NDVI or EVI, an area ratio for LAI, and a bounded fraction for FPAR, albedo, snow cover, cloud fraction, and ice concentration where the product defines such a fraction. Column gases retain species-specific units and vertical definitions. Do not convert a column to a surface concentration without an explicit model.

For a time series of annual precipitation totals expressed in millimeters, report the slope in millimeters per decade of annual-total change. For a temperature series, report degrees Celsius per decade. Include the temporal statistic beside the unit so users can distinguish a trend in annual totals from a trend in monthly rates.

## 3 3 Binding maturity and availability

Give every binding an availability state: catalogued, acquired, validated, analysis-ready, display-ready, or unavailable. These are project states. Only a binding with validated cached observations and a tested method may return a production scientific result. The interface can list a catalogued parameter while explaining that the selected region or record is not yet available.

Prioritize long-record NASA air temperature, MODIS LST, IMERG precipitation, and NOAA SST for complete end-to-end investigations. Add vegetation and hydrology after their QA and spatial aggregation contracts pass. Preserve every catalog family in the registry, including advanced missions and profile data, without implying that every family supports the same generic trend routine.



---

> **Navigation:** [← 02 Assessment of Supplied Implementation Specification](../02_assessment_of_the_supplied_implementation_specification/README.md) | [Table of Contents](../README.md) | [04 Geographic Support and Country Aggregation →](../04_geographic_support_and_country_aggregation/README.md)
