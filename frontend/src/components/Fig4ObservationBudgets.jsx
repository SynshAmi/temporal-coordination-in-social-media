import React from "react";
import FigureCaption from "./FigureCaption";
import NK from "./NK";
import { f3, sg, ci, ciu, cond, con, vmf } from "../lib/fmt";

// Study 2: single-view BA by edge budget on the common cohort (events eligible at every budget, as in the
// paper's Fig. 3), so every line compares the same events; bars span min–max over 10 sampling seeds
const COHORT = "common";
const SERIES = [
  { key: "FF|combined", label: "FF: full → full, all features", color: "#a8a396", dash: "6,3,1,3" },
  { key: "FF|struct6", label: "FF: full → full, structure", color: "#757065", dash: "2,3" },
  { key: "FK|struct6", label: "FK: full → view (frozen), structure", color: "#8f2626", dash: "" },
  { key: "KK|struct6", label: "KK: view → view (retrained), structure", color: "#23527c", dash: "" },
  { key: "KK|NK", label: "KK: sampled endpoint count N_K only", jsx: <>KK: sampled endpoint count <NK /> only</>, color: "#c27d38", dash: "5,3" },
  { key: "KK|combined", label: "KK: N_K + structure + content", jsx: <>KK: <NK /> + structure + content</>, color: "#15263a", dash: "" },
];
const BUDGETS = [250, 500, 1000];

export default function Fig4ObservationBudgets({ paper, revision: V }) {
  const EL = paper.eligibility;
  const common = paper.study2.results[`${COHORT}_K1000`];
  const svgWidth = 640;
  const svgHeight = 360;
  const margin = { top: 28, right: 40, bottom: 52, left: 56 };
  const innerWidth = svgWidth - margin.left - margin.right;
  const innerHeight = svgHeight - margin.top - margin.bottom;
  const yMin = 0.45;
  const yMax = 1.0;
  const yScale = (v) => innerHeight - ((Math.max(yMin, Math.min(yMax, v)) - yMin) / (yMax - yMin)) * innerHeight;
  const xs = [...BUDGETS, 2000];
  const xScale = (i) => (i / (xs.length - 1)) * (innerWidth - 80) + 40;
  const rt = con(paper, 250, "retrain_effect_struct6");

  return (
    <div className="bg-[#faf8f5] border border-[#dcd7ca] p-5 sm:p-8 lg:p-10 shadow-none">
      <div className="panel-head">
        <span className="section-label">Figure 4</span>
        <h3 className="text-xl font-serif font-medium text-[#15263a]">
          Single-View Performance Under Edge Budgets
        </h3>
        <p className="head-desc">
          Balanced accuracy of models scored on one K-edge sample per event, on the {common.n_events} events eligible at every budget; all conditions share events, folds and feature definitions.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-1.5 mb-4 text-xs font-mono text-[#3c3a37]">
        {SERIES.map((s) => (
          <span key={s.key} className="inline-flex items-center gap-2">
            <svg width="22" height="8" aria-hidden="true"><line x1="0" y1="4" x2="22" y2="4" stroke={s.color} strokeWidth="2.2" strokeDasharray={s.dash} /></svg>
            <span>{s.jsx || s.label}</span>
          </span>
        ))}
      </div>

      <div className="chart-frame">
        <svg viewBox={`0 0 ${svgWidth} ${svgHeight}`} className="select-none overflow-visible" role="img"
          aria-label="Line chart of single-view balanced accuracy at K = 250, 500 and 1000 for six training and feature conditions on the common cohort">
          <g transform={`translate(${margin.left}, ${margin.top})`}>
            <line x1={0} y1={0} x2={0} y2={innerHeight} stroke="#15263a" strokeWidth="1.5" />
            {[0.5, 0.6, 0.7, 0.8, 0.9, 1.0].map((v) => {
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

            {SERIES.map((s) => {
              const pts = BUDGETS.map((k, i) => ({ x: xScale(i), c: cond(paper, k, s.key, COHORT), k }));
              const path = pts.map((p, i) => `${i ? "L" : "M"} ${p.x} ${yScale(p.c.single_view_ba_mean)}`).join(" ");
              return (
                <g key={s.key}>
                  <path d={path} fill="none" stroke={s.color} strokeWidth="2.2" strokeDasharray={s.dash} />
                  {pts.map((p) => (
                    <g key={p.k}>
                      <line x1={p.x} y1={yScale(p.c.single_view_ba_min)} x2={p.x} y2={yScale(p.c.single_view_ba_max)} stroke={s.color} strokeWidth="1.3" strokeOpacity="0.6" />
                      <circle cx={p.x} cy={yScale(p.c.single_view_ba_mean)} r="4.5" fill={s.color} stroke="#faf8f5" strokeWidth="1.2">
                        <title>{`${s.label}, K = ${p.k}: ${f3(p.c.single_view_ba_mean)} (seed range ${f3(p.c.single_view_ba_min)}–${f3(p.c.single_view_ba_max)})`}</title>
                      </circle>
                    </g>
                  ))}
                </g>
              );
            })}

            {/* K = 2000 marker: infeasible for 5-fold stratified CV */}
            <rect x={xScale(3) - 34} y={yScale(0.8)} width="68" height={yScale(0.6) - yScale(0.8)} fill="#f4efe6" stroke="#d8d3c5" strokeDasharray="3,3" />
            <text x={xScale(3)} y={yScale(0.72)} textAnchor="middle" fontSize="11" fill="#8f2626" fontFamily="var(--font-mono)" fontWeight="bold">infeasible</text>
            <text x={xScale(3)} y={yScale(0.72) + 15} textAnchor="middle" fontSize="10.5" fill="#5e5a52" fontFamily="var(--font-mono)">{EL["2000"].campaign_eligible} campaign</text>

            <line x1={0} y1={innerHeight} x2={innerWidth} y2={innerHeight} stroke="#15263a" strokeWidth="1.5" />
            {xs.map((k, i) => (
              <g key={k}>
                <line x1={xScale(i)} y1={innerHeight} x2={xScale(i)} y2={innerHeight + 6} stroke="#15263a" strokeWidth="1.5" />
                <text x={xScale(i)} y={innerHeight + 22} textAnchor="middle" fontSize="12" fill="#15263a" fontFamily="var(--font-mono)" fontWeight="bold">K = {k}</text>
                <text x={xScale(i)} y={innerHeight + 38} textAnchor="middle" fontSize="10.5" fill="#5e5a52" fontFamily="var(--font-mono)">n = {k === 2000 ? EL["2000"].total_eligible : paper.study2.results[`${COHORT}_K${k}`].n_events}</text>
              </g>
            ))}
          </g>
        </svg>
      </div>

      <FigureCaption
        figNumber="FIG. 4"
        title="Training Regime Matters More Than Feature Choice"
        takeaway={<>On the same events, a model trained on single K-edge views was not detectably less accurate than the full-graph model with the same features (budget-specific cohorts, ΔBA view − full: {sg(vmf(V, 250).ba.delta)} {ci(vmf(V, 250).ba.ci)} at K = 250). With the same structural features, events and folds, training on views instead of applying the full-graph model raised single-view BA at K = 250 by {f3(rt.ba.delta)} {ciu(rt.ba.ci)}.</>}
        details={
          <div className="space-y-2.5">
            <p>
              <strong>Conditions:</strong> FF trains and evaluates on full graphs; FK applies the full-graph model to single K-edge views (frozen transfer); KK trains and evaluates on single views from the same sampling seed. Every feature is recomputed from the sampled edges only. Density is excluded because at fixed K it is determined by <NK />.
            </p>
            <p>
              <strong>Estimand:</strong> points are single-view BA averaged over 10 sampling seeds; bars span the minimum and maximum over seeds and are <em>not</em> confidence intervals. The 10-view ensemble changes BA by at most {f3(Math.max(...BUDGETS.map((k) => Math.abs(con(paper, k, "ensemble_vs_single_combined").ba.delta))))}, so averaging views contributes little.
            </p>
            <p>
              <strong>Cohorts:</strong> the plot shows the common cohort of the {common.n_events} events eligible at every budget ({common.n_campaign}/{common.n_comparison}), so full-graph (FF) values do not depend on K. The results table and the contrasts in the takeaway use budget-specific cohorts (K = 250: {EL["250"].total_eligible} events; K = 500: {EL["500"].total_eligible}; K = 1000: {EL["1000"].total_eligible}); on the common cohort the contrasts have the same directions at K = 250 and 500, although there the content interval at K = 500 excludes zero.
            </p>
            <p>
              <strong>K = 1000:</strong> the view-trained model was ahead of the full-graph model with all features (ΔBA {sg(vmf(V, 1000).ba.delta)} {ci(vmf(V, 1000).ba.ci)}; Δ log loss {sg(vmf(V, 1000).log_loss.delta)} {ci(vmf(V, 1000).log_loss.ci)}). This exploratory, uncorrected result comes from a small, imbalanced cohort and does not indicate that sampling generally improves classification. Study 2 contrasts use {V.study2_n_bootstrap.toLocaleString("en-US")} bootstrap resamples with no multiplicity correction.
            </p>
            <p>
              K = 2000 is infeasible for five-fold stratified evaluation because only {EL["2000"].campaign_eligible} campaign events have at least 2,000 edges.
            </p>
          </div>
        }
      />
    </div>
  );
}
