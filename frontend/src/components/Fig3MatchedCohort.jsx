import React from "react";
import FigureCaption from "./FigureCaption";
import { f2, f3 } from "../lib/fmt";

// Exploratory size matching: LR BA within matched cohorts, median and range over visiting orders
const LEVELS = [
  { id: "M0", label: "M0", sub: "counts" },
  { id: "M1", label: "M1", sub: "+ degree Gini" },
  { id: "M2", label: "M2", sub: "+ arrangement" },
  { id: "M3", label: "M3", sub: "counts + content" },
  { id: "M4", label: "M4", sub: "all features" },
];
const SCHEMES = [
  { id: "node_only", label: "Matched on log node count", color: "#8f2626", dx: -9 },
  { id: "node_edge", label: "Matched on log node + edge count", color: "#23527c", dx: 9 },
];

export default function Fig3MatchedCohort({ paper }) {
  const MT = paper.matching;

  const svgWidth = 640;
  const svgHeight = 360;
  const margin = { top: 28, right: 64, bottom: 60, left: 56 };
  const innerWidth = svgWidth - margin.left - margin.right;
  const innerHeight = svgHeight - margin.top - margin.bottom;
  const yMin = 0.35;
  const yMax = 0.95;
  const yScale = (v) => innerHeight - ((v - yMin) / (yMax - yMin)) * innerHeight;
  const gap = innerWidth / LEVELS.length;

  return (
    <div className="bg-[#faf8f5] border border-[#dcd7ca] p-5 sm:p-8 lg:p-10 shadow-none">
      <div className="panel-head">
        <span className="section-label">Figure 3 · Exploratory</span>
        <h3 className="text-xl font-serif font-medium text-[#15263a]">
          Size Matching Sensitivity
        </h3>
        <p className="head-desc">
          LR balanced accuracy within matched cohorts of {MT.node_only.n_pairs_range[0]}–{MT.node_only.n_pairs_range[1]} pairs, over {MT.node_only.n_order_seeds} matching orders.
        </p>
      </div>

      <div className="flex flex-wrap gap-x-6 gap-y-2 mb-4 text-xs font-mono text-[#3c3a37]">
        {SCHEMES.map((s) => (
          <span key={s.id} className="inline-flex items-center gap-2">
            <span className="inline-block w-3 h-3 rounded-full" style={{ background: s.color }}></span>
            {s.label}
          </span>
        ))}
      </div>

      <div className="chart-frame">
        <svg viewBox={`0 0 ${svgWidth} ${svgHeight}`} className="select-none overflow-visible" role="img"
          aria-label="Median and range of matched-cohort balanced accuracy by feature level for two matching schemes">
          <g transform={`translate(${margin.left}, ${margin.top})`}>
            <line x1={0} y1={0} x2={0} y2={innerHeight} stroke="#15263a" strokeWidth="1.5" />
            {[0.4, 0.5, 0.6, 0.7, 0.8, 0.9].map((v) => {
              const y = yScale(v);
              const isChance = v === 0.5;
              return (
                <g key={v}>
                  <line x1={0} y1={y} x2={innerWidth} y2={y} stroke={isChance ? "#8f2626" : "#e4dfd3"}
                    strokeDasharray={isChance ? "4,4" : "2,2"} strokeWidth={isChance ? 1.2 : 0.8} />
                  <text x={-12} y={y + 4} textAnchor="end" fontSize="12" fill={isChance ? "#8f2626" : "#5e5a52"}
                    fontFamily="var(--font-mono)" fontWeight={isChance ? "bold" : "normal"}>{v.toFixed(2)}</text>
                </g>
              );
            })}
            <text x={innerWidth + 8} y={yScale(0.5) + 4} fontSize="11" fill="#8f2626" fontFamily="var(--font-mono)" fontWeight="bold">Chance</text>

            {LEVELS.map((lv, i) => {
              const xc = i * gap + gap / 2;
              return (
                <g key={lv.id}>
                  {SCHEMES.map((s) => {
                    const b = MT[s.id].ba[lv.id];
                    const x = xc + s.dx;
                    return (
                      <g key={s.id}>
                        <line x1={x} y1={yScale(b.min)} x2={x} y2={yScale(b.max)} stroke={s.color} strokeWidth="2" strokeOpacity="0.55" />
                        <line x1={x - 4} y1={yScale(b.min)} x2={x + 4} y2={yScale(b.min)} stroke={s.color} strokeWidth="1.5" />
                        <line x1={x - 4} y1={yScale(b.max)} x2={x + 4} y2={yScale(b.max)} stroke={s.color} strokeWidth="1.5" />
                        <circle cx={x} cy={yScale(b.median)} r="5" fill={s.color} stroke="#faf8f5" strokeWidth="1.2">
                          <title>{`${lv.label} (${s.label}): median ${f3(b.median)}, range ${f3(b.min)}–${f3(b.max)}`}</title>
                        </circle>
                      </g>
                    );
                  })}
                  <text x={xc} y={innerHeight + 22} textAnchor="middle" fontSize="12.5" fill="#15263a" fontFamily="var(--font-mono)" fontWeight="bold">{lv.label}</text>
                  <text x={xc} y={innerHeight + 40} textAnchor="middle" fontSize="11" fill="#5e5a52" fontFamily="var(--font-sans)">{lv.sub}</text>
                </g>
              );
            })}
            <line x1={0} y1={innerHeight} x2={innerWidth} y2={innerHeight} stroke="#15263a" strokeWidth="1.5" />
          </g>
        </svg>
      </div>

      <FigureCaption
        figNumber="FIG. 3"
        title="Exploratory Matching Sensitivity"
        takeaway={`Within matched cohorts the count model falls to near chance (median BA ${f3(MT.node_only.ba.M0.median)}), while content stays above chance in every ordering (median ${f3(MT.node_only.ba.M3.median)}, range ${f3(MT.node_only.ba.M3.min)}–${f3(MT.node_only.ba.M3.max)}). With about 16 pairs this is sensitivity evidence only.`}
        details={
          <div className="space-y-2.5">
            <p>
              <strong>Protocol:</strong> 1:1 greedy matching on log node count with a caliper of {MT.caliper_sd_fraction} SD ({f3(MT.caliper_abs)}); the primary ordering gives {MT.primary_pairs} pairs and |SMD| {f2(Math.abs(MT.smd_before))} → {f2(Math.abs(MT.smd_after))}. Because greedy matching depends on visiting order, it is repeated over {MT.node_only.n_order_seeds} orders, with and without log edge count as a second matching variable; pairs stay in the same fold.
            </p>
            <p>
              <strong>Why two schemes:</strong> node-only matching leaves edge counts imbalanced (|SMD| of log edge count {f2(MT.node_only.smd_log_edges_range[0])}–{f2(MT.node_only.smd_log_edges_range[1])}); adding edge count reduces this to {f2(MT.node_edge.smd_log_edges_range[0])}–{f2(MT.node_edge.smd_log_edges_range[1])}.
            </p>
            <p>
              <strong>Caveats:</strong> points are medians and bars span the minimum and maximum over orderings; they are not confidence intervals. Matching changes the evaluated population, and with 15–17 pairs each estimate is imprecise. Not a causal estimate.
            </p>
          </div>
        }
      />
    </div>
  );
}
