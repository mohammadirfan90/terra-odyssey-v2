"use client";

import React, { useState } from "react";
import { X, ExternalLink, Download, Check, Copy, ShieldCheck, Database } from "lucide-react";

interface ProvenanceDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  result: any;
  isBangla?: boolean;
}

export default function ProvenanceDrawer({
  isOpen,
  onClose,
  result,
  isBangla = false,
}: ProvenanceDrawerProps) {
  const [copiedHash, setCopiedHash] = useState(false);
  const closeButtonRef = React.useRef<HTMLButtonElement>(null);

  React.useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    closeButtonRef.current?.focus();

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen, onClose]);

  if (!isOpen || !result) return null;

  const { identity, provenance, reproducibility, theil_sen, mann_kendall } = result;

  const handleCopyHash = () => {
    navigator.clipboard.writeText(identity.result_id);
    setCopiedHash(true);
    setTimeout(() => setCopiedHash(false), 2000);
  };

  return (
    <div
      className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex justify-end transition-opacity"
      role="dialog"
      aria-modal="true"
      aria-labelledby="provenance-title"
      onClick={(e) => {
        if (e.target === e.currentTarget) {
          onClose();
        }
      }}
    >
      <div className="w-full max-w-xl bg-slate-900 border-l border-slate-800 h-full flex flex-col p-6 overflow-y-auto shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center space-x-2">
            <Database className="w-4 h-4 text-cyan-400" />
            <h3 id="provenance-title" className="text-sm font-semibold tracking-wider uppercase text-slate-100">
              {isBangla ? "উৎস সূত্র ও অডিট ট্রেইল" : "Provenance & Scientific Audit"}
            </h3>
          </div>
          <button
            ref={closeButtonRef}
            onClick={onClose}
            aria-label={isBangla ? "বন্ধ করুন" : "Close drawer"}
            className="p-1 rounded-md text-slate-400 hover:text-slate-100 hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="space-y-6 pt-5 text-xs text-slate-300">
          {/* Result ID Block */}
          <div>
            <label className="text-[11px] font-semibold text-slate-400 block mb-1">
              {isBangla ? "অপরিবর্তনীয় রেজাল্ট হ্যাশ (SHA-256)" : "Immutable Result Hash (SHA-256)"}
            </label>
            <div className="flex items-center space-x-2 bg-slate-950 p-2.5 rounded-lg border border-slate-800 font-mono text-[11px] text-cyan-300 break-all">
              <span className="flex-1">{identity.result_id}</span>
              <button
                onClick={handleCopyHash}
                className="p-1.5 hover:bg-slate-800 rounded text-slate-400 hover:text-slate-200 transition-colors flex-shrink-0"
                title="Copy Result ID"
              >
                {copiedHash ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              </button>
            </div>
            <p className="text-[10px] text-slate-500 mt-1">
              {isBangla
                ? "পরামিতি, আঞ্চলিক সীমানা, বা কোড পরিবর্তনের সাথে সাথে এই হ্যাশ স্বয়ংক্রিয়ভাবে পরিবর্তিত হবে।"
                : "Cryptographically binds all input queries, observation checksums, and analysis policies."}
            </p>
          </div>

          {/* Dataset Source Collection Details */}
          <div className="bg-slate-950/70 p-4 rounded-lg border border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-slate-400 font-medium">{isBangla ? "উৎস কালেকশন:" : "Source Collection:"}</span>
              <span className="font-mono text-cyan-400">{provenance.collection_id}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-400 font-medium">{isBangla ? "সংস্করণ:" : "Version:"}</span>
              <span className="font-mono text-slate-200">{provenance.version}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-400 font-medium">{isBangla ? "অ্যাক্সেস মোড:" : "Access Mode:"}</span>
              <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 font-mono">
                {provenance.access_mode.toUpperCase()} (OFFLINE=1)
              </span>
            </div>
            {provenance.doi && (
              <div className="flex items-center justify-between">
                <span className="text-slate-400 font-medium">DOI:</span>
                <span className="font-mono text-slate-200">{provenance.doi}</span>
              </div>
            )}
            <div>
              <span className="text-slate-400 font-medium block mb-1">{isBangla ? "বৈজ্ঞানিক উদ্ধৃতি:" : "Scientific Citation:"}</span>
              <p className="text-[11px] text-slate-300 leading-relaxed italic bg-slate-900/60 p-2.5 rounded border border-slate-800">
                {provenance.citation}
              </p>
            </div>
          </div>

          {/* Method Reproducibility Manifest */}
          <div className="bg-slate-950/70 p-4 rounded-lg border border-slate-800 space-y-2">
            <span className="font-semibold text-slate-200 block mb-1">
              {isBangla ? "পুনরুৎপাদনযোগ্যতা ও অ্যালগরিদম সেটিংস" : "Reproducibility & Algorithm Settings"}
            </span>
            <div className="grid grid-cols-2 gap-2 text-[11px] font-mono">
              <div>
                <span className="text-slate-500">Code Revision:</span>
                <p className="text-slate-300">{reproducibility.code_revision}</p>
              </div>
              <div>
                <span className="text-slate-500">Policy ID:</span>
                <p className="text-slate-300">{reproducibility.policy_id}</p>
              </div>
              <div>
                <span className="text-slate-500">Bootstrap Replicates:</span>
                <p className="text-slate-300">{reproducibility.bootstrap_replicates}</p>
              </div>
              <div>
                <span className="text-slate-500">Bootstrap Seed:</span>
                <p className="text-slate-300">{reproducibility.bootstrap_seed}</p>
              </div>
            </div>
          </div>

          {/* Raw JSON Inspection */}
          <div>
            <label className="text-[11px] font-semibold text-slate-400 block mb-1">
              {isBangla ? "সম্পূর্ণ JSON ফলাফল ও পয়েন্টার" : "Immutable Result JSON Specification"}
            </label>
            <pre className="bg-slate-950 p-3 rounded-lg border border-slate-800 text-[10px] text-slate-300 font-mono max-h-48 overflow-y-auto">
              {JSON.stringify(result, null, 2)}
            </pre>
          </div>

          {/* Export Actions */}
          <div className="pt-2 flex space-x-3">
            <a
              href={`/api/results/${identity.result_id}/export?format=json`}
              download
              className="flex-1 py-2 px-3 bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold rounded-lg text-xs flex items-center justify-center space-x-2 transition-colors"
            >
              <Download className="w-3.5 h-3.5" />
              <span>{isBangla ? "সম্পূর্ণ অডিট প্যাকেজ (JSON)" : "Export JSON Bundle"}</span>
            </a>
            <a
              href={`/api/results/${identity.result_id}/export?format=csv`}
              download
              className="py-2 px-4 bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium rounded-lg text-xs flex items-center justify-center space-x-2 transition-colors"
            >
              <Download className="w-3.5 h-3.5" />
              <span>CSV</span>
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
