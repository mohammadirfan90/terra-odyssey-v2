> **Navigation:** [← 08 Flat Map Components and Scientific Layers](../08_flat_map_components_and_scientific_layers/README.md) | [Table of Contents](../README.md) | [10 Architecture API and Implementation Boundaries →](../10_architecture_api_and_implementation_boundaries/README.md)

---


# 9 Interface and interaction design

Design the workspace around the investigation rather than a wall of indicators. The first view should explain the parameter and guide a person to a supported result: select a country, choose a quantity, select an eligible period, and run the analysis. Make the map, estimate, and provenance readable together.

![Figure 1: Proposed flat map workspace with explicit pending scientific results](figure_1_proposed_flat_map_workspace.png)

**Figure 1  Proposed flat map workspace with explicit pending scientific results**

The figure is a layout specification. It deliberately shows a pending analysis rather than invented environmental numbers. A production screen fills the result and chart only from verified result objects.

## 9 1 Desktop mobile and bilingual organization

On a wide screen, place country search and parameter controls in a left rail, the map in the center, and the investigation summary to the right. Put the time-series area below, with tabs for series, comparison, seasonal diagnostics, and data. Keep source and method actions within the result panel. Use a restrained light theme for research reading, with an optional dark map theme that preserves the same quantitative scale.

On a narrow screen, use a sequential layout: selection controls, result summary, chart, and expandable map. A user must be able to select a region and inspect every result without panning a map. Keep the provenance drawer and data table usable on mobile. Avoid an always-open map that consumes the entire screen and hides the answer.

Use English and Bangla labels backed by stable ids. Localize units, dates, scientific glossary terms, and narrative templates consistently. Provide a visible language switch; preserve the current investigation when switching. Use a locally packaged Bengali font and test line wrapping, number localization, negative signs, and mixed Latin product identifiers.

## 9 2 State behavior that prevents misleading results

**Table 15  State behavior that prevents misleading results**

| State | Visible behavior | Required data behavior |
| :--- | :--- | :--- |
| No selection | Search guidance and available parameter domains | No sample environmental values |
| Selection changed | Draft controls and "Run analysis" action | Previous result clearly labeled or cleared; no silent relabeling |
| Running | Job progress and cancel action | Query id and committed settings remain fixed |
| Ready | Estimate, evidence, chart, map and sources | Every panel refers to the same result id |
| Limited or insufficient | Reason, coverage diagnostics and permitted alternatives | Null unsupported values remain null |
| Offline cache miss | Missing item and installed inventory | No upstream fetch or invented fallback |
| Computation error | Plain explanation and retry | Error id; no partially mixed result panels |

Treat control changes as draft input until committed. Cancel or ignore stale requests using a query fingerprint and abort signal. A map click during a running analysis must not put an old country's slope under the new country's name. Keep selection state distinct from map viewport state.

Restore investigations through a shareable URL containing stable selection and method identifiers, and through a saved investigation containing the immutable result id. A link to current data and a link to a frozen result are different artifacts; show which is being opened.

## 9 3 Chart and comparison requirements

Show observations as a legible series, the fitted Theil-Sen line, and the supported fitted-line uncertainty band. Include explicit gaps, units, aggregation, interval, and source. Expose raw and anomaly modes only when each is valid. Hover and keyboard inspection reveal date, value, quality, and provenance link.

Decimate a very long series only for drawing, with the original data available in the table and export. The scientific computation uses the full eligible series. Preserve extrema when drawing event-sensitive data; do not allow smoothing or interpolation to turn gaps into apparent measurements.

For comparison, use aligned axes and scales for the same quantity, a paired difference chart, and a direct contrast panel. Do not use dual axes to make unrelated variables appear tightly linked. A cross-variable exploration can use separate aligned panels with a disclosed standardization option.

Keep quantitative precision consistent with uncertainty and source support. Display rounded values for readability and the original serialized value in provenance. Render a tiny p value as a threshold or scientific notation rather than zero. A missing estimate is an unavailable value, not "0.00."

## 9 4 Accessibility and evidence literacy

Target WCAG 2.2 AA. Normal text needs at least 4.5:1 contrast and large text at least 3:1. Keep focus visible and unobscured, support keyboard controls, and respect text resizing. Charts, map controls, legends, and status messages need accessible alternatives and labels. [[82]](../15_references_and_dataset_directory/README.md#ref-82)

Use a colorblind-friendly sequential palette for absolute values and a balanced diverging palette for signed anomalies or slopes. Provide labels, hatching, or symbols as well as color. Avoid red-green evidence badges and avoid mapping "bad" to one direction without a physical interpretation.

Provide a table view of every mapped regional result. Country selection needs an accessible search and list; a chart needs keyboard focus points and a text summary. Draw focus and selected-state outlines separately from the scientific layer. Respect reduced motion and avoid animated transitions that hide the time being inspected.

Put a short explanation beside the evidence status: effect size is the amount of change; the p value describes evidence under a stated model; coverage describes observation support. Allow the user to inspect detailed methods without requiring them to read raw JSON first.

## 9 5 Provenance as a normal part of the experience

Each numerical display stores a JSON Pointer, result id, unit, display format, and source links. A "View source" action highlights that field in the drawer and shows a readable path from dataset to QA, aggregation, series, estimate, and display. A citation icon attached only to the page footer is insufficient for a multi-source result.

The drawer contains the exact result JSON, relevant source manifests, dataset citations, code version, analysis settings, geometry version, warnings, and downloadable observations. Do not export credentials, private local paths, or access tokens. Offline citation links can point to packaged metadata; opening an external source is an explicitly online action.



---

> **Navigation:** [← 08 Flat Map Components and Scientific Layers](../08_flat_map_components_and_scientific_layers/README.md) | [Table of Contents](../README.md) | [10 Architecture API and Implementation Boundaries →](../10_architecture_api_and_implementation_boundaries/README.md)
