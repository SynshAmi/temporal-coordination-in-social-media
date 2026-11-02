// Force-directed layout (ForceAtlas2) in a Web Worker, so the page stays responsive on the
// largest graphs. Input: { id, n, src, dst, nodes? } where `nodes` optionally restricts the
// layout to a subset of nodes (a sampled observation). Starting positions come from a seeded
// generator, so the same graph always gets the same layout. Positions are visual only.
import Graph from "graphology";
import forceAtlas2 from "graphology-layout-forceatlas2";

function mulberry32(seed) {
  return function () {
    seed |= 0;
    seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

self.onmessage = (e) => {
  const { id, n, src, dst, nodes, seed = 1 } = e.data;
  const t0 = performance.now();
  const rand = mulberry32(seed);
  const keep = nodes ? new Uint8Array(n) : null;
  if (nodes) nodes.forEach((v) => (keep[v] = 1));
  const g = new Graph({ type: "undirected", multi: false, allowSelfLoops: false });
  const spread = Math.sqrt(n) * 10;
  for (let v = 0; v < n; v++) {
    if (keep && !keep[v]) continue;
    g.addNode(v, { x: (rand() - 0.5) * spread, y: (rand() - 0.5) * spread });
  }
  for (let k = 0; k < src.length; k++) {
    const a = src[k], b = dst[k];
    if (a !== b && g.hasNode(a) && g.hasNode(b) && !g.hasEdge(a, b)) g.addEdge(a, b);
  }
  const order = g.order;
  const iterations = order > 4000 ? 120 : order > 1500 ? 200 : order > 400 ? 300 : 500;
  const settings = {
    ...forceAtlas2.inferSettings(g),
    barnesHutOptimize: order > 1000,
    strongGravityMode: true, // keeps the many small components near the centre
    gravity: 0.05,
    scalingRatio: 10,
    slowDown: 2,
  };
  forceAtlas2.assign(g, { iterations, settings });
  const pos = new Float32Array(2 * n).fill(NaN);
  g.forEachNode((v, a) => {
    pos[2 * v] = a.x;
    pos[2 * v + 1] = a.y;
  });
  self.postMessage({ id, pos, ms: Math.round(performance.now() - t0), iterations }, [pos.buffer]);
};
