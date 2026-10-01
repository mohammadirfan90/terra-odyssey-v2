"""API routes package."""
from .regions import router as regions_router
from .parameters import router as parameters_router
from .coverage import router as coverage_router
from .trend import router as trend_router
from .comparisons import router as comparisons_router
from .results import router as results_router
from .layers import router as layers_router
from .sources import router as sources_router

__all__ = [
    "regions_router",
    "parameters_router",
    "coverage_router",
    "trend_router",
    "comparisons_router",
    "results_router",
    "layers_router",
    "sources_router",
]
