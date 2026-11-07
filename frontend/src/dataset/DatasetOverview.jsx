import React, { useMemo, useState } from "react";
import { Search, ArrowRight, Network, FlaskConical, GitCompare } from "lucide-react";
import { LabelBadge, StatRows, Citation, ResearchNotes } from "./ui";
import { licenceNote } from "./notes";
import { FEATURE_ROWS, fmtFeature } from "./features";
import { PAGE } from "./palette";
import { f3, int } from "../lib/fmt";
import { median } from "./graph";

const STRIP_METRICS = [
  { key: "n_nodes", label: "Nodes", log: true, get: (e) => e.n_nodes },
  { key: "n_edges", label: "Edges", log: true, get: (e) => e.n_edges },
  { key: "reciprocity", label: "Reciprocity", get: (e) => e.features.reciprocity },
  { key: "largest_wcc_fraction", label: "Largest component", get: (e) => e.features.largest_wcc_fraction },
  { key: "indegree_gini", label: "In-degree Gini", get: (e) => e.features.indegree_gini },
  { key: "coreness_max", label: "Max core number", get: (e) => e.features.coreness_max },
];

export default function DatasetOverview({ index, selected, onSelect, go }) {
  const events = index.events;
  const [query, setQuery] = useState("");
  const [labelFilter, setLabelFilter] = useState("all");
  const [sort, setSort] = useState({ key: "n_nodes", dir: -1 });
  const [metric, setMetric] = useState("n_nodes");

  const totals = useMemo(() => {
    const by = (l) => events.filter((e) => e.label === l);
    return {
      nodes: events.reduce((a, e) => a + e.n_nodes, 0),
      edges: events.reduce((a, e) => a + e.n_edges, 0),
      loops: events.reduce((a, e) => a + e.n_self_loops, 0),
      medNodes: [median(by(1).map((e) => e.n_nodes)), median(by(0).map((e) => e.n_nodes))],
      medEdges: [median(by(1).map((e) => e.n_edges)), median(by(0).map((e) => e.n_edges))],
      withSamples: events.filter((e) => e.budgets.length).length,
    };
  }, [events]);

  const rows = useMemo(() => {
    const q = query.trim().toLowerCase();
    const val = (e) => (sort.key === "name" ? e.name.toLowerCase() : sort.key in e ? e[sort.key] : e.features[sort.key]);
    return events
      .filter((e) => labelFilter === "all" || e.label === (labelFilter === "campaign" ? 1 : 0))
      .filter((e) => !q || e.name.toLowerCase().includes(q) || e.id.toLowerCase().includes(q))
      .sort((a, b) => (val(a) < val(b) ? -1 : val(a) > val(b) ? 1 : a.i - b.i) * sort.dir);
  }, [events, query, labelFilter, sort]);

  const sel = selected != null ? events.find((e) => e.i === selected) : null;
  const sortBtn = (key, text) => (
    <button type="button" onClick={() => setSort((s) => ({ key, dir: s.key === key ? -s.dir : key === "name" ? 1 : -1 }))}
      className={`inline-flex items-center gap-1 hover:text-[#15263a] ${sort.key === key ? "text-[#15263a]" : ""}`} aria-label={`Sort by ${text}`}>
      {text}{sort.key === key && <span aria-hidden="true">{sort.dir > 0 ? "↑" : "↓"}</span>}
    </button>
  );

  return (
    <div className="space-y-12 lg:space-y-14">
      {/* Summary figures */}
      <section className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-px bg-[#dcd7ca] border border-[#dcd7ca]">
        {[
          ["Events", index.archive.n_events, `${index.archive.n_campaign} campaign · ${index.archive.n_comparison} comparison`],
          ["Nodes, all graphs", int(totals.nodes), "per-graph indices, not accounts"],
          ["Directed edges", int(totals.edges), `${int(totals.loops)} self-loops`],
          ["Median nodes", `${int(totals.medNodes[0])} / ${int(totals.medNodes[1])}`, "campaign / comparison"],
          ["Median edges", `${int(totals.medEdges[0])} / ${int(totals.medEdges[1])}`, "campaign / comparison"],
          ["Sampled observations", `${totals.withSamples} events`, `K = ${index.budgets.join(", ")} · ${index.n_seeds} seeds`],
        ].map(([k, v, sub]) => (
          <div key={k} className="bg-white px-4 py-4">
            <div className="text-[12.5px] font-mono text-[#757065]">{k}</div>
            <div className="mt-1 font-serif text-2xl text-[#15263a] leading-tight">{v}</div>
            <div className="mt-0.5 text-[13px] font-mono text-[#757065]">{sub}</div>
          </div>
        ))}
      </section>

      {/* Charts */}
      <section className="grid grid-cols-1 xl:grid-cols-2 gap-8 lg:gap-10">
        <div className="bg-[#faf8f5] border border-[#dcd7ca] p-5 sm:p-7">
          <div className="panel-head !mb-4">
            <span className="section-label">Size</span>
            <h3 className="text-xl font-serif text-[#15263a]">Nodes and edges per event</h3>
            <p className="head-desc">Each point is one event graph, on log scales. Select a point to inspect the event.</p>
          </div>
          <SizeScatter events={events} selected={selected} onSelect={onSelect} />
        </div>
        <div className="bg-[#faf8f5] border border-[#dcd7ca] p-5 sm:p-7">
          <div className="panel-head !mb-4 flex flex-wrap items-end justify-between gap-3">
            <div>
              <span className="section-label">Distributions</span>
              <h3 className="text-xl font-serif text-[#15263a]">One measure, by label</h3>
              <p className="head-desc">Full-graph values as computed in the paper; lines mark class medians.</p>
            </div>
            <select value={metric} onChange={(e) => setMetric(e.target.value)} aria-label="Measure to plot"
              className="bg-white border border-[#d8d3c5] px-2 py-1.5 text-[14px] font-mono text-[#15263a]">
              {STRIP_METRICS.map((m) => <option key={m.key} value={m.key}>{m.label}</option>)}
            </select>
          </div>
          <MetricStrip events={events} metric={STRIP_METRICS.find((m) => m.key === metric)} selected={selected} onSelect={onSelect} />
        </div>
      </section>

      {/* Event browser + selected event */}
      <section className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-10 items-start">
        <div className="lg:col-span-7 xl:col-span-8 bg-white border border-[#dcd7ca]">
          <div className="p-4 sm:p-5 border-b border-[#e5e0d4] flex flex-col sm:flex-row gap-3 sm:items-center">
            <h3 className="font-serif text-xl text-[#15263a] shrink-0 sm:mr-auto">Event browser</h3>
            <label className="relative flex-1 sm:max-w-[260px]">
              <span className="sr-only">Search events</span>
              <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-[#9a948a]" />
              <input type="search" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search event identifier"
                className="w-full pl-8 pr-2 py-2 text-[16px] border border-[#d8d3c5] bg-[#faf8f5] focus:outline-none focus:border-[#23527c]" />
            </label>
            <div className="inline-flex border border-[#d8d3c5] bg-[#faf8f5] p-0.5 text-[14px] font-mono self-start" role="group" aria-label="Filter by label">
              {[["all", "All"], ["campaign", "Campaign"], ["comparison", "Comparison"]].map(([k, t]) => (
                <button key={k} type="button" onClick={() => setLabelFilter(k)} aria-pressed={labelFilter === k}
                  className={`px-2.5 py-1.5 ${labelFilter === k ? "bg-[#15263a] text-white" : "text-[#3c3a37] hover:bg-[#ede9df]"}`}>{t}</button>
              ))}
            </div>
          </div>
          <div className="px-4 sm:px-5 py-2 text-[13px] font-mono text-[#757065] border-b border-[#e5e0d4]">
            {rows.length} of {events.length} events
          </div>
          <div className="max-h-[560px] overflow-y-auto">
            <table className="w-full text-[16px]">
              <thead className="sticky top-0 bg-[#f4efe6] text-[13px] font-mono text-[#757065]">
                <tr className="text-left">
                  <th className="px-4 sm:px-5 py-2 font-medium">{sortBtn("name", "Event")}</th>
                  <th className="px-2 py-2 font-medium hidden sm:table-cell">Label</th>
                  <th className="px-2 py-2 font-medium text-right">{sortBtn("n_nodes", "Nodes")}</th>
                  <th className="px-2 py-2 font-medium text-right">{sortBtn("n_edges", "Edges")}</th>
                  <th className="px-4 sm:px-5 py-2 font-medium text-right hidden md:table-cell">{sortBtn("reciprocity", "Recip.")}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#eee9df]">
                {rows.map((e) => (
                  <tr key={e.i} onClick={() => onSelect(e.i)} aria-selected={e.i === selected}
                    className={`cursor-pointer ${e.i === selected ? "bg-[#eef3f8]" : "hover:bg-[#faf8f5]"}`}>
                    <td className="px-4 sm:px-5 py-2">
                      <button type="button" className="text-left text-[#15263a] hover:underline underline-offset-4 break-all" onClick={() => onSelect(e.i)}>{e.name}</button>
                      <span className="sm:hidden ml-2"><LabelBadge label={e.label} small /></span>
                    </td>
                    <td className="px-2 py-2 hidden sm:table-cell"><LabelBadge label={e.label} small /></td>
                    <td className="px-2 py-2 text-right font-mono text-[15px]">{int(e.n_nodes)}</td>
                    <td className="px-2 py-2 text-right font-mono text-[15px]">{int(e.n_edges)}</td>
                    <td className="px-4 sm:px-5 py-2 text-right font-mono text-[15px] hidden md:table-cell">{f3(e.features.reciprocity)}</td>
                  </tr>
                ))}
                {!rows.length && (
                  <tr><td colSpan={5} className="px-5 py-8 text-center text-[16px] text-[#757065]">No events match this search.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        <aside className="lg:col-span-5 xl:col-span-4 lg:sticky lg:top-36 space-y-5">
          {sel ? <EventCard e={sel} go={go} /> : (
            <div className="border border-dashed border-[#cfc8b8] p-6 text-[16px] text-[#5e5a52] bg-[#faf8f5]">
              Select an event in the table or a chart to see its statistics and open its network.
            </div>
          )}
          <div className="bg-[#f4efe6] border border-[#dcd7ca] p-5">
            <div className="font-mono text-[13px] font-semibold text-[#15263a] mb-3">Data source</div>
            <Citation source={index.source} />
          </div>
        </aside>
      </section>

      <ResearchNotes index={index} items={[
        licenceNote(index.source),
        ["Values shown", "Statistics are computed on the full graphs as in the paper: features from its corrected run, counts from the archive. Charts use the same values; distributions show class medians, not tests."],
      ]} />
    </div>
  );
}

export function EventCard({ e, go, compact = false }) {
  return (
    <div className="bg-white border border-[#dcd7ca] border-t-2 p-5" style={{ borderTopColor: e.label === 1 ? PAGE.campaign : PAGE.comparison }}>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="text-[13px] font-mono text-[#757065]">Event {String(e.i).padStart(3, "0")}</div>
          <h3 className="mt-1 font-serif text-xl text-[#15263a] leading-snug break-words">{e.name}</h3>
        </div>
        <LabelBadge label={e.label} />
      </div>
      <div className="mt-1 text-[13px] font-mono text-[#9a948a] break-all">{e.id}</div>
      <StatRows className="mt-4" rows={[
        ["Nodes", int(e.n_nodes)],
        ["Directed edges", int(e.n_edges)],
        ["Self-loops", int(e.n_self_loops)],
        ["Weak components", `${int(e.n_wcc)} (largest ${int(e.largest_wcc)})`],
        ["Max in / out degree", `${e.max_in} / ${e.max_out}`],
        ...(compact ? [] : FEATURE_ROWS.filter(([k]) => k !== "density").map(([k, t, h]) => [t, fmtFeature(k, e.features[k]), h])),
        ["Study 2 observations", e.budgets.length ? `K = ${e.budgets.join(", ")}` : "none (fewer than 250 edges)"],
      ]} />
      {go && (
        <div className="mt-5 grid grid-cols-1 gap-2">
          <button type="button" onClick={() => go("event", e.i)}
            className="inline-flex items-center justify-between gap-2 px-4 py-2.5 bg-[#15263a] text-white text-[14px] font-medium hover:bg-[#23527c] transition-colors">
            <span className="inline-flex items-center gap-2"><Network size={14} /> Explore network</span><ArrowRight size={13} />
          </button>
          <div className="grid grid-cols-2 gap-2">
            <button type="button" onClick={() => go("sampling", e.i)} disabled={!e.budgets.length}
              className="inline-flex items-center justify-center gap-2 px-3 py-2 bg-white border border-[#15263a] text-[#15263a] text-[14px] hover:bg-[#f2eee5] disabled:opacity-40 disabled:cursor-not-allowed">
              <FlaskConical size={13} /> Sampling lab
            </button>
            <button type="button" onClick={() => go("compare", e.i)}
              className="inline-flex items-center justify-center gap-2 px-3 py-2 bg-white border border-[#15263a] text-[#15263a] text-[14px] hover:bg-[#f2eee5]">
              <GitCompare size={13} /> Compare
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// Log–log scatter of nodes vs edges
function SizeScatter({ events, selected, onSelect }) {
  const W = 560, H = 330, m = { t: 12, r: 16, b: 44, l: 56 };
  const lx = (v) => Math.log10(v), xs = events.map((e) => lx(e.n_nodes)), ys = events.map((e) => lx(e.n_edges));
  const x0 = Math.floor(Math.min(...xs) * 2) / 2, x1 = Math.ceil(Math.max(...xs) * 2) / 2;
  const y0 = Math.floor(Math.min(...ys) * 2) / 2, y1 = Math.ceil(Math.max(...ys) * 2) / 2;
  const X = (v) => m.l + ((v - x0) / (x1 - x0)) * (W - m.l - m.r), Y = (v) => H - m.b - ((v - y0) / (y1 - y0)) * (H - m.t - m.b);
  const ticks = (a, b) => [100, 300, 1000, 3000, 10000, 30000].filter((t) => lx(t) >= a && lx(t) <= b);
  const fmtT = (t) => (t >= 1000 ? `${t / 1000}k` : t);
  return (
    <div className="chart-frame">
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto" role="img" aria-label="Scatter plot of node count against edge count for every event, log scales">
        {ticks(x0, x1).map((t) => <g key={`x${t}`}><line x1={X(lx(t))} x2={X(lx(t))} y1={m.t} y2={H - m.b} stroke="#e4dfd3" /><text x={X(lx(t))} y={H - m.b + 16} textAnchor="middle" fontSize="11" fill="#5e5a52" fontFamily="var(--font-mono)">{fmtT(t)}</text></g>)}
        {ticks(y0, y1).map((t) => <g key={`y${t}`}><line x1={m.l} x2={W - m.r} y1={Y(lx(t))} y2={Y(lx(t))} stroke="#e4dfd3" /><text x={m.l - 8} y={Y(lx(t)) + 4} textAnchor="end" fontSize="11" fill="#5e5a52" fontFamily="var(--font-mono)">{fmtT(t)}</text></g>)}
        <text x={(W + m.l) / 2} y={H - 6} textAnchor="middle" fontSize="11" fill="#15263a" fontFamily="var(--font-mono)">Nodes |V|</text>
        <text x={14} y={(H - m.b) / 2} textAnchor="middle" fontSize="11" fill="#15263a" fontFamily="var(--font-mono)" transform={`rotate(-90 14 ${(H - m.b) / 2})`}>Edges |E|</text>
        {events.map((e) => {
          const on = e.i === selected;
          return (
            <circle key={e.i} cx={X(lx(e.n_nodes))} cy={Y(lx(e.n_edges))} r={on ? 7 : 4.2}
              fill={e.label === 1 ? PAGE.campaign : PAGE.comparison} fillOpacity={on ? 1 : 0.7}
              stroke={on ? "#15263a" : "#faf8f5"} strokeWidth={on ? 2 : 1} className="cursor-pointer"
              onClick={() => onSelect(e.i)}>
              <title>{`${e.name}: ${e.n_nodes} nodes, ${e.n_edges} edges`}</title>
            </circle>
          );
        })}
      </svg>
      <Legend />
    </div>
  );
}

function MetricStrip({ events, metric, selected, onSelect }) {
  const W = 560, H = 230, m = { t: 16, r: 18, b: 40, l: 104 };
  const t = (v) => (metric.log ? Math.log10(v) : v);
  const vals = events.map((e) => t(metric.get(e)));
  let a = Math.min(...vals), b = Math.max(...vals);
  if (a === b) { a -= 1; b += 1; }
  const pad = (b - a) * 0.04;
  const X = (v) => m.l + ((t(v) - (a - pad)) / (b - a + 2 * pad)) * (W - m.l - m.r);
  const rowsY = { 1: 70, 0: 160 };
  // deterministic vertical jitter by event index
  const jit = (i) => ((((i * 2654435761) >>> 0) % 1000) / 1000 - 0.5) * 44;
  const axis = metric.log ? [100, 300, 1000, 3000, 10000].filter((x) => Math.log10(x) >= a - pad && Math.log10(x) <= b + pad) : [0, 1, 2, 3, 4].map((k) => a + (k * (b - a)) / 4);
  const meds = { 1: median(events.filter((e) => e.label === 1).map(metric.get)), 0: median(events.filter((e) => e.label === 0).map(metric.get)) };
  const fmtV = (v) => (metric.log ? (v >= 1000 ? `${(v / 1000).toFixed(v >= 10000 ? 0 : 1)}k` : Math.round(v)) : metric.key === "coreness_max" ? Math.round(v) : v.toFixed(2));
  return (
    <div className="chart-frame">
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto" role="img" aria-label={`${metric.label} for every event, by label`}>
        {axis.map((v) => <g key={v}><line x1={X(v)} x2={X(v)} y1={m.t} y2={H - m.b} stroke="#e4dfd3" /><text x={X(v)} y={H - m.b + 16} textAnchor="middle" fontSize="11" fill="#5e5a52" fontFamily="var(--font-mono)">{fmtV(v)}</text></g>)}
        {[1, 0].map((l) => (
          <g key={l}>
            <text x={m.l - 12} y={rowsY[l] + 4} textAnchor="end" fontSize="12" fill={l === 1 ? PAGE.campaign : PAGE.comparison} fontFamily="var(--font-mono)" fontWeight="bold">{l === 1 ? "Campaign" : "Comparison"}</text>
            <line x1={X(meds[l])} x2={X(meds[l])} y1={rowsY[l] - 30} y2={rowsY[l] + 30} stroke={l === 1 ? PAGE.campaign : PAGE.comparison} strokeWidth="2" />
            <text x={X(meds[l])} y={rowsY[l] - 34} textAnchor="middle" fontSize="10.5" fill="#3c3a37" fontFamily="var(--font-mono)">median {fmtV(meds[l])}</text>
          </g>
        ))}
        {events.map((e) => {
          const on = e.i === selected;
          return (
            <circle key={e.i} cx={X(metric.get(e))} cy={rowsY[e.label] + jit(e.i) * 0.5} r={on ? 6.5 : 3.8}
              fill={e.label === 1 ? PAGE.campaign : PAGE.comparison} fillOpacity={on ? 1 : 0.55} stroke={on ? "#15263a" : "none"} strokeWidth="2"
              className="cursor-pointer" onClick={() => onSelect(e.i)}>
              <title>{`${e.name}: ${metric.label} ${fmtV(metric.get(e))}`}</title>
            </circle>
          );
        })}
        <text x={(W + m.l) / 2} y={H - 6} textAnchor="middle" fontSize="11" fill="#15263a" fontFamily="var(--font-mono)">{metric.label}{metric.log ? " (log scale)" : ""}</text>
      </svg>
    </div>
  );
}

export function Legend() {
  return (
    <div className="mt-3 flex flex-wrap gap-x-5 gap-y-1 text-[13px] font-mono text-[#4a4740]">
      <span className="inline-flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full" style={{ background: PAGE.campaign }} />Campaign (dataset label)</span>
      <span className="inline-flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full" style={{ background: PAGE.comparison }} />Comparison (dataset label)</span>
    </div>
  );
}
