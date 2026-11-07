import React from "react";
import { f3 } from "../lib/fmt";

/**
 * Single-view performance by edge budget (budget-specific cohorts, paper Table V).
 * series: [{ key, label, color, dash, values: {250, 500, 1000}, posthoc }]
 * metric: "log_loss" | "auc" | "ba" (log loss: lower is better).
 */
export default function EdgeBudgetChart({ series, metric, cohorts }) {
  const W = 980, H = 340, ml = 76, mr = 24, mt = 16, mb = 56;
  const ks = [250, 500, 1000];
  const all = series.flatMap((s) => ks.map((k) => s.values[k]));
  let lo = Math.min(...all), hi = Math.max(...all);
  const pad = (hi - lo) * 0.1 || 0.02;
  lo -= pad; hi += pad;
  const X = (i) => ml + 40 + i * ((W - ml - mr - 80) / 2);
  const Y = (v) => mt + (1 - (v - lo) / (hi - lo)) * (H - mt - mb);
  const raw = (hi - lo) / 4, p10 = Math.pow(10, Math.floor(Math.log10(raw))), mm = raw / p10;
  const step = (mm < 1.5 ? 1 : mm < 3.5 ? 2 : mm < 7.5 ? 5 : 10) * p10;
  const ticks = [];
  for (let t = Math.ceil(lo / step) * step; t <= hi + 1e-9; t += step) ticks.push(t);
  const label = { log_loss: "Single-view log loss (lower is better)", auc: "Single-view AUC (higher is better)", ba: "Single-view balanced accuracy (higher is better)" }[metric];

  return (
    <div>
      <div className="chart-frame">
        <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={label} style={{ maxWidth: "100%", width: "100%", minWidth: 600 }}>
          {ticks.map((t, i) => (
            <g key={i}>
              <line x1={ml} x2={W - mr} y1={Y(t)} y2={Y(t)} stroke="#ece6d8" />
              <text x={ml - 8} y={Y(t) + 4} textAnchor="end" fontSize="11" fill="#757065" fontFamily="var(--font-mono)">{t.toFixed(step < 0.01 ? 3 : 2)}</text>
            </g>
          ))}
          {ks.map((k, i) => (
            <g key={k}>
              <text x={X(i)} y={H - mb + 22} textAnchor="middle" fontSize="12" fill="#15263a" fontFamily="var(--font-mono)">K = {k}</text>
              <text x={X(i)} y={H - mb + 38} textAnchor="middle" fontSize="11" fill="#757065" fontFamily="var(--font-mono)">n = {cohorts[k].n} ({cohorts[k].camp}/{cohorts[k].comp})</text>
            </g>
          ))}
          <text x={12} y={(mt + H - mb) / 2} transform={`rotate(-90 12 ${(mt + H - mb) / 2})`} textAnchor="middle" fontSize="11" fill="#5e5a52" fontFamily="var(--font-sans)">{label}</text>
          {series.map((s) => (
            <g key={s.key}>
              <polyline points={ks.map((k, i) => `${X(i)},${Y(s.values[k])}`).join(" ")} fill="none" stroke={s.color} strokeWidth="1.75" strokeDasharray={s.dash || "none"} />
              {ks.map((k, i) => (
                <circle key={k} cx={X(i)} cy={Y(s.values[k])} r="3.5" fill={s.posthoc ? "#faf8f5" : s.color} stroke={s.color} strokeWidth="1.5">
                  <title>{`${s.label}, K = ${k}: ${f3(s.values[k])}`}</title>
                </circle>
              ))}
            </g>
          ))}
        </svg>
      </div>
      <ul className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-2 text-[15px] text-[#3c3a37]">
        {series.map((s) => (
          <li key={s.key} className="flex items-center gap-3">
            <svg width="28" height="10" aria-hidden="true" className="shrink-0">
              <line x1="0" x2="28" y1="5" y2="5" stroke={s.color} strokeWidth="2" strokeDasharray={s.dash || "none"} />
            </svg>
            <span>{s.label}{s.posthoc ? <span className="text-[#8f2626] font-mono text-[13px] ml-2">post hoc</span> : null}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
