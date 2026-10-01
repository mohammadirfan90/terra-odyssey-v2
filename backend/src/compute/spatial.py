"""Geodesic area-weighted spatial aggregation.

Implements Equation 1 from Chapter 4 and Table 19:
- Area-weighted mean of intensive quantities (e.g. temperature) using valid cell intersection areas
- Area-integrated sum of extensive quantities (e.g. burned area, water mass)
- Dynamic coverage denominator tracking
- Support for cell-polygon intersection using Shapely
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional, Sequence
import numpy as np
from shapely.geometry import Polygon, MultiPolygon, box
from shapely.ops import unary_union


EARTH_RADIUS_METERS = 6371008.8  # WGS-84 authalic sphere


@dataclass(frozen=True)
class SpatialAggregateResult:
    """Immutable result of spatial aggregation over an administrative or custom region."""
    area_weighted_mean: Optional[float]
    extensive_sum: Optional[float]
    total_region_area_m2: float
    valid_observed_area_m2: float
    coverage_fraction: float
    cell_count_total: int
    cell_count_valid: int
    is_sufficient_coverage: bool


def calculate_cell_geodesic_area_m2(
    lat_min: float,
    lat_max: float,
    lon_min: float,
    lon_max: float,
) -> float:
    """Compute the geodesic area of a regular lat-lon cell on the authalic sphere in square meters."""
    d_lon_rad = math.radians(abs(lon_max - lon_min))
    phi1_rad = math.radians(min(lat_min, lat_max))
    phi2_rad = math.radians(max(lat_min, lat_max))
    d_sin_phi = math.sin(phi2_rad) - math.sin(phi1_rad)
    return (EARTH_RADIUS_METERS**2) * d_lon_rad * d_sin_phi


def area_weighted_mean(
    cell_values: Sequence[float] | np.ndarray,
    cell_areas: Sequence[float] | np.ndarray,
    valid_mask: Optional[Sequence[bool] | np.ndarray] = None,
    min_coverage_pct: float = 50.0,
) -> SpatialAggregateResult:
    """Calculate the area-weighted regional mean following Equation 1.

    bar{x}_{R,t} = sum(a_c * v_c * x_c) / sum(a_c * v_c)

    Args:
        cell_values: Array of cell measurements x_c.
        cell_areas: Array of cell intersection areas with the region a_c (m^2 or km^2).
        valid_mask: Array of validity indicators v_c (True if valid observation, False if missing/cloud).
        min_coverage_pct: Minimum valid area coverage percentage required to consider the step valid.

    Returns:
        SpatialAggregateResult with intensive mean, extensive sum, and coverage diagnostics.
    """
    x = np.asarray(cell_values, dtype=np.float64)
    a = np.asarray(cell_areas, dtype=np.float64)

    if valid_mask is None:
        v = np.isfinite(x) & (a > 0)
    else:
        v = np.asarray(valid_mask, dtype=bool) & np.isfinite(x) & (a > 0)

    n_total = int(x.size)
    n_valid = int(np.sum(v))

    total_area = float(np.sum(a[a > 0])) if n_total > 0 else 0.0

    if total_area <= 0.0 or n_valid == 0:
        return SpatialAggregateResult(
            area_weighted_mean=None,
            extensive_sum=0.0,
            total_region_area_m2=total_area,
            valid_observed_area_m2=0.0,
            coverage_fraction=0.0,
            cell_count_total=n_total,
            cell_count_valid=0,
            is_sufficient_coverage=False,
        )

    valid_area = float(np.sum(a[v]))
    coverage_frac = valid_area / total_area

    # Equation 1: numerator = sum(a_c * v_c * x_c), denominator = sum(a_c * v_c)
    numerator = float(np.sum(a[v] * x[v]))
    mean_val = numerator / valid_area
    extensive_sum = numerator  # sum of area-integrated value

    is_sufficient = (coverage_frac * 100.0) >= min_coverage_pct

    return SpatialAggregateResult(
        area_weighted_mean=mean_val,
        extensive_sum=extensive_sum,
        total_region_area_m2=total_area,
        valid_observed_area_m2=valid_area,
        coverage_fraction=coverage_frac,
        cell_count_total=n_total,
        cell_count_valid=n_valid,
        is_sufficient_coverage=is_sufficient,
    )


def intersect_grid_with_polygon(
    lats: np.ndarray,
    lons: np.ndarray,
    region_geom: Polygon | MultiPolygon,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute cell intersection areas and cell indices overlapping a region polygon.

    Returns:
        (cell_indices, intersection_areas_m2)
    """
    d_lat = abs(lats[1] - lats[0]) if len(lats) > 1 else 1.0
    d_lon = abs(lons[1] - lons[0]) if len(lons) > 1 else 1.0

    minx, miny, maxx, maxy = region_geom.bounds

    # Filter bounding box
    lat_indices = np.where((lats >= miny - d_lat) & (lats <= maxy + d_lat))[0]
    lon_indices = np.where((lons >= minx - d_lon) & (lons <= maxx + d_lon))[0]

    intersecting_cells = []
    areas = []

    for ilat in lat_indices:
        lat = float(lats[ilat])
        lat1 = lat - d_lat / 2.0
        lat2 = lat + d_lat / 2.0
        full_cell_area = calculate_cell_geodesic_area_m2(lat1, lat2, 0.0, d_lon)

        for ilon in lon_indices:
            lon = float(lons[ilon])
            lon1 = lon - d_lon / 2.0
            lon2 = lon + d_lon / 2.0

            cell_box = box(lon1, lat1, lon2, lat2)
            if not region_geom.intersects(cell_box):
                continue

            intersection = region_geom.intersection(cell_box)
            if intersection.is_empty:
                continue

            # Fractional planar area in degree space
            frac = float(intersection.area / cell_box.area)
            cell_inter_area = full_cell_area * frac

            intersecting_cells.append((ilat, ilon))
            areas.append(cell_inter_area)

    return np.array(intersecting_cells), np.array(areas, dtype=np.float64)
