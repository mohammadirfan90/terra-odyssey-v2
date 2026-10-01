> **Navigation:** [← 05 Registry Ingestion and Offline Operation](../05_registry_ingestion_and_offline_operation/README.md) | [Table of Contents](../README.md) | [07 Derived Indicators and Special Investigations →](../07_derived_indicators_and_special_investigations/README.md)

---


# 6 Statistical contract and interpretation

Implement scientific functions in src/compute as pure, tested Python routines. Language models may describe the returned result, but may not calculate, alter, select, or invent statistical values. Keep statistical estimation separate from the product eligibility policy: a kernel can calculate a slope for three observations, while the application can reject those observations as insufficient for the requested climate interpretation.

## 6 1 Define the series before testing it

State whether the target is a country-area annual mean, a seasonal mean, an annual total, a monthly anomaly, a percentile, or a point series. Define land and ocean support, day and night sampling, QA, and time weighting. Require sorted, unique timestamps and finite retained measurements. Dates remain attached when observations are missing.

Use annual or predeclared seasonal aggregates for the initial climate inference workflow. Monthly records can use a seasonal method. Daily observations remain available for exploration, extremes, and eligible event indices. A daily generic trend test without dependence or seasonality handling is not a credible universal policy.

## 6 2 Mann Kendall estimation

For time-ordered observations, calculate S from all signed pairwise value differences. Include the tie correction in the independent-series variance. Use the usual continuity correction for the standardized Z statistic and a two-sided normal approximation when that approximation is appropriate. Record whether the p value is asymptotic or exact. [[9]](../15_references_and_dataset_directory/README.md#ref-9) [[10]](../15_references_and_dataset_directory/README.md#ref-10)

$$S = \sum_{i=1}^{n-1} \sum_{j=i+1}^n \operatorname{sgn}(y_j - y_i)$$

**Equation 2  Mann Kendall statistic from ordered observation pairs**

$$\operatorname{Var}(S) = \frac{n(n-1)(2n+5) - \sum_{k=1}^g t_k(t_k - 1)(2t_k + 5)}{18}$$

**Equation 3  Independent series variance with tied value groups**

$$Z = \begin{cases} \frac{S-1}{\sqrt{\operatorname{Var}(S)}} & \text{if } S > 0 \\ 0 & \text{if } S = 0 \\ \frac{S+1}{\sqrt{\operatorname{Var}(S)}} & \text{if } S < 0 \end{cases}, \qquad p = 2[1 - \Phi(|Z|)]$$

**Equation 4  Continuity corrected normal statistic and two sided p value**

Here n is the retained sample count and t is a tied-value group size. Return S, variance, Z, p_value, test_method, p_value_method, sample_count, and diagnostics. For a constant valid series with enough observations, S=0, variance=0, Z=0, and p=1 under the explicit constant-series convention. For fewer than two retained observations or invalid input, return a typed insufficient-data state with null inferential values, not p=1.

Keep slope direction and evidence status separate. The direction can be increasing, decreasing, or flat according to the estimated slope and a documented numeric tolerance. A result can have an increasing slope and inconclusive statistical evidence. Never encode "not significant" as "flat."

For small samples, choose and test an exact procedure where supported, or disclose the approximation and withhold the production evidence label under the eligibility policy. A nominal p value is conditional on the test assumptions; it is not the probability that the trend is real.

## 6 3 Theil Sen slope and its interval

Calculate the median of pairwise slopes using actual elapsed time. Convert datetime differences to a documented time unit, such as years based on 365.2425 days, and report the public slope per decade. Omitting missing observations does not compress elapsed time. Specify the joint intercept convention as the median of value minus slope times centered time. [[60]](../15_references_and_dataset_directory/README.md#ref-60) [[61]](../15_references_and_dataset_directory/README.md#ref-61)

$$\hat{\beta} = \operatorname{median}_{i < j} \left( \frac{y_j - y_i}{t_j - t_i} \right)$$

$$\hat{b} = \operatorname{median}_i [y_i - \hat{\beta}(t_i - t_{\text{ref}})]$$

**Equation 5  Theil Sen median pairwise slope and joint intercept**

The standard rank-based 95 percent slope interval assumes an appropriate independent-series setting and uses ordered slopes with the stated tie and rank convention. Verify its implementation against a trusted reference and preserve the convention in method metadata. An autocorrelation-adjusted p value does not automatically make that independent-series slope interval valid for dependent observations.

For dependent annual records, use a predeclared dependence-aware slope uncertainty procedure, such as a reviewed residual block bootstrap around a fitted trend. Specify block length, replicate count, random seed, residual handling, and assumptions. Do not stitch across large missing intervals as if contiguous observations were adjacent. If the uncertainty method is not supported or calibrated for the series, return a slope with a clear uncertainty limitation and withhold a definitive evidence claim.

## 6 4 The chart confidence band is a separate quantity

A slope interval is not a confidence band for the fitted line, and it is not a prediction interval. SciPy's theilslopes documentation explicitly notes that its slope bounds do not supply intercept bounds. Drawing low and high slope lines through an arbitrarily fixed anchor creates an unjustified band. [[61]](../15_references_and_dataset_directory/README.md#ref-61)

For a supported bootstrap method, refit both slope and intercept in each replicate and evaluate the fitted trajectory at each displayed date. Pointwise quantiles form a pointwise fitted-line uncertainty band; a simultaneous band requires a separate construction. Label the chart with the actual method and coverage. Bootstrap calibration, residual stationarity, and missingness assumptions remain part of the result. Hide the band when those conditions fail; never manufacture one to complete the design.

Keep instrument or retrieval uncertainty, spatial representativeness, slope uncertainty, and fitted-line uncertainty as different fields. A regional bootstrap across independent-looking fine display pixels does not account for correlated satellite errors or GRACE mascon support.

## 6 5 Seasonality and serial dependence

For monthly data with recurrent seasons, consider Seasonal Kendall following Hirsch, Slack, and Smith, with a dependence-aware treatment when required. For annual or fixed-season observations, diagnose serial correlation in detrended residuals and use a predeclared method such as the Hamed-Rao modified variance where justified. Do not choose lag settings after seeing which one produces significance. [[9]](../15_references_and_dataset_directory/README.md#ref-9) [[10]](../15_references_and_dataset_directory/README.md#ref-10)

Return the primary test and, where useful, a separately labeled sensitivity result using the ordinary independent-series test. Preserve the correction method, lag settings, diagnostic values, and warnings. Do not treat disagreement between methods as a reason to hide the less favorable output.

Use robust STL for regular monthly observations with period 12 as a diagnostic decomposition. Record trend and seasonal smoothing settings. Classical seasonal_decompose requires two complete cycles; for this product, recommend at least five years before presenting a stable seasonal interpretation. The five-year rule is a project choice, not a universal STL requirement. Annual data do not require a manufactured monthly seasonal decomposition. [[62]](../15_references_and_dataset_directory/README.md#ref-62) [[63]](../15_references_and_dataset_directory/README.md#ref-63)

STL does not make missing observations disappear. Permit only explicitly configured short-gap interpolation in a separate diagnostic copy, expose the imputation mask, and exclude those fabricated values from the primary inference series. When the diagnostic cannot be produced reliably, show an unavailable decomposition with the reason.

## 6 6 Missingness coverage and baselines

Establish thresholds by binding, because a station's daily coverage and a cloud-limited satellite retrieval are different sampling processes. As an initial project policy for eligible daily air-temperature data, require at least 80 percent valid days and no gap longer than seven days for a monthly mean. Review these choices against the dataset and perform sensitivity checks. Do not apply them blindly to LST, profiles, composites, or accumulated rainfall.

For annual temperature, a candidate policy is at least ten eligible months with representation in every calendar quarter; require all twelve eligible months for an annual precipitation total unless a reviewed estimator explicitly accounts for missing intervals. Monthly means should be duration-weighted when building a time-average. Never scale an incomplete rain total to a full year without labeling and validating the estimation method.

**Table 8  Missingness coverage and baselines**

| Quantity or source | Recommended baseline handling | Interpretation |
| :--- | :--- | :--- |
| GISTEMP | Retain native 1951 to 1980 reference | Do not relabel native anomalies as another reference [12] |
| Long air temperature or OISST record | Offer a fully available 1991 to 2020 climatology | A 30-year reference following the contemporary WMO normal period [64] |
| MODIS record | Consider a complete 2001 to 2020 project reference | A 20-year reference, not a WMO 30-year normal |
| SMAP | If complete, use a documented 2016 to 2025 short reference | Recent mission-era anomaly; short baseline disclosed |
| Short missions or sparse features | Keep observed values and recent change | Do not invent a long historical climatology |

An unavailable baseline can disable anomaly mode without preventing an eligible trend in the original quantity. Subtracting a single constant does not alter pairwise slopes. Subtracting a changing seasonal climatology or applying a nonlinear transformation changes the target and must be recorded.

As an initial annual climate policy, prefer at least twenty eligible years, mark ten to nineteen years as exploratory, and treat fewer than ten years as recent change or insufficient support for a climate-trend claim. These are conservative project defaults to validate, not universal scientific thresholds. A 30-year climate normal and a minimum record for detecting a trend are separate concepts. Power depends on variability, dependence, sampling, and effect size.

## 6 7 Maps and multiple testing

A large pixel map performs many tests. Define the family in advance: one parameter, one analysis window, one method, and one fixed eligible geographic extent. Apply Benjamini-Hochberg only under its appropriate dependence assumptions; use a defensible alternative, such as Benjamini-Yekutieli under arbitrary dependence, when required. Return the family definition, family size, adjustment, p values, and q values. The viewport must not redefine the family as users pan. [[65]](../15_references_and_dataset_directory/README.md#ref-65) [[66]](../15_references_and_dataset_directory/README.md#ref-66)

Display slope everywhere supported and use a separate evidence layer, stippling, or filter for corrected evidence. Show no-data and ineligible cells distinctly. Do not average p values, call the fraction of small p values a national p value, or turn q values into an unexplained confidence score. A country-series test is a separate test of that series.

## 6 8 Comparing regions and investigating relationships

Use the same binding, quantity, time interval, aggregation, baseline, QA, and support policy for the primary comparison. Show record overlap before running it. Calculate a paired difference series on common eligible dates and estimate its trend with the declared method. The slope of the difference series is not generally the difference of two Theil-Sen slopes.

It is invalid to conclude that two regions differ merely because one trend is significant and the other is not. Return a direct contrast estimate and its uncertainty. If products or definitions differ, show a descriptive source comparison and its limitations rather than enabling a scientific region contrast badge.

Cross-variable exploration can show aligned anomalies, lagged associations, and linked events, but must specify the estimator, units, standardization, detrending, lag family, and multiple-testing treatment. A correlation does not establish causation, and a causal statement cannot originate from a trend object alone.

## 6 9 Machine readable scientific states

**Table 9  Machine readable scientific states**

| State | Meaning | User wording |
| :--- | :--- | :--- |
| supported_increase or supported_decrease | Eligible data and predeclared inference support the direction | Evidence of an increase or decrease over the selected interval |
| inconclusive | Eligible estimate but evidence criterion not met | Estimated direction with no clear statistical evidence in this interval |
| limited | Estimate available with important sampling or method limitations | Estimate available with limitations; inspect diagnostics |
| insufficient | Too little eligible temporal or spatial support | Not enough suitable observations for this analysis |
| unavailable | Required binding, data, geometry, or method absent locally | Required data or method are not available for this selection |

Use the named primary inference and a supported uncertainty method to assign evidence. When interval and test disagree materially, explain the method difference and downgrade interpretation under an explicit policy. Always show effect size when it is meaningful, even when evidence is inconclusive. No state establishes a cause.



---

> **Navigation:** [← 05 Registry Ingestion and Offline Operation](../05_registry_ingestion_and_offline_operation/README.md) | [Table of Contents](../README.md) | [07 Derived Indicators and Special Investigations →](../07_derived_indicators_and_special_investigations/README.md)
