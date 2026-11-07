import React, { useState } from "react";
import FigureCaption from "./FigureCaption";
import { f2, int } from "../lib/fmt";

export default function Fig1SizeConfounding({ eventPoints, stats, dataset: D }) {
  const [metricType, setMetricType] = useState("nodes"); // "nodes" or "edges"
  const [hoveredEvent, setHoveredEvent] = useState(null);

  const isNodes = metricType === "nodes";
  // The payload provides raw quantiles (p25, median, p75, mean); derive their
  // log(1+x) positions so the IQR box and median/mean rules share the y-scale.
  const withLog = (s) =>
    s && {
      ...s,
      log_q25: s.log_q25 ?? Math.log1p(s.p25),
      log_q75: s.log_q75 ?? Math.log1p(s.p75),
      log_median: s.log_median ?? Math.log1p(s.median),
      log_mean: s.log_mean ?? Math.log1p(s.mean),
    };
  const campStats = withLog(isNodes ? stats?.campaign_nodes : stats?.campaign_edges);
  const compStats = withLog(isNodes ? stats?.comparison_nodes : stats?.comparison_edges);

  // Chart layout dimensions — spacious to prevent label clipping
  const svgWidth = 640;
  const svgHeight = 360;
  const margin = { top: 24, right: 24, bottom: 64, left: 72 };
  const innerWidth = svgWidth - margin.left - margin.right;
  const innerHeight = svgHeight - margin.top - margin.bottom;

  // Y-axis: log scale range from ~4 to ~10 (in log(1+x))
  const minY = isNodes ? 4.0 : 4.5;
  const maxY = isNodes ? 9.5 : 10.0;

  const yScale = (logVal) => {
    const clamped = Math.max(minY, Math.min(maxY, logVal));
    return innerHeight - ((clamped - minY) / (maxY - minY)) * innerHeight;
  };

  const xPosComp = innerWidth * 0.28;
  const xPosCamp = innerWidth * 0.72;

  // Generate deterministic jitter for points
  const getJitter = (id) => {
    let hash = 0;
    for (let i = 0; i < id.length; i++) hash = (hash << 5) - hash + id.charCodeAt(i);
    return ((Math.abs(hash) % 100) / 100 - 0.5) * 60;
  };

  return (
    <div className="panel">
      {/* Figure Header & Control */}
      <div className="pb-4 mb-5 border-b border-[#e5e0d4] flex flex-wrap items-end justify-between gap-x-6 gap-y-3">
        <div className="min-w-0 flex-1 basis-80">
          <span className="section-label !mb-1">Figure 1</span>
          <h3 className="font-serif text-[21px] text-[#15263a] leading-snug">
            Graph size by class
          </h3>
          <p className="head-desc !mt-1">
            Node and edge counts of every event on a logarithmic scale.
          </p>
        </div>
        <div className="flex items-center gap-2 text-[14px] font-mono">
          <span className="sr-only">Measure</span>
          <div className="inline-flex border border-[#d8d3c5] rounded-[8px] bg-[#faf8f5] p-1">
            <button
              type="button"
              onClick={() => setMetricType("nodes")}
              className={`h-8 px-3 text-[15px] rounded-[4px] font-sans ${
                isNodes
                  ? "bg-[#15263a] text-white font-medium shadow-xs"
                  : "text-[#3c3a37] hover:bg-[#ede9df]"
              }`}
            >
              Node count
            </button>
            <button
              type="button"
              onClick={() => setMetricType("edges")}
              className={`h-8 px-3 text-[15px] rounded-[4px] font-sans ${
                !isNodes
                  ? "bg-[#15263a] text-white font-medium shadow-xs"
                  : "text-[#3c3a37] hover:bg-[#ede9df]"
              }`}
            >
              Edge count
            </button>
          </div>
        </div>
      </div>

      {/* SVG Canvas */}
      <div className="relative chart-frame">
        <svg
          viewBox={`0 0 ${svgWidth} ${svgHeight}`}
          className="select-none overflow-visible"
          role="img"
          aria-label="Jittered strip plot of log graph size for comparison and campaign events"
        >
          <g transform={`translate(${margin.left}, ${margin.top})`}>
            {/* Left Y Axis Line & Ticks */}
            <line x1={0} y1={0} x2={0} y2={innerHeight} stroke="#15263a" strokeWidth="1.5" />

            {/* Horizontal Gridlines & Left Ticks */}
            {[5, 6, 7, 8, 9].map((logVal) => {
              const y = yScale(logVal);
              const naturalVal = Math.round(Math.expm1(logVal));
              return (
                <g key={logVal}>
                  <line
                    x1={0}
                    y1={y}
                    x2={innerWidth}
                    y2={y}
                    stroke="#e4dfd3"
                    strokeDasharray="2,3"
                  />
                  <line
                    x1={-5}
                    y1={y}
                    x2={0}
                    y2={y}
                    stroke="#15263a"
                    strokeWidth="1.2"
                  />
                  <text
                    x={-12}
                    y={y + 4}
                    textAnchor="end"
                    fontSize="12"
                    fill="#5e5a52"
                    fontFamily="var(--font-mono)"
                  >
                    {naturalVal >= 1000 ? `${(naturalVal / 1000).toFixed(0)}k` : naturalVal}
                  </text>
                </g>
              );
            })}

            {/* Y-axis Label */}
            <text
              transform="rotate(-90)"
              x={-innerHeight / 2}
              y={-52}
              textAnchor="middle"
              fontSize="11"
              fill="#15263a"
              fontFamily="var(--font-sans)"
              fontWeight="600"
              letterSpacing="0.04em"
            >
              {isNodes ? "LOG NODE COUNT (N)" : "LOG EDGE COUNT (E)"}
            </text>

            {/* Comparison Boxplot / Summary */}
            <g>
              {compStats && (
                <>
                  {/* IQR Box */}
                  <rect
                    x={xPosComp - 32}
                    y={yScale(compStats.log_q75)}
                    width={64}
                    height={Math.max(2, yScale(compStats.log_q25) - yScale(compStats.log_q75))}
                    fill="#23527c"
                    fillOpacity="0.12"
                    stroke="#23527c"
                    strokeWidth="1"
                  />
                  {/* Median Line */}
                  <line
                    x1={xPosComp - 40}
                    y1={yScale(compStats.log_median)}
                    x2={xPosComp + 40}
                    y2={yScale(compStats.log_median)}
                    stroke="#23527c"
                    strokeWidth="2.5"
                  />
                  {/* Mean Line (dashed) */}
                  <line
                    x1={xPosComp - 35}
                    y1={yScale(compStats.log_mean)}
                    x2={xPosComp + 35}
                    y2={yScale(compStats.log_mean)}
                    stroke="#23527c"
                    strokeWidth="1"
                    strokeDasharray="3,3"
                  />
                </>
              )}
            </g>

            {/* Campaign Boxplot / Summary */}
            <g>
              {campStats && (
                <>
                  {/* IQR Box */}
                  <rect
                    x={xPosCamp - 32}
                    y={yScale(campStats.log_q75)}
                    width={64}
                    height={Math.max(2, yScale(campStats.log_q25) - yScale(campStats.log_q75))}
                    fill="#8f2626"
                    fillOpacity="0.12"
                    stroke="#8f2626"
                    strokeWidth="1"
                  />
                  {/* Median Line */}
                  <line
                    x1={xPosCamp - 40}
                    y1={yScale(campStats.log_median)}
                    x2={xPosCamp + 40}
                    y2={yScale(campStats.log_median)}
                    stroke="#8f2626"
                    strokeWidth="2.5"
                  />
                  {/* Mean Line (dashed) */}
                  <line
                    x1={xPosCamp - 35}
                    y1={yScale(campStats.log_mean)}
                    x2={xPosCamp + 35}
                    y2={yScale(campStats.log_mean)}
                    stroke="#8f2626"
                    strokeWidth="1"
                    strokeDasharray="3,3"
                  />
                </>
              )}
            </g>

            {/* Jittered event points */}
            {eventPoints?.map((ev) => {
              const isCamp = ev.label === 1;
              const colX = isCamp ? xPosCamp : xPosComp;
              const jitter = getJitter(ev.event_id);
              const logVal = isNodes ? ev.log_nodes : ev.log_edges;
              const cx = colX + jitter;
              const cy = yScale(logVal);

              const isHovered = hoveredEvent?.event_id === ev.event_id;

              return (
                <circle
                  key={ev.event_id}
                  cx={cx}
                  cy={cy}
                  r={isHovered ? 6 : 3.5}
                  fill={isCamp ? "#8f2626" : "#23527c"}
                  fillOpacity={isHovered ? 1 : 0.65}
                  stroke={isHovered ? "#15263a" : "none"}
                  strokeWidth={1.5}
                  className="cursor-pointer transition-all"
                  onMouseEnter={() => setHoveredEvent(ev)}
                  onMouseLeave={() => setHoveredEvent(null)}
                />
              );
            })}

            {/* X-axis baseline, ticks, and labels */}
            <g transform={`translate(0, ${innerHeight})`}>
              <line x1={0} y1={0} x2={innerWidth} y2={0} stroke="#15263a" strokeWidth="1.5" />
              <line x1={xPosComp} y1={0} x2={xPosComp} y2={6} stroke="#15263a" strokeWidth="1.5" />
              <line x1={xPosCamp} y1={0} x2={xPosCamp} y2={6} stroke="#15263a" strokeWidth="1.5" />

              {/* Comparison class labels */}
              <text
                x={xPosComp}
                y={26}
                textAnchor="middle"
                fontSize="13"
                fill="#23527c"
                fontFamily="var(--font-sans)"
                fontWeight="600"
              >
                Comparison Events (n={D.n_comparison})
              </text>
              <text
                x={xPosComp}
                y={46}
                textAnchor="middle"
                fontSize="11"
                fill="#555"
                fontFamily="var(--font-mono)"
              >
                Median: {compStats?.median.toLocaleString()} | Mean: {compStats?.mean.toLocaleString()}
              </text>

              {/* Campaign class labels */}
              <text
                x={xPosCamp}
                y={26}
                textAnchor="middle"
                fontSize="13"
                fill="#8f2626"
                fontFamily="var(--font-sans)"
                fontWeight="600"
              >
                Campaign Events (n={D.n_campaign})
              </text>
              <text
                x={xPosCamp}
                y={46}
                textAnchor="middle"
                fontSize="11"
                fill="#555"
                fontFamily="var(--font-mono)"
              >
                Median: {campStats?.median.toLocaleString()} | Mean: {campStats?.mean.toLocaleString()}
              </text>
            </g>
          </g>
        </svg>

        {/* Hover Tooltip */}
        {hoveredEvent && (
          <div className="absolute top-2 right-2 bg-white border border-[#15263a] px-3.5 py-2.5 shadow-md text-[14px] font-mono z-10 pointer-events-none">
            <div className="font-semibold text-[#15263a] mb-1">
              {hoveredEvent.label_str.toUpperCase()} EVENT
            </div>
            <div className="text-[#3c3a37] text-[13px] truncate max-w-[280px]">
              ID: {hoveredEvent.event_id}
            </div>
            <div className="mt-1 flex gap-4 text-[#555]">
              <span>Nodes: <b>{hoveredEvent.n_nodes.toLocaleString()}</b></span>
              <span>Edges: <b>{hoveredEvent.n_edges.toLocaleString()}</b></span>
            </div>
          </div>
        )}
      </div>

      {/* Two-Level Publication Caption */}
      <FigureCaption
        figNumber="FIG. 1"
        title="Event-graph size by class"
        takeaway={`Comparison graphs (blue, n = ${D.n_comparison}) are several times larger than campaign graphs (red, n = ${D.n_campaign}) in both node count (median ${int(D.nodes.comparison.median)} vs ${int(D.nodes.campaign.median)}) and edge count (median ${int(D.edges.comparison.median)} vs ${int(D.edges.campaign.median)}).`}
        details={
          <div className="space-y-2.5">
            <p>
              <strong>Size difference:</strong> the signed standardized mean difference of log node count (campaign − comparison) is {f2(D.smd_log_nodes_full_cohort)}, i.e. |SMD| = {f2(Math.abs(D.smd_log_nodes_full_cohort))}.
            </p>
            <p>
              <strong>Encoding:</strong> Solid horizontal bars indicate group medians; dashed bars represent group arithmetic means on log scale; shaded rectangular bounds enclose the Interquartile Range (IQR, 25th–75th percentiles). Individual circles depict exact event graphs jittered along the column axis for visual clarity.
            </p>
            <p>
              <strong>Why it matters:</strong> in this archive the classes differ strongly in size, so any classifier score on these data should be read against a count-only baseline (Fig. 2).
            </p>
          </div>
        }
      />
    </div>
  );
}
