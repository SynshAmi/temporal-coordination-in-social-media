import React from "react";
import { Info, Loader2, ChevronDown } from "lucide-react";
import { LABEL_TEXT } from "./palette";
import { int } from "../lib/fmt";

export function LabelBadge({ label, small = false }) {
  const camp = label === 1;
  return (
    <span
      className={`inline-flex items-center gap-1.5 font-mono uppercase tracking-wider border ${small ? "text-[10px] px-1.5 py-px" : "text-[11px] px-2 py-0.5"} ${
        camp ? "text-[#8f2626] border-[#e3c4c0] bg-[#f8eeec]" : "text-[#23527c] border-[#c3d3e3] bg-[#eef3f8]"
      }`}
      title="Label provided by the dataset (from the file name); not independently verified"
    >
      <span className={`w-1.5 h-1.5 rounded-full ${camp ? "bg-[#8f2626]" : "bg-[#23527c]"}`} />
      {LABEL_TEXT[label]}
    </span>
  );
}

// Native select, grouped by label and sorted by name: keyboard type-ahead and accessible on mobile
export function EventSelect({ events, value, onChange, filter = null, label = "Event", placeholder = "Choose an event…", id }) {
  const list = filter ? events.filter(filter) : events;
  const groups = [1, 0].map((l) => [l, list.filter((e) => e.label === l).sort((a, b) => a.name.localeCompare(b.name))]);
  return (
    <label className="flex flex-col gap-1 min-w-0" htmlFor={id}>
      <span className="text-[11px] font-mono uppercase tracking-wider text-[#757065]">{label}</span>
      <select
        id={id}
        value={value ?? ""}
        onChange={(e) => onChange(e.target.value ? Number(e.target.value) : null)}
        className="w-full min-w-0 bg-white border border-[#d8d3c5] px-2.5 py-2 text-sm text-[#15263a] focus:outline-none focus:border-[#23527c]"
      >
        <option value="">{placeholder}</option>
        {groups.map(([l, evs]) => (
          <optgroup key={l} label={`${LABEL_TEXT[l]} (${evs.length})`}>
            {evs.map((e) => (
              <option key={e.i} value={e.i}>
                {e.name} · {int(e.n_nodes)} nodes · {int(e.n_edges)} edges
              </option>
            ))}
          </optgroup>
        ))}
      </select>
    </label>
  );
}

// Definition-list rows: [label, value, hint?]
export function StatRows({ rows, className = "" }) {
  return (
    <dl className={`divide-y divide-[#e5e0d4] text-sm ${className}`}>
      {rows.filter(Boolean).map(([k, v, hint]) => (
        <div key={k} className="flex items-baseline justify-between gap-4 py-1.5">
          <dt className="text-[#4a4740] min-w-0">
            {k}
            {hint && <Hint text={hint} />}
          </dt>
          <dd className="font-mono text-[13px] text-[#15263a] text-right shrink-0">{v}</dd>
        </div>
      ))}
    </dl>
  );
}

export function Hint({ text }) {
  return (
    <span className="inline-flex align-middle ml-1 text-[#9a948a] hover:text-[#23527c] cursor-help" title={text} aria-label={text} tabIndex={0}>
      <Info size={12} />
    </span>
  );
}

/**
 * Research notes for one explorer section, placed after its primary content: collapsed by default.
 * items: [[heading, content], ...]. When `index` is given, the dataset-wide notes on labels and on
 * the analysed archive are appended, so every section carries them.
 */
export function ResearchNotes({ items, index = null }) {
  const all = [
    ...items,
    ...(index
      ? [
          ["Dataset labels", "Campaign and comparison labels are provided by the dataset (from its file names) and are not independently verified; comparison events are not verified as organic."],
          ["Analysed archive", `These are the ${index.archive.n_events} events of the archive analysed in the paper (${index.archive.n_campaign} campaign, ${index.archive.n_comparison} comparison), not the official ${index.archive.official.n_events}-event LEN-Small release (${index.archive.official.n_campaign}/${index.archive.official.n_comparison}). The ${index.archive.n_events - index.archive.official.n_events} additional events cannot be identified, so no event is marked as official or extra.`],
        ]
      : []),
  ].filter(Boolean);
  return (
    <details className="group mt-2 border-t border-[#dcd7ca]">
      <summary className="list-none [&::-webkit-details-marker]:hidden flex items-center gap-2 py-3 cursor-pointer select-none text-[11px] font-mono uppercase tracking-wider text-[#5e5a52] hover:text-[#15263a] focus-visible:outline focus-visible:outline-1 focus-visible:outline-[#23527c]">
        <Info size={13} className="shrink-0 text-[#23527c]" aria-hidden="true" />
        <span>Research notes</span>
        <span className="normal-case tracking-normal text-[#9a948a]">({all.length})</span>
        <ChevronDown size={13} className="ml-auto transition-transform group-open:rotate-180" aria-hidden="true" />
      </summary>
      <dl className="mb-2 grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-3.5 bg-[#f4efe6] border border-[#e2dcd0] px-4 sm:px-5 py-4 text-[13px] leading-relaxed text-[#3c3a37]">
        {all.map(([h, body]) => (
          <div key={h} className="min-w-0">
            <dt className="text-[11px] font-mono font-semibold uppercase tracking-wider text-[#15263a]">{h}</dt>
            <dd className="mt-1">{body}</dd>
          </div>
        ))}
      </dl>
    </details>
  );
}

export function Loading({ children = "Loading…" }) {
  return (
    <div className="flex items-center gap-2 text-xs font-mono text-[#5e5a52]" role="status">
      <Loader2 size={14} className="animate-spin" /> {children}
    </div>
  );
}

export function ErrorBox({ error, onRetry }) {
  return (
    <div className="p-4 border border-[#8f2626] bg-white text-sm text-[#3c3a37] space-y-2" role="alert">
      <div className="font-mono text-xs font-bold uppercase tracking-wider text-[#8f2626]">Could not load the data</div>
      <p>{String(error?.message || error)}</p>
      {onRetry && (
        <button type="button" onClick={onRetry} className="text-xs font-mono underline underline-offset-4 text-[#23527c]">Try again</button>
      )}
    </div>
  );
}

export function Citation({ source }) {
  return (
    <div className="text-[13px] text-[#3c3a37] leading-relaxed space-y-2">
      <p>
        <strong className="text-[#15263a]">Source.</strong> {source.authors}, “{source.paper},” <em>{source.venue}</em>, doi:{" "}
        <a href={`https://doi.org/${source.doi}`} target="_blank" rel="noopener noreferrer" className="underline decoration-[#b5ad9e] underline-offset-4 hover:text-[#23527c]">{source.doi}</a>. Dataset:{" "}
        <a href={source.project_url} target="_blank" rel="noopener noreferrer" className="underline decoration-[#b5ad9e] underline-offset-4 hover:text-[#23527c]">LEN project page</a>.
      </p>
    </div>
  );
}
