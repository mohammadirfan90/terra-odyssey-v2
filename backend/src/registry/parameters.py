"""Physical parameter definitions and domain registry.

Implements Table 4 and Table 5:
- Stable parameter IDs across diverse dataset bindings
- Explicit separation of air temp, LST day/night, SST, and blended anomalies
- Canonical vs display units
- Spatial support and observation physics
"""

from __future__ import annotations

from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class ParameterDefinition(BaseModel):
    """Scientific parameter definition independent of any specific dataset source."""
    id: str = Field(..., description="Unique immutable parameter identifier")
    name_en: str = Field(..., description="English human-readable name")
    name_bn: str = Field(..., description="Bangla human-readable name")
    definition_en: str = Field(..., description="Scientific definition in English")
    definition_bn: str = Field(..., description="Scientific definition in Bangla")
    domain: Literal[
        "atmosphere",
        "land_surface",
        "ocean",
        "hydrology",
        "biosphere",
        "cryosphere",
        "radiation",
    ]
    physical_quantity: str
    canonical_unit: str = Field(..., description="Internal storage unit (e.g. K, m, kg/m2)")
    display_unit: str = Field(..., description="UI display unit (e.g. °C, mm, mm/decade)")
    supported_temporal_statistics: List[str] = Field(
        default_factory=lambda: ["annual_mean"],
        description="Supported statistical aggregations (annual_mean, annual_total, monthly_anomaly)",
    )
    valid_spatial_support: Literal["land", "ocean", "global", "point", "polar"]
    observation_type: Literal[
        "satellite_retrieval",
        "reanalysis_model",
        "in_situ_station",
        "point_sample",
        "blended_analysis",
    ]
    default_binding_id: str


# Catalog of core physical parameters
PARAMETER_REGISTRY: Dict[str, ParameterDefinition] = {
    "air_temperature_2m": ParameterDefinition(
        id="air_temperature_2m",
        name_en="Near-Surface Air Temperature (2m)",
        name_bn="ভূপৃষ্ঠ সংলগ্ন বায়ুর তাপমাত্রা (২ মিটার)",
        definition_en="Air temperature at 2 meters above the displacement height, derived from atmospheric reanalysis assimilating global surface and satellite observations.",
        definition_bn="বায়ুমণ্ডলীয় পুনঃবিশ্লেষণ মডেল এবং উপগ্রহ পর্যবেক্ষণের সমন্বয়ে ভূপৃষ্ঠের ২ মিটার উচ্চতায় পরিমাপকৃত বায়ুর তাপমাত্রা।",
        domain="atmosphere",
        physical_quantity="thermodynamic_temperature",
        canonical_unit="K",
        display_unit="°C",
        supported_temporal_statistics=["annual_mean", "monthly_mean"],
        valid_spatial_support="global",
        observation_type="reanalysis_model",
        default_binding_id="NASA_MERRA2_M2TMNXSLV",
    ),
    "land_surface_temperature_day": ParameterDefinition(
        id="land_surface_temperature_day",
        name_en="Land Surface Temperature (Daytime)",
        name_bn="দিনের ভূপৃষ্ঠের তাপমাত্রা (এলএসটি)",
        definition_en="Radiative skin temperature of the land surface retrieved under clear-sky daytime satellite overpasses (~10:30 local solar time).",
        definition_bn="স্বচ্ছ মেঘমুক্ত দিনে স্যাটেলাইট ওভারপাস চলাকালে পরিমাপকৃত মাটির উপরিভাগের বিকিরণ তাপমাত্রা।",
        domain="land_surface",
        physical_quantity="radiometric_temperature",
        canonical_unit="K",
        display_unit="°C",
        supported_temporal_statistics=["annual_mean", "seasonal_mean"],
        valid_spatial_support="land",
        observation_type="satellite_retrieval",
        default_binding_id="MODIS_MOD11A1_061_DAY",
    ),
    "land_surface_temperature_night": ParameterDefinition(
        id="land_surface_temperature_night",
        name_en="Land Surface Temperature (Nighttime)",
        name_bn="রাতের ভূপৃষ্ঠের তাপমাত্রা (এলএসটি)",
        definition_en="Radiative skin temperature of the land surface retrieved under clear-sky nighttime satellite overpasses (~22:30 local solar time).",
        definition_bn="স্বচ্ছ মেঘমুক্ত রাতে স্যাটেলাইট ওভারপাস চলাকালে পরিমাপকৃত মাটির উপরিভাগের বিকিরণ তাপমাত্রা।",
        domain="land_surface",
        physical_quantity="radiometric_temperature",
        canonical_unit="K",
        display_unit="°C",
        supported_temporal_statistics=["annual_mean", "seasonal_mean"],
        valid_spatial_support="land",
        observation_type="satellite_retrieval",
        default_binding_id="MODIS_MOD11A1_061_NIGHT",
    ),
    "sea_surface_temperature": ParameterDefinition(
        id="sea_surface_temperature",
        name_en="Sea Surface Temperature (SST)",
        name_bn="সমুদ্রপৃষ্ঠের তাপমাত্রা (এসএসটি)",
        definition_en="Temperature of the ocean surface layer (bulk SST at ~0.5 m depth) derived from satellite AVHRR and in-situ buoy observations.",
        definition_bn="উপগ্রহ এবং ভাসমান বয়ার তথ্যের ভিত্তিতে সমুদ্রের উপরিভাগের পানির তাপমাত্রা।",
        domain="ocean",
        physical_quantity="thermodynamic_temperature",
        canonical_unit="°C",
        display_unit="°C",
        supported_temporal_statistics=["annual_mean", "monthly_anomaly"],
        valid_spatial_support="ocean",
        observation_type="blended_analysis",
        default_binding_id="NOAA_OISST_V2_1",
    ),
    "precipitation_total": ParameterDefinition(
        id="precipitation_total",
        name_en="Total Accumulated Precipitation",
        name_bn="মোট বৃষ্টিপাত ও বারিপাত",
        definition_en="Total accumulated liquid water equivalent precipitation depth over time, retrieved from satellite passive microwave, radar, and gauge integration.",
        definition_bn="উপগ্রহ রাডার এবং বৃষ্টির পরিমাপক যন্ত্রের সমন্বয়ে নির্ধারিত মোট পুঞ্জীভূত বৃষ্টিপাত।",
        domain="hydrology",
        physical_quantity="liquid_water_equivalent_depth",
        canonical_unit="mm",
        display_unit="mm",
        supported_temporal_statistics=["annual_total", "monthly_total"],
        valid_spatial_support="global",
        observation_type="satellite_retrieval",
        default_binding_id="GPM_IMERG_FINAL_V07",
    ),
    "point_air_temperature": ParameterDefinition(
        id="point_air_temperature",
        name_en="Point Sample Air Temperature (Centroid)",
        name_bn="বিন্দু নমুনা বায়ুর তাপমাত্রা (কেন্দ্রবিন্দু)",
        definition_en="Daily air temperature point time series sampled at an explicit geographic coordinate (e.g. country centroid) from NASA POWER.",
        definition_bn="নাসা পাওয়ার থেকে একটি নির্দিষ্ট ভৌগোলিক স্থানাঙ্কে সংরক্ষিত একক বিন্দু নমুনা তাপমাত্রা।",
        domain="atmosphere",
        physical_quantity="thermodynamic_temperature",
        canonical_unit="°C",
        display_unit="°C",
        supported_temporal_statistics=["annual_mean", "daily_mean"],
        valid_spatial_support="point",
        observation_type="point_sample",
        default_binding_id="NASA_POWER_DAILY_POINT",
    ),
    "surface_temperature_anomaly": ParameterDefinition(
        id="surface_temperature_anomaly",
        name_en="Blended Surface Temperature Anomaly",
        name_bn="সম্মিলিত ভূপৃষ্ঠের তাপমাত্রা বিচ্যুতি (GISTEMP)",
        definition_en="Coarse-resolution (2°x2°) blended land-air and sea-surface temperature anomaly relative to the 1951-1980 baseline from NASA GISTEMP v4.",
        definition_bn="১৯৫১-১৯৮০ সালের ভিত্তিরেখার সাপেক্ষে নাসা গিসটেম্প ভি৪ দ্বারা পরিমাপকৃত তাপমাত্রা বিচ্যুতি।",
        domain="atmosphere",
        physical_quantity="temperature_anomaly",
        canonical_unit="K",
        display_unit="°C",
        supported_temporal_statistics=["annual_mean", "monthly_anomaly"],
        valid_spatial_support="global",
        observation_type="blended_analysis",
        default_binding_id="NASA_GISTEMP_V4",
    ),
}
