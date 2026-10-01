"""Pure mathematical, statistical, and spatial compute routines."""
from .mann_kendall import mann_kendall_test, MannKendallResult
from .theil_sen import theil_sen_slope, TheilSenResult
from .uncertainty import calculate_fitted_line_band, FittedBandResult
from .serial_corr import check_autocorrelation, hamed_rao_variance_correction
from .seasonal import stl_decomposition, SeasonalResult
from .spatial import area_weighted_mean, SpatialAggregateResult
from .multiple_testing import false_discovery_rate_correction

__all__ = [
    "mann_kendall_test",
    "MannKendallResult",
    "theil_sen_slope",
    "TheilSenResult",
    "calculate_fitted_line_band",
    "FittedBandResult",
    "check_autocorrelation",
    "hamed_rao_variance_correction",
    "stl_decomposition",
    "SeasonalResult",
    "area_weighted_mean",
    "SpatialAggregateResult",
    "false_discovery_rate_correction",
]
