import React, { useState, useMemo } from "react";
import { Search, Filter, ArrowUpDown } from "lucide-react";
import { f3 } from "../lib/fmt";

const CORE_IDS = [
  "S1_LogReg_M0", "S1_LogReg_M0q", "S1_LogReg_M2", "S1_LogReg_M3", "S1_LogReg_M4", "S1_HGBT_M4",
  "S2_K250_FF_combined", "S2_K250_FF_struct6", "S2_K250_FK_struct6", "S2_K250_KK_struct6", "S2_K250_KK_NK", "S2_K250_KK_combined",
];

// Readable row label from the internal row ID, e.g. S1_LogReg_M4d -> "LR · M4 + density",
// S2_K250_KK_NK -> "KK · N_K only"
const S2_SETS = { NK: "N_K only", struct7: "structure + density", struct6: "structure", NK_struct6: "N_K + structure", content: "content", combined: "N_K + structure + content" };
function rowLabel(id) {
  const p = id.split("_");
  if (p[0] === "S1") return `${p[1] === "LogReg" ? "LR" : p[1]} · ${p[2] === "M4d" ? "M4 + density" : p[2]}`;
  return `${p[2]} · ${S2_SETS[p.slice(3).join("_")] || p.slice(3).join(" ")}`;
}

export default function ResultsTable({ experiments }) {
  const [searchTerm, setSearchTerm] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("all");
  const [sortField, setSortField] = useState(null); // null keeps the study order
  const [sortAsc, setSortAsc] = useState(false);
  const [viewMode, setViewMode] = useState("core");

  const coreIds = useMemo(() => new Set(CORE_IDS), []);
  const categories = useMemo(
    () => [{ id: "all", label: "All" }, ...[...new Set((experiments || []).map((e) => e.category))].map((c) => ({ id: c, label: c }))],
    [experiments],
  );

  const filtered = useMemo(() => {
    const q = searchTerm.toLowerCase();
    return (experiments || []).filter((exp) => {
      if (viewMode === "core" && !searchTerm && !coreIds.has(exp.experiment_id)) return false;
      const matchCat = categoryFilter === "all" || exp.category === categoryFilter;
      const matchSearch = [exp.experiment_id, exp.feature_group, exp.model, exp.note].some((t) => t && t.toLowerCase().includes(q));
      return matchCat && matchSearch;
    });
  }, [experiments, categoryFilter, searchTerm, viewMode, coreIds]);

  const sorted = useMemo(() => {
    if (!sortField) return filtered;
    return [...filtered].sort((a, b) => {
      const valA = a[sortField] ?? -999;
      const valB = b[sortField] ?? -999;
      if (valA < valB) return sortAsc ? -1 : 1;
      if (valA > valB) return sortAsc ? 1 : -1;
      return 0;
    });
  }, [filtered, sortField, sortAsc]);

  const handleSort = (field) => {
    if (sortField === field) setSortAsc(!sortAsc);
    else {
      setSortField(field);
      setSortAsc(field === "log_loss");
    }
  };

  const SortHead = ({ field, children, className = "" }) => (
    <th className={`cursor-pointer ${className}`} onClick={() => handleSort(field)}>
      <div className="flex items-center gap-1.5">
        <span>{children}</span>
        <ArrowUpDown size={11} />
      </div>
    </th>
  );

  return (
    <div className="bg-[#faf8f5] border border-[#dcd7ca] p-5 sm:p-8 lg:p-10 shadow-none w-full">
      <div className="panel-head flex flex-col lg:flex-row lg:items-end justify-between gap-6">
        <div className="min-w-0">
          <span className="section-label">Numerical Results</span>
          <h3 className="text-xl font-serif font-medium text-[#15263a]">
            Out-of-Fold Results, Study 1 and Study 2
          </h3>
          <p className="head-desc">
            Study 1 brackets are 95% event-level bootstrap intervals of fixed out-of-fold predictions. Study 2 brackets are the minimum and maximum over 10 sampling seeds, not confidence intervals.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-1 border border-[#d8d3c5] bg-white p-1 text-xs font-mono self-start lg:self-end shrink-0 shadow-2xs">
          {[
            { id: "core", label: `Key Rows (${CORE_IDS.length})` },
            { id: "all", label: `All Rows (${experiments.length})` },
          ].map((m) => (
            <button
              key={m.id}
              type="button"
              onClick={() => setViewMode(m.id)}
              className={`px-3.5 py-2 transition-colors ${
                viewMode === m.id ? "bg-[#15263a] text-white font-medium shadow-xs" : "text-[#3c3a37] hover:bg-[#ede9df]"
              }`}
            >
              {m.label}
            </button>
          ))}
        </div>
      </div>

      <div className="flex flex-col xl:flex-row items-stretch xl:items-center justify-between gap-x-8 gap-y-4 mb-6 p-4 sm:px-5 bg-[#f4efe6] border border-[#e2dcd0]">
        <div className="flex flex-wrap items-center gap-2 text-xs font-mono">
          <span className="inline-flex items-center gap-1.5 mr-2 text-[11px] uppercase tracking-wider text-[#6b6862]">
            <Filter size={13} className="shrink-0" />
            <span>Category</span>
          </span>
          {categories.map((c) => (
            <button
              key={c.id}
              type="button"
              onClick={() => setCategoryFilter(c.id)}
              className={`px-3.5 py-1.5 border transition-colors ${
                categoryFilter === c.id
                  ? "bg-[#15263a] text-white border-[#15263a] font-medium shadow-2xs"
                  : "bg-white text-[#3c3a37] border-[#d8d3c5] hover:bg-[#ede9df]"
              }`}
            >
              {c.label}
            </button>
          ))}
        </div>

        <label className="relative block w-full xl:w-80 shrink-0">
          <span className="sr-only">Search results</span>
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#757065] pointer-events-none" />
          <input
            type="text"
            placeholder="Search models, features, notes..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-white border border-[#d8d3c5] pl-10 pr-4 py-2.5 text-sm text-[#15263a] placeholder:text-[#8a857a] focus:outline-none focus:border-[#15263a] shadow-2xs"
          />
        </label>
      </div>

      <div className="overflow-x-auto border border-[#dcd7ca] bg-white">
        <table className="ieee-table">
          <thead>
            <tr>
              <SortHead field="experiment_id">Model / Condition</SortHead>
              <th>Category</th>
              <th>Model</th>
              <SortHead field="balanced_accuracy">Bal. Acc [interval]</SortHead>
              <SortHead field="log_loss">Log Loss</SortHead>
              <SortHead field="roc_auc">ROC-AUC</SortHead>
              <SortHead field="n_events" className="text-center">N</SortHead>
            </tr>
          </thead>
          {sorted.map((exp) => {
            const isKey = exp.experiment_id === "S1_LogReg_M0" || exp.experiment_id === "S1_LogReg_M4" || exp.experiment_id === "S2_K250_KK_NK";
            const rowTone = isKey ? "bg-[#fbf8f0]" : "";
            return (
              <tbody key={exp.experiment_id}>
                <tr className={`${rowTone} [&>td]:border-b-0 [&>td]:pb-2`}>
                  <td className="font-mono text-xs font-semibold text-[#15263a]">
                    <div>{rowLabel(exp.experiment_id)}</div>
                    <div className="text-[11px] font-sans font-normal text-[#5e5a52]">{exp.feature_group}</div>
                  </td>
                  <td className="text-xs text-[#4a4740] font-sans whitespace-nowrap">{exp.category}</td>
                  <td className="font-mono text-xs text-[#15263a] whitespace-nowrap">{exp.model}</td>
                  <td className="font-mono text-xs whitespace-nowrap">
                    <span className="font-bold text-[#15263a]">{f3(exp.balanced_accuracy)}</span>
                    {exp.ba_ci_lower != null && (
                      <span className="text-[10.5px] text-[#757065] ml-1">
                        [{f3(exp.ba_ci_lower)}, {f3(exp.ba_ci_upper)}]
                      </span>
                    )}
                    <div className="text-[10px] text-[#8a857a]">{exp.interval_kind}</div>
                  </td>
                  <td className="font-mono text-xs text-[#333] whitespace-nowrap">{f3(exp.log_loss)}</td>
                  <td className="font-mono text-xs text-[#333] whitespace-nowrap">{f3(exp.roc_auc)}</td>
                  <td className="font-mono text-xs text-center text-[#15263a] font-semibold">{exp.n_events}</td>
                </tr>
                <tr className={rowTone}>
                  <td colSpan={7} className="pt-0 pb-4 text-[13px] font-sans text-[#4a4740] leading-relaxed">
                    {/* Sticky + viewport-capped so the note stays readable when the table scrolls horizontally */}
                    <div className="sticky left-4 max-w-[calc(100vw-6.5rem)]">
                      <span className="font-mono text-[10.5px] uppercase tracking-wider text-[#757065] mr-2">Note</span>
                      {exp.note}
                    </div>
                  </td>
                </tr>
              </tbody>
            );
          })}
          <tfoot>
            <tr>
              <td colSpan={7} className="text-xs text-[#6b6862] font-sans">
                {viewMode === "core"
                  ? `Showing ${sorted.length} key rows. Switch to "All Rows" to inspect all ${experiments.length}.`
                  : `Showing ${sorted.length} of ${experiments.length} rows: Study 1 feature levels (LR and HGBT) and Study 2 conditions at K = 250, 500 and 1000.`}
              </td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  );
}
