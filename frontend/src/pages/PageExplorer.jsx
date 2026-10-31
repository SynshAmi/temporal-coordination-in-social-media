import React, { useState } from "react";
import Fig3MatchedCohort from "../components/Fig3MatchedCohort";
import Fig4ObservationBudgets from "../components/Fig4ObservationBudgets";
import CohortFlowDiagram from "../components/CohortFlowDiagram";
import ResultsTable from "../components/ResultsTable";
import NK from "../components/NK";
import { ShieldAlert } from "lucide-react";
import { f3, sg, ci, pct, con } from "../lib/fmt";

export default function PageExplorer({ data }) {
  const P = data.paper;
  const experiments = data.experiments || [];
  const MT = P.matching;
  const mech = P.study2.mechanism.K250, r2 = P.study2.mechanism_r2_K250;
  const [activeExplorerSection, setActiveExplorerSection] = useState("all");

  return (
    <div className="space-y-16 lg:space-y-20">
      <header className="border-b border-[#15263a] pb-10 lg:pb-12">
        <div className="max-w-4xl">
          <span className="section-label">Evidence Explorer</span>
          <h1 className="page-title">
            Size Matching and Restricted Observation
          </h1>
          <p className="mt-5 text-base sm:text-[17px] text-[#3c3a37] leading-relaxed max-w-[62ch]">
            An exploratory check of what survives when campaign and comparison events are matched on size, and the Study 2 analysis of how much label information a single fixed-size edge sample retains.
          </p>
        </div>

        <div className="mt-8 flex flex-wrap items-center gap-2.5 text-xs font-mono">
          <span className="text-[#6b6862] text-[11px] uppercase tracking-wider mr-2">Jump to View:</span>
          {[
            { id: "all", label: "All Evidence" },
            { id: "matched", label: "Fig 3: Size Matching" },
            { id: "budgets", label: "Fig 4: Edge Budgets" },
            { id: "flow", label: "Study Design" },
            { id: "table", label: "Results Table" },
          ].map((sec) => (
            <button
              key={sec.id}
              type="button"
              onClick={() => setActiveExplorerSection(sec.id)}
              className={`px-3.5 py-1.5 border transition-colors shadow-2xs ${
                activeExplorerSection === sec.id
                  ? "bg-[#15263a] text-white border-[#15263a] font-medium shadow-xs"
                  : "bg-white text-[#3c3a37] border-[#d8d3c5] hover:bg-[#ede9df]"
              }`}
            >
              {sec.label}
            </button>
          ))}
        </div>
      </header>

      {(activeExplorerSection === "all" || activeExplorerSection === "matched" || activeExplorerSection === "budgets") && (
        <section>
          <div className={`grid grid-cols-1 gap-8 lg:gap-10 items-start ${activeExplorerSection === "all" ? "xl:grid-cols-2" : "max-w-[900px]"}`}>
            {(activeExplorerSection === "all" || activeExplorerSection === "matched") && <Fig3MatchedCohort paper={P} />}
            {(activeExplorerSection === "all" || activeExplorerSection === "budgets") && <Fig4ObservationBudgets paper={P} />}
          </div>
        </section>
      )}

      <section className="p-5 sm:p-8 lg:px-10 bg-[#f4efe6] border border-[#d8d3c5] border-l-4 border-l-[#8f2626] grid grid-cols-1 lg:grid-cols-12 gap-x-10 gap-y-3">
        <div className="lg:col-span-4 flex items-start gap-2 text-[#8f2626] font-mono font-bold uppercase tracking-wider text-xs leading-relaxed">
          <ShieldAlert size={15} className="shrink-0 mt-0.5" />
          <span>Uncertainty and Scope</span>
        </div>
        <div className="lg:col-span-8 text-[15px] leading-relaxed text-[#3c3a37] max-w-[80ch] space-y-3">
          <p>
            Size matching keeps {MT.node_only.n_pairs_range[0]}–{MT.node_only.n_pairs_range[1]} pairs, changes the evaluated population and does not balance every size measure; it is exploratory sensitivity evidence, not a causal estimate. Study 1 intervals are percentile bootstraps over fixed out-of-fold predictions; they exclude refitting and fold-split variability and cannot account for dependence between events that share accounts, which the release does not allow us to measure.
          </p>
          <p>
            The expected number of distinct endpoints <NK /> in a 250-edge sample matches the observed mean within {pct(mech.max_abs_rel_error_expected_vs_observed)}% and has AUC {f3(mech.auc_expectedNK_label)} for the label (full-graph log node count: {f3(mech.auc_log_N_full_label)}). It is strongly associated with full-graph node count and mean degree, which together explain {pct(r2["log N + log mean degree"])}% of its variation at K = 250; in/out-degree Gini adds no measurable explanatory power. Structure did not detectably improve on <NK /> at K = 250 (ΔBA {sg(con(P, 250, "structure_beyond_NK").ba.delta)} {ci(con(P, 250, "structure_beyond_NK").ba.ci)}).
          </p>
        </div>
      </section>

      {(activeExplorerSection === "all" || activeExplorerSection === "flow") && (
        <section>
          <CohortFlowDiagram paper={P} />
        </section>
      )}

      {(activeExplorerSection === "all" || activeExplorerSection === "table") && (
        <section>
          <ResultsTable experiments={experiments} />
        </section>
      )}
    </div>
  );
}
