import React from "react";
import { sg, ci } from "../lib/fmt";

// Evidence groups, in the order the paper uses them
const GROUP_TITLE = {
  primary: "Prespecified comparisons",
  sensitivity: "Sensitivity analyses",
  exploratory: "Exploratory analyses",
  posthoc: "Post-hoc analyses",
};
const GROUP_COLOR = { primary: "#15263a", sensitivity: "#5e5a52", exploratory: "#23527c", posthoc: "#8f2626" };

/**
 * Paired differences with 95% intervals, laid out as a table: comparison | interval plot | estimate | interval | extra.
 * rows: [{ key, label, sub, status, est, lo, hi, extra }] — est == null means the value was not computed.
 * Rows are grouped under a running head whenever `status` changes (showGroups={false} for single-group charts).
 * groupNotes: { [status]: one-line description of that group's adjustment }.
 * extraLabel: heading of the last column (for example "Holm-adjusted p").
 */
export default function IntervalChart({ rows, xLabel, better = "lower", extraLabel, groupNotes = {}, showGroups = true, ariaLabel }) {
  const vals = rows.filter((r) => r.est != null).flatMap((r) => [r.lo, r.hi]).concat([0]);
  let lo = Math.min(...vals), hi = Math.max(...vals);
  const pad = (hi - lo) * 0.06 || 0.01;
  lo -= pad; hi += pad;
  const P = (v) => ((v - lo) / (hi - lo)) * 100;
  const step = niceStep((hi - lo) / 4);
  const ticks = [];
  for (let t = Math.ceil(lo / step) * step; t <= hi + 1e-9; t += step) ticks.push(Math.round(t / step) * step);

  const grid = "md:grid md:grid-cols-[minmax(190px,1.15fr)_minmax(200px,1.7fr)_76px_150px_minmax(96px,auto)] md:gap-x-5 md:items-center";


  return (
    <div role="table" aria-label={ariaLabel} className="text-[17px]">
      <div role="row" className={`hidden ${grid} pb-2 border-b border-[#d8d3c5] text-[15px] text-[#5e5a52]`}>
        <span role="columnheader">Comparison</span>
        <span role="columnheader" className="text-center">{xLabel}, 95% interval</span>
        <span role="columnheader" className="text-right">Estimate</span>
        <span role="columnheader" className="text-right">95% interval</span>
        <span role="columnheader" className="text-right">{extraLabel || ""}</span>
      </div>

      {rows.map((r, i) => {
        const head = showGroups && (i === 0 || rows[i - 1].status !== r.status);

        const color = GROUP_COLOR[r.status] || "#15263a";
        const excl = r.est != null && (r.lo > 0 || r.hi < 0);
        return (
          <React.Fragment key={r.key}>
            {head && (
              <div role="row" className="pt-6 pb-1 flex flex-wrap items-baseline gap-x-4 gap-y-1">
                <span role="rowheader" className="font-serif italic text-[20px] leading-snug" style={{ color }}>{GROUP_TITLE[r.status]}</span>
                {groupNotes[r.status] && <span className="text-[16px] text-[#5e5a52]">{groupNotes[r.status]}</span>}
              </div>
            )}
            <div role="row" className={`${grid} py-3 border-b border-[#ece6d8]`}>
              <div role="cell" className="min-w-0">
                <div className="text-[#15263a] leading-snug">{r.label}</div>
                {r.sub && <div className="text-[15.5px] text-[#6b6862] leading-snug">{r.sub}</div>}
              </div>
              <div role="cell" className="mt-2 md:mt-0" aria-hidden="true">
                <svg width="100%" height="26" className="block overflow-visible">
                  {ticks.map((t) => <line key={t} x1={`${P(t)}%`} x2={`${P(t)}%`} y1="0" y2="26" stroke="#ece6d8" />)}
                  <line x1={`${P(0)}%`} x2={`${P(0)}%`} y1="0" y2="26" stroke="#9a948a" strokeDasharray="3 3" />
                  {r.est != null && (
                    <>
                      <line x1={`${P(r.lo)}%`} x2={`${P(r.hi)}%`} y1="13" y2="13" stroke={color} strokeWidth="1.6" />
                      <line x1={`${P(r.lo)}%`} x2={`${P(r.lo)}%`} y1="8" y2="18" stroke={color} strokeWidth="1.6" />
                      <line x1={`${P(r.hi)}%`} x2={`${P(r.hi)}%`} y1="8" y2="18" stroke={color} strokeWidth="1.6" />
                      <circle cx={`${P(r.est)}%`} cy="13" r="4.5" fill={excl ? color : "#ffffff"} stroke={color} strokeWidth="1.6" />
                    </>
                  )}
                </svg>
              </div>
              {r.est == null ? (
                <div role="cell" className="md:col-span-3 mt-1 md:mt-0 md:text-right text-[16px] italic text-[#8a847a]">Not computed for this partitioning</div>
              ) : (
                <>
                  <div role="cell" className="inline md:block mt-1 md:mt-0 md:text-right font-mono text-[18px] text-[#15263a]">{sg(r.est)}</div>
                  <div role="cell" className="inline md:block ml-3 md:ml-0 md:text-right font-mono text-[17px] text-[#3c3a37] whitespace-nowrap">{ci([r.lo, r.hi])}</div>
                  <div role="cell" className="block mt-0.5 md:mt-0 md:text-right font-mono text-[16px] text-[#6b6862] whitespace-nowrap">
                    {r.extra ? <><span className="md:hidden">{extraLabel} </span>{r.extra}</> : null}
                  </div>
                </>
              )}
            </div>
          </React.Fragment>
        );
      })}

      {/* shared axis under the plot column */}
      <div className={`hidden ${grid} pt-2`} aria-hidden="true">
        <span />
        <div className="relative h-5 text-[15px] text-[#6b6862] font-mono">
          {ticks.map((t) => (
            <span key={t} className="absolute -translate-x-1/2 whitespace-nowrap" style={{ left: `${P(t)}%` }}>{t === 0 ? "0" : sg(t)}</span>
          ))}
        </div>
      </div>
      <p className="mt-3 md:mt-2 text-[15px] text-[#5e5a52]">
        {xLabel}: {better === "lower" ? "values below zero favour the first model" : "values above zero favour the first model"}. Filled points mark intervals that exclude zero.
      </p>
    </div>
  );
}

function niceStep(raw) {
  const p = Math.pow(10, Math.floor(Math.log10(raw)));
  const m = raw / p;
  return (m < 1.5 ? 1 : m < 3.5 ? 2 : m < 7.5 ? 5 : 10) * p;
}
