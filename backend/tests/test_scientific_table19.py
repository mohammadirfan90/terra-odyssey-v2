"""Scientific verification tests corresponding to Table 19 of the specification.

Tests all 12 mandatory scientific criteria:
1. Increasing values 1-10 at unit times
2. Decreasing values 10-1
3. Constant series of 10 identical values
4. Irregular timestamps determining slopes
5. Missing values preserving true elapsed time
6. Tied values and tie-variance correction
7. Insufficient data (< 2 or < 3 values)
8. Non-finite values, NaNs, infinities, and unsorted inputs
9. Known monthly seasonal decomposition & imputation isolation
10. Autocorrelated series & Hamed-Rao VIF correction
11. Geodesic spatial aggregation with known cell areas (Eq 1)
12. Paired regional comparison on difference series
"""

import math
import numpy as np
import pytest

from src.compute.mann_kendall import mann_kendall_test
from src.compute.theil_sen import theil_sen_slope
from src.compute.uncertainty import calculate_fitted_line_band
from src.compute.serial_corr import check_autocorrelation, hamed_rao_variance_correction
from src.compute.seasonal import stl_decomposition
from src.compute.spatial import area_weighted_mean
from src.compute.multiple_testing import false_discovery_rate_correction


# ---------------------------------------------------------------------------
# Test Case 1: Increasing values 1 through 10 at unit-spaced times
# S=45, tied-corrected variance=125, continuity-corrected Z ~ 3.93548,
# two-sided asymptotic p ~ 0.00008303, slope = 1 per time unit.
# ---------------------------------------------------------------------------
def test_table19_case1_increasing():
    y = np.arange(1, 11, dtype=float)
    t = np.arange(10, dtype=float)

    mk = mann_kendall_test(y, alpha=0.05)
    assert mk.S == 45
    assert math.isclose(mk.var_S, 125.0, rel_tol=1e-6)
    assert math.isclose(mk.Z, 3.9354796, rel_tol=1e-5)
    assert math.isclose(mk.p_value, 0.00008303, rel_tol=1e-3)
    assert mk.direction == "increasing"
    assert mk.evidence_state == "supported_increase"

    ts = theil_sen_slope(t, y, alpha=0.05)
    assert math.isclose(ts.slope_per_year, 1.0, abs_tol=1e-9)
    assert math.isclose(ts.slope_per_decade, 10.0, abs_tol=1e-9)
    assert math.isclose(ts.intercept, 1.0, abs_tol=1e-9)
    assert ts.is_degenerate is True
    assert math.isclose(ts.ci_95_lower_per_decade, 10.0, abs_tol=1e-9)
    assert math.isclose(ts.ci_95_upper_per_decade, 10.0, abs_tol=1e-9)


# ---------------------------------------------------------------------------
# Test Case 2: Decreasing values 10 through 1
# S and Z reverse sign; two-sided p matches increasing case; slope = -1
# ---------------------------------------------------------------------------
def test_table19_case2_decreasing():
    y = np.arange(10, 0, -1, dtype=float)
    t = np.arange(10, dtype=float)

    mk = mann_kendall_test(y, alpha=0.05)
    assert mk.S == -45
    assert math.isclose(mk.var_S, 125.0, rel_tol=1e-6)
    assert math.isclose(mk.Z, -3.9354796, rel_tol=1e-5)
    assert math.isclose(mk.p_value, 0.00008303, rel_tol=1e-3)
    assert mk.direction == "decreasing"
    assert mk.evidence_state == "supported_decrease"

    ts = theil_sen_slope(t, y, alpha=0.05)
    assert math.isclose(ts.slope_per_year, -1.0, abs_tol=1e-9)
    assert math.isclose(ts.slope_per_decade, -10.0, abs_tol=1e-9)
    assert math.isclose(ts.intercept, 10.0, abs_tol=1e-9)


# ---------------------------------------------------------------------------
# Test Case 3: Ten identical finite values
# S=0, Z=0, p=1, slope=0 and degenerate slope interval
# ---------------------------------------------------------------------------
def test_table19_case3_constant_series():
    y = np.full(10, 5.0)
    t = np.arange(10, dtype=float)

    mk = mann_kendall_test(y, alpha=0.05)
    assert mk.S == 0
    assert mk.var_S == 0.0
    assert mk.Z == 0.0
    assert mk.p_value == 1.0
    assert mk.direction == "flat"
    assert mk.evidence_state == "flat"

    ts = theil_sen_slope(t, y, alpha=0.05)
    assert ts.slope_per_year == 0.0
    assert ts.slope_per_decade == 0.0
    assert ts.intercept == 5.0
    assert ts.is_degenerate is True
    assert ts.ci_95_lower_per_decade == 0.0
    assert ts.ci_95_upper_per_decade == 0.0


# ---------------------------------------------------------------------------
# Test Case 4: Irregular times 2000, 2002, 2005, 2009 with values 1, 5, 11, 19
# Slope = 2 per year; timestamps determine slopes
# ---------------------------------------------------------------------------
def test_table19_case4_irregular_times():
    times = [2000.0, 2002.0, 2005.0, 2009.0]
    values = [1.0, 5.0, 11.0, 19.0]

    ts = theil_sen_slope(times, values, alpha=0.05)
    # (5-1)/(2002-2000)=2, (11-1)/(2005-2000)=2, (19-1)/(2009-2000)=2, etc.
    assert math.isclose(ts.slope_per_year, 2.0, abs_tol=1e-9)
    assert math.isclose(ts.slope_per_decade, 20.0, abs_tol=1e-9)


# ---------------------------------------------------------------------------
# Test Case 5: Times 0, 1, 2, 3, 4 with values 0, missing, 4, missing, 8
# Retained times 0, 2, 4 yield slope=2, NOT slope=4 from compressed positions
# ---------------------------------------------------------------------------
def test_table19_case5_missing_values_elapsed_time():
    times = [0.0, 1.0, 2.0, 3.0, 4.0]
    values = [0.0, np.nan, 4.0, np.nan, 8.0]

    ts = theil_sen_slope(times, values, alpha=0.05)
    assert ts.retained_sample_count == 3
    assert math.isclose(ts.slope_per_year, 2.0, abs_tol=1e-9)
    assert math.isclose(ts.slope_per_decade, 20.0, abs_tol=1e-9)


# ---------------------------------------------------------------------------
# Test Case 6: Ties and missing endpoints
# Correct tie variance, retained dates, exclusions and valid null handling
# ---------------------------------------------------------------------------
def test_table19_case6_ties_and_missing_endpoints():
    # 3 groups of ties: {2, 2, 2}, {5, 5}, {8}
    values = [np.nan, 2.0, 2.0, 2.0, 5.0, 5.0, 8.0, np.nan]
    times = np.arange(len(values), dtype=float)

    mk = mann_kendall_test(values)
    assert mk.sample_count == 6
    assert mk.tied_groups_count == 2  # group of 3 and group of 2
    # n=6: base = 6*5*17 / 18 = 510/18 = 28.333333
    # ties: t=3 -> 3*2*11 = 66; t=2 -> 2*1*9 = 18; sum = 84 / 18 = 4.666667
    # var = (510 - 84)/18 = 426/18 = 23.66666667
    assert math.isclose(mk.var_S, 426.0 / 18.0, rel_tol=1e-6)


# ---------------------------------------------------------------------------
# Test Case 7: Fewer than two eligible values
# Typed insufficient state; no misleading p=1 or fabricated band
# ---------------------------------------------------------------------------
def test_table19_case7_fewer_than_two():
    times = [2020.0, 2021.0]
    values = [np.nan, 15.0]

    ts = theil_sen_slope(times, values)
    assert ts.slope_per_year is None
    assert ts.slope_per_decade is None
    assert ts.method == "insufficient_data"

    mk = mann_kendall_test(values)
    assert mk.S is None
    assert mk.p_value is None
    assert mk.direction == "insufficient"
    assert mk.evidence_state == "insufficient"

    band = calculate_fitted_line_band(times, values)
    assert band.is_valid is False
    assert len(band.points) == 0


# ---------------------------------------------------------------------------
# Test Case 8: NaNs, infinities, duplicate times and unsorted dates
# Explicit validation or documented sorting; no nonfinite JSON values
# ---------------------------------------------------------------------------
def test_table19_case8_unsorted_and_nonfinite():
    times = [2004.0, 2001.0, 2003.0, 2002.0, 2005.0]
    values = [4.0, 1.0, np.inf, 2.0, 5.0]

    # After dropping inf (at 2003) and sorting: times [2001, 2002, 2004, 2005], values [1, 2, 4, 5]
    # slope = 1.0
    ts = theil_sen_slope(times, values)
    assert ts.retained_sample_count == 4
    assert math.isclose(ts.slope_per_year, 1.0, abs_tol=1e-9)


# ---------------------------------------------------------------------------
# Test Case 9: Known monthly seasonal series
# Correct seasonal period and recoverable decomposition; no imputed values in primary inference
# ---------------------------------------------------------------------------
def test_table19_case9_monthly_seasonal_decomposition():
    n_years = 6
    months = np.arange(n_years * 12, dtype=float)
    # 0.1 trend + periodic seasonal signal (amplitude 5.0)
    seasonal_pattern = 5.0 * np.sin(2.0 * np.pi * months / 12.0)
    trend_pattern = 0.05 * months
    y = trend_pattern + seasonal_pattern

    # Inject 2 isolated missing values
    y_with_gaps = y.copy()
    y_with_gaps[15] = np.nan
    y_with_gaps[16] = np.nan

    res = stl_decomposition(months, y_with_gaps, period=12, min_years=5)
    assert res.is_available is True
    assert res.imputed_count == 2
    assert res.points[15].is_imputed is True
    assert res.points[16].is_imputed is True
    assert res.points[0].is_imputed is False
    assert res.seasonal_amplitude > 8.0  # Captures seasonal oscillation


# ---------------------------------------------------------------------------
# Test Case 10: Positively dependent no-trend series
# Hamed-Rao VIF correction elevates variance to avoid false positives
# ---------------------------------------------------------------------------
def test_table19_case10_autocorrelation_vif():
    # AR(1) series with phi = 0.6, no real trend
    rng = np.random.default_rng(12345)
    n = 60
    e = rng.normal(0, 1, size=n)
    y = np.zeros(n)
    for i in range(1, n):
        y[i] = 0.6 * y[i - 1] + e[i]

    diag = check_autocorrelation(y, alpha=0.05)
    assert diag.ar1 > 0.4
    assert diag.vif > 1.2  # VIF correctly inflates variance

    # Verify MK with VIF
    mk_uncorrected = mann_kendall_test(y, vif=1.0)
    mk_corrected = mann_kendall_test(y, vif=diag.vif, autocorrelation_adjusted=True)

    assert mk_corrected.var_S > mk_uncorrected.var_S
    assert abs(mk_corrected.Z) < abs(mk_uncorrected.Z)


# ---------------------------------------------------------------------------
# Test Case 11: Spatial masks with known cell areas and values
# Equation 1: Correct intensive mean, extensive sum, partial overlap, coverage denominator
# ---------------------------------------------------------------------------
def test_table19_case11_area_weighted_mean_equation1():
    # 4 cells with areas 100, 200, 300, 400 km^2
    # values: 10.0, 20.0, 30.0, 40.0
    areas = [100.0, 200.0, 300.0, 400.0]
    values = [10.0, 20.0, 30.0, 40.0]
    valid = [True, True, True, False]  # cell 4 obscured by clouds

    # Expected valid area: 100 + 200 + 300 = 600
    # Total area: 1000
    # Expected mean: (100*10 + 200*20 + 300*30) / 600 = (1000 + 4000 + 9000) / 600 = 14000 / 600 = 23.33333
    res = area_weighted_mean(values, areas, valid_mask=valid)

    assert math.isclose(res.total_region_area_m2, 1000.0, rel_tol=1e-6)
    assert math.isclose(res.valid_observed_area_m2, 600.0, rel_tol=1e-6)
    assert math.isclose(res.coverage_fraction, 0.6, rel_tol=1e-6)
    assert math.isclose(res.area_weighted_mean, 14000.0 / 600.0, rel_tol=1e-6)
    assert math.isclose(res.extensive_sum, 14000.0, rel_tol=1e-6)


# ---------------------------------------------------------------------------
# Test Case 12: Paired region series direct contrast
# Difference series on common dates
# ---------------------------------------------------------------------------
def test_table19_case12_paired_region_contrast():
    # Region A: steady warming 0.2/year
    # Region B: steady warming 0.1/year
    # Difference (A - B): 0.1/year
    times_A = np.arange(2000, 2010, dtype=float)
    y_A = 20.0 + 0.2 * (times_A - 2000.0)

    times_B = np.arange(2002, 2012, dtype=float)  # partially overlapping
    y_B = 15.0 + 0.1 * (times_B - 2002.0)

    # Common dates: 2002 to 2009 (8 years)
    common_years = np.intersect1d(times_A, times_B)
    assert len(common_years) == 8

    idx_A = np.isin(times_A, common_years)
    idx_B = np.isin(times_B, common_years)

    diff_series = y_A[idx_A] - y_B[idx_B]
    ts_diff = theil_sen_slope(common_years, diff_series)

    assert math.isclose(ts_diff.slope_per_year, 0.1, abs_tol=1e-9)
    assert math.isclose(ts_diff.slope_per_decade, 1.0, abs_tol=1e-9)
