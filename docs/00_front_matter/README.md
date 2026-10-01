> **Navigation:** [← Master Index](../README.md) | [Table of Contents](../README.md) | [01 Challenge Requirements and Product Behavior →](../01_challenge_requirements_and_product_behavior/README.md)

---


# Earth System Trend Detective Research and Engineering Design

### Research report and implementation specification

Prepared for the Earth System Trend Detective project team

1 October 2026

Build a global investigation workspace that lets a person select a country, choose a physical parameter, and inspect the amount, location, uncertainty, and statistical evidence of change. Use a flat 2D world map with custom scientific layers, linked time series, comparisons, and citations attached to every reported result.

The central design decision is to calculate country results from spatially supported observations. NASA POWER data at a country centroid remain useful as a named point sample, but cannot represent the country's average. Keep land-surface temperature, near-surface air temperature, sea-surface temperature, and blended surface-temperature anomalies as separate parameters.

The recommended stack is Next.js 16.3.8 or a newer verified stable patch, TypeScript, mapcn components over MapLibre GL JS for the 2D map, and FastAPI with deterministic Python calculations for the scientific service. All scientific requests read local, versioned data. Online acquisition runs separately, with NASA Earthdata MCP available for discovery. A local deployment includes the map assets, data, and narration needed to work without internet access. [[1]](../15_references_and_dataset_directory/README.md#ref-1) [[2]](../15_references_and_dataset_directory/README.md#ref-2) [[3]](../15_references_and_dataset_directory/README.md#ref-3)

This report provides a complete assessment of the supplied implementation specification, a mapping of the attached catalog into physical parameters, product corrections supported by official documentation, a statistical contract, an interface design, and a detailed prompt for a coding agent. Recommendations and engineering thresholds are identified as project choices rather than agency requirements. There is no timed hackathon schedule.

# Contents

[1 Challenge requirements and product behavior](../01_challenge_requirements_and_product_behavior/README.md)

[2 Assessment of the supplied implementation specification](../02_assessment_of_the_supplied_implementation_specification/README.md)

[3 Catalog assessment and corrections](../03_catalog_assessment_and_corrections/README.md)

[4 Geographic support and country aggregation](../04_geographic_support_and_country_aggregation/README.md)

[5 Registry ingestion and offline operation](../05_registry_ingestion_and_offline_operation/README.md)

[6 Statistical contract and interpretation](../06_statistical_contract_and_interpretation/README.md)

[7 Derived indicators and special investigations](../07_derived_indicators_and_special_investigations/README.md)

[8 Flat map components and scientific layers](../08_flat_map_components_and_scientific_layers/README.md)

[9 Interface and interaction design](../09_interface_and_interaction_design/README.md)

[10 Architecture API and implementation boundaries](../10_architecture_api_and_implementation_boundaries/README.md)

[11 Constrained narration in English and Bangla](../11_constrained_narration_in_english_and_bangla/README.md)

[12 Verification and acceptance criteria](../12_verification_and_acceptance_criteria/README.md)

[13 Completion gates licensing and responsible product scope](../13_completion_gates_licensing_and_responsible_product_scope/README.md)

[14 Detailed implementation prompt](../14_detailed_implementation_prompt/README.md)

[15 References and dataset directory](../15_references_and_dataset_directory/README.md)

Dataset mappings appear in Section 3, map and plugin decisions in Section 8, API fields in Section 10, and the complete coding instruction in Section 14.



---

> **Navigation:** [← Master Index](../README.md) | [Table of Contents](../README.md) | [01 Challenge Requirements and Product Behavior →](../01_challenge_requirements_and_product_behavior/README.md)
