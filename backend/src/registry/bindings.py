"""Dataset bindings connecting physical parameters to specific collection sources.

Implements Table 4 and Table 5:
- Exact provider collection IDs, versions, DOIs, and URLs
- Scale and offset transformations
- Native spatial grid and temporal cadence
- Measurement support classification
"""

from __future__ import annotations

from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class DatasetBinding(BaseModel):
    """Scientific dataset binding specification."""
    id: str = Field(..., description="Unique dataset binding identifier")
    parameter_id: str
    provider: str
    collection_id: str
    collection_name: str
    version: str
    doi: Optional[str]
    source_url: str
    citation: str
    variable_name: str
    canonical_unit: str
    scale_factor: float = 1.0
    add_offset: float = 0.0
    fill_values: List[float] = Field(default_factory=lambda: [-9999.0, -999.0, 1e20])
    qa_band_name: Optional[str] = None
    native_spatial_resolution: str
    temporal_cadence: Literal["daily", "monthly", "16_day", "annual"]
    record_start_date: str
    record_end_date: str
    is_gridded: bool
    availability_state: Literal[
        "catalogued",
        "acquired",
        "validated",
        "analysis_ready",
        "display_ready",
        "unavailable",
    ] = "analysis_ready"
    unavailability_reason: Optional[str] = None


DATASET_BINDINGS: Dict[str, DatasetBinding] = {
    "NASA_MERRA2_M2TMNXSLV": DatasetBinding(
        id="NASA_MERRA2_M2TMNXSLV",
        parameter_id="air_temperature_2m",
        provider="NASA GMAO",
        collection_id="M2TMNXSLV",
        collection_name="MERRA-2 tavgM_2d_slv_Nx: 2d, Monthly mean, Time-Averaged, Single-Level, Assimilation, Diagnostics V5.12.4",
        version="5.12.4",
        doi="10.5067/AP1B0BA5PD2K",
        source_url="https://goldsmr4.gesdisc.eosdis.nasa.gov/data/MERRA2/M2TMNXSLV.5.12.4/",
        citation="Global Modeling and Assimilation Office (GMAO) (2015), MERRA-2 tavgM_2d_slv_Nx, Goddard Earth Sciences Data and Information Services Center (GES DISC), doi:10.5067/AP1B0BA5PD2K.",
        variable_name="T2M",
        canonical_unit="K",
        scale_factor=1.0,
        add_offset=0.0,
        fill_values=[1e15, 1e20],
        native_spatial_resolution="0.5° latitude x 0.625° longitude",
        temporal_cadence="monthly",
        record_start_date="1980-01-01",
        record_end_date="2024-12-31",
        is_gridded=True,
        availability_state="analysis_ready",
    ),
    "MODIS_MOD11A1_061_DAY": DatasetBinding(
        id="MODIS_MOD11A1_061_DAY",
        parameter_id="land_surface_temperature_day",
        provider="NASA LP DAAC",
        collection_id="MOD11A1",
        collection_name="MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V061",
        version="061",
        doi="10.5067/MODIS/MOD11A1.061",
        source_url="https://doi.org/10.5067/MODIS/MOD11A1.061",
        citation="Wan, Z., Hook, S., Hulley, G. (2021). MOD11A1 MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V061. NASA EOSDIS Land Processes Distributed Active Archive Center.",
        variable_name="LST_Day_1km",
        canonical_unit="K",
        scale_factor=0.02,
        add_offset=0.0,
        fill_values=[0.0],
        qa_band_name="QC_Day",
        native_spatial_resolution="1 km sinusoidal (~0.01°)",
        temporal_cadence="daily",
        record_start_date="2000-03-05",
        record_end_date="2024-12-31",
        is_gridded=True,
        availability_state="analysis_ready",
    ),
    "MODIS_MOD11A1_061_NIGHT": DatasetBinding(
        id="MODIS_MOD11A1_061_NIGHT",
        parameter_id="land_surface_temperature_night",
        provider="NASA LP DAAC",
        collection_id="MOD11A1",
        collection_name="MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V061",
        version="061",
        doi="10.5067/MODIS/MOD11A1.061",
        source_url="https://doi.org/10.5067/MODIS/MOD11A1.061",
        citation="Wan, Z., Hook, S., Hulley, G. (2021). MOD11A1 MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V061. NASA EOSDIS LP DAAC.",
        variable_name="LST_Night_1km",
        canonical_unit="K",
        scale_factor=0.02,
        add_offset=0.0,
        fill_values=[0.0],
        qa_band_name="QC_Night",
        native_spatial_resolution="1 km sinusoidal (~0.01°)",
        temporal_cadence="daily",
        record_start_date="2000-03-05",
        record_end_date="2024-12-31",
        is_gridded=True,
        availability_state="analysis_ready",
    ),
    "NOAA_OISST_V2_1": DatasetBinding(
        id="NOAA_OISST_V2_1",
        parameter_id="sea_surface_temperature",
        provider="NOAA NCEI",
        collection_id="NOAA_OISST_V2_1",
        collection_name="NOAA 1/4° Daily Optimum Interpolation Sea Surface Temperature (OISST) v2.1",
        version="v2.1",
        doi="10.25921/RE9P-PT57",
        source_url="https://www.ncei.noaa.gov/products/optimum-interpolation-sst",
        citation="Huang, B. et al. (2021). Improvements of the Daily Optimum Interpolation Sea Surface Temperature (DOISST) Version 2.1. J. Climate, 34, 2923-2939.",
        variable_name="sst",
        canonical_unit="°C",
        scale_factor=0.01,
        add_offset=0.0,
        fill_values=[-999.0],
        native_spatial_resolution="0.25° latitude x 0.25° longitude",
        temporal_cadence="daily",
        record_start_date="1981-09-01",
        record_end_date="2024-12-31",
        is_gridded=True,
        availability_state="analysis_ready",
    ),
    "NASA_POWER_DAILY_POINT": DatasetBinding(
        id="NASA_POWER_DAILY_POINT",
        parameter_id="point_air_temperature",
        provider="NASA LaRC",
        collection_id="NASA_POWER_POINT_DAILY",
        collection_name="NASA Prediction Of Worldwide Energy Resources (POWER) Daily Point Meteorology",
        version="v2.0",
        doi=None,
        source_url="https://power.larc.nasa.gov/",
        citation="NASA Langley Research Center (LaRC) POWER Project. Single-point daily meteorological parameters derived from GMAO reanalyses.",
        variable_name="T2M",
        canonical_unit="°C",
        scale_factor=1.0,
        add_offset=0.0,
        fill_values=[-999.0],
        native_spatial_resolution="Point sample at explicit centroid coordinate",
        temporal_cadence="daily",
        record_start_date="1981-01-01",
        record_end_date="2024-12-31",
        is_gridded=False,
        availability_state="analysis_ready",
    ),
    "GPM_IMERG_FINAL_V07": DatasetBinding(
        id="GPM_IMERG_FINAL_V07",
        parameter_id="precipitation_total",
        provider="NASA GES DISC",
        collection_id="GPM_3IMERGM",
        collection_name="GPM IMERG Final Precipitation L3 1 month 0.1 degree x 0.1 degree V07",
        version="V07B",
        doi="10.5067/GPM/IMERG/3B-MONTH/07",
        source_url="https://disc.gsfc.nasa.gov/datasets/GPM_3IMERGM_07/summary",
        citation="Huffman, G.J. et al. (2023), GPM IMERG Final Precipitation L3 1 month 0.1 degree V07, Greenbelt, MD, Goddard Earth Sciences Data and Information Services Center (GES DISC).",
        variable_name="precipitation",
        canonical_unit="mm",
        scale_factor=1.0,
        add_offset=0.0,
        fill_values=[-9999.9],
        native_spatial_resolution="0.1° latitude x 0.1° longitude",
        temporal_cadence="monthly",
        record_start_date="2000-06-01",
        record_end_date="2024-12-31",
        is_gridded=True,
        availability_state="catalogued",
        unavailability_reason="Granule acquisition pending local ingestion pipeline; no synthetic records are manufactured in offline mode.",
    ),
    "NASA_GISTEMP_V4": DatasetBinding(
        id="NASA_GISTEMP_V4",
        parameter_id="surface_temperature_anomaly",
        provider="NASA GISS",
        collection_id="GISTEMP_V4",
        collection_name="GISS Surface Temperature Analysis (GISTEMP v4)",
        version="v4",
        doi=None,
        source_url="https://data.giss.nasa.gov/gistemp/",
        citation="GISTEMP Team, 2026: GISS Surface Temperature Analysis (GISTEMP), version 4. NASA Goddard Institute for Space Studies. dataset: https://data.giss.nasa.gov/gistemp/",
        variable_name="tempanomaly",
        canonical_unit="K",
        scale_factor=1.0,
        add_offset=0.0,
        fill_values=[9999.0],
        native_spatial_resolution="2.0° latitude x 2.0° longitude",
        temporal_cadence="monthly",
        record_start_date="1880-01-01",
        record_end_date="2024-12-31",
        is_gridded=True,
        availability_state="catalogued",
        unavailability_reason="Global anomaly grid acquisition pending local ingestion pipeline; 1951-1980 baseline preserved.",
    ),
}
