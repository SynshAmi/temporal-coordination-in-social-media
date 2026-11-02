import React, { useMemo, useState } from "react";
import { Network, Search } from "lucide-react";
import NetworkCanvas from "./NetworkCanvas";
import { useEventGraph } from "./hooks";
import { EventCard } from "./DatasetOverview";
import { EventSelect, StatRows, Loading, ErrorBox, Hint, ResearchNotes } from "./ui";
import { nodeNotes } from "./notes";
import { CANVAS, LABEL_COLOR } from "./palette";
import { topByDegree } from "./graph";
import { int } from "../lib/fmt";

const EDGE_MODES = [
  ["all", "All edges"],
  ["reciprocal", "Reciprocated only"],
  ["selected", "Selected node's edges"],
];

export default function Playground({ index, eventIdx, onPickEvent, go, autoLoad }) {
  const event = index.events.find((e) => e.i === eventIdx) || null;
  const [requestedFor, setRequestedFor] = useState(null);
  const requested = !!autoLoad || (event != null && requestedFor === event.i);
  const G = useEventGraph(event, requested);

  return (
    <div className="space-y-6">
      <div className="max-w-[420px]">
        <EventSelect id="pg-event" events={index.events} value={eventIdx} onChange={onPickEvent} label="Event" />
      </div>

      {!event && <div className="border border-dashed border-[#cfc8b8] p-8 text-sm text-[#5e5a52] bg-[#faf8f5]">Choose an event to explore its network.</div>}

      {event && !requested && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          <div className="lg:col-span-5"><EventCard e={event} /></div>
          <div className="lg:col-span-7 graph-canvas min-h-[320px] flex flex-col items-center justify-center gap-4 p-8 text-center">
            <Network size={28} className="text-[#8fa3b8]" />
            <p className="text-sm text-[#d8dee6] max-w-[44ch]">
              {int(event.n_nodes)} nodes and {int(event.n_edges)} directed edges. The graph file is loaded and laid out on request.
            </p>
            <button type="button" onClick={() => setRequestedFor(event.i)}
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-[#f4efe6] text-[#15263a] text-sm font-medium hover:bg-white transition-colors">
              <Network size={15} /> Explore network
            </button>
          </div>
        </div>
      )}

      {event && requested && <Viewer key={event.i} event={event} G={G} go={go} />}

      <ResearchNotes index={index} items={[
        ...nodeNotes(false),
        ["Loading", "Each graph file is downloaded only when you open its network, and is then cached for the session along with its layout."],
      ]} />
    </div>
  );
}

function Viewer({ event, G, go }) {
  const [selected, setSelected] = useState(null);
  const [hubsOn, setHubsOn] = useState(false);
  const [labels, setLabels] = useState(false);
  const [edgeMode, setEdgeMode] = useState("all");
  const [goto, setGoto] = useState("");

  const hubs = useMemo(() => (hubsOn && G.d ? new Set(topByDegree(G.d, 10)) : null), [hubsOn, G.d]);

  if (G.status === "error") return <ErrorBox error={G.error} />;
  if (G.status !== "ready")
    return (
      <div className="graph-canvas h-[420px] flex items-center justify-center">
        <div className="bg-[#f4efe6] px-4 py-3"><Loading>{G.phase === "layout" ? `Computing layout for ${int(event.n_nodes)} nodes…` : "Loading graph…"}</Loading></div>
      </div>
    );

  const jump = (e) => {
    e.preventDefault();
    const v = Number(goto.replace("#", ""));
    if (Number.isInteger(v) && v >= 0 && v < G.g.n && G.d.present[v]) setSelected(v);
  };

  return (
    <div className="grid grid-cols-1 xl:grid-cols-12 gap-5 items-start">
      <div className="xl:col-span-8 space-y-3">
        {/* Controls */}
        <div className="flex flex-wrap items-center gap-2 text-xs font-mono">
          <button type="button" onClick={() => setHubsOn((h) => !h)} aria-pressed={hubsOn}
            className={`px-3 py-1.5 border ${hubsOn ? "bg-[#15263a] text-white border-[#15263a]" : "bg-white border-[#d8d3c5] text-[#3c3a37] hover:bg-[#ede9df]"}`}
            title="Highlight the ten nodes with the highest total degree">Top-10 by degree</button>
          <button type="button" onClick={() => setLabels((l) => !l)} aria-pressed={labels}
            className={`hidden sm:inline-block px-3 py-1.5 border ${labels ? "bg-[#15263a] text-white border-[#15263a]" : "bg-white border-[#d8d3c5] text-[#3c3a37] hover:bg-[#ede9df]"}`}
            title="Show node indices for highlighted nodes (always shown for the selected node)">Labels</button>
          <select value={edgeMode} onChange={(e) => setEdgeMode(e.target.value)} aria-label="Edge filter"
            className="bg-white border border-[#d8d3c5] px-2 py-1.5 text-[#15263a]">
            {EDGE_MODES.map(([k, t]) => <option key={k} value={k}>{t}</option>)}
          </select>
          <form onSubmit={jump} className="flex items-center ml-auto">
            <label className="relative">
              <span className="sr-only">Find node by index</span>
              <Search size={12} className="absolute left-2 top-1/2 -translate-y-1/2 text-[#9a948a]" />
              <input value={goto} onChange={(e) => setGoto(e.target.value)} placeholder="Node #" inputMode="numeric"
                className="w-24 pl-6 pr-2 py-1.5 border border-[#d8d3c5] bg-white focus:outline-none focus:border-[#23527c]" />
            </label>
          </form>
        </div>

        <NetworkCanvas g={G.g} d={G.d} pos={G.pos} label={event.label} selected={selected} onSelect={setSelected}
          hubs={hubs} edgeMode={edgeMode} showLabels={labels} onRelayout={G.relayout}
          banner={`Full graph · ${event.name}`} className="h-[62vh] min-h-[380px] max-h-[720px]" />
        <EncodingLegend label={event.label} />
        <p className="text-[11px] font-mono text-[#757065]">
          Loaded in {Math.round(G.tLoad)} ms · layout {G.layoutMs} ms ({G.iterations} ForceAtlas2 iterations, in a background worker) · self-loops ({event.n_self_loops}) are counted but not drawn.
        </p>
      </div>
      <aside className="xl:col-span-4 space-y-4">
        <NodeInspector G={G} v={selected} onSelect={setSelected} />
        {go && (
          <div className="grid grid-cols-2 gap-2">
            <button type="button" onClick={() => go("sampling", event.i)} disabled={!event.budgets.length}
              className="px-3 py-2 bg-white border border-[#15263a] text-[#15263a] text-xs hover:bg-[#f2eee5] disabled:opacity-40">Open in sampling lab</button>
            <button type="button" onClick={() => go("compare", event.i)}
              className="px-3 py-2 bg-white border border-[#15263a] text-[#15263a] text-xs hover:bg-[#f2eee5]">Compare with another event</button>
          </div>
        )}
      </aside>
    </div>
  );
}

export function NodeInspector({ G, v, onSelect, sampled = false }) {
  const { d, g } = G;
  const rank = useMemo(() => {
    if (v == null) return null;
    const t = d.indeg[v] + d.outdeg[v];
    let r = 1;
    for (let u = 0; u < d.n; u++) if (d.present[u] && d.indeg[u] + d.outdeg[u] > t) r++;
    return r;
  }, [d, v]);
  const nCount = useMemo(() => Array.from(d.present).reduce((a, b) => a + b, 0), [d]);

  if (v == null)
    return (
      <div className="bg-white border border-[#dcd7ca] p-5 space-y-3">
        <div className="font-mono text-[11px] font-bold uppercase tracking-wider text-[#15263a]">{sampled ? "This observation" : "This graph"}</div>
        <StatRows rows={[
          ["Nodes", int(nCount)],
          ["Directed edges", int(d.m)],
          ["Reciprocated pairs", int(d.recipPairs)],
          ["Weak components", int(d.compSize.size)],
          ["Max in / out degree", `${Math.max(...d.indeg)} / ${Math.max(...d.outdeg)}`],
        ]} />
        <p className="text-[13px] text-[#5e5a52] leading-relaxed">Select a node, or hover for a quick summary.</p>
      </div>
    );

  const list = (start, adj) => {
    const out = [];
    for (let a = start[v]; a < start[v + 1]; a++) out.push(adj[a]);
    return out.sort((x, y) => d.indeg[y] + d.outdeg[y] - (d.indeg[x] + d.outdeg[x]) || x - y);
  };
  const outs = list(d.outStart, d.outAdj), ins = list(d.inStart, d.inAdj);
  const core = G.core ? G.core[v] : g.core ? g.core[v] : null;
  const chips = (arr) => (
    <div className="flex flex-wrap gap-1 mt-1.5">
      {arr.slice(0, 12).map((u) => (
        <button key={u} type="button" onClick={() => onSelect(u)} title={`in ${d.indeg[u]} · out ${d.outdeg[u]}`}
          className="px-1.5 py-0.5 border border-[#d8d3c5] bg-[#faf8f5] text-[11px] font-mono text-[#15263a] hover:border-[#23527c]">#{u}</button>
      ))}
      {arr.length > 12 && <span className="text-[11px] font-mono text-[#757065] self-center">+{arr.length - 12} more</span>}
      {!arr.length && <span className="text-[11px] font-mono text-[#9a948a]">none</span>}
    </div>
  );

  return (
    <div className="bg-white border border-[#dcd7ca] border-t-2 border-t-[#15263a] p-5 space-y-4">
      <div className="flex items-start justify-between gap-2">
        <div>
          <div className="font-mono text-[11px] uppercase tracking-wider text-[#757065]">Selected node</div>
          <div className="font-serif text-2xl text-[#15263a]">#{v}</div>
        </div>
        <button type="button" onClick={() => onSelect(null)} className="text-xs font-mono text-[#23527c] underline underline-offset-4">Clear</button>
      </div>
      <StatRows rows={[
        ["In-degree", int(d.indeg[v]), "Directed edges pointing to this node (a self-loop counts once)."],
        ["Out-degree", int(d.outdeg[v]), "Directed edges leaving this node."],
        ["Total degree", int(d.indeg[v] + d.outdeg[v])],
        ["Distinct in / out neighbours", `${ins.length} / ${outs.length}`],
        ["Reciprocated partners", int(d.recip[v]), "Neighbours linked in both directions."],
        ["Self-loop", d.loops[v] ? "yes" : "no"],
        core != null && ["Core number", core, sampled ? "Computed on this observation, with the paper's convention." : "Undirected projection without self-loops, as in the paper."],
        ["Component size", int(d.compSize.get(d.comp[v]) || 0), "Nodes in this node's weakly connected component."],
        ["Degree rank", `${rank} of ${int(nCount)}`],
      ]} />
      <div>
        <div className="text-[11px] font-mono uppercase tracking-wider" style={{ color: "#a0672a" }}>Incoming from ({ins.length})</div>
        {chips(ins)}
      </div>
      <div>
        <div className="text-[11px] font-mono uppercase tracking-wider text-[#15263a]">Outgoing to ({outs.length})</div>
        {chips(outs)}
      </div>
    </div>
  );
}

export function EncodingLegend({ label, sampled = false }) {
  const dot = (c, r = 5) => <span className="inline-block rounded-full shrink-0" style={{ width: r * 2, height: r * 2, background: c }} />;
  const line = (c) => <span className="inline-block w-5 h-[2px] shrink-0" style={{ background: c }} />;
  return (
    <div className="flex flex-wrap gap-x-5 gap-y-1.5 text-[11px] font-mono text-[#4a4740]">
      <span className="inline-flex items-center gap-1.5">{dot(LABEL_COLOR[label])}{label === 1 ? "Campaign" : "Comparison"} event (dataset label)</span>
      <span className="inline-flex items-center gap-1.5">Size ∝ √degree</span>
      <span className="inline-flex items-center gap-1.5">{dot(CANVAS.selected)}<span className="-ml-0.5">selected</span></span>
      <span className="inline-flex items-center gap-1.5">{line(CANVAS.edgeOut)}outgoing</span>
      <span className="inline-flex items-center gap-1.5">{line(CANVAS.edgeIn)}incoming</span>
      <span className="inline-flex items-center gap-1.5">{dot(CANVAS.hub)}top-10 degree</span>
      {sampled && <span className="inline-flex items-center gap-1.5">{dot(CANVAS.ghost, 3)}not in this observation</span>}
      <Hint text="Positions come from a force-directed layout: a visual arrangement, not physical distance. Visual clusters do not establish coordination." />
    </div>
  );
}

