import React from "react";
import { BookOpen, BarChart3, FileCode, CheckCircle2 } from "lucide-react";

export default function Navbar({ activeTab, setActiveTab, meta }) {
  return (
    <header className="masthead-border bg-[#faf8f5] sticky top-0 z-30 shadow-2xs">
      {/* Top micro metadata header */}
      <div className="border-b border-[#e8e3d5] bg-[#f4efe6]">
        <div className="site-container py-2 flex gap-x-6 gap-y-1 flex-wrap items-center justify-between text-[11px] text-[#5e5a52] font-mono">
          <div className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-[#8f2626]"></span>
            <span className="font-semibold uppercase tracking-wider text-[#15263a]">
              {meta?.project_identity || "Temporal Coordination in Social Media"}
            </span>
            <span className="text-[#a8a396]">/</span>
            <span className="text-[#757065]">Benchmark Validity Study</span>
          </div>

          <div className="flex items-center gap-4">
            <span className="inline-flex items-center gap-1 text-[#23527c] font-medium">
              <CheckCircle2 size={12} className="text-[#23527c]" />
              <span>103-event archive &middot; official release: 100</span>
            </span>
            <span className="hidden xl:inline text-[#dcd7ca]">&bull;</span>
            <span className="hidden xl:inline text-[#757065]">5-Fold Stratified Out-of-Fold CV</span>
          </div>
        </div>
      </div>

      {/* Sleek, Compact Masthead Bar */}
      <div className="site-container py-4 flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div className="flex items-baseline gap-3 flex-wrap">
          <button
            type="button"
            onClick={() => setActiveTab("overview")}
            className="text-left group"
          >
            <span className="font-serif text-xl sm:text-2xl text-[#15263a] font-normal tracking-tight group-hover:text-[#23527c] transition-colors">
              Temporal Coordination in Social Media
            </span>
          </button>
          <span className="text-xs text-[#5e5a52] hidden xl:inline pl-3 border-l border-[#dcd7ca] font-sans">
            What Does LEN-Small Measure?
          </span>
        </div>

        {/* Publication Nav Tabs */}
        <nav className="flex items-center gap-1 bg-[#ede8dc] p-1 border border-[#d8d3c5] max-w-full overflow-x-auto text-xs font-mono self-start md:self-auto shrink-0">
          <button
            type="button"
            onClick={() => setActiveTab("overview")}
            className={`flex items-center gap-1.5 px-3 py-1.5 whitespace-nowrap transition-colors ${
              activeTab === "overview"
                ? "bg-[#15263a] text-white font-medium shadow-xs"
                : "text-[#3c3a37] hover:text-[#15263a] hover:bg-[#e4dfd2]"
            }`}
          >
            <BookOpen size={13} className="shrink-0" />
            <span>Overview</span>
            <span className="hidden sm:inline">Research</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("explorer")}
            className={`flex items-center gap-1.5 px-3 py-1.5 whitespace-nowrap transition-colors ${
              activeTab === "explorer"
                ? "bg-[#15263a] text-white font-medium shadow-xs"
                : "text-[#3c3a37] hover:text-[#15263a] hover:bg-[#e4dfd2]"
            }`}
          >
            <BarChart3 size={13} className="shrink-0" />
            <span>Results</span>
            <span className="hidden sm:inline">Explorer</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("methods")}
            className={`flex items-center gap-1.5 px-3 py-1.5 whitespace-nowrap transition-colors ${
              activeTab === "methods"
                ? "bg-[#15263a] text-white font-medium shadow-xs"
                : "text-[#3c3a37] hover:text-[#15263a] hover:bg-[#e4dfd2]"
            }`}
          >
            <FileCode size={13} className="shrink-0" />
            <span>Methods</span>
            <span className="hidden sm:inline">&amp; Reproducibility</span>
          </button>
        </nav>
      </div>
    </header>
  );
}
