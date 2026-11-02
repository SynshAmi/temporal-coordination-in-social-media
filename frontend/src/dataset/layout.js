// Client for the layout worker. Layouts are cached by key for the page session, so revisiting
// an event, or switching between its full graph and its sampled observations, never recomputes.

let worker = null;
let nextId = 1;
const pending = new Map();
const cache = new Map();

function getWorker() {
  if (!worker) {
    worker = new Worker(new URL("./layout.worker.js", import.meta.url), { type: "module" });
    worker.onmessage = (e) => {
      const { id, pos, ms, iterations } = e.data;
      const p = pending.get(id);
      pending.delete(id);
      if (p) p.resolve({ pos, ms, iterations });
    };
    worker.onerror = (err) => {
      for (const p of pending.values()) p.reject(err);
      pending.clear();
      worker = null;
    };
  }
  return worker;
}

// key: cache key; g: { n, src, dst }; nodes: optional node subset; seed: start-position seed
export function computeLayout(key, g, { nodes = null, seed = 1, fresh = false } = {}) {
  if (!fresh && cache.has(key)) return cache.get(key);
  const id = nextId++;
  const promise = new Promise((resolve, reject) => {
    pending.set(id, { resolve, reject });
    getWorker().postMessage({ id, n: g.n, src: g.src, dst: g.dst, nodes, seed });
  }).catch((err) => {
    cache.delete(key);
    throw err;
  });
  cache.set(key, promise);
  return promise;
}

export const hasLayout = (key) => cache.has(key);
