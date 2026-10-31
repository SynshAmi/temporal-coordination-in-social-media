import React from "react";
import { ArrowDown, ArrowRight, GitBranch, ShieldCheck, BarChart3 } from "lucide-react";
import NK from "./NK";
import { f2, f3, sg, ci, ciu, con, cond } from "../lib/fmt";

// Vertical connector between flowchart tiers
function Connector({ label, icon: Icon = ArrowDown }) {
  return (
    <div className="flex items-center gap-4 py-6">
      <div className="h-px bg-[#dcd7ca] flex-1"></div>
      <div className="flex items-center gap-2 px-4 py-2 bg-[#ede8dc] border border-[#d8d3c5] text-xs font-mono text-[#15263a] text-center">
        <Icon size={13} className="text-[#23527c] shrink-0" />
        <span>{label}</span>
      </div>
      <div className="h-px bg-[#dcd7ca] flex-1"></div>
    </div>
  );
}

function BranchCard({ tag, tagColor, count, title, body, findingLabel, finding, footer }) {
  return (
    <div className="bg-white border border-[#dcd7ca] p-5 sm:p-6 flex flex-col h-full">
      <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1 text-xs font-mono">
        <span className="font-bold uppercase tracking-wider" style={{ color: tagColor }}>{tag}</span>
        <span className="font-bold" style={{ color: tagColor }}>{count}</span>
      </div>
      <h4 className="mt-3 font-serif text-lg font-medium leading-snug text-[#15263a]">{title}</h4>
      <p className="mt-2 text-sm text-[#4a4740] leading-relaxed">{body}</p>
      <div className="mt-4 p-4 bg-[#fbfaf6] border border-[#e5e0d4] text-[13px] text-[#2a2825] leading-relaxed">
        <strong>{findingLabel}:</strong> {finding}
      </div>
      <div className="mt-auto pt-5">
        <div className="pt-3.5 border-t border-[#e2dcd0] font-mono text-xs text-[#5e5a52]">{footer}</div>
      </div>
    </div>
  );
}

export default function CohortFlowDiagram({ paper }) {
  const D = paper.dataset, EL = paper.eligibility, MT = paper.matching, NM = paper.null_model;
  const LC = paper.study1.confirmatory.logreg, lr = paper.study1.performance.logreg;
  const rt = con(paper, 250, "retrain_effect_struct6");

  return (
    <div className="bg-[#faf8f5] border border-[#dcd7ca] p-5 sm:p-8 lg:p-10 w-full">
      <div className="panel-head">
        <span className="section-label">Study Design</span>
        <h3 className="text-xl font-serif font-medium text-[#15263a]">
          From Archive to Analysis Cohorts
        </h3>
        <p className="head-desc">
          Provenance of the analysed archive and the cohorts used by each study.
        </p>
      </div>

      {/* Tier 1: ingestion → deduplication */}
      <div className="grid grid-cols-1 lg:grid-cols-[1fr_auto_1fr] gap-4 lg:gap-6 items-stretch">
        <div className="bg-[#f4efe6] border border-[#dcd7ca] p-5 sm:p-6 flex flex-col">
          <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1 text-xs font-mono">
            <span className="font-bold text-[#8f2626] uppercase tracking-wider">Stage 1: Archive</span>
            <span className="text-[#757065]">Distributed LEN-Small files</span>
          </div>
          <h4 className="mt-3 font-serif text-lg font-medium text-[#15263a]">
            {D.archive_json_files} NetworkX Node-Link JSON Files
          </h4>
          <p className="mt-2 text-sm text-[#4a4740] leading-relaxed">
            Labels are read from the file-name tokens <code className="bg-white px-1 py-0.5 font-mono">_campaign_</code> and <code className="bg-white px-1 py-0.5 font-mono">_noncampaign_</code>. Pretrained text and profile embeddings are excluded; node identifiers are per-graph indices, so the release contains no account identifiers.
          </p>
          <div className="mt-auto pt-5">
            <div className="pt-3.5 border-t border-[#e2dcd0] flex flex-wrap items-center justify-between gap-2 font-mono text-xs text-[#15263a]">
              <span className="font-semibold">Official release: {D.official_len_small.n_graphs} graphs</span>
              <span className="text-[#5e5a52]">{D.official_len_small.n_campaign} / {D.official_len_small.n_noncampaign}</span>
            </div>
          </div>
        </div>

        <div className="flex items-center justify-center text-[#23527c]" aria-hidden="true">
          <ArrowRight size={20} className="hidden lg:block" />
          <ArrowDown size={20} className="lg:hidden" />
        </div>

        <div className="bg-white border border-[#15263a] p-5 sm:p-6 flex flex-col shadow-xs">
          <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1 text-xs font-mono">
            <span className="font-bold text-[#23527c] uppercase tracking-wider inline-flex items-center gap-1.5">
              <ShieldCheck size={13} />
              <span>Stage 2: Deduplication</span>
            </span>
            <span className="text-[#757065]">SHA-256 per file</span>
          </div>
          <h4 className="mt-3 font-serif text-lg font-medium text-[#15263a]">
            {D.n_events} Canonical Events
          </h4>
          <p className="mt-2 text-sm text-[#4a4740] leading-relaxed">
            {D.duplicates_removed} byte-identical duplicate (a campaign graph whose file names differ only in a Turkish dotless <code className="bg-[#f4efe6] px-1 py-0.5 font-mono">ı</code> vs ASCII <code className="bg-[#f4efe6] px-1 py-0.5 font-mono">i</code>) is removed. <strong>The archive holds {D.n_events - D.official_len_small.n_graphs} more events than the official {D.official_len_small.n_graphs}-graph release, for a reason we could not determine</strong>; all results refer to this archive.
          </p>
          <div className="mt-auto pt-5">
            <div className="pt-3.5 border-t border-[#e2dcd0] flex flex-wrap items-center justify-between gap-2 font-mono text-xs text-[#23527c]">
              <span className="font-bold">{D.n_events} events</span>
              <span className="text-[#5e5a52]">{D.n_campaign} campaign / {D.n_comparison} comparison</span>
            </div>
          </div>
        </div>
      </div>

      <Connector label="Two primary studies and one exploratory analysis" icon={GitBranch} />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 lg:gap-6 items-stretch">
        <BranchCard
          tag="Study 1 · RQ1"
          tagColor="#15263a"
          count={`N = ${D.n_events}`}
          title="Incremental Information Beyond Counts"
          body="Seven nested feature levels on identical folds, from counts (M0) to all features (M4); three confirmatory paired contrasts; a degree-preserving rewiring null for arrangement features."
          findingLabel="Finding"
          finding={`Counts reach BA ${f3(lr.M0.balanced_accuracy)}. All features vs counts: ΔBA ${sg(LC.C1.ba.delta_ba)} ${ci(LC.C1.ba.delta_ba_ci)} (inconclusive), Δ log loss ${sg(LC.C1.log_loss.delta_logloss)}. Real vs rewired arrangement: ΔBA ${sg(NM.real_minus_null_ba.delta_ba)} ${ci(NM.real_minus_null_ba.delta_ba_ci)}.`}
          footer={<>{D.n_campaign} campaign &bull; {D.n_comparison} comparison</>}
        />
        <BranchCard
          tag="Exploratory"
          tagColor="#8f2626"
          count={`${MT.node_only.n_pairs_range[0]}–${MT.node_only.n_pairs_range[1]} pairs`}
          title="Size-Matching Sensitivity"
          body={`1:1 greedy matching on log node count (caliper ${MT.caliper_sd_fraction} SD), with and without log edge count, repeated over ${MT.node_only.n_order_seeds} visiting orders. |SMD| ${f2(Math.abs(MT.smd_before))} → ${f2(Math.abs(MT.smd_after))} in the primary ordering.`}
          findingLabel="Sensitivity"
          finding={`Counts fall to near chance within matched cohorts (median BA ${f3(MT.node_only.ba.M0.median)}); content stays above chance (median ${f3(MT.node_only.ba.M3.median)}). Imprecise; changes the evaluated population.`}
          footer={<>{MT.primary_pairs} pairs in the primary ordering &bull; {MT.n_excluded} excluded</>}
        />
        <BranchCard
          tag="Study 2 · RQ2"
          tagColor="#23527c"
          count="K ∈ {250, 500, 1000}"
          title="Single-View Observation Validity"
          body="Each eligible event is reduced to K uniformly sampled edges (10 seeds) and every feature is recomputed from the sample. Full-graph, frozen-transfer and retrained conditions share events, folds and feature definitions."
          findingLabel="Finding"
          finding={<>Single views stay predictive, mostly through the sampled endpoint count (KK, <NK /> only: {f3(cond(paper, 250, "KK|NK").single_view_ba_mean)} at K = 250). Retraining on views vs frozen transfer, same structural features, K = 250: +{f3(rt.ba.delta)} {ciu(rt.ba.ci)}. K = 2000 infeasible ({EL["2000"].campaign_eligible} campaign events).</>}
          footer={<>n = {EL["250"].total_eligible} (K250) &bull; {EL["500"].total_eligible} (K500) &bull; {EL["1000"].total_eligible} (K1000)</>}
        />
      </div>

      <Connector label="Event-level out-of-fold evaluation" icon={ArrowDown} />

      <div className="bg-white border border-[#15263a] p-5 sm:p-6 grid grid-cols-1 md:grid-cols-[auto_1fr] gap-x-8 gap-y-3 items-center">
        <div className="flex items-center gap-2 font-mono text-xs font-bold uppercase tracking-wider text-[#15263a]">
          <BarChart3 size={14} className="text-[#23527c]" />
          <span>Stage 3: Evaluation</span>
        </div>
        <p className="text-sm text-[#4a4740] leading-relaxed">
          Event-level stratified 5-fold cross-validation with hyperparameters tuned by inner 3-fold cross-validation inside each training fold. Balanced accuracy and log loss are separate estimands with separately tuned fits; AUC is secondary. Differences use an event-level paired bootstrap ({paper.study1.n_bootstrap.toLocaleString("en-US")} resamples) of fixed out-of-fold predictions, with Holm correction for the confirmatory contrasts.
        </p>
      </div>

      <div className="fig-caption mt-8">
        <strong>FLOWCHART 1. Study Design.</strong> Every evaluated event is scored by a model that did not train on it, and all sampled views of an event share its fold. Frozen full-graph models score each sampled event with the fold model that held that event out.
      </div>
    </div>
  );
}
