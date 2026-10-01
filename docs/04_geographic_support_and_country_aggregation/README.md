> **Navigation:** [← 03 Catalog Assessment and Corrections](../03_catalog_assessment_and_corrections/README.md) | [Table of Contents](../README.md) | [05 Registry Ingestion and Offline Operation →](../05_registry_ingestion_and_offline_operation/README.md)

---


# 4 Geographic support and country aggregation

Use one region model for countries, administrative subdivisions, custom polygons, ocean basins, and marine zones. Give each region a stable internal identifier, parent identifier, translated labels, region type, geometry version, and citation. Country selection uses an ISO code where available, but must also support territories and other regions that do not fit a single country-code list.

Use simplified Natural Earth geometry for the world overview and a separately versioned boundary source for analysis. Natural Earth data are public domain; geoBoundaries offers explicitly licensed administrative boundaries. Simplification improves drawing speed but can remove islands and distort small-area statistics. Record the actual analysis boundary and its license in the result. [[54]](../15_references_and_dataset_directory/README.md#ref-54) [[55]](../15_references_and_dataset_directory/README.md#ref-55)

## 4 1 The area mean is a scientific calculation

Intersect the analysis polygon with native source cells. For an intensive quantity such as temperature, weight each valid cell by the geodesic area of its intersection with the region and the relevant land or ocean mask. Use provided cell areas where suitable; otherwise calculate areas on the source grid. A cosine-latitude approximation is only a documented fallback for an appropriate regular longitude-latitude grid.

$$\bar{x}_{R,t} = \frac{\sum_{c \in R} a_c v_{c,t} x_{c,t}}{\sum_{c \in R} a_c v_{c,t}}$$

**Equation 1  Area weighted regional mean using valid cell intersection areas**

In the equation, x is the cell value, a is the area inside the eligible region, and v indicates validity. The valid-area denominator changes when observations are missing. Return both the observed area mean and the coverage fraction. Do not interpret an average of a changing observed subset as a fixed-area country average without a coverage diagnostic.

Extensive quantities require different rules. Sum burned pixel areas to estimate burned area. Integrate a density over area to estimate a total. Precipitation depth is commonly area-averaged over space and accumulated over time; summing millimeters across pixels has no defensible country interpretation. Never use screen-space or Web Mercator pixel area as the scientific weight.

Retain holes, islands, multipolygons, antimeridian crossings, and source grid conventions. Test Fiji, Russia, small island countries, and the United States as geometry cases. A representative point should be guaranteed to fall in the intended polygon when used for display or POWER acquisition. If the requested centroid lies outside the country, keep its original coordinates and either label that fact or use a documented point-on-surface alternative; never silently change the location.

## 4 2 Ocean quantities need an ocean region

For SST, salinity, chlorophyll, waves, and regional sea level, offer an explicit ocean basin, coastal polygon, or selected EEZ geometry. A country's land boundary is not an ocean analysis mask. An inland country has no valid national SST result; show "Choose an ocean region" rather than a zero.

Marine Regions supplies versioned EEZ boundaries; the inspected download list includes Version 12. Preserve the source, release, attribution, and treatment of overlaps or disputed areas. A displayed marine region is an analytical selection, not a legal judgment. [[56]](../15_references_and_dataset_directory/README.md#ref-56)

## 4 3 Resolution and changing observation footprints

Record both grid spacing and effective measurement support. A small country intersecting a coarse atmospheric cell may have a computed area-weighted result, but it does not gain independent country-scale detail. GRACE display grids likewise do not supply independent water-storage measurements at every fine output cell. Show a resolution warning or reject the requested scale when the selected binding cannot support the interpretation. [[5]](../15_references_and_dataset_directory/README.md#ref-5) [[15]](../15_references_and_dataset_directory/README.md#ref-15)

Calculate a trend of a country-mean series and a map of cell-level trends as separate outputs. The median pairwise slope of an area mean is not generally equal to the area mean of cell-level median pairwise slopes. Label each output and preserve its own valid support. Displaying the two together helps users investigate within-country differences without treating them as interchangeable estimates.

For clear-sky LST and ocean-color products, examine changing observed area, season, and overpass sampling. Compare an available-area estimator against a reasonably stable common mask, when enough data exist. If the stable mask excludes too much of the region, report the limitation rather than claiming that either estimator covers the full region. Mission and processor transitions belong in the diagnostic panel.



---

> **Navigation:** [← 03 Catalog Assessment and Corrections](../03_catalog_assessment_and_corrections/README.md) | [Table of Contents](../README.md) | [05 Registry Ingestion and Offline Operation →](../05_registry_ingestion_and_offline_operation/README.md)
