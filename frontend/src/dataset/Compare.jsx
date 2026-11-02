import React, { useState } from "react";
import { GitCompare } from "lucide-react";
import NetworkCanvas from "./NetworkCanvas";
import { useEventGraph } from "./hooks";
import { EventSelect, LabelBadge, Loading, ErrorBox, Hint, ResearchNotes } from "./ui";
import { fmtFeature } from "./features";
import { PAGE } from "./palette";
import { int } from "../lib/fmt";

// kind "count": notable if one is at least twice the other; "share": notable if they differ by 0.1 or more
const METRICS = [
  { t: "Nodes", get: (e) => e.n_nodes, kind: "count", h: "Distinct nodes in the graph." },
  { t: "Directed edges", get: (e) => e.n_edges, kind: "count", h: "Engagement edges between nodes." },
  { t: "Edges per node", get: (e) => e.n_edges / e.n_nodes, kind: "count", fmt: (v) => v.toFixed(2), h: "Average out-degree (equivalently, in-degree)." },
  { t: "Self-loops", get: (e) => e.n_self_loops, kind: "count" },
  { t: "Max in-degree", get: (e) => e.max_in, kind: "count", h: "Largest number of edges pointing to one node." },
  { t: "Max out-degree", get: (e) => e.max_out, kind: "count", h: "Largest number of edges leaving one node." },
  { t: "Weak components", get: (e) => e.n_wcc, kind: "count", h: "Separate pieces of the graph when edge direction is ignored." },
  { t: "Largest component", get: (e) => e.features.largest_wcc_fraction, kind: "share", key: "largest_wcc_fraction", h: "Fraction of nodes in the biggest piece." },
  { t: "Reciprocity", get: (e) => e.features.reciprocity, kind: "share", key: "reciprocity", h: "Share of edges answered by an edge in the opposite direction." },
  { t: "In-degree Gini", get: (e) => e.features.indegree_gini, kind: "share", key: "indegree_gini", h: "How concentrated incoming edges are (0 even, 1 all on one node)." },
  { t: "Out-degree Gini", get: (e) => e.features.outdegree_gini, kind: "share", key: "outdegree_gini", h: "How concentrated outgoing edges are." },
  { t: "Median core number", get: (e) => e.features.coreness_median, kind: "count", key: "coreness_median", h: "Typical depth of a node in the k-core decomposition." },
  { t: "Max core number", get: (e) => e.features.coreness_max, kind: "count", key: "coreness_max", h: "Depth of the most tightly interlinked group." },
];

const notable = (m, a, b) => (m.kind === "share" ? Math.abs(a - b) >= 0.1 : Math.max(a, b) >= 2 * Math.max(Math.min(a, b), 1e-9) && Math.max(a, b) > 0);

export default function Compare({ index, a, b, onPick }) {
  const A = index.events.find((e) => e.i === a) || null, B = index.events.find((e) => e.i === b) || null;
  const [loadedPair, setLoadedPair] = useState(null);
  const load = loadedPair === `${a}-${b}`;
  const setLoad = () => setLoadedPair(`${a}-${b}`);

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <EventSelect id="cmp-a" events={index.events} value={a} onChange={(v) => onPick(v, b)} label="Event A" />
        <EventSelect id="cmp-b" events={index.events} value={b} onChange={(v) => onPick(a, v)} label="Event B" />
      </div>

      {!(A && B) && <div className="border border-dashed border-[#cfc8b8] p-8 text-sm text-[#5e5a52] bg-[#faf8f5]">Choose two events to compare their size and structure.</div>}

      {A && B && (
        <>
          <div className="bg-white border border-[#dcd7ca] overflow-x-auto">
            <table className="w-full text-sm min-w-[560px]">
              <thead className="bg-[#f4efe6] text-[11px] font-mono uppercase tracking-wider text-[#757065]">
                <tr>
                  <th className="text-left font-medium px-4 py-2.5">Measure (full graph)</th>
                  <th className="text-right font-medium px-3 py-2.5"><span className="inline-flex flex-col items-end gap-1"><span className="normal-case font-sans text-[13px] text-[#15263a] break-all">A · {A.name}</span><LabelBadge label={A.label} small /></span></th>
                  <th className="text-right font-medium px-3 py-2.5"><span className="inline-flex flex-col items-end gap-1"><span className="normal-case font-sans text-[13px] text-[#15263a] break-all">B · {B.name}</span><LabelBadge label={B.label} small /></span></th>
                  <th className="text-left font-medium px-4 py-2.5 w-[34%]">Relative size</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#eee9df]">
                {METRICS.map((m) => {
                  const va = m.get(A), vb = m.get(B), mx = Math.max(va, vb, 1e-9), big = notable(m, va, vb);
                  const f = (v) => (m.fmt ? m.fmt(v) : m.key ? fmtFeature(m.key, v) : int(v));
                  return (
                    <tr key={m.t} className={big ? "bg-[#fbf6ec]" : ""}>
                      <td className="px-4 py-2 text-[#3c3a37]">
                        {m.t}{m.h && <Hint text={m.h} />}
                        {big && <span className="ml-2 text-[10px] font-mono uppercase tracking-wider text-[#a0672a]" title="Counts differing by a factor of two or more, or fractions differing by at least 0.1; a reading aid, not a statistical test">notable difference</span>}
                      </td>
                      <td className="px-3 py-2 text-right font-mono text-[13px] text-[#15263a]">{f(va)}</td>
                      <td className="px-3 py-2 text-right font-mono text-[13px] text-[#15263a]">{f(vb)}</td>
                      <td className="px-4 py-2">
                        <div className="space-y-1" aria-hidden="true">
                          <div className="h-1.5" style={{ width: `${(100 * va) / mx}%`, background: A.label === 1 ? PAGE.campaign : PAGE.comparison }} />
                          <div className="h-1.5 opacity-60" style={{ width: `${(100 * vb) / mx}%`, background: B.label === 1 ? PAGE.campaign : PAGE.comparison }} />
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          {!load ? (
            <div className="graph-canvas p-8 flex flex-col sm:flex-row items-center justify-center gap-4 text-center">
              <p className="text-sm text-[#d8dee6]">Load both graphs ({int(A.n_nodes + B.n_nodes)} nodes in total) to view them side by side.</p>
              <button type="button" onClick={() => setLoad(true)} className="inline-flex items-center gap-2 px-5 py-2.5 bg-[#f4efe6] text-[#15263a] text-sm font-medium hover:bg-white">
                <GitCompare size={15} /> Compare networks
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <Side key={`A${A.i}`} tag="A" event={A} />
                <Side key={`B${B.i}`} tag="B" event={B} />
              </div>
            </div>
          )}
        </>
      )}

      <ResearchNotes index={index} items={[
        ["“Notable” differences", "Flags counts that differ by a factor of two or more and fractions that differ by at least 0.1. It is a reading aid, not a statistical test, and two events are not a sample from which to generalise."],
        ["What a comparison shows", "Similar or different structure does not show that two events share, or lack, coordination. All measures are descriptive properties of the full graphs, computed as in the paper."],
        ["Side-by-side layouts", "Each graph is laid out independently; positions and scale are not comparable across the two panels."],
      ]} />
    </div>
  );
}

function Side({ tag, event }) {
  const G = useEventGraph(event, true);
  const [sel, setSel] = useState(null);
  return (
    <div className="space-y-2">
      {G.status === "error" && <ErrorBox error={G.error} />}
      {G.status === "ready" ? (
        <NetworkCanvas g={G.g} d={G.d} pos={G.pos} label={event.label} selected={sel} onSelect={setSel} compact
          banner={`${tag} · ${event.name}`} className="h-[46vh] min-h-[320px] max-h-[520px]" />
      ) : G.status !== "error" && (
        <div className="graph-canvas h-[46vh] min-h-[320px] flex items-center justify-center"><div className="bg-[#f4efe6] px-4 py-3"><Loading>{G.phase === "layout" ? "Computing layout…" : "Loading graph…"}</Loading></div></div>
      )}
      {G.status === "ready" && (
        <div className="text-[12px] font-mono text-[#4a4740]">
          {sel == null ? "Select a node for its degree." : `Node #${sel}: in ${G.d.indeg[sel]} · out ${G.d.outdeg[sel]} · reciprocal ${G.d.recip[sel]}`}
        </div>
      )}
    </div>
  );
}
