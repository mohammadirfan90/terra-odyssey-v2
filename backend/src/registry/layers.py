"""Scientific map layer definitions and rendering contract.

Implements Section 8.2 and Table 12:
- Separation of observed state, anomaly, trend slope, evidence, and coverage QA
- Diverging color palettes for signed trends, sequential for absolute values
- Quantitative inspector contracts (not reading rendered pixel colors)
"""

from __future__ import annotations

from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class LegendStop(BaseModel):
    value: float
    color: str
    label_en: str
    label_bn: str


class LayerDefinition(BaseModel):
    """Specification of a visual scientific layer on the 2D flat map."""
    id: str
    parameter_id: str
    binding_id: str
    name_en: str
    name_bn: str
    layer_mode: Literal[
        "observed_state",
        "anomaly",
        "trend_slope",
        "evidence",
        "coverage_qa",
        "context",
    ]
    unit: str
    native_spatial_resolution: str
    time_window_default: str
    color_scale_type: Literal["sequential", "diverging", "categorical"]
    legend_stops: List[LegendStop]
    nodata_value: Optional[float] = None
    attribution: str


LAYER_REGISTRY: Dict[str, LayerDefinition] = {
    "merra2_trend_slope": LayerDefinition(
        id="merra2_trend_slope",
        parameter_id="air_temperature_2m",
        binding_id="NASA_MERRA2_M2TMNXSLV",
        name_en="MERRA-2 2m Air Temperature 40-Year Trend Slope",
        name_bn="মেরা-২ বায়ুর তাপমাত্রা ৪০ বছরের পরিবর্তনের হার",
        layer_mode="trend_slope",
        unit="°C/decade",
        native_spatial_resolution="0.5° x 0.625°",
        time_window_default="1980-2024",
        color_scale_type="diverging",
        legend_stops=[
            LegendStop(value=-0.5, color="#2166ac", label_en="-0.5 °C/dec (Cooling)", label_bn="-০.৫ °C/দশক (হ্রাস)"),
            LegendStop(value=0.0, color="#f7f7f7", label_en="0.0 °C/dec (Neutral)", label_bn="০.০ °C/দশক (নিরপেক্ষ)"),
            LegendStop(value=0.5, color="#b2182b", label_en="+0.5 °C/dec (Warming)", label_bn="+০.৫ °C/দশক (বৃদ্ধি)"),
        ],
        nodata_value=-9999.0,
        attribution="NASA Global Modeling and Assimilation Office (GMAO) MERRA-2",
    ),
    "modis_lst_trend_slope": LayerDefinition(
        id="modis_lst_trend_slope",
        parameter_id="land_surface_temperature_day",
        binding_id="MODIS_MOD11A1_061_DAY",
        name_en="MODIS Terra Daytime LST 20-Year Trend Slope",
        name_bn="মোডিস দিনের ভূপৃষ্ঠের তাপমাত্রা ২০ বছরের পরিবর্তনের হার",
        layer_mode="trend_slope",
        unit="°C/decade",
        native_spatial_resolution="1 km sinusoidal",
        time_window_default="2000-2024",
        color_scale_type="diverging",
        legend_stops=[
            LegendStop(value=-0.8, color="#2166ac", label_en="-0.8 °C/dec", label_bn="-০.৮ °C/দশক"),
            LegendStop(value=0.0, color="#f7f7f7", label_en="0.0 °C/dec", label_bn="০.০ °C/দশক"),
            LegendStop(value=0.8, color="#d6604d", label_en="+0.8 °C/dec", label_bn="+০.৮ °C/দশক"),
        ],
        nodata_value=0.0,
        attribution="NASA LP DAAC / MODIS Terra Science Team",
    ),
    "modis_lst_night_trend_slope": LayerDefinition(
        id="modis_lst_night_trend_slope",
        parameter_id="land_surface_temperature_night",
        binding_id="MODIS_MOD11A1_061_NIGHT",
        name_en="MODIS Terra Nighttime LST 20-Year Trend Slope",
        name_bn="মোডিস রাতের ভূপৃষ্ঠের তাপমাত্রা ২০ বছরের পরিবর্তনের হার",
        layer_mode="trend_slope",
        unit="°C/decade",
        native_spatial_resolution="1 km sinusoidal",
        time_window_default="2000-2024",
        color_scale_type="diverging",
        legend_stops=[
            LegendStop(value=-0.8, color="#2166ac", label_en="-0.8 °C/dec", label_bn="-০.৮ °C/দশক"),
            LegendStop(value=0.0, color="#f7f7f7", label_en="0.0 °C/dec", label_bn="০.০ °C/দশক"),
            LegendStop(value=0.8, color="#d6604d", label_en="+0.8 °C/dec", label_bn="+০.৮ °C/দশক"),
        ],
        nodata_value=0.0,
        attribution="NASA LP DAAC / MODIS Terra Science Team",
    ),
    "oisst_trend_slope": LayerDefinition(
        id="oisst_trend_slope",
        parameter_id="sea_surface_temperature",
        binding_id="NOAA_OISST_V2_1",
        name_en="NOAA OISST Sea Surface Temperature 40-Year Trend Slope",
        name_bn="এনওএএ ওআইএসএসটি সমুদ্রপৃষ্ঠের তাপমাত্রা ৪০ বছরের পরিবর্তনের হার",
        layer_mode="trend_slope",
        unit="°C/decade",
        native_spatial_resolution="0.25° ocean grid",
        time_window_default="1981-2024",
        color_scale_type="diverging",
        legend_stops=[
            LegendStop(value=-0.5, color="#2166ac", label_en="-0.5 °C/dec", label_bn="-০.৫ °C/দশক"),
            LegendStop(value=0.0, color="#f7f7f7", label_en="0.0 °C/dec", label_bn="০.০ °C/দশক"),
            LegendStop(value=0.5, color="#b2182b", label_en="+0.5 °C/dec", label_bn="+০.৫ °C/দশক"),
        ],
        nodata_value=-999.0,
        attribution="NOAA National Centers for Environmental Information (NCEI) OISST",
    ),
    "power_point_trend_slope": LayerDefinition(
        id="power_point_trend_slope",
        parameter_id="point_air_temperature",
        binding_id="NASA_POWER_DAILY_POINT",
        name_en="NASA POWER Point 2m Air Temperature Trend Slope",
        name_bn="নাসা পাওয়ার পয়েন্ট ২মি বায়ুর তাপমাত্রা পরিবর্তনের হার",
        layer_mode="trend_slope",
        unit="°C/decade",
        native_spatial_resolution="Point sample",
        time_window_default="1981-2024",
        color_scale_type="diverging",
        legend_stops=[
            LegendStop(value=-0.5, color="#2166ac", label_en="-0.5 °C/dec", label_bn="-০.৫ °C/দশক"),
            LegendStop(value=0.0, color="#f7f7f7", label_en="0.0 °C/dec", label_bn="০.০ °C/দশক"),
            LegendStop(value=0.5, color="#b2182b", label_en="+0.5 °C/dec", label_bn="+০.৫ °C/দশক"),
        ],
        nodata_value=-9999.0,
        attribution="NASA Langley Research Center (LaRC) POWER Project",
    ),
}
