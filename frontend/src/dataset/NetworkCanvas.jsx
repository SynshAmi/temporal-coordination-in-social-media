import React, { useEffect, useMemo, useRef, useState } from "react";
import Graph from "graphology";
import Sigma from "sigma";
import { EdgeArrowProgram } from "sigma/rendering";
import { ZoomIn, ZoomOut, Maximize2, RotateCcw } from "lucide-react";
import { CANVAS, LABEL_COLOR } from "./palette";

/**
 * WebGL network view (sigma.js) of one graph or one sampled observation of it.
 *
 * g          full graph { n, src, dst }
 * d          description of the displayed graph (graph.js describe): degrees, adjacency
 * pos        Float32Array [x0, y0, ...]; NaN hides a node
 * edgeMask   Uint8Array over g's edges (1 = in the displayed graph); null = all
 * nodeMask   Uint8Array over nodes (1 = in the displayed graph); null = all
 * showDropped  draw nodes and edges outside the observation faintly
 * label      dataset label of the event (node colour)
 * selected, onSelect, hubs (Set), edgeMode ("all" | "reciprocal" | "selected" | "noloops"), showLabels
 */
export default function NetworkCanvas({
  g, d, pos, edgeMask = null, nodeMask = null, showDropped = false, label,
  selected = null, onSelect, hubs = null, edgeMode = "all", showLabels = false,
  onRelayout = null, banner = null, className = "h-[480px]", compact = false,
}) {
  const container = useRef(null);
  const sigmaRef = useRef(null);
  const state = useRef({});
  const onSelectRef = useRef(onSelect);
  const [hover, setHover] = useState(null);

  // Neighbours of the selected node in the displayed graph
  const nbrs = useMemo(() => {
    if (selected == null || !d) return null;
    const out = new Set(), inn = new Set();
    for (let a = d.outStart[selected]; a < d.outStart[selected + 1]; a++) out.add(d.outAdj[a]);
    for (let a = d.inStart[selected]; a < d.inStart[selected + 1]; a++) inn.add(d.inAdj[a]);
    return { out, inn };
  }, [selected, d]);

  // Build the graphology graph whenever the displayed data change
  const graph = useMemo(() => {
    if (!g || !pos || !d) return null;
    const G = new Graph({ type: "directed", multi: false, allowSelfLoops: true });
    const base = LABEL_COLOR[label] || CANVAS.comparison;
    const dense = g.n > 3000;
    for (let v = 0; v < g.n; v++) {
      const x = pos[2 * v], y = pos[2 * v + 1];
      if (Number.isNaN(x)) continue;
      const inObs = !nodeMask || nodeMask[v];
      if (!inObs && !showDropped) continue;
      const deg = d.indeg[v] + d.outdeg[v];
      G.addNode(v, {
        x, y, inObs,
        size: inObs ? (dense ? Math.min(9, 1 + 0.35 * Math.sqrt(deg)) : Math.min(13, 1.8 + 0.9 * Math.sqrt(deg))) : 1.1,
        color: inObs ? base : CANVAS.ghost,
        label: `#${v}`,
        zIndex: inObs ? 1 : 0,
      });
    }
    for (let k = 0; k < g.src.length; k++) {
      const s = g.src[k], t = g.dst[k];
      if (s === t || !G.hasNode(s) || !G.hasNode(t)) continue; // self-loops are counted, not drawn
      const inObs = !edgeMask || edgeMask[k];
      if (!inObs && !showDropped) continue;
      G.addDirectedEdgeWithKey(k, s, t, {
        inObs, s, t,
        size: dense ? 0.5 : 0.8,
        // in an observation shown against the full graph, the observed edges are drawn brighter
        color: !inObs ? CANVAS.edgeDropped : edgeMask && showDropped ? CANVAS.edgeObserved : dense ? CANVAS.edgeDense : CANVAS.edge,
        zIndex: inObs ? 1 : 0,
      });
    }
    return G;
  }, [g, d, pos, edgeMask, nodeMask, showDropped, label]);

  // Reciprocated directed edges (both directions present), for the edge filter
  const recipSet = useMemo(() => {
    if (!graph) return null;
    const set = new Set();
    graph.forEachEdge((key, a) => {
      if (a.inObs && graph.hasDirectedEdge(a.t, a.s)) set.add(key);
    });
    return set;
  }, [graph]);

  // The reducers read the current view state from this ref; it is synced before every render
  useEffect(() => {
    onSelectRef.current = onSelect;
    state.current = { selected, nbrs, hubs, edgeMode, showLabels, hover: hover?.node ?? null, recipSet };
    sigmaRef.current?.refresh();
  }, [onSelect, selected, nbrs, hubs, edgeMode, showLabels, hover, recipSet]);

  // Create sigma once; swap graphs in place so the camera survives regime switches
  useEffect(() => {
    if (!graph || !container.current) return;
    if (sigmaRef.current) {
      sigmaRef.current.setGraph(graph);
      return;
    }
    const s = new Sigma(graph, container.current, {
      allowInvalidContainer: true,
      defaultEdgeType: "line",
      edgeProgramClasses: { arrow: EdgeArrowProgram },
      zIndex: true,
      renderEdgeLabels: false,
      labelFont: "JetBrains Mono, monospace",
      labelSize: 11,
      labelWeight: "500",
      labelColor: { color: CANVAS.label },
      labelRenderedSizeThreshold: 1e9,
      minCameraRatio: 0.02,
      maxCameraRatio: 4,
      stagePadding: compact ? 12 : 28,
      nodeReducer: (node, attr) => {
        const st = state.current, v = Number(node), out = { ...attr };
        if (!attr.inObs) return { ...out, label: null };
        const isHub = st.hubs && st.hubs.has(v);
        if (st.selected != null) {
          if (v === st.selected) return { ...out, color: CANVAS.selected, size: attr.size * 1.5 + 3, zIndex: 4, forceLabel: true };
          if (st.nbrs && (st.nbrs.out.has(v) || st.nbrs.inn.has(v))) return { ...out, color: CANVAS.neighbour, zIndex: 3, forceLabel: st.showLabels };
          return { ...out, color: CANVAS.dim, label: null, zIndex: 0 };
        }
        if (v === st.hover) return { ...out, color: CANVAS.selected, zIndex: 4, forceLabel: true };
        if (isHub) return { ...out, color: CANVAS.hub, zIndex: 3, forceLabel: st.showLabels };
        if (st.hubs && st.hubs.size) return { ...out, zIndex: 1, label: st.showLabels ? attr.label : null };
        return { ...out, label: st.showLabels ? attr.label : null };
      },
      edgeReducer: (edge, attr) => {
        const st = state.current, out = { ...attr };
        if (!attr.inObs) return out;
        const sel = st.selected;
        const incident = sel != null && (attr.s === sel || attr.t === sel);
        if (st.edgeMode === "reciprocal" && !(st.recipSet && st.recipSet.has(edge))) return { ...out, hidden: true };
        if (st.edgeMode === "selected" && !incident) return { ...out, hidden: true };
        if (sel != null) {
          if (attr.s === sel) return { ...out, color: CANVAS.edgeOut, size: 1.4, type: "arrow", zIndex: 3 };
          if (attr.t === sel) return { ...out, color: CANVAS.edgeIn, size: 1.4, type: "arrow", zIndex: 3 };
          return { ...out, color: CANVAS.edgeFaint };
        }
        if (st.hubs && st.hubs.size && (st.hubs.has(attr.s) || st.hubs.has(attr.t))) return { ...out, color: CANVAS.edgeHub, zIndex: 2 };
        return out;
      },
    });
    s.on("clickNode", ({ node }) => {
      const a = s.getGraph().getNodeAttributes(node);
      if (a.inObs) onSelectRef.current?.(Number(node));
    });
    s.on("clickStage", () => onSelectRef.current?.(null));
    s.on("enterNode", ({ node }) => {
      const a = s.getGraph().getNodeAttributes(node);
      if (!a.inObs) return;
      const p = s.framedGraphToViewport(s.getNodeDisplayData(node));
      setHover({ node: Number(node), x: p.x, y: p.y, w: s.getContainer().clientWidth });
    });
    s.on("leaveNode", () => setHover(null));
    s.getCamera().on("updated", () => setHover(null));
    sigmaRef.current = s;
  }, [graph, compact]);

  useEffect(() => () => {
    sigmaRef.current?.kill();
    sigmaRef.current = null;
  }, []);

  const cam = () => sigmaRef.current?.getCamera();
  const btn = "w-8 h-8 flex items-center justify-center bg-[#0f1d30]/90 border border-[#3a4b63] text-[#d8dee6] hover:text-white hover:border-[#8fa3b8] transition-colors";

  return (
    <div className={`relative graph-canvas overflow-hidden ${className}`}>
      <div ref={container} className="absolute inset-0" role="img" aria-label="Interactive network graph; use the zoom buttons or scroll to zoom, drag to pan, select a node to inspect it" />
      {banner && (
        <div className="absolute top-3 left-3 right-14 pointer-events-none">
          <span className="inline-block px-2 py-1 bg-[#0f1d30]/90 border border-[#3a4b63] text-[12.5px] font-mono text-[#e9e4d8]">{banner}</span>
        </div>
      )}
      <div className="absolute top-3 right-3 flex flex-col gap-1.5">
        <button type="button" className={btn} aria-label="Zoom in" title="Zoom in" onClick={() => cam()?.animatedZoom({ duration: 200 })}><ZoomIn size={14} /></button>
        <button type="button" className={btn} aria-label="Zoom out" title="Zoom out" onClick={() => cam()?.animatedUnzoom({ duration: 200 })}><ZoomOut size={14} /></button>
        <button type="button" className={btn} aria-label="Fit graph to view" title="Fit graph to view" onClick={() => cam()?.animatedReset({ duration: 250 })}><Maximize2 size={14} /></button>
        {onRelayout && (
          <button type="button" className={btn} aria-label="Recompute layout" title="Recompute layout from new starting positions" onClick={onRelayout}><RotateCcw size={14} /></button>
        )}
      </div>
      {hover && d && (
        <div className="absolute pointer-events-none z-10 px-2.5 py-1.5 bg-[#f4efe6] text-[#15263a] border border-[#d8d3c5] text-[13px] font-mono shadow-md whitespace-nowrap"
          style={{ left: Math.max(4, Math.min(hover.x + 12, hover.w - 170)), top: Math.max(hover.y - 40, 4) }}>
          <div className="font-semibold">Node #{hover.node}</div>
          <div>in {d.indeg[hover.node]} · out {d.outdeg[hover.node]}{d.recip[hover.node] ? ` · reciprocal ${d.recip[hover.node]}` : ""}</div>
        </div>
      )}
    </div>
  );
}
