// Descriptive statistics for a directed graph given as edge arrays over nodes 0..n-1, optionally
// restricted to a subset of edges (a sampled observation). Conventions follow src/features.py:
// degrees count directed edges (a self-loop adds one to in- and out-degree); core numbers are
// computed on the simple undirected projection with self-loops removed; components are weak.

export function subgraph(g, edgeIdx) {
  if (!edgeIdx) return { n: g.n, src: g.src, dst: g.dst, edgeIdx: null };
  const src = new Int32Array(edgeIdx.length), dst = new Int32Array(edgeIdx.length);
  edgeIdx.forEach((e, k) => {
    src[k] = g.src[e];
    dst[k] = g.dst[e];
  });
  return { n: g.n, src, dst, edgeIdx };
}

export function describe({ n, src, dst }) {
  const m = src.length;
  const indeg = new Int32Array(n), outdeg = new Int32Array(n), loops = new Uint8Array(n);
  const present = new Uint8Array(n);
  for (let k = 0; k < m; k++) {
    outdeg[src[k]]++;
    indeg[dst[k]]++;
    present[src[k]] = 1;
    present[dst[k]] = 1;
    if (src[k] === dst[k]) loops[src[k]] = 1;
  }
  // Adjacency (directed, without self-loops) as CSR for in- and out-neighbours
  const outStart = new Int32Array(n + 1), inStart = new Int32Array(n + 1);
  for (let k = 0; k < m; k++) if (src[k] !== dst[k]) { outStart[src[k] + 1]++; inStart[dst[k] + 1]++; }
  for (let v = 0; v < n; v++) { outStart[v + 1] += outStart[v]; inStart[v + 1] += inStart[v]; }
  const outAdj = new Int32Array(outStart[n]), inAdj = new Int32Array(inStart[n]);
  const oc = outStart.slice(0, n), ic = inStart.slice(0, n);
  for (let k = 0; k < m; k++) if (src[k] !== dst[k]) { outAdj[oc[src[k]]++] = dst[k]; inAdj[ic[dst[k]]++] = src[k]; }

  // Reciprocated partners: v -> u and u -> v both present
  const recip = new Int32Array(n);
  const mark = new Int32Array(n).fill(-1);
  let recipPairs = 0;
  for (let v = 0; v < n; v++) {
    for (let a = outStart[v]; a < outStart[v + 1]; a++) mark[outAdj[a]] = v;
    for (let a = inStart[v]; a < inStart[v + 1]; a++) if (mark[inAdj[a]] === v) recip[v]++;
    recipPairs += recip[v];
  }
  recipPairs /= 2;

  // Weak components (union-find), over nodes present in this graph
  const parent = new Int32Array(n).map((_, i) => i);
  const find = (x) => { while (parent[x] !== x) { parent[x] = parent[parent[x]]; x = parent[x]; } return x; };
  for (let k = 0; k < m; k++) { const a = find(src[k]), b = find(dst[k]); if (a !== b) parent[a] = b; }
  const compSize = new Map();
  for (let v = 0; v < n; v++) if (present[v]) { const r = find(v); compSize.set(r, (compSize.get(r) || 0) + 1); }
  const comp = new Int32Array(n).fill(-1);
  for (let v = 0; v < n; v++) if (present[v]) comp[v] = find(v);

  return { n, m, indeg, outdeg, loops, present, outStart, outAdj, inStart, inAdj, recip, recipPairs, comp, compSize };
}

// Core numbers (Batagelj–Zaversnik) on the simple undirected projection without self-loops.
export function coreNumbers(d) {
  const { n, outStart, outAdj, inStart, inAdj } = d;
  const nbrs = Array.from({ length: n }, () => new Set());
  for (let v = 0; v < n; v++) {
    for (let a = outStart[v]; a < outStart[v + 1]; a++) { nbrs[v].add(outAdj[a]); nbrs[outAdj[a]].add(v); }
    for (let a = inStart[v]; a < inStart[v + 1]; a++) { nbrs[v].add(inAdj[a]); nbrs[inAdj[a]].add(v); }
  }
  const deg = nbrs.map((s) => s.size);
  const maxd = deg.reduce((a, b) => Math.max(a, b), 0);
  const bins = new Int32Array(maxd + 1);
  deg.forEach((x) => bins[x]++);
  let start = 0;
  for (let k = 0; k <= maxd; k++) { const c = bins[k]; bins[k] = start; start += c; }
  const pos = new Int32Array(n), vert = new Int32Array(n);
  deg.forEach((x, v) => { pos[v] = bins[x]; vert[pos[v]] = v; bins[x]++; });
  for (let k = maxd; k > 0; k--) bins[k] = bins[k - 1];
  bins[0] = 0;
  const core = deg.slice();
  for (let i = 0; i < n; i++) {
    const v = vert[i];
    for (const u of nbrs[v]) {
      if (core[u] > core[v]) {
        const du = core[u], pu = pos[u], pw = bins[du], w = vert[pw];
        if (u !== w) { pos[u] = pw; vert[pu] = w; pos[w] = pu; vert[pw] = u; }
        bins[du]++;
        core[u]--;
      }
    }
  }
  return core;
}

export const median = (arr) => {
  if (!arr.length) return 0;
  const s = Array.from(arr).sort((a, b) => a - b), h = s.length >> 1;
  return s.length % 2 ? s[h] : (s[h - 1] + s[h]) / 2;
};

// Nodes ranked by total degree (in + out), highest first
export function topByDegree(d, k) {
  const idx = [];
  for (let v = 0; v < d.n; v++) if (d.present[v]) idx.push(v);
  idx.sort((a, b) => d.indeg[b] + d.outdeg[b] - (d.indeg[a] + d.outdeg[a]) || a - b);
  return idx.slice(0, k);
}
