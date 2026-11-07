import React, { useMemo, useState } from "react";
import { FlaskConical } from "lucide-react";
import NetworkCanvas from "./NetworkCanvas";
import { useEventGraph, useAsync } from "./hooks";
import { loadSamples } from "./data";
import { computeLayout } from "./layout";
import { describe, subgraph, coreNumbers } from "./graph";
import { NodeInspector, EncodingLegend } from "./Playground";
import { EventSelect, Loading, ErrorBox, Hint, ResearchNotes } from "./ui";
import { nodeNotes } from "./notes";
import { FEATURE_ROWS, fmtFeature } from "./features";
import { PAGE } from "./palette";
import { int, sg } from "../lib/fmt";

// Remount per event, so regime, seed and selection start fresh for each one
export default function SamplingLab(props) {
  return <Lab key={props.eventIdx ?? "none"} {...props} />;
}

function Lab({ index, eventIdx, onPickEvent }) {
  const event = index.events.find((e) => e.i === eventIdx) || null;
  const eligible = event && event.budgets.length > 0;
  const [regime, setRegime] = useState(event?.budgets[0] ? String(event.budgets[0]) : "full");
  const [seedIdx, setSeedIdx] = useState(0);
  const [layoutMode, setLayoutMode] = useState("shared");
  const [showDropped, setShowDropped] = useState(true);
  const [selectedRaw, setSelected] = useState(null);

  const G = useEventGraph(event, !!eligible);
  const samples = useAsync(eligible ? `samples-${event.i}` : null, async () => ({ s: await loadSamples(event) }));

  const K = regime === "full" ? null : Number(regime);
  const obs = samples.status === "ready" && K ? samples.s.budgets[String(K)] : null;

  // The displayed observation: sampled edge indices -> subgraph description, masks, core numbers
  const view = useMemo(() => {
    if (G.status !== "ready") return null;
    if (!obs) return { d: G.d, edgeMask: null, nodeMask: null, core: G.g.core, edgeIdx: null };
    const edgeIdx = obs.edges[seedIdx];
    const sub = subgraph(G.g, edgeIdx);
    const d = describe(sub);
    const edgeMask = new Uint8Array(G.g.src.length);
    edgeIdx.forEach((k) => (edgeMask[k] = 1));
    return { d, edgeMask, nodeMask: d.present, core: coreNumbers(d), edgeIdx, sub };
  }, [G.status, G.g, G.d, obs, seedIdx]);

  // Optional layout of the observation on its own (cached per event, budget and seed)
  const ownKey = layoutMode === "own" && view?.sub ? `e${event.i}-K${K}-s${seedIdx}` : null;
  const own = useAsync(ownKey, async () => {
    const nodes = [];
    view.d.present.forEach((p, v) => p && nodes.push(v));
    return { pos: (await computeLayout(ownKey, view.sub, { nodes })).pos };
  });
  const ownPos = own.status === "ready" ? own.pos : null;
  // A selection outside the current observation is dropped
  const selected = selectedRaw != null && view && view.d.present[selectedRaw] ? selectedRaw : null;

  if (!event)
    return (
      <div className="space-y-6">
        <div className="max-w-[420px]"><EventSelect id="sl-event" events={index.events} value={null} onChange={onPickEvent} filter={(e) => e.budgets.length} label="Event (at least 250 edges)" /></div>
        <div className="border border-dashed border-[#cfc8b8] p-8 text-[16px] text-[#5e5a52] bg-[#faf8f5]">Choose an event to compare its full graph with the Study 2 observations of it.</div>
        <SamplingNotes index={index} />
      </div>
    );

  const pos = layoutMode === "own" && K ? ownPos : G.pos;
  const feats = obs ? obs.features[seedIdx] : null;
  const banner = K ? `Observation · K = ${K} edges · seed ${obs ? obs.seeds[seedIdx] : ""} · not the complete graph` : `Full graph · ${int(event.n_edges)} edges`;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,420px)_1fr] gap-4 items-end">
        <EventSelect id="sl-event" events={index.events} value={eventIdx} onChange={onPickEvent} filter={(e) => e.budgets.length} label="Event (at least 250 edges)" />
        {!eligible && <p className="text-[16px] text-[#8f2626]">This event has fewer than 250 edges, so Study 2 drew no observations of it.</p>}
      </div>

      {eligible && (
        <>
          {/* Regime switch */}
          <div className="flex flex-wrap items-end gap-x-6 gap-y-3">
            <div>
              <div className="text-[13px] font-mono text-[#757065] mb-1">Observation regime</div>
              <div className="inline-flex border border-[#15263a] bg-white text-[14px] font-mono" role="radiogroup" aria-label="Observation regime">
                {["full", ...index.budgets.map(String)].map((r) => {
                  const ok = r === "full" || event.budgets.includes(Number(r));
                  return (
                    <button key={r} type="button" role="radio" aria-checked={regime === r} disabled={!ok} onClick={() => setRegime(r)}
                      title={ok ? "" : `This event has fewer than ${r} edges`}
                      className={`px-3.5 py-2 border-r last:border-r-0 border-[#15263a] ${regime === r ? "bg-[#15263a] text-white" : "text-[#15263a] hover:bg-[#ede9df]"} disabled:text-[#b5ad9e] disabled:cursor-not-allowed disabled:hover:bg-white`}>
                      {r === "full" ? "Full graph" : `K = ${r}`}
                    </button>
                  );
                })}
              </div>
            </div>
            {K && obs && (
              <label className="flex flex-col gap-1">
                <span className="text-[13px] font-mono text-[#757065]">Sampling seed</span>
                <select value={seedIdx} onChange={(e) => setSeedIdx(Number(e.target.value))} className="bg-white border border-[#d8d3c5] px-2 py-2 text-[14px] font-mono text-[#15263a]">
                  {obs.seeds.map((s, k) => <option key={s} value={k}>Seed {s} ({k + 1} of {obs.seeds.length})</option>)}
                </select>
              </label>
            )}
            {K && (
              <div className="flex flex-wrap gap-2 text-[14px] font-mono">
                <div className="inline-flex border border-[#d8d3c5] bg-white p-0.5" role="group" aria-label="Node positions">
                  {[["shared", "Full-graph positions"], ["own", "Re-layout observation"]].map(([k, t]) => (
                    <button key={k} type="button" onClick={() => setLayoutMode(k)} aria-pressed={layoutMode === k}
                      className={`px-2.5 py-1.5 ${layoutMode === k ? "bg-[#15263a] text-white" : "text-[#3c3a37] hover:bg-[#ede9df]"}`}>{t}</button>
                  ))}
                </div>
                {layoutMode === "shared" && (
                  <button type="button" onClick={() => setShowDropped((s) => !s)} aria-pressed={showDropped}
                    className={`px-3 py-1.5 border ${showDropped ? "bg-[#15263a] text-white border-[#15263a]" : "bg-white border-[#d8d3c5] text-[#3c3a37]"}`}>Show what is not observed</button>
                )}
              </div>
            )}
          </div>

          {(G.status === "error" || samples.status === "error") && <ErrorBox error={G.error || samples.error} />}
          {(G.status === "loading" || samples.status === "loading" || G.status === "idle") && (
            <div className="graph-canvas h-[420px] flex items-center justify-center"><div className="bg-[#f4efe6] px-4 py-3"><Loading>{G.phase === "layout" ? `Computing full-graph layout (${int(event.n_nodes)} nodes)…` : "Loading graph and observations…"}</Loading></div></div>
          )}

          {G.status === "ready" && view && (
            <div className="grid grid-cols-1 xl:grid-cols-12 gap-5 items-start">
              <div className="xl:col-span-8 space-y-3">
                {pos ? (
                  <NetworkCanvas g={G.g} d={view.d} pos={pos} edgeMask={view.edgeMask} nodeMask={view.nodeMask}
                    showDropped={K && layoutMode === "shared" && showDropped} label={event.label}
                    selected={selected} onSelect={setSelected} banner={banner} className="h-[60vh] min-h-[380px] max-h-[680px]" />
                ) : (
                  <div className="graph-canvas h-[60vh] min-h-[380px] flex items-center justify-center"><div className="bg-[#f4efe6] px-4 py-3"><Loading>Laying out this observation…</Loading></div></div>
                )}
                <EncodingLegend label={event.label} sampled={!!K} />
              </div>
              <aside className="xl:col-span-4 space-y-4">
                <Comparison event={event} K={K} feats={feats} view={view} />
                {obs && <SeedStrip samples={samples.s} event={event} K={K} seedIdx={seedIdx} onSeed={setSeedIdx} />}
                <NodeInspector G={{ ...G, d: view.d, core: view.core }} event={event} v={selected} onSelect={setSelected} sampled={!!K} />
              </aside>
            </div>
          )}
        </>
      )}

      <SamplingNotes index={index} />
    </div>
  );
}

function SamplingNotes({ index }) {
  return (
    <ResearchNotes index={index} items={[
      ["Study 2 observations", `Each view keeps K edges drawn uniformly without replacement, and only the nodes they touch. These are the exact views used in the paper (${index.n_seeds} seeds per budget), regenerated with the pipeline's seeds and checked against its stored features (${int(index.verification.views_regenerated_and_matched)} views match).`],
      ["A partial observation", "A view is a partial observation, never the complete graph. Its statistics describe what a fixed edge budget reveals, and differences from the full graph reflect sampling, not a change in the event."],
      ["Full-graph positions", "Nodes keep their full-graph positions, so you can see which parts of the graph an observation touches. Faint nodes and red-tinted edges are in the full graph but not in the observation."],
      ["Re-laid-out observations", "The observation is laid out on its own, as if it were the only data available. Its shape can look very different from the full graph's."],
      ["Values shown", "Full-graph features come from the paper's corrected run and each view's features from its stored Study 2 values; node-level values in the inspector are computed on the displayed observation with the paper's conventions."],
      ...nodeNotes(true),
    ]} />
  );
}

function Comparison({ event, K, feats, view }) {
  const nObs = feats ? feats.n_nodes : event.n_nodes;
  const rows = [
    ["Nodes", int(event.n_nodes), int(nObs), K ? `${((100 * nObs) / event.n_nodes).toFixed(0)}% retained` : null, "In an observation this is N_K, the number of distinct sampled endpoints."],
    ["Directed edges", int(event.n_edges), K ? int(K) : int(event.n_edges), K ? `${((100 * K) / event.n_edges).toFixed(0)}% retained` : null],
    ...FEATURE_ROWS.map(([k, t, h]) => [t, fmtFeature(k, event.features[k]), feats ? fmtFeature(k, feats[k]) : fmtFeature(k, event.features[k]), feats && !k.startsWith("coreness") && k !== "density" ? sg(feats[k] - event.features[k]) : null, h]),
  ];
  return (
    <div className="bg-white border border-[#dcd7ca] p-5">
      <div className="flex items-center gap-2 font-mono text-[13px] font-semibold text-[#15263a] mb-3">
        <FlaskConical size={13} /> Full graph vs {K ? `K = ${K}` : "full graph"}
      </div>
      <table className="w-full text-[15px]">
        <thead className="text-[12.5px] font-mono text-[#757065]">
          <tr><th className="text-left font-medium pb-1.5">Measure</th><th className="text-right font-medium pb-1.5">Full</th><th className="text-right font-medium pb-1.5">{K ? "Observed" : "—"}</th></tr>
        </thead>
        <tbody className="divide-y divide-[#eee9df]">
          {rows.map(([t, a, b, delta, h]) => (
            <tr key={t}>
              <td className="py-1.5 text-[#4a4740]">{t}{h && <Hint text={h} />}{delta && <div className="text-[12.5px] font-mono text-[#9a948a]">{delta}</div>}</td>
              <td className="py-1.5 text-right font-mono text-[#15263a]">{a}</td>
              <td className="py-1.5 text-right font-mono" style={{ color: K ? PAGE.campaign : "#9a948a" }}>{K ? b : ""}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="mt-3 text-[13px] font-mono text-[#757065]">Self-loops in this view: {int(view.d.loops.reduce((a, b) => a + b, 0))}</p>
    </div>
  );
}

// N_K across the ten seeds at each budget (stored features)
function SeedStrip({ samples, event, K, seedIdx, onSeed }) {
  const ks = event.budgets.map(String);
  const W = 320, H = 10 + ks.length * 40, ml = 64, mr = 14;
  const range = (k) => { const v = samples.budgets[k].features.map((f) => f.n_nodes); return [Math.min(...v), Math.max(...v)]; };
  return (
    <div className="bg-white border border-[#dcd7ca] p-5">
      <div className="font-mono text-[13px] font-semibold text-[#15263a] mb-1">Sampled endpoint count N<sub>K</sub> by seed</div>
      <p className="text-[14px] text-[#5e5a52] mb-2">The count that remains in a fixed-budget view (Study 2): its expectation is set by the full graph's size and degree sequence. Each row has its own scale (minimum to maximum over the ten seeds); select a point on the current budget's row to switch seed.</p>
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto" role="img" aria-label="Sampled endpoint count for each seed at each budget">
        {ks.map((k, r) => {
          const y = 16 + r * 40;
          const [lo, hi] = range(k);
          const X = (v) => ml + 8 + ((v - lo) / Math.max(1, hi - lo)) * (W - ml - mr - 16);
          return (
            <g key={k}>
              <text x={ml - 8} y={y + 4} textAnchor="end" fontSize="11" fill="#15263a" fontFamily="var(--font-mono)">K = {k}</text>
              <line x1={ml} x2={W - mr} y1={y} y2={y} stroke="#e4dfd3" />
              {samples.budgets[k].features.map((f, s) => {
                const on = String(K) === k && s === seedIdx;
                return (
                  <circle key={s} cx={X(f.n_nodes)} cy={y} r={on ? 6 : 4} fill={on ? PAGE.campaign : PAGE.comparison} fillOpacity={on ? 1 : 0.5}
                    stroke={on ? "#15263a" : "none"} strokeWidth="1.5" className={String(K) === k ? "cursor-pointer" : ""}
                    onClick={() => String(K) === k && onSeed(s)}>
                    <title>{`K = ${k}, seed ${samples.budgets[k].seeds[s]}: N_K = ${f.n_nodes}`}</title>
                  </circle>
                );
              })}
              <text x={ml} y={y + 18} fontSize="10" fill="#757065" fontFamily="var(--font-mono)">{int(lo)}</text>
              <text x={W - mr} y={y + 18} textAnchor="end" fontSize="10" fill="#757065" fontFamily="var(--font-mono)">{int(hi)}</text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
