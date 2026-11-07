import React, { useEffect, useState, useCallback } from "react";
import { LayoutGrid, Network, GitCompare, FlaskConical, ArrowLeft } from "lucide-react";
import { loadIndex } from "../dataset/data";
import DatasetOverview from "../dataset/DatasetOverview";
import Playground from "../dataset/Playground";
import Compare from "../dataset/Compare";
import SamplingLab from "../dataset/SamplingLab";
import { Loading, ErrorBox } from "../dataset/ui";

// Routes: #dataset · #dataset/event/<i> · #dataset/compare/<a>/<b> · #dataset/sampling/<i>
const VIEWS = [
  { id: "overview", label: "Dataset Overview", short: "Overview", icon: LayoutGrid },
  { id: "event", label: "Network Playground", short: "Network", icon: Network },
  { id: "compare", label: "Event Comparison", short: "Compare", icon: GitCompare },
  { id: "sampling", label: "Sampling Lab", short: "Sampling", icon: FlaskConical },
];

function parseRoute() {
  const parts = window.location.hash.replace(/^#/, "").split("/");
  const num = (s) => (s && /^\d+$/.test(s) ? Number(s) : null);
  const view = VIEWS.some((v) => v.id === parts[1]) ? parts[1] : "overview";
  return { view, a: num(parts[2]), b: num(parts[3]) };
}

export default function PageDataset() {
  const [index, setIndex] = useState(null);
  const [error, setError] = useState(null);
  const [route, setRoute] = useState(parseRoute);
  const [selected, setSelected] = useState(() => parseRoute().a);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let live = true;
    loadIndex().then((d) => live && setIndex(d)).catch((e) => live && setError(e));
    return () => { live = false; };
  }, [attempt]);

  useEffect(() => {
    const onHash = () => {
      const r = parseRoute();
      setRoute(r);
      if (r.a != null) setSelected(r.a);
    };
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  const navigate = useCallback((view, a = null, b = null, scroll = true) => {
    const path = ["dataset", view === "overview" ? null : view, a, b].filter((x) => x != null).join("/");
    if (window.location.hash !== `#${path}`) window.location.hash = path;
    if (scroll) window.scrollTo({ top: 0, behavior: "smooth" });
  }, []);

  // Event-aware navigation used by buttons ("Explore network", "Sampling lab", "Compare")
  const go = useCallback((view, i) => {
    setSelected(i);
    if (view === "compare") navigate("compare", i, route.view === "compare" ? route.b : null);
    else navigate(view, i);
  }, [navigate, route]);

  const exists = (i) => index && index.events.some((e) => e.i === i);
  const cur = route.view;
  const eventFor = (v) => (exists(route.a) ? route.a : exists(selected) ? selected : null) ?? v;

  return (
    <div className="space-y-10 lg:space-y-12">
      <header className="border-b border-[#15263a] pb-8 lg:pb-10">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-x-12 gap-y-5 items-end">
          <div className="lg:col-span-8">
            <span className="section-label">Dataset Explorer</span>
            <h1 className="page-title">The archive, event by event</h1>
            <p className="mt-4 text-base sm:text-[18px] text-[#3c3a37] leading-relaxed max-w-[64ch]">
              Browse the engagement graphs analysed in the paper, open any event's network, compare two events, and see what a fixed-budget sample of edges keeps of a graph.
            </p>
          </div>
          <dl className="lg:col-span-4 lg:justify-self-end border-l-2 border-[#d8d3c5] pl-4 lg:border-l-0 lg:pl-0 lg:border-r-2 lg:pr-4 lg:text-right">
            <dt className="text-[12.5px] font-mono font-semibold text-[#8f2626]">Data source</dt>
            <dd className="mt-1.5 font-serif text-[17px] text-[#15263a] leading-snug">Gopalakrishnan, Hossain, Elmas &amp; Sarıyüce</dd>
            <dd className="mt-0.5 text-[14px] font-mono text-[#5e5a52]">LEN · ICWSM 2025 · CC-BY (per the authors)</dd>
            <dd className="mt-0.5 text-[14px] font-mono text-[#757065]">Graph structure only</dd>
          </dl>
        </div>
      </header>

      {/* Sub-navigation */}
      <nav aria-label="Dataset explorer sections" className="no-scrollbar grid grid-cols-4 sm:flex items-stretch border-b border-[#dcd7ca] -mt-4 overflow-x-auto overflow-y-hidden">
        {VIEWS.map((v) => {
          const Icon = v.icon, on = cur === v.id;
          return (
            <button key={v.id} type="button" aria-current={on ? "page" : undefined}
              onClick={() => (v.id === "overview" ? navigate("overview") : v.id === "compare" ? navigate("compare", selected, null) : navigate(v.id, selected))}
              className={`inline-flex flex-col sm:flex-row items-center justify-center gap-1 sm:gap-2 px-1 sm:px-4 py-2.5 sm:py-3 text-[13px] sm:text-[15px] font-medium whitespace-nowrap border-b-2 transition-colors ${
                on ? "border-[#8f2626] text-[#15263a]" : "border-transparent text-[#5e5a52] hover:text-[#15263a]"
              }`}>
              <Icon size={14} className={on ? "text-[#8f2626]" : ""} />
              <span className="sm:hidden">{v.short}</span><span className="hidden sm:inline">{v.label}</span>
            </button>
          );
        })}
      </nav>

      {error && <ErrorBox error={error} onRetry={() => { setError(null); setAttempt((x) => x + 1); }} />}
      {!index && !error && <Loading>Loading dataset index…</Loading>}

      {index && (
        <>
          {cur !== "overview" && (
            <button type="button" onClick={() => navigate("overview")} className="inline-flex items-center gap-1.5 text-[14px] font-mono text-[#23527c] hover:text-[#15263a] -mt-4">
              <ArrowLeft size={13} /> Back to the dataset overview
            </button>
          )}
          {cur === "overview" && <DatasetOverview index={index} selected={selected} onSelect={setSelected} go={go} />}
          {cur === "event" && (
            <Playground index={index} eventIdx={eventFor(null)} autoLoad={false}
              onPickEvent={(i) => { setSelected(i); navigate("event", i, null, false); }} go={go} />
          )}
          {cur === "compare" && (
            <Compare index={index} a={exists(route.a) ? route.a : null} b={exists(route.b) ? route.b : null}
              onPick={(a, b) => { if (a != null) setSelected(a); navigate("compare", a ?? 0, b, false); }} />
          )}
          {cur === "sampling" && (
            <SamplingLab index={index} eventIdx={(() => { const i = eventFor(null); return i != null && index.events.find((e) => e.i === i)?.budgets.length ? i : null; })()}
              onPickEvent={(i) => { setSelected(i); navigate("sampling", i, null, false); }} />
          )}
        </>
      )}
    </div>
  );
}
