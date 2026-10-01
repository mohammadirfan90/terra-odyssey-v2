"use client";

import React from "react";
import {
  TrendingUp,
  TrendingDown,
  Minus,
  AlertTriangle,
  HelpCircle,
  ShieldCheck,
  FileText,
  Activity,
  Compass,
  ArrowRight,
  Database,
  Sparkles,
  Info,
} from "lucide-react";
import { formatSlope, formatPValue, toBengaliDigits } from "../../lib/formatters";
import { PARAM_REGION_CACHE } from "./selection_rail";

interface ResultPanelProps {
  result: any;
  error?: string | null;
  currentParams?: { regionId: string; parameterId: string; startYear: number; endYear: number };
  onSwitchSelection?: (params: { regionId: string; parameterId: string }) => void;
  onOpenProvenance: () => void;
  isBangla?: boolean;
}

export default function ResultPanel({
  result,
  error,
  currentParams,
  onSwitchSelection,
  onOpenProvenance,
  isBangla = false,
}: ResultPanelProps) {
  // If there is an error (e.g. offline cache miss), display an elegant, actionable remediation card
  if (error) {
    const isManifestMissing =
      error.includes("not registered in the verified acquisition manifest") ||
      error.includes("Cache Miss") ||
      error.includes("CACHE_MISS_OFFLINE");

    const currentReg = currentParams?.regionId || "IND";
    const currentParam = currentParams?.parameterId || "land_surface_temperature_night";

    // Find parameters available for this region
    const availableParamsForThisRegion = Object.entries(PARAM_REGION_CACHE)
      .filter(([_, regs]) => regs.includes(currentReg))
      .map(([pid]) => pid);

    // Find regions available for this parameter
    const availableRegionsForThisParam = PARAM_REGION_CACHE[currentParam] || [];

    return (
      <div className="w-full lg:w-96 flex-shrink-0 flex flex-col space-y-4 bg-slate-900/95 border border-slate-800 rounded-xl p-5 backdrop-blur shadow-2xl">
        <div className="border-b border-slate-800 pb-3">
          <div className="flex items-center space-x-2 text-amber-400 mb-1">
            <Database className="w-4 h-4" />
            <span className="text-[11px] font-mono uppercase tracking-wider font-semibold">
              {isBangla ? "অফলাইন ক্যাশ নোটিশ" : "Offline Cache Notice"}
            </span>
          </div>
          <h3 className="text-base font-bold text-slate-100">
            {isBangla ? "তথ্য অফলাইনে সংরক্ষিত নেই" : "Dataset Unavailable Offline"}
          </h3>
        </div>

        {/* Informative Explanation */}
        <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-3 text-xs text-amber-200">
          <p className="leading-relaxed">
            {isBangla
              ? "কঠোর অফলাইন-ফার্স্ট নীতির কারণে বাহ্যিক ডাউনলোড নিষিদ্ধ। শুধুমাত্র পূর্ব-যাচাইকৃত পর্যবেক্ষণ বিশ্লেষণ করা যাবে।"
              : "Strict offline compliance (OFFLINE=1) bars unverified runtime network downloads. Only pre-acquired local series can be analyzed."}
          </p>
          <div className="mt-2 text-[11px] font-mono text-slate-400 bg-slate-950/70 p-2 rounded border border-slate-800/80">
            {error}
          </div>
        </div>

        {/* Actionable Suggestions */}
        {isManifestMissing && onSwitchSelection && (
          <div className="space-y-3 pt-1">
            {/* 1. Switch to an available parameter for this region */}
            {availableParamsForThisRegion.length > 0 && (
              <div>
                <span className="text-[11px] font-semibold text-slate-300 block mb-1.5 flex items-center space-x-1">
                  <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
                  <span>
                    {isBangla ? "এই অঞ্চলের জন্য উপলব্ধ পরামিতি:" : `Available for Region (${currentReg}):`}
                  </span>
                </span>
                <div className="space-y-1">
                  {availableParamsForThisRegion.map((pId) => {
                    const label =
                      pId === "air_temperature_2m"
                        ? "Air Temperature (2m) [MERRA-2]"
                        : pId === "sea_surface_temperature"
                        ? "Sea Surface Temperature [OISST]"
                        : pId;
                    return (
                      <button
                        key={pId}
                        type="button"
                        onClick={() => onSwitchSelection({ regionId: currentReg, parameterId: pId })}
                        className="w-full text-left text-xs bg-cyan-500/15 hover:bg-cyan-500/25 border border-cyan-500/40 text-cyan-200 px-3 py-2 rounded-lg font-medium transition-all flex items-center justify-between group"
                      >
                        <span>{label}</span>
                        <ArrowRight className="w-3.5 h-3.5 text-cyan-400 group-hover:translate-x-1 transition-transform" />
                      </button>
                    );
                  })}
                </div>
              </div>
            )}

            {/* 2. Switch to an available region for this parameter */}
            {availableRegionsForThisParam.length > 0 && (
              <div>
                <span className="text-[11px] font-semibold text-slate-300 block mb-1.5">
                  {isBangla ? "এই পরামিতির জন্য উপলব্ধ অঞ্চল:" : "Regions with verified data for this parameter:"}
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {availableRegionsForThisParam.slice(0, 5).map((rId) => (
                    <button
                      key={rId}
                      type="button"
                      onClick={() => onSwitchSelection({ regionId: rId, parameterId: currentParam })}
                      className="text-[11px] font-mono bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 px-2.5 py-1 rounded-md transition-colors"
                    >
                      {rId}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    );
  }

  // Initial Empty State
  if (!result) {
    return (
      <div className="w-full lg:w-96 flex-shrink-0 flex flex-col justify-center items-center text-center space-y-3 bg-slate-900/90 border border-slate-800 rounded-xl p-6 backdrop-blur shadow-2xl">
        <div className="w-12 h-12 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 mb-1">
          <Compass className="w-6 h-6" />
        </div>
        <h3 className="text-base font-bold text-slate-200">
          {isBangla ? "অনুসন্ধান প্রস্তুত" : "Investigation Ready"}
        </h3>
        <p className="text-xs text-slate-400 leading-relaxed max-w-xs">
          {isBangla
            ? "বাম পাশের তালিকা থেকে একটি অঞ্চল এবং ভৌত পরামিতি নির্বাচন করে 'বিশ্লেষণ চালান'-এ ক্লিক করুন।"
            : "Select a region and physical parameter on the left rail, or click any region on the map to begin."}
        </p>
      </div>
    );
  }

  const { region, parameter, theil_sen, mann_kendall, evidence, diagnostics, data_support, narration, provenance } = result;

  // Determine badge styling based on scientific evidence state
  const getEvidenceBadge = () => {
    switch (evidence.state) {
      case "supported_increase":
        return {
          bg: "bg-emerald-500/15 border-emerald-500/40 text-emerald-300",
          icon: <TrendingUp className="w-4 h-4 text-emerald-400" />,
          title: isBangla ? "পরিসংখ্যানগতভাবে সমর্থিত বৃদ্ধি" : "Supported Upward Trend",
        };
      case "supported_decrease":
        return {
          bg: "bg-cyan-500/15 border-cyan-500/40 text-cyan-300",
          icon: <TrendingDown className="w-4 h-4 text-cyan-400" />,
          title: isBangla ? "পরিসংখ্যানগতভাবে সমর্থিত হ্রাস" : "Supported Downward Trend",
        };
      case "inconclusive":
        return {
          bg: "bg-slate-700/30 border-slate-600 text-slate-300",
          icon: <Minus className="w-4 h-4 text-slate-400" />,
          title: isBangla ? "অমীমাংসিত প্রমাণ (কোনো একক ধারা নেই)" : "Inconclusive Statistical Evidence",
        };
      case "limited": {
        const isGap = evidence?.interpretation_en?.includes("missing gap");
        return {
          bg: "bg-amber-500/15 border-amber-500/40 text-amber-300",
          icon: <AlertTriangle className="w-4 h-4 text-amber-400" />,
          title: isGap
            ? isBangla
              ? "সীমিত তথ্যাদি (অনুপস্থিত ব্যবধান)"
              : "Limited Record (Missing Gap)"
            : isBangla
            ? "সীমিত তথ্যাদি / অনুসন্ধানমূলক"
            : "Limited Record Duration (<20 Yrs)",
        };
      }
      case "flat":
        return {
          bg: "bg-slate-700/30 border-slate-600 text-slate-300",
          icon: <Minus className="w-4 h-4 text-slate-400" />,
          title: isBangla ? "ধারাবাহিক পরিবর্তনহীন (প্রায় শূন্য)" : "Flat / Near-Zero Rate",
        };
      default:
        return {
          bg: "bg-rose-500/15 border-rose-500/40 text-rose-300",
          icon: <AlertTriangle className="w-4 h-4 text-rose-400" />,
          title: isBangla ? "অপর্যাপ্ত পর্যবেক্ষণ তথ্য" : "Insufficient Data",
        };
    }
  };

  const badge = getEvidenceBadge();

  return (
    <div className="w-full lg:w-96 flex-shrink-0 flex flex-col space-y-4 bg-slate-900/95 border border-slate-800 rounded-xl p-5 backdrop-blur shadow-2xl">
      {/* Title & Region Header */}
      <div className="border-b border-slate-800 pb-3">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-mono text-cyan-400 uppercase tracking-wider font-semibold">
            {isBangla ? "তদন্তের ফলাফল" : (result?.identity?.verification_status === "verified" ? "Verified Finding" : "Investigative Finding")}
          </span>
          <span className="text-[11px] font-mono text-slate-400">
            {isBangla ? `${toBengaliDigits(data_support.retained_interval[0])}-${toBengaliDigits(data_support.retained_interval[1])}` : `${data_support.retained_interval[0]}-${data_support.retained_interval[1]}`}
          </span>
        </div>
        <h3 className="text-lg font-bold text-slate-100 mt-1">
          {isBangla ? region.name_bn : region.name_en}
        </h3>
        <p className="text-xs text-slate-400">
          {isBangla ? parameter.name_bn : parameter.name_en} ({parameter.display_unit})
        </p>
      </div>

      {/* Magnitude & Evidence Highlight Card */}
      <div className="p-3.5 rounded-lg border border-slate-800 bg-slate-950/70 space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-300">
            {isBangla ? "পরিবর্তনের মাত্রা (থিয়েল-সেন)" : "Decadal Rate (Theil-Sen)"}
          </span>
          <span className="text-sm font-bold font-mono text-cyan-300">
            {formatSlope(theil_sen.slope_per_decade, parameter.display_unit, isBangla)}
          </span>
        </div>

        {/* 95% Confidence Interval */}
        <div className="flex items-center justify-between text-xs text-slate-400 border-t border-slate-800/80 pt-2">
          <span>{isBangla ? "৯৫% আত্মবিশ্বাস ব্যবধান" : "95% Confidence Interval"}</span>
          <span className="font-mono text-slate-300">
            {typeof theil_sen?.ci_95_lower_per_decade === "number" &&
            typeof theil_sen?.ci_95_upper_per_decade === "number" &&
            !isNaN(theil_sen.ci_95_lower_per_decade) &&
            !isNaN(theil_sen.ci_95_upper_per_decade) ? (
              isBangla
                ? `[${toBengaliDigits(theil_sen.ci_95_lower_per_decade.toFixed(2))}, ${toBengaliDigits(theil_sen.ci_95_upper_per_decade.toFixed(2))}]`
                : `[${theil_sen.ci_95_lower_per_decade.toFixed(2)}, ${theil_sen.ci_95_upper_per_decade.toFixed(2)}]`
            ) : "N/A"}
          </span>
        </div>

        {/* Evidence Status Pill */}
        <div className={`p-2.5 rounded-lg border flex items-center space-x-2 ${badge.bg}`}>
          {badge.icon}
          <span className="text-xs font-semibold leading-tight">{badge.title}</span>
        </div>
      </div>

      {/* Statistical Rigor Table */}
      <div className="grid grid-cols-2 gap-2 text-xs">
        <div className="p-2.5 rounded-lg bg-slate-950/50 border border-slate-800">
          <span className="text-[10px] text-slate-400 block font-medium">Mann-Kendall p-value</span>
          <span className="font-mono font-bold text-slate-200 text-sm mt-0.5 block">
            {formatPValue(mann_kendall?.p_value, isBangla)}
          </span>
        </div>
        <div className="p-2.5 rounded-lg bg-slate-950/50 border border-slate-800">
          <span className="text-[10px] text-slate-400 block font-medium">Standardized Z</span>
          <span className="font-mono font-bold text-slate-200 text-sm mt-0.5 block">
            {(() => {
              const zVal = mann_kendall?.Z ?? mann_kendall?.z_score;
              return typeof zVal === "number" && !isNaN(zVal)
                ? (isBangla ? toBengaliDigits(zVal.toFixed(2)) : zVal.toFixed(2))
                : "N/A";
            })()}
          </span>
        </div>
        <div className="p-2.5 rounded-lg bg-slate-950/50 border border-slate-800">
          <span className="text-[10px] text-slate-400 block font-medium">Autocorrelation VIF</span>
          <span className="font-mono font-bold text-slate-200 text-sm mt-0.5 block">
            {typeof diagnostics?.vif === "number" && !isNaN(diagnostics.vif)
              ? (isBangla ? toBengaliDigits(diagnostics.vif.toFixed(2)) : diagnostics.vif.toFixed(2))
              : "1.00"}
          </span>
        </div>
        <div className="p-2.5 rounded-lg bg-slate-950/50 border border-slate-800">
          <span className="text-[10px] text-slate-400 block font-medium">Valid Coverage</span>
          <span className="font-mono font-bold text-slate-200 text-sm mt-0.5 block">
            {data_support?.average_coverage_pct !== undefined && data_support?.average_coverage_pct !== null
              ? (isBangla
                  ? `${toBengaliDigits(Math.round(data_support.average_coverage_pct))}%`
                  : `${Math.round(data_support.average_coverage_pct)}%`)
              : "100%"}
          </span>
        </div>
      </div>

      {/* Bilingual Plain-Language Narration (Section 7) */}
      <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 text-xs text-slate-300 space-y-1.5">
        <div className="flex items-center space-x-1.5 text-cyan-400 font-semibold text-[11px] mb-1">
          <FileText className="w-3.5 h-3.5" />
          <span>{isBangla ? "বৈজ্ঞানিক বিবরণ" : "Deterministic Narration"}</span>
        </div>
        <p className="leading-relaxed text-slate-200">
          {isBangla ? narration.narrative_bn : narration.narrative_en}
        </p>
      </div>

      {/* Provenance & Audit Trigger */}
      <div className="pt-1">
        <button
          onClick={onOpenProvenance}
          className="w-full py-2 px-3 rounded-lg bg-slate-800 hover:bg-slate-700/80 border border-slate-700 text-slate-200 text-xs font-medium flex items-center justify-center space-x-2 transition-colors"
        >
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <span>{isBangla ? "উপাত্তের নির্ভুলতা ও অডিট ট্রেস" : "Inspect Provenance & Audit Trace"}</span>
        </button>
      </div>
    </div>
  );
}
