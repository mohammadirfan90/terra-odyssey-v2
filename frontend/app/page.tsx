"use client";

import React, { useEffect, useState } from "react";
import {
  Compass,
  Languages,
  Shield,
  Radio,
  RefreshCw,
  ExternalLink,
} from "lucide-react";
import Scientific2DMap from "../components/ui/map";
import SelectionRail, { SelectionParams } from "../components/investigation/selection_rail";
import ResultPanel from "../components/investigation/result_panel";
import ChartArea from "../components/investigation/chart_area";
import ProvenanceDrawer from "../components/investigation/provenance_drawer";

export default function EarthSystemTrendDetectiveApp() {
  const [isBangla, setIsBangla] = useState(false);
  const [regions, setRegions] = useState<any[]>([]);
  const [parameters, setParameters] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [committedParams, setCommittedParams] = useState<SelectionParams>({
    regionId: "BGD",
    parameterId: "air_temperature_2m",
    startYear: 1980,
    endYear: 2024,
  });

  const [currentResult, setCurrentResult] = useState<any | null>(null);
  const [isProvenanceOpen, setIsProvenanceOpen] = useState(false);

  // Sync document language attribute
  useEffect(() => {
    if (typeof document !== "undefined") {
      document.documentElement.lang = isBangla ? "bn" : "en";
    }
  }, [isBangla]);

  // Initial data loading (regions & parameters)
  useEffect(() => {
    async function initData() {
      try {
        const [regRes, paramRes] = await Promise.all([
          fetch("/api/regions"),
          fetch("/api/parameters"),
        ]);

        if (regRes.ok && paramRes.ok) {
          const regData = await regRes.json();
          const paramData = await paramRes.json();
          setRegions(regData);
          setParameters(paramData);
        }
      } catch (err) {
        console.error("Failed to load initial metadata:", err);
        setError("Failed to load metadata registry from local scientific backend.");
      }
    }
    initData();
  }, []);

  // Fetch trend investigation when committedParams change
  useEffect(() => {
    const controller = new AbortController();

    async function loadTrend() {
      setIsLoading(true);
      setError(null);
      setCurrentResult(null);
      try {
        const url = `/api/trend?region_id=${committedParams.regionId}&parameter_id=${committedParams.parameterId}&start_year=${committedParams.startYear}&end_year=${committedParams.endYear}`;
        const res = await fetch(url, { signal: controller.signal });
        if (res.ok) {
          const data = await res.json();
          setCurrentResult(data);
        } else {
          const errData = await res.json();
          setCurrentResult(null);
          setError(errData.detail || "Investigation failed to compute.");
        }
      } catch (err: any) {
        if (err.name === "AbortError") {
          return; // Ignore aborted requests
        }
        console.error("Error executing trend investigation:", err);
        setCurrentResult(null);
        setError("Network error connecting to local FastAPI compute kernel.");
      } finally {
        if (!controller.signal.aborted) {
          setIsLoading(false);
        }
      }
    }

    loadTrend();

    return () => {
      controller.abort();
    };
  }, [committedParams]);

  const handleMapSelectRegion = React.useCallback((regionId: string) => {
    setCommittedParams((prev) => ({
      ...prev,
      regionId,
    }));
  }, []);

  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100 selection:bg-cyan-500/20">
      {/* Top Application Header */}
      <header className="h-14 border-b border-slate-800 bg-slate-900/90 backdrop-blur px-4 lg:px-6 flex items-center justify-between z-20">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-cyan-600 to-emerald-500 flex items-center justify-center shadow-lg shadow-cyan-500/20">
            <Compass className="w-5 h-5 text-slate-950" />
          </div>
          <div>
            <h1 className="text-sm font-bold tracking-tight text-slate-100 flex items-center space-x-2">
              <span>{isBangla ? "আর্থ সিস্টেম ট্রেন্ড ডিটেকটিভ" : "Earth System Trend Detective"}</span>
              <span className="text-[11px] font-sans font-semibold px-2.5 py-0.5 rounded-full bg-cyan-950/70 text-cyan-300 border border-cyan-500/40 shadow-sm">
                NASA Research Edition
              </span>
            </h1>
            <p className="text-[10px] text-slate-400">
              {isBangla
                ? "অফলাইন-ফার্স্ট বৈজ্ঞানিক জলবায়ু ও পরিবেশ পরিবর্তন অনুসন্ধান প্ল্যাটফর্ম"
                : "Offline-first scientific investigation platform for Earth observations & trends"}
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          {/* OFFLINE=1 Guard Indicator */}
          <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-[11px] text-emerald-400 font-mono">
            <Shield className="w-3.5 h-3.5 text-emerald-400" />
            <span className="font-semibold">OFFLINE=1</span>
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse ml-1" />
          </div>

          {/* Bilingual English / Bangla Switch */}
          <button
            onClick={() => setIsBangla(!isBangla)}
            className="flex items-center space-x-1.5 px-3 py-1 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-lg text-xs font-medium text-slate-200 transition-colors"
          >
            <Languages className="w-3.5 h-3.5 text-cyan-400" />
            <span>{isBangla ? "English" : "বাংলা (BN)"}</span>
          </button>
        </div>
      </header>

      {/* Main Workspace Layout (Figure 1 Layout Specification) */}
      <main className="flex-1 p-4 lg:p-6 flex flex-col space-y-4 max-w-[1800px] w-full mx-auto">
        {/* Tri-Panel Upper Section: Left Query Rail, Center 2D Map, Right Result Summary */}
        <div className="flex flex-col lg:flex-row gap-4 flex-1">
          {/* 1. Left Selection Rail */}
          <SelectionRail
            regions={regions}
            parameters={parameters}
            currentParams={committedParams}
            onCommit={(newParams) => setCommittedParams(newParams)}
            isLoading={isLoading}
            isBangla={isBangla}
          />

          {/* 2. Center 2D Flat Map */}
          <div className="flex-1 min-h-[380px] flex flex-col">
            <Scientific2DMap
              selectedRegionId={committedParams.regionId}
              parameterId={committedParams.parameterId}
              onSelectRegion={handleMapSelectRegion}
              isBangla={isBangla}
              className="flex-1 shadow-xl"
            />
          </div>

          {/* 3. Right Result Summary Panel */}
          <ResultPanel
            result={currentResult}
            error={error}
            currentParams={committedParams}
            onSwitchSelection={(params) =>
              setCommittedParams((prev) => ({
                ...prev,
                ...params,
              }))
            }
            onOpenProvenance={() => setIsProvenanceOpen(true)}
            isBangla={isBangla}
          />
        </div>

        {/* Bottom Section: Analytical Time-Series, Uncertainty Band, Comparison, and Data */}
        <ChartArea
          result={currentResult}
          allRegions={regions}
          onSelectSampleQuery={(params) => setCommittedParams(params)}
          isBangla={isBangla}
        />
      </main>

      {/* Provenance & Audit Drawer */}
      <ProvenanceDrawer
        isOpen={isProvenanceOpen}
        onClose={() => setIsProvenanceOpen(false)}
        result={currentResult}
        isBangla={isBangla}
      />
    </div>
  );
}
