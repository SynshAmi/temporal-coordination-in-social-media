// Dataset Explorer data access. Files are produced by src/export_dataset_explorer.py into
// public/data/len/. Each file is fetched at most once per page session: requests are cached
// as promises, so concurrent callers share one download, and a failed request is evicted so
// it can be retried.

const BASE = "/data/len/";
const cache = new Map();

function load(path) {
  if (!cache.has(path)) {
    const p = fetch(BASE + path)
      .then((res) => {
        if (!res.ok) throw new Error(`Could not load ${path} (HTTP ${res.status})`);
        return res.json();
      })
      .catch((err) => {
        cache.delete(path);
        throw err;
      });
    cache.set(path, p);
  }
  return cache.get(path);
}

export const loadIndex = () => load("index.json");

// Graph file: { i, n, edges: [s0, t0, s1, t1, ...], w: interaction counts | null, core: [...] }
export async function loadGraph(event) {
  const g = await load(event.graph);
  const m = g.edges.length / 2;
  const src = new Int32Array(m), dst = new Int32Array(m);
  for (let k = 0; k < m; k++) {
    src[k] = g.edges[2 * k];
    dst[k] = g.edges[2 * k + 1];
  }
  return { i: g.i, n: g.n, src, dst, w: g.w, core: g.core };
}

// Sample file: { i, budgets: { "250": { seeds, edges: [[edge indices], ...], features: [...] } } }
export const loadSamples = (event) => (event.samples ? load(event.samples) : Promise.resolve(null));

export const isLoaded = (path) => cache.has(path);
