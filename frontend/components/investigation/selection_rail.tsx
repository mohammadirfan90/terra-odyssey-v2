"use client";

import React, { useState } from "react";
import { Search, Play, Filter, Globe, Waves, AlertCircle, CheckCircle2, Sparkles } from "lucide-react";
import { toBengaliDigits } from "../../lib/formatters";

export interface SelectionParams {
  regionId: string;
  parameterId: string;
  startYear: number;
  endYear: number;
}

// Registry of verified offline cached datasets per parameter
export const PARAM_REGION_CACHE: Record<string, string[]> = {
  air_temperature_2m: ["IND", "KEN", "BRA", "DEU", "ZMB", "MOZ", "BGD", "USA", "MDV", "BAY_OF_BENGAL"],
  land_surface_temperature_day: ["KEN", "BRA", "DEU", "BGD", "USA", "MDV"],
  land_surface_temperature_night: ["KEN", "BRA", "DEU", "BGD", "USA", "MDV"],
  point_air_temperature: ["KEN", "BRA", "DEU", "BGD", "USA", "MDV"],
  sea_surface_temperature: ["BAY_OF_BENGAL", "NORTH_ATLANTIC"],
  precipitation_total: [],
  surface_temperature_anomaly: [],
};

export const OFFLINE_VERIFIED_REGIONS = [
  "BGD", "USA", "IND", "KEN", "BRA", "DEU", "ZMB", "MOZ", "MDV", "BAY_OF_BENGAL", "NORTH_ATLANTIC"
];

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
  const [regionFilterMode, setRegionFilterMode] = useState<"verified" | "all">("verified");

  // Synchronize draft state when active query changes (e.g. via map click)
  React.useEffect(() => {
    setDraftParams(currentParams);
  }, [currentParams]);

  const selectedRegion = regions.find((r) => r.id === draftParams.regionId);
  const selectedParam = parameters.find((p) => p.id === draftParams.parameterId);

  // Filter regions based on search and verified toggle
  const filteredRegions = regions.filter((r) => {
    if (regionFilterMode === "verified" && !OFFLINE_VERIFIED_REGIONS.includes(r.id)) {
      return false;
    }
    const q = searchQuery.toLowerCase().trim();
    if (!q) return true;
    return (
      r.name_en.toLowerCase().includes(q) ||
      (r.name_bn && r.name_bn.includes(q)) ||
      r.id.toLowerCase().includes(q)
    );
  });

  const isOceanParam = selectedParam?.valid_spatial_support === "ocean";
  const isOceanRegion = selectedRegion?.has_ocean_support;
  const isSpatialIncompatible = isOceanParam && !isOceanRegion;

  // Offline cache availability check
  const supportedRegionsForParam = PARAM_REGION_CACHE[draftParams.parameterId] || [];
  const isCachedForSelection = supportedRegionsForParam.includes(draftParams.regionId);
  const availableParamsForRegion = parameters.filter((p) =>
    (PARAM_REGION_CACHE[p.id] || []).includes(draftParams.regionId)
  );

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
    <aside className="w-full lg:w-80 flex-shrink-0 flex flex-col space-y-4 bg-slate-900/95 border border-slate-800 rounded-xl p-4 backdrop-blur shadow-2xl">
      {/* Header with Title and Status */}
      <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
        <h2 className="text-xs font-bold tracking-wider uppercase text-cyan-400 flex items-center space-x-2">
          <Filter className="w-4 h-4 text-cyan-400" />
          <span>{isBangla ? "অনুসন্ধান পরামিতি" : "Investigation Query"}</span>
        </h2>
        {hasDraftChanges && (
          <span className="text-[10px] font-medium text-amber-300 bg-amber-500/10 px-2 py-0.5 rounded-full border border-amber-500/30 animate-pulse">
            {isBangla ? "ড্রাফট পরিবর্তিত" : "Draft Changed"}
          </span>
        )}
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col space-y-4">
        {/* Region Search & Filter Tabs */}
        <div>
          <div className="flex items-center justify-between mb-1.5">
            <label className="text-xs font-semibold text-slate-200">
              {isBangla ? "অঞ্চল বা দেশ নির্বাচন" : "Region or Ocean Basin"}
            </label>
            <span className="text-[10px] text-cyan-400 font-mono font-medium">
              {selectedRegion ? selectedRegion.id : draftParams.regionId}
            </span>
          </div>

          {/* Tab Filter: Verified Offline vs All Boundaries */}
          <div className="grid grid-cols-2 gap-1 p-1 bg-slate-950/80 rounded-lg border border-slate-800/80 mb-2 text-[11px]">
            <button
              type="button"
              onClick={() => setRegionFilterMode("verified")}
              className={`py-1 px-2 rounded-md font-medium transition-all flex items-center justify-center space-x-1 ${
                regionFilterMode === "verified"
                  ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <CheckCircle2 className="w-3 h-3 text-cyan-400" />
              <span>{isBangla ? "অফলাইন যাচাইকৃত" : "Verified Offline (10)"}</span>
            </button>
            <button
              type="button"
              onClick={() => setRegionFilterMode("all")}
              className={`py-1 px-2 rounded-md font-medium transition-all flex items-center justify-center space-x-1 ${
                regionFilterMode === "all"
                  ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <Globe className="w-3 h-3 text-slate-400" />
              <span>{isBangla ? "সকল অঞ্চল" : "All Regions (261)"}</span>
            </button>
          </div>

          {/* Search Input */}
          <div className="relative mb-2">
            <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder={isBangla ? "দেশ বা সমুদ্র খুঁজুন..." : "Search (e.g. Bangladesh, India, USA)..."}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-8 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition-colors"
            />
          </div>

          {/* Region Listbox */}
          <div className="max-h-44 overflow-y-auto space-y-1 p-1.5 border border-slate-800/80 rounded-lg bg-slate-950/70">
            {filteredRegions.length === 0 ? (
              <div className="text-center py-4 text-slate-500 text-xs">
                {isBangla ? "কোনো অঞ্চল পাওয়া যায়নি" : "No regions match your filter"}
              </div>
            ) : (
              filteredRegions.map((reg) => {
                const isSelected = draftParams.regionId === reg.id;
                const isOcean = reg.region_type === "ocean_basin";
                const isCachedForActiveParam = supportedRegionsForParam.includes(reg.id);

                return (
                  <button
                    type="button"
                    key={reg.id}
                    onClick={() => setDraftParams({ ...draftParams, regionId: reg.id })}
                    className={`w-full text-left px-2.5 py-1.5 rounded-md text-xs flex items-center justify-between transition-all ${
                      isSelected
                        ? "bg-cyan-500/20 text-cyan-200 font-semibold border border-cyan-500/40 shadow-sm"
                        : "text-slate-300 hover:bg-slate-800/70 hover:text-slate-100"
                    }`}
                  >
                    <div className="flex items-center space-x-2 truncate">
                      {isOcean ? (
                        <Waves className="w-3.5 h-3.5 text-sky-400 flex-shrink-0" />
                      ) : (
                        <Globe className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
                      )}
                      <span className="truncate">{isBangla ? reg.name_bn : reg.name_en}</span>
                    </div>

                    <div className="flex items-center space-x-1.5 ml-2 flex-shrink-0">
                      {isCachedForActiveParam && (
                        <span className="text-[9px] font-medium bg-emerald-500/20 text-emerald-300 px-1 py-0.2 rounded border border-emerald-500/30">
                          Ready
                        </span>
                      )}
                      <span className="text-[11px] font-mono text-slate-400 font-medium">{reg.id}</span>
                    </div>
                  </button>
                );
              })
            )}
          </div>
        </div>

        {/* Parameter Selector */}
        <div>
          <label className="block text-xs font-semibold text-slate-200 mb-1.5">
            {isBangla ? "ভৌত পরামিতি" : "Physical Parameter"}
          </label>
          <select
            value={draftParams.parameterId}
            onChange={(e) => setDraftParams({ ...draftParams, parameterId: e.target.value })}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-cyan-500 transition-colors"
          >
            {parameters.map((param) => {
              const isParamReadyForRegion = (PARAM_REGION_CACHE[param.id] || []).includes(draftParams.regionId);
              return (
                <option key={param.id} value={param.id}>
                  {isBangla ? param.name_bn : param.name_en} ({param.display_unit}) {isParamReadyForRegion ? "— ✓ Ready" : ""}
                </option>
              );
            })}
          </select>
          <p className="text-[11px] text-slate-400 mt-1.5 leading-relaxed bg-slate-950/60 p-2 rounded-lg border border-slate-800/60">
            {isBangla ? selectedParam?.definition_bn : selectedParam?.definition_en}
          </p>
        </div>

        {/* Offline Cache Notice & Auto-Fix Switcher */}
        {!isCachedForSelection && (
          <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-2.5 text-xs text-amber-300">
            <div className="flex items-start space-x-2">
              <AlertCircle className="w-4 h-4 text-amber-400 mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <p className="font-semibold text-amber-300">
                  {isBangla ? "অফলাইন ডেটা অনুপলব্ধ" : "Dataset Not Cached Offline"}
                </p>
                <p className="text-[11px] text-amber-200/80 mt-0.5 leading-tight">
                  {selectedParam?.name_en} is not in the local offline cache for{" "}
                  <strong>{selectedRegion?.name_en || draftParams.regionId}</strong>.
                </p>
                {availableParamsForRegion.length > 0 && (
                  <div className="mt-2 pt-2 border-t border-amber-500/20">
                    <span className="text-[10px] text-amber-300 block mb-1">
                      {isBangla ? "উপলব্ধ পরামিতি:" : "Recommended available for this region:"}
                    </span>
                    <button
                      type="button"
                      onClick={() =>
                        setDraftParams({ ...draftParams, parameterId: availableParamsForRegion[0].id })
                      }
                      className="w-full text-left text-[11px] font-semibold bg-amber-500/20 hover:bg-amber-500/30 border border-amber-500/40 text-amber-100 px-2 py-1 rounded transition-colors flex items-center justify-between"
                    >
                      <span className="truncate">Switch to {availableParamsForRegion[0].name_en}</span>
                      <Sparkles className="w-3 h-3 text-amber-300 ml-1 flex-shrink-0" />
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Spatial Incompatibility Warning */}
        {isSpatialIncompatible && (
          <div className="bg-rose-500/10 border border-rose-500/30 rounded-lg p-2.5 text-xs text-rose-300 flex items-start space-x-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5 text-rose-400" />
            <div>
              <p className="font-semibold">{isBangla ? "অঞ্চল অসঙ্গতি" : "Spatial Boundary Mismatch"}</p>
              <p className="text-[11px] text-rose-200/80 mt-0.5">
                {isBangla
                  ? "সমুদ্রপৃষ্ঠের তাপমাত্রা (এসএসটি) মূল্যায়নের জন্য একটি সমুদ্র অঞ্চল (যেমন বঙ্গোপসাগর) নির্বাচন করুন।"
                  : "Sea surface temperature requires an ocean basin. Choose an ocean basin like Bay of Bengal."}
              </p>
            </div>
          </div>
        )}

        {/* Analysis Window */}
        <div>
          <label className="block text-xs font-semibold text-slate-200 mb-1.5 flex justify-between">
            <span>{isBangla ? "বিশ্লেষণ সময়কাল" : "Observation Window"}</span>
            <span className="font-mono text-cyan-400 font-medium">
              {isBangla
                ? `${toBengaliDigits(draftParams.startYear)} - ${toBengaliDigits(draftParams.endYear)}`
                : `${draftParams.startYear} - ${draftParams.endYear}`}
            </span>
          </label>
          <div className="grid grid-cols-2 gap-2">
            <div>
              <span className="text-[10px] text-slate-400 block mb-0.5 font-medium">
                {isBangla ? "শুরু" : "Start"}
              </span>
              <input
                type="number"
                min={1980}
                max={draftParams.endYear - 3}
                value={draftParams.startYear}
                onChange={(e) =>
                  setDraftParams({ ...draftParams, startYear: parseInt(e.target.value) || 1980 })
                }
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1 text-xs text-slate-200 focus:outline-none focus:border-cyan-500 font-mono"
              />
            </div>
            <div>
              <span className="text-[10px] text-slate-400 block mb-0.5 font-medium">
                {isBangla ? "শেষ" : "End"}
              </span>
              <input
                type="number"
                min={draftParams.startYear + 3}
                max={2024}
                value={draftParams.endYear}
                onChange={(e) =>
                  setDraftParams({ ...draftParams, endYear: parseInt(e.target.value) || 2024 })
                }
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1 text-xs text-slate-200 focus:outline-none focus:border-cyan-500 font-mono"
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
              ? "bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold shadow-lg shadow-cyan-500/25"
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
