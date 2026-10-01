> **Navigation:** [← 06 Statistical Contract and Interpretation](../06_statistical_contract_and_interpretation/README.md) | [Table of Contents](../README.md) | [08 Flat Map Components and Scientific Layers →](../08_flat_map_components_and_scientific_layers/README.md)

---


# 7 Derived indicators and special investigations

The catalog's derived feature section is valuable because it expands the project beyond a single slope. Implement each indicator as a named, versioned recipe with its input bindings, temporal and spatial support, QA, uncertainty, and interpretation. These are computed products, not additional raw datasets. [[11]](../15_references_and_dataset_directory/README.md#ref-11)

**Table 10  Derived indicators and special investigations**

| Derived capability | Scientific contract | Suitable interface |
| :--- | :--- | :--- |
| Anomaly | Difference from a declared monthly or annual reference; retain baseline sample count | Reference selector, anomaly chart and map |
| Monotonic trend | Theil-Sen estimate with named inference and uncertainty | Slope layer and evidence panel |
| Seasonal change | Predeclared seasonal means, amplitude, or timing estimator | Seasonal charts with separate uncertainty |
| Percentile and extremes | Declared reference distribution, calendar handling, and eligibility | Exceedance frequency and percentile layers |
| Persistence | Consecutive eligible observations beyond a stated threshold; gaps break or censor runs | Event timeline with duration and missingness |
| Rapid rate of change | Difference over a stated elapsed interval and measurement uncertainty | Short-term change map; no climate-trend badge |
| Drought | Implement a recognized index such as SPI or SPEI only with its full fitting and input contract | Index values, reference fit, timescale and method citation |
| Vegetation stress | Tested recipe using greenness and relevant water or thermal measurements | Exploratory multi-variable panel; disclose recipe and validation |
| Marine heatwave | Hobday-style threshold and event definition with an appropriate climatology | Events with peak anomaly, duration and baseline [67] |
| Fire and aerosol association | Sensor-aware fire indicators linked to aligned aerosol observations | Linked timeline; association language only |
| Snow and albedo association | Common support and comparable seasonal sampling | Seasonal linked charts and coverage masks |
| Storage and rainfall divergence | Aligned GRACE, rainfall and moisture series with distinct physical units | Water-balance investigation; no automatic groundwater attribution |
| Sea-level divergence and ocean state | Aligned regional SSH, SST and salinity with distinct physical meanings | Ocean-state association; no automatic attribution of height change to one component |
| Sea level and land-motion contrast | Consistent reference frames and measurement support | Coastal investigation distinguishing absolute and relative height |
| Deformation and events | Coherence, LOS geometry, release, reference point and event timing | Recent displacement map and event context |

For marine heatwaves, the original definition uses at least five days above a seasonally varying 90th-percentile threshold based on a 30-year climatology. Any project modification must be named and disclosed. Do not equate a hot SST map with a detected marine heatwave. [[67]](../15_references_and_dataset_directory/README.md#ref-67)

Keep ice motion and ice surface elevation separate. ICESat-2 land-ice height products can support elevation-change estimators with repeat-track, uncertainty, and reference-frame handling; height is not ice velocity. SAR or optical feature tracking can supply motion under a different binding. Static DEMs remain terrain context. [[42]](../15_references_and_dataset_directory/README.md#ref-42) [[11]](../15_references_and_dataset_directory/README.md#ref-11)

If a drought or vegetation-stress score is not a validated scientific index, call it an exploratory project indicator and show its components. Do not hide unrelated variables inside a single Earth health score or claim that the score represents the planet's condition objectively. Offer evidence-rich investigations that users can reproduce.



---

> **Navigation:** [← 06 Statistical Contract and Interpretation](../06_statistical_contract_and_interpretation/README.md) | [Table of Contents](../README.md) | [08 Flat Map Components and Scientific Layers →](../08_flat_map_components_and_scientific_layers/README.md)
