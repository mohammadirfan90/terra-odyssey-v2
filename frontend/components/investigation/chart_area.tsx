"use client";

import React, { useState, useEffect } from "react";
import {
  LineChart as LineChartIcon,
  GitCompare,
  Layers,
  Table as TableIcon,
  Download,
  Info,
  AlertTriangle,
} from "lucide-react";
import { toBengaliDigits, formatSlope } from "../../lib/formatters";

interface ChartAreaProps {
  result: any;
  allRegions: any[];
  isBangla?: boolean;
}

export default function ChartArea({
  result,
  allRegions,
  isBangla = false,
}: ChartAreaProps) {
  const [activeTab, setActiveTab] = useState<"timeseries" | "comparison" | "seasonal" | "data">("timeseries");
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);

  // Comparison State
  const [compareRegionId, setCompareRegionId] = useState<string>("USA");
  const [comparisonData, setComparisonData] = useState<any | null>(null);
  const [isComparing, setIsComparing] = useState(false);
  const [comparisonError, setComparisonError] = useState<string | null>(null);

  // Reset comparison when primary result changes (Placed before early return to strictly adhere to Rules of Hooks)
  useEffect(() => {
    setComparisonData(null);
    setComparisonError(null);
  }, [result?.identity?.result_id]);

  if (!result) return null;

  const { series, theil_sen, fitted_band, parameter, region, identity, data_support, provenance, time_window } = result;
  const years: number[] = series.years;
  const values: number[] = series.values;
  const unit: string = series.unit;

  // Chart dimensions & scaling
  const width = 800;
  const height = 280;
  const padding = { top: 20, right: 30, bottom: 40, left: 55 };

  const minYear = Math.min(...years);
  const maxYear = Math.max(...years);

  // Determine Y range from both points and bootstrap bounds
  let minY = Math.min(...values);
  let maxY = Math.max(...values);

  if (fitted_band && fitted_band.points) {
    fitted_band.points.forEach((p: any) => {
      if (p.lower < minY) minY = p.lower;
      if (p.upper > maxY) maxY = p.upper;
    });
  }

  // Add 10% vertical padding
  const ySpan = maxY - minY || 1;
  const yDomainMin = minY - ySpan * 0.1;
  const yDomainMax = maxY + ySpan * 0.1;

  const scaleX = (yr: number) => {
    return padding.left + ((yr - minYear) / (maxYear - minYear || 1)) * (width - padding.left - padding.right);
  };

  const scaleY = (val: number) => {
    return height - padding.bottom - ((val - yDomainMin) / (yDomainMax - yDomainMin)) * (height - padding.top - padding.bottom);
  };

  // Build SVG path for Theil-Sen line
  const refTime = theil_sen.ref_time;
  const slope = theil_sen.slope_per_year;
  const intercept = theil_sen.intercept;

  const lineStartVal = intercept + slope * (minYear - refTime);
  const lineEndVal = intercept + slope * (maxYear - refTime);

  const trendLinePath = `M ${scaleX(minYear)} ${scaleY(lineStartVal)} L ${scaleX(maxYear)} ${scaleY(lineEndVal)}`;

  // Build SVG path for Bootstrap Uncertainty Band
  let bandPolygonPoints = "";
  if (fitted_band && fitted_band.points && fitted_band.points.length > 0) {
    const upperPoints = fitted_band.points.map((p: any) => `${scaleX(p.time)},${scaleY(p.upper)}`).join(" ");
    const lowerPoints = [...fitted_band.points].reverse().map((p: any) => `${scaleX(p.time)},${scaleY(p.lower)}`).join(" ");
    bandPolygonPoints = `${upperPoints} ${lowerPoints}`;
  }

  // Handle comparison query
  const handleRunComparison = async () => {
    setIsComparing(true);
    setComparisonError(null);
    try {
      const res = await fetch("/api/comparisons", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          region_id_a: region.id,
          region_id_b: compareRegionId,
          parameter_id: parameter.id,
          start_year: time_window?.start_year ?? data_support?.retained_interval?.[0],
          end_year: time_window?.end_year ?? data_support?.retained_interval?.[1],
          binding_id: provenance?.dataset_id || provenance?.collection_id,
          policy_id: result?.reproducibility?.policy_id || result?.identity?.normalized_query?.policy_id || "standard_climate_temperature",
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setComparisonData(data);
        setComparisonError(null);
      } else {
        const errJson = await res.json();
        setComparisonError(errJson.detail?.detail || errJson.detail || "Comparison could not be computed.");
        setComparisonData(null);
      }
    } catch (err) {
      console.error("Comparison failed:", err);
      setComparisonError("Failed to connect to local comparison service.");
    } finally {
      setIsComparing(false);
    }
  };

  return (
    <div className="w-full bg-slate-900/90 border border-slate-800 rounded-xl overflow-hidden backdrop-blur flex flex-col">
      {/* Tab Navigation Header */}
      <div className="flex items-center justify-between border-b border-slate-800 px-4 pt-2 bg-slate-950/40">
        <div className="flex space-x-1">
          <button
            onClick={() => setActiveTab("timeseries")}
            className={`px-3 py-2 text-xs font-medium rounded-t-lg flex items-center space-x-2 border-b-2 transition-colors ${
              activeTab === "timeseries"
                ? "border-cyan-400 text-cyan-300 bg-slate-900/80"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            <LineChartIcon className="w-3.5 h-3.5" />
            <span>{isBangla ? "সময় সিরিজ ও অনিশ্চয়তা ব্যান্ড" : "Time Series & Fitted Band"}</span>
          </button>

          <button
            onClick={() => setActiveTab("comparison")}
            className={`px-3 py-2 text-xs font-medium rounded-t-lg flex items-center space-x-2 border-b-2 transition-colors ${
              activeTab === "comparison"
                ? "border-cyan-400 text-cyan-300 bg-slate-900/80"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            <GitCompare className="w-3.5 h-3.5" />
            <span>{isBangla ? "আঞ্চলিক তুলনা ও ব্যবধান" : "Paired Comparison"}</span>
          </button>

          <button
            onClick={() => setActiveTab("seasonal")}
            className={`px-3 py-2 text-xs font-medium rounded-t-lg flex items-center space-x-2 border-b-2 transition-colors ${
              activeTab === "seasonal"
                ? "border-cyan-400 text-cyan-300 bg-slate-900/80"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>{isBangla ? "মৌসুমি বিশ্লেষণ (STL)" : "Seasonal Diagnostics"}</span>
          </button>

          <button
            onClick={() => setActiveTab("data")}
            className={`px-3 py-2 text-xs font-medium rounded-t-lg flex items-center space-x-2 border-b-2 transition-colors ${
              activeTab === "data"
                ? "border-cyan-400 text-cyan-300 bg-slate-900/80"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            <TableIcon className="w-3.5 h-3.5" />
            <span>{isBangla ? "উপাত্ত তালিকা" : "Data Table"}</span>
          </button>
        </div>

        {/* Download Action */}
        <div className="flex items-center space-x-2 pb-1.5">
          <a
            href={`/api/results/${identity.result_id}/export?format=csv`}
            download
            className="text-[11px] px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded flex items-center space-x-1.5 transition-colors"
          >
            <Download className="w-3 h-3 text-cyan-400" />
            <span>CSV</span>
          </a>
        </div>
      </div>

      {/* Tab 1: Time Series & Fitted Band */}
      {activeTab === "timeseries" && (
        <div className="p-4 flex flex-col items-center">
          <div className="w-full flex items-center justify-between text-xs text-slate-400 mb-2">
            <div className="flex items-center space-x-4">
              <span className="flex items-center space-x-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 inline-block" />
                <span>{isBangla ? "বার্ষিক পর্যবেক্ষণ" : "Observed Annual Points"}</span>
              </span>
              <span className="flex items-center space-x-1.5">
                <span className="w-4 h-0.5 bg-emerald-400 inline-block" />
                <span>{isBangla ? "থেইল-সেন রেখা" : "Theil-Sen Trend Line"}</span>
              </span>
              <span className="flex items-center space-x-1.5">
                <span className="w-3 h-2 bg-emerald-400/20 border border-emerald-400/40 inline-block rounded-sm" />
                <span>{isBangla ? "৯৫% বুটস্ট্র্যাপ ব্যান্ড" : "95% Pointwise Bootstrap Band"}</span>
              </span>
            </div>
            <span className="font-mono text-[11px] text-slate-500">
              {isBangla ? `একক: ${unit}` : `Units: ${unit}`}
            </span>
          </div>

          <div className="w-full overflow-x-auto">
            <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-auto min-w-[600px] select-none">
              {/* Y Axis Grid lines */}
              {[0, 0.25, 0.5, 0.75, 1].map((frac, idx) => {
                const yVal = yDomainMin + frac * (yDomainMax - yDomainMin);
                const yPos = scaleY(yVal);
                return (
                  <g key={idx}>
                    <line
                      x1={padding.left}
                      y1={yPos}
                      x2={width - padding.right}
                      y2={yPos}
                      stroke="#1e293b"
                      strokeDasharray="3 3"
                    />
                    <text
                      x={padding.left - 8}
                      y={yPos + 4}
                      fill="#64748b"
                      fontSize="10"
                      textAnchor="end"
                      fontFamily="monospace"
                    >
                      {isBangla ? toBengaliDigits(yVal.toFixed(1)) : yVal.toFixed(1)}
                    </text>
                  </g>
                );
              })}

              {/* X Axis Grid lines */}
              {years.filter((_, i) => i % 5 === 0 || i === years.length - 1).map((yr, idx) => {
                const xPos = scaleX(yr);
                return (
                  <g key={idx}>
                    <line
                      x1={xPos}
                      y1={padding.top}
                      x2={xPos}
                      y2={height - padding.bottom}
                      stroke="#1e293b"
                      strokeDasharray="2 4"
                    />
                    <text
                      x={xPos}
                      y={height - padding.bottom + 18}
                      fill="#64748b"
                      fontSize="10"
                      textAnchor="middle"
                      fontFamily="monospace"
                    >
                      {isBangla ? toBengaliDigits(yr) : yr}
                    </text>
                  </g>
                );
              })}

              {/* Bootstrap Uncertainty Band Polygon */}
              {bandPolygonPoints && (
                <polygon
                  points={bandPolygonPoints}
                  fill="#10b981"
                  fillOpacity="0.12"
                  stroke="#10b981"
                  strokeWidth="0.8"
                  strokeDasharray="2 2"
                />
              )}

              {/* Theil-Sen Fitted Trend Line */}
              <path d={trendLinePath} stroke="#34d399" strokeWidth="2.5" fill="none" />

              {/* Observed Points & Interactive Hover Circles */}
              {years.map((yr, idx) => {
                const x = scaleX(yr);
                const y = scaleY(values[idx]);
                const isHovered = hoveredIndex === idx;

                return (
                  <g key={yr} onMouseEnter={() => setHoveredIndex(idx)} onMouseLeave={() => setHoveredIndex(null)}>
                    <circle
                      cx={x}
                      cy={y}
                      r={isHovered ? 6 : 3.5}
                      fill={isHovered ? "#22d3ee" : "#06b6d4"}
                      stroke="#0f172a"
                      strokeWidth="1.5"
                      className="cursor-pointer transition-all"
                    />
                  </g>
                );
              })}

              {/* Hover Tooltip Box */}
              {hoveredIndex !== null && (
                <g transform={`translate(${scaleX(years[hoveredIndex])}, ${scaleY(values[hoveredIndex]) - 35})`}>
                  <rect
                    x="-45"
                    y="-12"
                    width="90"
                    height="28"
                    rx="4"
                    fill="#090d16"
                    stroke="#06b6d4"
                    strokeWidth="1"
                  />
                  <text x="0" y="2" fill="#e2e8f0" fontSize="10" fontWeight="bold" textAnchor="middle" fontFamily="monospace">
                    {isBangla ? `${toBengaliDigits(years[hoveredIndex])}: ${toBengaliDigits(values[hoveredIndex].toFixed(2))} ${unit}` : `${years[hoveredIndex]}: ${values[hoveredIndex].toFixed(2)} ${unit}`}
                  </text>
                </g>
              )}
            </svg>
          </div>
        </div>
      )}

      {/* Tab 2: Regional Comparison */}
      {activeTab === "comparison" && (
        <div className="p-4 space-y-4">
          <div className="flex items-center space-x-3 bg-slate-950 p-3 rounded-lg border border-slate-800">
            <span className="text-xs text-slate-300">
              {isBangla ? "তুলনার জন্য অঞ্চল নির্বাচন করুন:" : "Compare with paired region:"}
            </span>
            <select
              value={compareRegionId}
              onChange={(e) => setCompareRegionId(e.target.value)}
              className="bg-slate-900 border border-slate-700 rounded px-2.5 py-1 text-xs text-slate-200"
            >
              {allRegions
                .filter((r) => r.id !== region.id && r.has_ocean_support === region.has_ocean_support)
                .map((r) => (
                  <option key={r.id} value={r.id}>
                    {isBangla ? r.name_bn : r.name_en} ({r.id})
                  </option>
                ))}
            </select>
            <button
              onClick={handleRunComparison}
              disabled={isComparing}
              className="px-3 py-1 bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold rounded text-xs transition-colors"
            >
              {isComparing ? (isBangla ? "গণনা..." : "Contrasting...") : (isBangla ? "তুলনা করুন" : "Compute Contrast")}
            </button>
          </div>

          {comparisonError && (
            <div className="p-3 bg-red-950/40 border border-red-800/60 rounded-lg text-xs text-red-300 flex items-center space-x-2">
              <AlertTriangle className="w-4 h-4 text-red-400 flex-shrink-0" />
              <span>{comparisonError}</span>
            </div>
          )}

          {comparisonData && (
            <div className="space-y-3">
              <div className="grid grid-cols-3 gap-3">
                <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                  <span className="text-[10px] text-slate-500 block">{comparisonData.region_a.name}</span>
                  <span className="text-sm font-bold font-mono text-cyan-300">
                    {formatSlope(comparisonData.region_a.slope_per_decade, comparisonData.unit, isBangla)}
                  </span>
                </div>
                <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                  <span className="text-[10px] text-slate-500 block">{comparisonData.region_b.name}</span>
                  <span className="text-sm font-bold font-mono text-cyan-300">
                    {formatSlope(comparisonData.region_b.slope_per_decade, comparisonData.unit, isBangla)}
                  </span>
                </div>
                <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                  <span className="text-[10px] text-slate-500 block">
                    {isBangla ? "ব্যবধানের ধারা (A - B)" : "Difference Trend (A - B)"}
                  </span>
                  <span className="text-sm font-bold font-mono text-emerald-400">
                    {formatSlope(comparisonData.contrast_difference_series.slope_per_decade, comparisonData.unit, isBangla)}
                  </span>
                </div>
              </div>

              <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 text-xs text-slate-300">
                <span className="font-semibold text-cyan-300">
                  {isBangla ? "সরাসরি পার্থক্য বিশ্লেষণ:" : "Direct Contrast Finding:"}
                </span>{" "}
                {isBangla
                  ? `${comparisonData.common_years_count} টি যৌথ বছরে ${comparisonData.region_a.name} অঞ্চলের পরিবর্তনের হার ছিল ${comparisonData.contrast_difference_series.slope_per_decade > 0 ? "অধিকতর দ্রুত" : "মন্থর"}।`
                  : `Over ${comparisonData.common_years_count} common eligible years, the paired difference series exhibits a median trend of ${formatSlope(comparisonData.contrast_difference_series.slope_per_decade, comparisonData.unit)}.`}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Tab 3: Seasonal Diagnostics */}
      {activeTab === "seasonal" && (
        <div className="p-6 text-center text-xs text-slate-400 space-y-2">
          <Info className="w-5 h-5 mx-auto text-cyan-400" />
          <p className="font-semibold text-slate-200">
            {isBangla ? "মৌসুমি বিশ্লেষণ (STL)" : "Robust Seasonal-Trend Decomposition (STL)"}
          </p>
          <p className="max-w-md mx-auto text-slate-400 text-[11px] leading-relaxed">
            {isBangla
              ? "বার্ষিক গড় ধারার জন্য মৌসুমি বিয়োজন প্রযোজ্য নয়। মাসিক উপাত্তের জন্য STL বিয়োজন স্বয়ংক্রিয়ভাবে ট্রেন্ড, সাইক্লিক্যাল এবং অবশিষ্টাংশ পৃথক করে।"
              : "Annual series represent fixed-cadence observations where intra-annual seasonality has been integrated. For monthly collections (e.g. MERRA-2 monthly), STL decomposes components across 12-month periods."}
          </p>
        </div>
      )}

      {/* Tab 4: Data Table */}
      {activeTab === "data" && (
        <div className="p-3 max-h-64 overflow-y-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 font-mono text-[11px]">
                <th className="py-2 px-3">{isBangla ? "বছর" : "Year"}</th>
                <th className="py-2 px-3">{isBangla ? `মান (${unit})` : `Observed Value (${unit})`}</th>
                <th className="py-2 px-3">{isBangla ? "গুণগত মান (QA)" : "QA Validity"}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/40 font-mono text-slate-300">
              {years.map((yr, idx) => (
                <tr key={yr} className="hover:bg-slate-800/30">
                  <td className="py-1.5 px-3">{isBangla ? toBengaliDigits(yr) : yr}</td>
                  <td className="py-1.5 px-3 text-cyan-300">
                    {isBangla ? toBengaliDigits(values[idx].toFixed(3)) : values[idx].toFixed(3)}
                  </td>
                  <td className="py-1.5 px-3 text-emerald-400 text-[11px]">
                    {isBangla ? "উত্তীর্ণ (বৈধ)" : "PASSED (Valid)"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
