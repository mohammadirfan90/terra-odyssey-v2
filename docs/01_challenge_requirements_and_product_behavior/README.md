> **Navigation:** [← 00 Front Matter](../00_front_matter/README.md) | [Table of Contents](../README.md) | [02 Assessment of Supplied Implementation Specification →](../02_assessment_of_the_supplied_implementation_specification/README.md)

---


# 1 Challenge requirements and product behavior

The challenge is an investigation task. An attractive map meets only part of it. A completed investigation must identify the measured quantity, establish the geographic support, quantify a change over a stated interval, and explain the statistical evidence and its limits. The same parameter may rise in one region and fall in another, so a country average must remain connected to a spatial map and a regional comparison. [[4]](../15_references_and_dataset_directory/README.md#ref-4)

**Table 1  Challenge requirements and product behavior**

| Challenge question | Required result | Required interface |
| :--- | :--- | :--- |
| What is changing | Parameter definition, units, source product, observation type | Parameter selector with a concise scientific definition |
| Where is it changing | Analysis geometry, valid coverage, local trend field | Selectable 2D map, country outline, pixel or region inspector |
| How much is it changing | Slope, slope interval, elapsed period, sample count | Trend estimate beside the time series and fitted line |
| Is the change significant | Named test, assumptions, p value and applicable multiplicity correction | Evidence status, diagnostics, method explanation |
| Can regions behave differently | Trends for compatible regions and a direct contrast estimate | Linked comparison view with a difference series |
| Can the result be checked | Data identifiers, transformation history, methods, hashes | Citations, provenance drawer, downloadable investigation |

## 1 1 Interpreting the challenge language

"Interconnected environmental system" justifies cross-variable investigations, such as precipitation, soil moisture, and terrestrial water storage. It does not establish a causal explanation. The application should distinguish a measured association from a mechanism supported by external research.

"Consistent direction" calls for a trend estimate over a defined period. Two endpoint images, an unusually hot month, or a sudden flood are changes or events; each can be valuable, but each answers a different question from a multi-year trend.

"Measured by NASA missions or produced by NASA models" permits both observation products and modeled or assimilated products. Preserve those labels. NASA POWER meteorology is derived from MERRA-2, while MODIS land-surface temperature is a satellite retrieval. A partner source such as NOAA OISST may complement a NASA source, with its provider clearly named. [[5]](../15_references_and_dataset_directory/README.md#ref-5) [[6]](../15_references_and_dataset_directory/README.md#ref-6) [[7]](../15_references_and_dataset_directory/README.md#ref-7)

"Opposite way in another region" requires the application to keep signed estimates. A national mean can hide warming and cooling subregions or offsetting wetting and drying. Report the share of eligible analysis area with positive and negative slopes, with the denominator and evidence criterion visible.

"Significant" requires inference with explicit assumptions. A small p value does not measure the size of a change or establish its cause. A result that does not meet the evidence criterion should read "No clear statistical evidence in this interval," rather than "No change."

## 1 2 A complete country investigation

For "United States land-surface temperature," the application first selects the country's land geometry, including the chosen treatment of Alaska, Hawaii, and territories. It loads a QA-filtered MODIS day or night LST series, calculates area-weighted aggregates, and analyzes eligible annual or seasonal observations. The user sees the source's sampling limits, a trend map for the same interval, a national time series, uncertainty, and references. No numerical finding is implied by this example; the result must come from the selected cached data.

The map offers a regional selection to compare, for example, two parts of the country. Changing the selection must update the analysis geometry, series, methods, and provenance together. A stale result must never appear underneath a newly selected country or parameter.



---

> **Navigation:** [← 00 Front Matter](../00_front_matter/README.md) | [Table of Contents](../README.md) | [02 Assessment of Supplied Implementation Specification →](../02_assessment_of_the_supplied_implementation_specification/README.md)
