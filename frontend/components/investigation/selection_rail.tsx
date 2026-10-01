"use client";

import React, { useState } from "react";
import { Search, Play, Filter, Globe, Waves, AlertCircle } from "lucide-react";
import { toBengaliDigits } from "../../lib/formatters";

export interface SelectionParams {
  regionId: string;
  parameterId: string;
  startYear: number;
  endYear: number;
}

interface SelectionRailProps {
  regions: any[];
  parameters: any[];
  currentParams: SelectionParams;
  onCommit: (params: SelectionParams) => void;
  isLoading: boolean;
  isBangla?: boolean;
}

export default function SelectionRail({
  regions,
  parameters,
  currentParams,
  onCommit,
  isLoading,
  isBangla = false,
}: SelectionRailProps) {
  const [draftParams, setDraftParams] = useState<SelectionParams>(currentParams);
  const [searchQuery, setSearchQuery] = useState("");

  // Synchronize draft state when active query changes (e.g. via map click)
  React.useEffect(() => {
    setDraftParams(currentParams);
  }, [currentParams]);

  const filteredRegions = regions.filter((r) => {
    const q = searchQuery.toLowerCase();
    return (
      r.name_en.toLowerCase().includes(q) ||
      r.name_bn.includes(q) ||
      r.id.toLowerCase().includes(q)
    );
  });

  const selectedRegion = regions.find((r) => r.id === draftParams.regionId);
  const selectedParam = parameters.find((p) => p.id === draftParams.parameterId);

  const isOceanParam = selectedParam?.valid_spatial_support === "ocean";
  const isOceanRegion = selectedRegion?.has_ocean_support;
  const isSpatialIncompatible = isOceanParam && !isOceanRegion;

  const hasDraftChanges =
    draftParams.regionId !== currentParams.regionId ||
    draftParams.parameterId !== currentParams.parameterId ||
    draftParams.startYear !== currentParams.startYear ||
    draftParams.endYear !== currentParams.endYear;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!isSpatialIncompatible) {
      onCommit(draftParams);
    }
  };

  return (
    <aside className="w-full lg:w-80 flex-shrink-0 flex flex-col space-y-5 bg-slate-900/90 border border-slate-800 rounded-xl p-4 backdrop-blur">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <h2 className="text-sm font-semibold tracking-wider uppercase text-cyan-400 flex items-center space-x-2">
          <Filter className="w-4 h-4" />
          <span>{isBangla ? "অনুসন্ধান পরামিতি" : "Investigation Query"}</span>
        </h2>
        {hasDraftChanges && (
          <span className="text-[11px] font-mono text-amber-400 bg-amber-400/10 px-2 py-0.5 rounded border border-amber-400/30 animate-pulse">
            {isBangla ? "অসংরক্ষিত ড্রাফট" : "Draft Changed"}
          </span>
        )}
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col space-y-4">
        {/* Region Search & Selection */}
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1.5 flex items-center justify-between">
            <span>{isBangla ? "অঞ্চল বা দেশ নির্বাচন" : "Region or Ocean Basin"}</span>
            <span className="text-[10px] text-slate-500 font-mono">
              {filteredRegions.length} {isBangla ? "উপলব্ধ" : "available"}
            </span>
          </label>
          <div className="relative mb-2">
            <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-slate-500" />
            <input
              type="text"
              placeholder={isBangla ? "দেশ বা সমুদ্র খুঁজুন..." : "Filter regions (e.g. Bangladesh, USA)..."}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-8 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition-colors"
            />
          </div>

          <div className="max-h-40 overflow-y-auto space-y-1 pr-1 border border-slate-800/80 rounded-lg p-1 bg-slate-950/50">
            {filteredRegions.map((reg) => {
              const isSelected = draftParams.regionId === reg.id;
              const isOcean = reg.region_type === "ocean_basin";
              return (
                <button
                  type="button"
                  key={reg.id}
                  onClick={() => setDraftParams({ ...draftParams, regionId: reg.id })}
                  className={`w-full text-left px-2.5 py-1.5 rounded-md text-xs flex items-center justify-between transition-colors ${
                    isSelected
                      ? "bg-cyan-500/20 text-cyan-300 font-medium border border-cyan-500/30"
                      : "text-slate-300 hover:bg-slate-800/60"
                  }`}
                >
                  <div className="flex items-center space-x-2 truncate">
                    {isOcean ? (
                      <Waves className="w-3 h-3 text-sky-400 flex-shrink-0" />
                    ) : (
                      <Globe className="w-3 h-3 text-emerald-400 flex-shrink-0" />
                    )}
                    <span className="truncate">{isBangla ? reg.name_bn : reg.name_en}</span>
                  </div>
                  <span className="text-[10px] font-mono text-slate-500 ml-2">{reg.id}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Parameter Selector */}
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1.5">
            {isBangla ? "ভৌত পরামিতি" : "Physical Parameter"}
          </label>
          <select
            value={draftParams.parameterId}
            onChange={(e) => setDraftParams({ ...draftParams, parameterId: e.target.value })}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-cyan-500 transition-colors"
          >
            {parameters.map((param) => (
              <option key={param.id} value={param.id}>
                {isBangla ? param.name_bn : param.name_en} ({param.display_unit})
              </option>
            ))}
          </select>
          <p className="text-[11px] text-slate-400 mt-1.5 leading-relaxed bg-slate-950/40 p-2 rounded border border-slate-800/40">
            {isBangla ? selectedParam?.definition_bn : selectedParam?.definition_en}
          </p>
        </div>

        {/* Spatial Incompatibility Warning */}
        {isSpatialIncompatible && (
          <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-2.5 text-xs text-amber-300 flex items-start space-x-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5 text-amber-400" />
            <div>
              <p className="font-semibold">{isBangla ? "অঞ্চল অসঙ্গতি" : "Spatial Boundary Mismatch"}</p>
              <p className="text-[11px] text-amber-200/80 mt-0.5">
                {isBangla
                  ? "সমুদ্রপৃষ্ঠের তাপমাত্রা (এসএসটি) মূল্যায়নের জন্য একটি সমুদ্র অঞ্চল (যেমন বঙ্গোপসাগর) নির্বাচন করুন।"
                  : "Sea surface temperature requires an ocean basin or marine region. Choose an ocean basin from the list above."}
              </p>
            </div>
          </div>
        )}

        {/* Analysis Window */}
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1.5 flex justify-between">
            <span>{isBangla ? "বিশ্লেষণ সময়কাল" : "Observation Window"}</span>
            <span className="font-mono text-cyan-400">
              {isBangla
                ? `${toBengaliDigits(draftParams.startYear)} - ${toBengaliDigits(draftParams.endYear)}`
                : `${draftParams.startYear} - ${draftParams.endYear}`}
            </span>
          </label>
          <div className="grid grid-cols-2 gap-2">
            <div>
              <span className="text-[10px] text-slate-500 block mb-0.5">{isBangla ? "শুরু" : "Start"}</span>
              <input
                type="number"
                min={1980}
                max={draftParams.endYear - 3}
                value={draftParams.startYear}
                onChange={(e) =>
                  setDraftParams({ ...draftParams, startYear: parseInt(e.target.value) || 1980 })
                }
                className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1 text-xs text-slate-200 focus:outline-none focus:border-cyan-500 font-mono"
              />
            </div>
            <div>
              <span className="text-[10px] text-slate-500 block mb-0.5">{isBangla ? "শেষ" : "End"}</span>
              <input
                type="number"
                min={draftParams.startYear + 3}
                max={2024}
                value={draftParams.endYear}
                onChange={(e) =>
                  setDraftParams({ ...draftParams, endYear: parseInt(e.target.value) || 2024 })
                }
                className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1 text-xs text-slate-200 focus:outline-none focus:border-cyan-500 font-mono"
              />
            </div>
          </div>
        </div>

        {/* Submit Commit Action */}
        <button
          type="submit"
          disabled={isLoading || isSpatialIncompatible}
          className={`w-full py-2.5 px-4 rounded-lg font-medium text-xs flex items-center justify-center space-x-2 transition-all ${
            isLoading || isSpatialIncompatible
              ? "bg-slate-800 text-slate-500 cursor-not-allowed"
              : hasDraftChanges
              ? "bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold shadow-lg shadow-cyan-500/25"
              : "bg-slate-800 hover:bg-slate-700 text-slate-200"
          }`}
        >
          {isLoading ? (
            <>
              <div className="w-3.5 h-3.5 border-2 border-slate-400 border-t-transparent rounded-full animate-spin" />
              <span>{isBangla ? "গণনা চলছে..." : "Computing Evidence..."}</span>
            </>
          ) : (
            <>
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>{isBangla ? "বিশ্লেষণ চালান" : "Run Investigation"}</span>
            </>
          )}
        </button>
      </form>
    </aside>
  );
}
