import React, { useState } from "react";
import FigureCaption from "./FigureCaption";
import { f2, f3, sg, ci, pv, baMaxHi } from "../lib/fmt";

// Study 1 primary contrasts (LR, N = 103): paired differences A − B on identical events
const CONTRASTS = [
  { id: "C1", label: "all features vs counts", short: "M4 − M0q" },
  { id: "C2", label: "arrangement beyond degree", short: "M2 − M1" },
  { id: "C3", label: "content beyond counts", short: "M3 − M0q" },
];
const METRICS = [
  { id: "ba", name: "Balanced Acc", pick: (c) => [c.ba.delta_ba, c.ba.delta_ba_ci, c.ba.p_holm], better: "higher" },
  { id: "ll", name: "Log Loss", pick: (c) => [c.log_loss.delta_logloss, c.log_loss.delta_logloss_ci, c.log_loss.p_holm], better: "lower" },
  { id: "auc", name: "ROC-AUC", pick: (c) => [c.auc_ll_fit.delta_auc, c.auc_ll_fit.delta_auc_ci, null], better: "higher" },
];

export default function Fig2Baselines({ paper }) {
  const [metricKey, setMetricKey] = useState("ba");
  const S1 = paper.study1;
  const LC = S1.confirmatory.logreg;
  const lr = S1.performance.logreg;
  const metric = METRICS.find((m) => m.id === metricKey);
  const rows = CONTRASTS.map((c) => {
    const [d, interval, p] = metric.pick(LC[c.id]);
    return { ...c, d, lo: interval[0], hi: interval[1], p, excludesZero: interval[0] > 0 || interval[1] < 0 };
  });

  const svgWidth = 640;
  const rowH = 78;
  const margin = { top: 34, right: 140, bottom: 52, left: 196 };
  const innerWidth = svgWidth - margin.left - margin.right;
  const innerHeight = rows.length * rowH;
  const svgHeight = innerHeight + margin.top + margin.bottom;

  const span = Math.max(...rows.flatMap((r) => [Math.abs(r.lo), Math.abs(r.hi)]));
  const step = span > 0.15 ? 0.1 : 0.05;
  const xMax = Math.ceil((span * 1.08) / step) * step;
  const xScale = (v) => ((v + xMax) / (2 * xMax)) * innerWidth;
  const ticks = [];
  for (let t = -xMax; t <= xMax + 1e-9; t += step) ticks.push(Math.round(t * 100) / 100);

  return (
    <div className="bg-[#faf8f5] border border-[#dcd7ca] p-5 sm:p-8 lg:p-10 shadow-none">
      <div className="panel-head flex flex-wrap items-end justify-between gap-x-6 gap-y-4">
        <div className="min-w-0 flex-1 basis-80">
          <span className="section-label">Figure 2</span>
          <h3 className="text-xl font-serif font-medium text-[#15263a]">
            What Do Richer Features Add Beyond Counts?
          </h3>
          <p className="head-desc">
            Primary paired contrasts, logistic regression, full cohort (N = {paper.dataset.n_events}).
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs font-mono">
          <span className="text-[#6b6862] text-[11px] uppercase tracking-wider">Estimand:</span>
          <div className="inline-flex border border-[#d8d3c5] bg-white p-0.5 shadow-2xs">
            {METRICS.map((m) => (
              <button
                key={m.id}
                type="button"
                onClick={() => setMetricKey(m.id)}
                className={`px-3.5 py-1 text-xs transition-colors ${
                  metricKey === m.id ? "bg-[#15263a] text-white font-medium shadow-xs" : "text-[#3c3a37] hover:bg-[#ede9df]"
                }`}
              >
                {m.name}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="chart-frame">
        <svg viewBox={`0 0 ${svgWidth} ${svgHeight}`} className="select-none overflow-visible" role="img"
          aria-label={`Forest plot of paired ${metric.name} differences for contrasts C1 to C3 with 95% bootstrap intervals`}>
          <g transform={`translate(${margin.left}, ${margin.top})`}>
            {ticks.map((t) => (
              <g key={t}>
                <line x1={xScale(t)} y1={0} x2={xScale(t)} y2={innerHeight}
                  stroke={t === 0 ? "#15263a" : "#e4dfd3"} strokeWidth={t === 0 ? 1.4 : 0.8} strokeDasharray={t === 0 ? "" : "2,2"} />
                <text x={xScale(t)} y={innerHeight + 20} textAnchor="middle" fontSize="12" fill="#5e5a52" fontFamily="var(--font-mono)">
                  {t === 0 ? "0" : sg(t).replace(/0+$/, "").replace(/\.$/, "")}
                </text>
              </g>
            ))}
            <text x={innerWidth / 2} y={innerHeight + 42} textAnchor="middle" fontSize="12" fill="#15263a" fontFamily="var(--font-sans)">
              Δ {metric.name} (A − B){metric.better === "lower" ? " · negative = better" : " · positive = better"}
            </text>

            {rows.map((r, i) => {
              const y = i * rowH + rowH / 2;
              const color = r.excludesZero ? "#8f2626" : "#15263a";
              return (
                <g key={r.id}>
                  <text x={-16} y={y - 4} textAnchor="end" fontSize="13" fill="#15263a" fontFamily="var(--font-mono)" fontWeight="bold">{r.id}: {r.short}</text>
                  <text x={-16} y={y + 14} textAnchor="end" fontSize="12" fill="#5e5a52" fontFamily="var(--font-sans)">{r.label}</text>
                  <line x1={xScale(r.lo)} y1={y} x2={xScale(r.hi)} y2={y} stroke={color} strokeWidth="1.8" />
                  <line x1={xScale(r.lo)} y1={y - 6} x2={xScale(r.lo)} y2={y + 6} stroke={color} strokeWidth="1.5" />
                  <line x1={xScale(r.hi)} y1={y - 6} x2={xScale(r.hi)} y2={y + 6} stroke={color} strokeWidth="1.5" />
                  <circle cx={xScale(r.d)} cy={y} r="6" fill={r.excludesZero ? "#8f2626" : "#faf8f5"} stroke={color} strokeWidth="1.8" />
                  <text x={innerWidth + 14} y={y - 3} fontSize="12" fill={color} fontFamily="var(--font-mono)" fontWeight="bold">{sg(r.d)}</text>
                  <text x={innerWidth + 14} y={y + 13} fontSize="11" fill="#5e5a52" fontFamily="var(--font-mono)">
                    {ci([r.lo, r.hi])}
                  </text>
                </g>
              );
            })}
          </g>
        </svg>
      </div>

      <FigureCaption
        figNumber="FIG. 2"
        title="Primary Paired Contrasts (LR)"
        takeaway={`Counts alone reach BA ${f3(lr.M0.balanced_accuracy)}. Adding degree, arrangement and content features did not detectably improve classification decisions (C1 ΔBA ${sg(LC.C1.ba.delta_ba)} ${ci(LC.C1.ba.delta_ba_ci)}), but improved log loss by ${f3(-LC.C1.log_loss.delta_logloss)} and AUC by ${f3(LC.C1.auc_ll_fit.delta_auc)}.`}
        details={
          <div className="space-y-2.5">
            <p>
              <strong>Reading the plot:</strong> points are differences A − B computed on identical events; bars are 95% event-level paired bootstrap intervals ({S1.n_bootstrap.toLocaleString("en-US")} resamples) of fixed out-of-fold predictions. Filled red points have intervals excluding zero. Holm-adjusted p-values (BA family / log-loss family):{" "}
              {CONTRASTS.map((c) => `${c.id} ${pv(LC[c.id].ba.p_holm)} / ${pv(LC[c.id].log_loss.p_holm)}`).join("; ")}.
            </p>
            <p>
              <strong>Inconclusive, not equivalent:</strong> the BA intervals admit gains of up to about {f2(baMaxHi(paper))}, so the absence of a detectable BA gain is not evidence that the features are useless. Neither arrangement beyond degree (C2) nor content alone (C3) reproduces the C1 log-loss gain.
            </p>
            <p>
              <strong>Estimands:</strong> BA uses fits tuned for BA; log loss and AUC use separately tuned log-loss fits on the same outer folds. Intervals resample events for one fixed set of predictions and exclude refitting and split variability: across {S1.n_split_seeds} fold splits the C1 BA difference ranged from {sg(S1.repeated_splits_lr.C1.dBA_min)} to {sg(S1.repeated_splits_lr.C1.dBA_max)} and the log-loss difference from {sg(S1.repeated_splits_lr.C1.dLL_min)} to {sg(S1.repeated_splits_lr.C1.dLL_max)}. Positive BA point estimates in every split are not a significance result, because the splits reuse the same events.
            </p>
          </div>
        }
      />
    </div>
  );
}
