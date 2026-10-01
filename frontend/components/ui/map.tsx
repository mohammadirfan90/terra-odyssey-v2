"use client";

import React, { useEffect, useRef, useState } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { Globe, ZoomIn, ZoomOut, RotateCcw, Crosshair } from "lucide-react";

interface MapProps {
  selectedRegionId?: string;
  onSelectRegion: (regionId: string) => void;
  className?: string;
  isBangla?: boolean;
}

export default function Scientific2DMap({
  selectedRegionId,
  onSelectRegion,
  className = "",
  isBangla = false,
}: MapProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const [mapLoaded, setMapLoaded] = useState(false);
  const [hoveredCountry, setHoveredCountry] = useState<{ name: string; id: string } | null>(null);
  const [cursorCoords, setCursorCoords] = useState<{ lat: number; lon: number } | null>(null);
  const hoveredFeatureIdRef = useRef<string | number | null>(null);
  const onSelectRegionRef = useRef(onSelectRegion);
  useEffect(() => {
    onSelectRegionRef.current = onSelectRegion;
  }, [onSelectRegion]);
  const geojsonCacheRef = useRef<any>(null);

  useEffect(() => {
    if (!mapContainer.current || mapRef.current) return;

    // Initialize 2D Flat MapLibre map (Strictly pitch 0, no 3D globe)
    const map = new maplibregl.Map({
      container: mapContainer.current,
      style: "/offline/style.json",
      center: [20, 20],
      zoom: 1.6,
      minZoom: 1,
      maxZoom: 9,
      pitch: 0,
      maxPitch: 0,
      dragRotate: false,
      touchPitch: false,
      attributionControl: false,
    });

    map.on("load", () => {
      setMapLoaded(true);

      // Selected region overlay source & layers
      if (!map.getSource("selected-region-source")) {
        map.addSource("selected-region-source", {
          type: "geojson",
          data: {
            type: "FeatureCollection",
            features: [],
          },
        });

        // Glowing cyan highlight for selected country
        map.addLayer({
          id: "selected-region-fill",
          type: "fill",
          source: "selected-region-source",
          paint: {
            "fill-color": "#06b6d4",
            "fill-opacity": 0.35,
          },
        });

        map.addLayer({
          id: "selected-region-border-glow",
          type: "line",
          source: "selected-region-source",
          paint: {
            "line-color": "#0891b2",
            "line-width": 4.5,
            "line-opacity": 0.6,
          },
        });

        map.addLayer({
          id: "selected-region-border",
          type: "line",
          source: "selected-region-source",
          paint: {
            "line-color": "#22d3ee",
            "line-width": 2.5,
          },
        });
      }

      // Feature hover state
      map.on("mousemove", "regions-fill", (e) => {
        if (e.features && e.features.length > 0) {
          const feat = e.features[0];
          const name = feat.properties?.name || feat.properties?.ADMIN || "Region";
          const id = feat.properties?.id || feat.properties?.ISO3166_1_Alpha_3 || "";

          setHoveredCountry({ name, id });

          if (feat.id !== undefined) {
            if (hoveredFeatureIdRef.current !== null) {
              map.setFeatureState(
                { source: "offline-regions", id: hoveredFeatureIdRef.current },
                { hover: false }
              );
            }
            hoveredFeatureIdRef.current = feat.id;
            map.setFeatureState(
              { source: "offline-regions", id: feat.id },
              { hover: true }
            );
          }
        }
      });

      map.on("mouseleave", "regions-fill", () => {
        setHoveredCountry(null);
        if (hoveredFeatureIdRef.current !== null) {
          map.setFeatureState(
            { source: "offline-regions", id: hoveredFeatureIdRef.current },
            { hover: false }
          );
          hoveredFeatureIdRef.current = null;
        }
      });

      // Cursor coordinates tracker
      map.on("mousemove", (e) => {
        setCursorCoords({
          lat: parseFloat(e.lngLat.lat.toFixed(2)),
          lon: parseFloat(e.lngLat.lng.toFixed(2)),
        });
      });

      // Click on any country in the world
      map.on("click", "regions-fill", (e) => {
        if (e.features && e.features.length > 0) {
          const props = e.features[0].properties;
          const regId = props?.id || props?.ISO3166_1_Alpha_3 || props?.ISO_A3;
          if (regId && onSelectRegionRef.current) {
            onSelectRegionRef.current(regId);
          }
        }
      });

      // Cursor styling
      map.on("mouseenter", "regions-fill", () => {
        map.getCanvas().style.cursor = "pointer";
      });
      map.on("mouseleave", "regions-fill", () => {
        map.getCanvas().style.cursor = "";
      });
    });

    mapRef.current = map;

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // Update selected region highlight and camera flyTo
  useEffect(() => {
    if (!mapRef.current || !mapLoaded || !selectedRegionId) return;
    const map = mapRef.current;

    const loadGeojson = async () => {
      if (geojsonCacheRef.current) {
        return geojsonCacheRef.current;
      }
      const res = await fetch("/offline/geojson/countries.json");
      const data = await res.json();
      geojsonCacheRef.current = data;
      return data;
    };

    loadGeojson()
      .then((geojson) => {
        const matchingFeature = geojson.features.find(
          (f: any) =>
            f.properties?.id === selectedRegionId ||
            f.properties?.ISO3166_1_Alpha_3 === selectedRegionId ||
            f.properties?.ISO_A3 === selectedRegionId
        );

        const source = map.getSource("selected-region-source") as maplibregl.GeoJSONSource;
        if (source) {
          source.setData({
            type: "FeatureCollection",
            features: matchingFeature ? [matchingFeature] : [],
          });
        }

        // Fly to region bounds
        if (matchingFeature && matchingFeature.geometry) {
          const coords = matchingFeature.geometry.coordinates;
          const bounds = new maplibregl.LngLatBounds();

          const addPoints = (c: any) => {
            if (Array.isArray(c)) {
              if (c.length === 2 && typeof c[0] === "number" && typeof c[1] === "number") {
                bounds.extend([c[0], c[1]]);
              } else {
                c.forEach(addPoints);
              }
            }
          };

          addPoints(coords);

          if (!bounds.isEmpty()) {
            map.fitBounds(bounds, {
              padding: 60,
              maxZoom: 4.5,
              duration: 1200,
            });
          }
        }
      })
      .catch((err) => console.error("Error updating selected region boundary:", err));
  }, [selectedRegionId, mapLoaded]);

  const handleZoomIn = () => mapRef.current?.zoomIn();
  const handleZoomOut = () => mapRef.current?.zoomOut();
  const handleResetView = () => {
    mapRef.current?.flyTo({ center: [20, 20], zoom: 1.6, duration: 1000 });
  };

  return (
    <div className={`relative w-full h-full min-h-[420px] overflow-hidden rounded-xl border border-slate-800 bg-slate-950 shadow-2xl flex flex-col ${className}`}>
      <div ref={mapContainer} className="w-full h-full flex-1" />

      {/* Floating Hover Country Pill */}
      {hoveredCountry && (
        <div className="absolute top-4 left-4 z-10 bg-slate-900/90 backdrop-blur border border-cyan-500/50 rounded-lg px-3 py-1.5 shadow-xl text-xs text-slate-100 flex items-center space-x-2 animate-fadeIn pointer-events-none">
          <Globe className="w-3.5 h-3.5 text-cyan-400" />
          <span className="font-semibold text-cyan-300">{hoveredCountry.name}</span>
          <span className="font-mono text-[10px] bg-slate-800 px-1.5 py-0.5 rounded text-slate-400">
            {hoveredCountry.id}
          </span>
          <span className="text-[10px] text-slate-500 italic pl-1">
            {isBangla ? "(ক্লিক করে নির্বাচন করুন)" : "(Click to investigate)"}
          </span>
        </div>
      )}

      {/* Floating Map Controls */}
      <div className="absolute top-4 right-4 z-10 flex flex-col space-y-1.5">
        <button
          onClick={handleZoomIn}
          className="p-2 bg-slate-900/85 hover:bg-slate-800 text-slate-200 border border-slate-700/60 rounded-lg shadow-lg backdrop-blur transition-colors"
          title="Zoom In"
        >
          <ZoomIn className="w-4 h-4" />
        </button>
        <button
          onClick={handleZoomOut}
          className="p-2 bg-slate-900/85 hover:bg-slate-800 text-slate-200 border border-slate-700/60 rounded-lg shadow-lg backdrop-blur transition-colors"
          title="Zoom Out"
        >
          <ZoomOut className="w-4 h-4" />
        </button>
        <button
          onClick={handleResetView}
          className="p-2 bg-slate-900/85 hover:bg-slate-800 text-slate-200 border border-slate-700/60 rounded-lg shadow-lg backdrop-blur transition-colors"
          title="Reset Global View"
        >
          <RotateCcw className="w-4 h-4" />
        </button>
      </div>

      {/* Bottom Bar: Mode Indicator & Coordinates */}
      <div className="absolute bottom-3 left-3 right-3 z-10 flex items-center justify-between pointer-events-none">
        <div className="bg-slate-900/90 backdrop-blur border border-slate-700/70 rounded-lg px-3 py-1.5 text-xs text-slate-300 flex items-center space-x-2.5 shadow-lg">
          <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-pulse" />
          <span className="font-mono font-medium text-cyan-300">
            {isBangla ? "দ্বিমাত্রিক সমতল মানচিত্র (পিচ ০°)" : "2D Flat Cartography (Pitch 0°)"}
          </span>
          <span className="text-[11px] text-slate-500">|</span>
          <span className="text-[11px] text-slate-400">
            {isBangla ? "২৬১ টি বৈশ্বিক অঞ্চল ও দেশ" : "261 Global Regions & Ocean Basins"}
          </span>
        </div>

        {cursorCoords && (
          <div className="bg-slate-900/90 backdrop-blur border border-slate-700/70 rounded-lg px-2.5 py-1 text-[11px] font-mono text-slate-400 flex items-center space-x-1.5 shadow-lg">
            <Crosshair className="w-3 h-3 text-cyan-500" />
            <span>
              {cursorCoords.lat > 0 ? `${cursorCoords.lat}°N` : `${Math.abs(cursorCoords.lat)}°S`},{" "}
              {cursorCoords.lon > 0 ? `${cursorCoords.lon}°E` : `${Math.abs(cursorCoords.lon)}°W`}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
