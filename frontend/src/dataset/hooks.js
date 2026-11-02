import { useEffect, useState, useCallback } from "react";
import { loadGraph } from "./data";
import { computeLayout } from "./layout";
import { describe } from "./graph";

// Runs `run()` whenever `key` changes (null = idle). State is stored with the key it belongs to,
// so a result for an earlier key is never shown, and "loading" is derived rather than set.
export function useAsync(key, run) {
  const [st, setSt] = useState({ key: null });
  useEffect(() => {
    if (key == null) return;
    let live = true;
    run((partial) => live && setSt({ key, ...partial }))
      .then((data) => live && setSt({ key, status: "ready", ...data }))
      .catch((error) => live && setSt({ key, status: "error", error }));
    return () => {
      live = false;
    };
    // `run` is recreated each render; the key fully determines the request
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);
  if (key == null) return { status: "idle" };
  if (st.key !== key) return { status: "loading" };
  return st.status ? st : { ...st, status: "loading" };
}

// One event's graph and full-graph layout, loaded only when `enabled`. Both are cached for the
// session (data.js, layout.js), so returning to an event is instant.
export function useEventGraph(event, enabled) {
  const [layoutSeed, setLayoutSeed] = useState(1);
  const key = event && enabled ? `e${event.i}-full-${layoutSeed}` : null;
  const st = useAsync(key, async (progress) => {
    const t0 = performance.now();
    const g = await loadGraph(event);
    const tLoad = performance.now() - t0;
    const d = describe(g);
    progress({ phase: "layout", g, d, tLoad });
    const lay = await computeLayout(key, g, { seed: layoutSeed });
    return { g, d, pos: lay.pos, tLoad, layoutMs: lay.ms, iterations: lay.iterations, tTotal: performance.now() - t0 };
  });
  const relayout = useCallback(() => setLayoutSeed((s) => s + 1), []);
  return { ...st, relayout, layoutSeed };
}
