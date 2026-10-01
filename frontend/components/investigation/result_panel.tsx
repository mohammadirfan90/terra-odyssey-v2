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
} from "lucide-react";
import { formatSlope, formatPValue, toBengaliDigits } from "../../lib/formatters";

interface ResultPanelProps {
  result: any;
  onOpenProvenance: () => void;
  isBangla?: boolean;
}

export default function ResultPanel({
  result,
  onOpenProvenance,
  isBangla = false,
}: ResultPanelProps) {
  if (!result) return null;

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
    <div className="w-full lg:w-96 flex-shrink-0 flex flex-col space-y-4 bg-slate-900/90 border border-slate-800 rounded-xl p-4 backdrop-blur">
      {/* Title & Region Header */}
      <div className="border-b border-slate-800 pb-3">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-mono text-cyan-400 uppercase tracking-wider">
            {isBangla ? "তদন্তের ফলাফল" : (result?.identity?.verification_status === "verified" ? "Verified Finding" : "Investigative Finding")}
          </span>
          <span className="text-[11px] font-mono text-slate-500">
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

      {/* Evidence Status Badge */}
      <div className={`p-3 rounded-lg border flex items-center space-x-3 ${badge.bg}`}>
        <div className="p-1.5 rounded-md bg-slate-950/40">{badge.icon}</div>
        <div>
          <h4 className="text-xs font-semibold leading-tight">{badge.title}</h4>
          <p className="text-[11px] opacity-80 mt-0.5">
            {isBangla ? evidence.interpretation_bn : evidence.interpretation_en}
          </p>
        </div>
      </div>

      {/* Quantitative Scientific Metrics Grid */}
      <div className="grid grid-cols-2 gap-2.5">
        {/* Metric 1: Theil-Sen Median Slope */}
        <div className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-2.5">
          <span className="text-[10px] text-slate-500 uppercase tracking-wide block">
            {isBangla ? "থেইল-সেন পরিবর্তনের হার" : "Theil-Sen Median Slope"}
          </span>
          <span className="text-base font-bold font-mono text-cyan-300 mt-0.5 block">
            {formatSlope(theil_sen.slope_per_decade, parameter.display_unit, isBangla)}
          </span>
          <span className="text-[10px] text-slate-400 font-mono block mt-0.5">
            {isBangla
              ? `৯৫% ব্যবধান: ${toBengaliDigits(theil_sen.ci_95_lower_per_decade?.toFixed(2) || "0")} হতে ${toBengaliDigits(theil_sen.ci_95_upper_per_decade?.toFixed(2) || "0")}`
              : `95% CI: [${theil_sen.ci_95_lower_per_decade?.toFixed(2)}, ${theil_sen.ci_95_upper_per_decade?.toFixed(2)}]`}
          </span>
        </div>

        {/* Metric 2: Mann-Kendall Significance */}
        <div className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-2.5">
          <span className="text-[10px] text-slate-500 uppercase tracking-wide block">
            {isBangla ? "ম্যান-কেন্ডাল প্রমাণ (p-মান)" : "Mann-Kendall p-value"}
          </span>
          <span className="text-base font-bold font-mono text-emerald-400 mt-0.5 block">
            {formatPValue(mann_kendall.p_value, isBangla)}
          </span>
          <span className="text-[10px] text-slate-400 font-mono block mt-0.5">
            {isBangla ? `মানক Z: ${toBengaliDigits(mann_kendall.Z?.toFixed(3) || "0")}` : `Standardized Z: ${mann_kendall.Z?.toFixed(3)}`}
          </span>
        </div>

        {/* Metric 3: Serial Correlation & VIF */}
        <div className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-2.5">
          <span className="text-[10px] text-slate-500 uppercase tracking-wide block">
            {isBangla ? "ধারাবাহিক অটোকরিলেশন" : "Serial Correlation AR(1)"}
          </span>
          <span className="text-xs font-bold font-mono text-slate-200 mt-1 block">
            {isBangla ? `r₁ = ${toBengaliDigits(diagnostics.ar1.toFixed(3))}` : `r₁ = ${diagnostics.ar1.toFixed(3)}`}
          </span>
          <span className="text-[10px] text-slate-400 font-mono block mt-0.5">
            {isBangla ? `হামেদ-রাও VIF = ${toBengaliDigits(diagnostics.vif.toFixed(2))}` : `Hamed-Rao VIF = ${diagnostics.vif.toFixed(2)}`}
          </span>
        </div>

        {/* Metric 4: Geodesic Spatial Coverage */}
        <div className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-2.5">
          <span className="text-[10px] text-slate-500 uppercase tracking-wide block">
            {isBangla ? "স্থানিক বিস্তার ও নমুনা" : "Valid Area Coverage"}
          </span>
          <span className="text-xs font-bold font-mono text-slate-200 mt-1 block">
            {isBangla
              ? `${toBengaliDigits(data_support.valid_area_coverage_pct.toFixed(1))}%`
              : `${data_support.valid_area_coverage_pct.toFixed(1)}%`}
          </span>
          <span className="text-[10px] text-slate-400 font-mono block mt-0.5">
            {isBangla
              ? `${toBengaliDigits(data_support.sample_count)} বার্ষিক পরিমাপ`
              : `${data_support.sample_count} annual samples`}
          </span>
        </div>
      </div>

      {/* Two-Sentence Constrained Narration Card (Chapter 11) */}
      <div className="bg-slate-950/80 border border-cyan-900/40 rounded-lg p-3 relative overflow-hidden">
        <div className="flex items-center space-x-1.5 mb-2">
          <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" />
          <span className="text-[11px] font-semibold tracking-wider uppercase text-cyan-300">
            {isBangla ? "যাচাইকৃত দ্বৈত বাক্য বর্ণনা (বাংলা)" : "Audited Narration (English)"}
          </span>
        </div>
        <p className="text-xs text-slate-200 leading-relaxed">
          {isBangla ? narration.bn[0] : narration.en[0]}
        </p>
        <p className="text-xs text-slate-300 leading-relaxed mt-2 pt-2 border-t border-slate-800/60">
          {isBangla ? narration.bn[1] : narration.en[1]}
        </p>
        <div className="mt-2.5 flex items-center justify-between text-[10px] text-slate-500 font-mono">
          <span>{isBangla ? "শূন্য বিভ্রম নিশ্চয়তা" : "Zero-Hallucination Safe"}</span>
          <span>JSON Pointer Validated</span>
        </div>
      </div>

      {/* Provenance & Audit Trigger */}
      <button
        onClick={onOpenProvenance}
        className="w-full py-2 px-3 rounded-lg border border-slate-800 bg-slate-950/60 hover:bg-slate-850 text-slate-300 text-xs flex items-center justify-center space-x-2 transition-colors"
      >
        <FileText className="w-3.5 h-3.5 text-slate-400" />
        <span>{isBangla ? "উৎস সূত্র ও অডিট ট্রেইল দেখুন" : "View Source Provenance & Audit"}</span>
      </button>
    </div>
  );
}
