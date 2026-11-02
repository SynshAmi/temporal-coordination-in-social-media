import React, { useState } from "react";
import Fig1SizeConfounding from "../components/Fig1SizeConfounding";
import Fig2Baselines from "../components/Fig2Baselines";
import NK from "../components/NK";
import { ArrowRight, ChevronDown, ChevronUp, FileText, CheckCircle2, ShieldCheck, AlertTriangle } from "lucide-react";
import { f2, f3, sg, ci, ciu, pct, pct0, con, cond, baMaxHi, vmf, proxyR2 } from "../lib/fmt";

export default function PageOverview({ data, setActiveTab }) {
  const P = data.paper, V = data.revision;
  const SP = V.repeated_splits_signs, H1 = V.h1, CH = V.null_feature_change;
  const k1000 = V.rq2_baselines.budget_specific_K1000;
  const stats = data.cohort_statistics;
  const eventPoints = data.event_points;
  const D = P.dataset, NM = P.null_model, MT = P.matching, EL = P.eligibility;
  const lr = P.study1.performance.logreg, LC = P.study1.confirmatory.logreg;
  const rt = con(P, 250, "retrain_effect_struct6");
  const r2 = P.study2.mechanism_r2_K250;
  const extra = D.n_events - D.official_len_small.n_graphs;

  const [showFullAbstract, setShowFullAbstract] = useState(false);
  const [openRq, setOpenRq] = useState(null);
  const [activeInterpretationTab, setActiveInterpretationTab] = useState("takeaway");
  const toggleRq = (id) => setOpenRq(openRq === id ? null : id);

  return (
    <div className="space-y-16 lg:space-y-20">
      {/* 1. Hero */}
      <section className="border-b border-[#dcd7ca] pb-16 lg:pb-20">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 xl:gap-16 items-start">
          <div className="lg:col-span-7 space-y-6">
            <div className="flex flex-wrap items-center gap-2 text-xs font-mono font-semibold tracking-wider uppercase text-[#8f2626]">
              <span className="w-2 h-2 rounded-full bg-[#8f2626]"></span>
              <span>Benchmark Validity Study</span>
              <span className="text-[#a8a396]">/</span>
              <span className="text-[#5e5a52]">LEN-Small, ICWSM 2025</span>
            </div>

            <h1 className="page-title max-w-[30ch]">
              What Does LEN-Small Measure? Predictive Information Beyond Scale in Retained Engagement Graphs
            </h1>

            <p className="text-base sm:text-lg text-[#3c3a37] font-sans leading-relaxed max-w-[60ch]">
              LEN-Small is a benchmark of Twitter engagement graphs labeled as campaign-associated or comparison events. We ask what its labels can be predicted from, and how much of that information survives when only a fixed-size sample of edges is observed.
            </p>

            <p className="text-[15px] text-[#4a4740] font-sans leading-relaxed max-w-[64ch]">
              A high benchmark score is usually read as evidence that a model has learned something about coordination. Whether that reading is justified depends on what the labels are predictable from. The unit of analysis is the event graph throughout; we make no claims about individual accounts, bots, intent or causal effects.
            </p>

            <div className="pt-2 flex flex-wrap items-center gap-2 sm:gap-3 text-xs font-mono text-[#5e5a52]">
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-[#ede8dc] border border-[#d8d3c5] text-[#15263a]">
                <CheckCircle2 size={12} className="text-[#23527c]" />
                <span>N = {D.n_events} Events</span>
              </span>
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-[#ede8dc] border border-[#d8d3c5] text-[#15263a]">
                <ShieldCheck size={12} className="text-[#23527c]" />
                <span>Paired Event-Level Inference</span>
              </span>
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-[#ede8dc] border border-[#d8d3c5] text-[#15263a]">
                <ShieldCheck size={12} className="text-[#23527c]" />
                <span>{P.verification.n_pass}/{P.verification.n_checks} Independent Checks Pass</span>
              </span>
            </div>

            <DatasetInvite eventPoints={eventPoints} onOpen={() => setActiveTab("dataset")} />
          </div>

          <div className="lg:col-span-5 space-y-5 lg:pt-1">
            <div className="p-5 sm:p-7 lg:p-8 bg-[#f4efe6] border border-[#d8d3c5] border-l-4 border-l-[#8f2626] shadow-2xs space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-2 font-mono text-xs">
                <span className="font-bold uppercase tracking-wider text-[#8f2626]">Core Finding</span>
                <span className="text-[11px] text-[#757065]">Study 1 · LR · N = {D.n_events}</span>
              </div>
              <p className="text-[15px] text-[#2a2825] leading-relaxed font-sans">
                Node and edge counts alone reach <strong>balanced accuracy {f3(lr.M0.balanced_accuracy)}</strong>. Adding degree, arrangement and content features did not detectably improve classification decisions (ΔBA {sg(LC.C1.ba.delta_ba)}, 95% interval {ci(LC.C1.ba.delta_ba_ci)}), but improved probability quality and ranking.
              </p>

              <div className="grid grid-cols-3 gap-2 sm:gap-3 pt-4 border-t border-[#e2dcd0] text-center font-mono">
                <div className="bg-white px-2 py-3 border border-[#dcd7ca]">
                  <div className="text-[10.5px] uppercase tracking-wide text-[#757065]">Counts BA</div>
                  <div className="text-lg font-bold text-[#8f2626]">{f3(lr.M0.balanced_accuracy)}</div>
                  <div className="text-[10px] text-[#757065]">M0</div>
                </div>
                <div className="bg-white px-2 py-3 border border-[#dcd7ca]">
                  <div className="text-[10.5px] uppercase tracking-wide text-[#757065]">All Feat. BA</div>
                  <div className="text-lg font-bold text-[#15263a]">{f3(lr.M4.balanced_accuracy)}</div>
                  <div className="text-[10px] text-[#757065]">M4</div>
                </div>
                <div className="bg-white px-2 py-3 border border-[#dcd7ca]">
                  <div className="text-[10.5px] uppercase tracking-wide text-[#757065]">Δ Log Loss</div>
                  <div className="text-lg font-bold text-[#23527c]">{sg(LC.C1.log_loss.delta_logloss)}</div>
                  <div className="text-[10px] text-[#757065]">M4 − M0q</div>
                </div>
              </div>
              <p className="text-[11px] font-mono text-[#757065] leading-relaxed">
                Log loss {f3(lr.M0q.log_loss)} → {f3(lr.M4.log_loss)}, interval {ci(LC.C1.log_loss.delta_logloss_ci)}, Holm p = {f3(LC.C1.log_loss.p_holm)}. The BA result is inconclusive, not evidence of equivalence.
              </p>
            </div>

            <div className="p-5 sm:p-6 bg-white border border-[#dcd7ca] text-xs font-mono text-[#4a4740] space-y-3">
              <div className="font-bold text-[#15263a] uppercase tracking-wider text-[11px] pb-2 border-b border-[#e5e0d4]">
                Data & Provenance
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-1 xl:grid-cols-2 gap-x-6 gap-y-2 text-xs">
                <div><span className="text-[#757065]">Analysed archive: </span><strong className="text-[#15263a]">{D.n_events} events ({D.n_campaign}/{D.n_comparison})</strong></div>
                <div><span className="text-[#757065]">Official release: </span><strong className="text-[#15263a]">{D.official_len_small.n_graphs} ({D.official_len_small.n_campaign}/{D.official_len_small.n_noncampaign})</strong></div>
                <div><span className="text-[#757065]">Model: </span><strong className="text-[#15263a]">LR primary, HGBT secondary</strong></div>
                <div><span className="text-[#757065]">Account IDs: </span><strong className="text-[#15263a]">none in release</strong></div>
              </div>
              <div className="flex items-start gap-2 pt-3 border-t border-[#e5e0d4] text-[#8f2626] leading-relaxed">
                <AlertTriangle size={13} className="shrink-0 mt-0.5" />
                <span>The analysed archive holds {extra} more events than the official release, for a reason we could not determine. All results refer to the {D.n_events}-event archive.</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 2. Abstract */}
      <section className="border-b border-[#dcd7ca] pb-16 lg:pb-20">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12 xl:gap-16 items-start">
          <div className="lg:col-span-5 xl:col-span-4">
            <span className="section-label">Abstract</span>
            <h2 className="section-title">Summary of Findings</h2>
            <p className="head-desc">
              A short summary, with the paper's full abstract on request.
            </p>
            <button
              type="button"
              onClick={() => setShowFullAbstract(!showFullAbstract)}
              aria-expanded={showFullAbstract}
              className="inline-flex items-center gap-2 px-4 py-2.5 bg-white border border-[#d8d3c5] hover:border-[#15263a] text-xs font-mono font-medium text-[#15263a] transition-colors shadow-2xs mt-6"
            >
              <span>{showFullAbstract ? "Collapse to summary" : "Read the paper's abstract"}</span>
              {showFullAbstract ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
            </button>
          </div>

          <div className="lg:col-span-7 xl:col-span-8">
            <div className="text-[17px] text-[#2a2825] font-sans leading-[1.75] max-w-[68ch]">
              <p>
                On this archive, the released labels are highly predictable from how large an event graph is. Richer features improve probability quality and ranking, without a reliable improvement in classification decisions. In fixed-size edge samples, a model trained on single samples was not detectably less accurate than the full-graph model on the same events; the number of distinct endpoints a sample touches and its structural features carry largely overlapping, size-like information. Training on observations of the kind being scored matters far more than averaging many views.
              </p>
            </div>

            {showFullAbstract && (
              <div className="mt-6 pt-6 border-t border-[#e2dcd0] text-[15px] text-[#3c3a37] space-y-4 font-sans leading-relaxed max-w-[72ch]">
                <p>
                  LEN-Small is a benchmark of Twitter engagement graphs labeled as campaign-associated or comparison events. We ask what its labels can be predicted from. On a distributed archive of {D.n_events} canonical event graphs, {extra} more than the official {D.official_len_small.n_graphs}-graph release, logistic regression given only node and edge counts reaches a balanced accuracy of {f3(lr.M0.balanced_accuracy)}. Adding degree, higher-order arrangement and content features did not detectably improve balanced accuracy on the primary fold split (paired difference {sg(LC.C1.ba.delta_ba)}, 95 percent interval {sg(LC.C1.ba.delta_ba_ci[0])} to {sg(LC.C1.ba.delta_ba_ci[1])}), although its point estimate was positive, and small, in all {SP.n_splits} fold splits examined. The same features improved log loss by {f3(-LC.C1.log_loss.delta_logloss)} (in {SP.C1.n_dLL_negative} of {SP.n_splits} splits) and ranking quality by {f3(LC.C1.auc_ll_fit.delta_auc)} in area under the curve.
                </p>
                <p>
                  The arrangement features showed no detectable improvement over the same features computed on degree-preserving rewired graphs. In fixed-budget edge samples, a model trained on single views was not detectably less accurate than the full-graph model on the same events. Much of the information in a view is size-like: the number of distinct sampled endpoints, whose expectation is strongly associated with full-graph node count and mean degree, is also closely encoded by the structural features. Training on observations of the kind being scored matters far more than averaging repeated views. The results describe what the released labels are predictable from; they do not detect coordinating accounts.
                </p>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* 3. Research questions */}
      <section>
        <div className="section-head">
          <h2 className="section-title">Research Questions</h2>
          <span className="section-head-meta">Two Studies</span>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-10">
          <div className="bg-white border border-[#dcd7ca] p-5 sm:p-8 flex flex-col gap-6">
            <div>
              <div className="flex flex-wrap items-center gap-x-3 gap-y-2 mb-4">
                <span className="font-mono text-xs font-bold px-2 py-0.5 bg-[#15263a] text-white">RQ 1</span>
                <span className="text-xs font-mono uppercase tracking-wider text-[#757065]">Incremental Information</span>
              </div>
              <h3 className="subsection-title">
                What do degree concentration, higher-order arrangement and retained content add beyond node and edge counts?
              </h3>
              <p className="text-[15px] text-[#4a4740] font-sans mt-3 leading-relaxed">
                Seven feature sets in two nested chains on identical folds, three primary paired contrasts, and a degree-preserving rewiring null for arrangement features.
              </p>
              <div className="mt-5 p-4 bg-[#fbfaf6] border border-[#e5e0d4] text-xs font-mono text-[#8f2626] leading-relaxed">
                <strong>Finding:</strong> No contrast shows a detectable BA gain. All features vs counts improve log loss by {f3(-LC.C1.log_loss.delta_logloss)} {ci(LC.C1.log_loss.delta_logloss_ci)} and AUC by {f3(LC.C1.auc_ll_fit.delta_auc)}. Real vs rewired arrangement: ΔBA {sg(NM.real_minus_null_ba.delta_ba)} {ci(NM.real_minus_null_ba.delta_ba_ci)}, no detectable improvement.
              </div>
            </div>

            <div className="mt-auto pt-4 border-t border-[#e5e0d4]">
              <button
                type="button"
                onClick={() => toggleRq("rq1")}
                aria-expanded={openRq === "rq1"}
                className="inline-flex items-center gap-1.5 text-xs font-mono text-[#23527c] hover:text-[#15263a] transition-colors"
              >
                <span>{openRq === "rq1" ? "Hide details" : "How to read these results"}</span>
                {openRq === "rq1" ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
              </button>
              {openRq === "rq1" && (
                <div className="mt-4 p-4 sm:p-5 bg-[#f4efe6] text-[13px] text-[#3c3a37] space-y-2.5 leading-relaxed font-sans">
                  <p><strong>Inconclusive, not equivalent:</strong> the BA intervals admit gains of up to about {f2(baMaxHi(P))}. With {D.n_events} events, a null BA result is not evidence that the features are useless.</p>
                  <p><strong>Null model:</strong> real graphs differ strongly from their rewired counterparts, so their arrangement is not random, but the tested arrangement features showed no detectable improvement over the degree sequences. The rewiring is a constrained comparison: it changed reciprocity in {pct0(CH.reciprocity.share_events_changed_in_some_realization)}% of events and the largest-component fraction in {pct0(CH.largest_wcc_fraction.share_events_changed_in_some_realization)}%, but the median core number in only {pct0(CH.coreness_median.share_events_changed_in_some_realization)}%. This is neither evidence of equivalence nor evidence that topology is uninformative.</p>
                  <p><strong>Fold splits:</strong> the bootstrap intervals resample events for one fixed set of predictions; refitting on {SP.n_splits} fold splits measures a different source of variation. The C1 BA difference was positive in all {SP.C1.n_dBA_positive} ({sg(P.study1.repeated_splits_lr.C1.dBA_min)} to {sg(P.study1.repeated_splits_lr.C1.dBA_max)}), but the splits reuse the same events, so this does not establish a reliable gain.</p>
                  <p><strong>Regularization grid:</strong> widening the count model's C grid to {H1.grid[0]}–{H1.grid[H1.grid.length - 1].toLocaleString("en-US")} made its log loss worse ({f3(lr.M0q.log_loss)} → {f3(H1.M0q.log_loss)}), and C1 log loss became {sg(H1.C1.delta_logloss)} {ci(H1.C1.delta_logloss_ci)}, so under-tuning does not explain the gap. Some other fits still chose the largest C in some folds.</p>
                </div>
              )}
            </div>
          </div>

          <div className="bg-white border border-[#dcd7ca] p-5 sm:p-8 flex flex-col gap-6">
            <div>
              <div className="flex flex-wrap items-center gap-x-3 gap-y-2 mb-4">
                <span className="font-mono text-xs font-bold px-2 py-0.5 bg-[#23527c] text-white">RQ 2</span>
                <span className="text-xs font-mono uppercase tracking-wider text-[#757065]">Restricted Observation</span>
              </div>
              <h3 className="subsection-title">
                How much label information survives in a single fixed-size sample of edges, and what makes it predictive?
              </h3>
              <p className="text-[15px] text-[#4a4740] font-sans mt-3 leading-relaxed">
                Single K-edge views (K ∈ &#123;250, 500, 1000&#125;) with full-graph, frozen-transfer and retrained conditions sharing events, folds and feature definitions.
              </p>
              <div className="mt-5 p-4 bg-[#fbfaf6] border border-[#e5e0d4] text-xs font-mono text-[#23527c] leading-relaxed">
                <strong>Finding:</strong> On the same events, view-trained models with all features were not detectably less accurate than full-graph models (ΔBA, view − full: {sg(vmf(V, 250).ba.delta)} {ci(vmf(V, 250).ba.ci)} at K = 250, {sg(vmf(V, 500).ba.delta)} {ci(vmf(V, 500).ba.ci)} at K = 500). <NK /> alone ({f3(cond(P, 250, "KK|NK").single_view_ba_mean)} at K = 250) and structure alone did not differ detectably. Retraining on views vs frozen transfer, same structural features, K = 250: +{f3(rt.ba.delta)} {ciu(rt.ba.ci)}.
              </div>
            </div>

            <div className="mt-auto pt-4 border-t border-[#e5e0d4]">
              <button
                type="button"
                onClick={() => toggleRq("rq2")}
                aria-expanded={openRq === "rq2"}
                className="inline-flex items-center gap-1.5 text-xs font-mono text-[#23527c] hover:text-[#15263a] transition-colors"
              >
                <span>{openRq === "rq2" ? "Hide details" : "What the endpoint count reflects"}</span>
                {openRq === "rq2" ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
              </button>
              {openRq === "rq2" && (
                <div className="mt-4 p-4 sm:p-5 bg-[#f4efe6] text-[13px] text-[#3c3a37] space-y-2.5 leading-relaxed font-sans">
                  <p>The expected number of distinct endpoints in a fixed-budget edge sample is strongly associated with full-graph node count and mean degree. Together, these variables explain {pct(r2["log N + log mean degree"])}% of its variation at K = 250 in the analysed archive. Adding in/out-degree Gini provides no measurable additional explanatory power.</p>
                  <p><strong>Overlap with structure:</strong> the six structural features predict log <NK /> with cross-validated R² of {f3(proxyR2(V, 250))}, {f3(proxyR2(V, 500))} and {f3(proxyR2(V, 1000))} at K = 250, 500 and 1000, so <NK /> and structure carry largely overlapping, size-like information; the analysis does not attribute the signal to <NK /> rather than structure.</p>
                  <p><strong>K = 1000:</strong> the view-trained model was ahead of the full-graph model (ΔBA {sg(vmf(V, 1000).ba.delta)} {ci(vmf(V, 1000).ba.ci)}; Δ log loss {sg(vmf(V, 1000).log_loss.delta)} {ci(vmf(V, 1000).log_loss.ci)}), but on a small, imbalanced cohort ({k1000.n_events} events, {k1000.n_campaign}/{k1000.n_comparison}) in an exploratory, uncorrected comparison. It does not indicate that sampling generally improves classification.</p>
                  <p><strong>Ensembling:</strong> averaging ten views changes BA by at most {f3(Math.max(...[250, 500, 1000].map((k) => Math.abs(con(P, k, "ensemble_vs_single_combined").ba.delta))))}.</p>
                  <p><strong>K = 2000:</strong> infeasible for five-fold stratified evaluation; only {EL["2000"].campaign_eligible} campaign events have at least 2,000 edges.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* 4. Figures 1 & 2 */}
      <section>
        <div className="section-head">
          <h2 className="section-title">Section 1. Size and Incremental Information</h2>
          <span className="section-head-meta">Study 1, Full Cohort</span>
        </div>
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-8 lg:gap-10 items-start">
          <Fig1SizeConfounding eventPoints={eventPoints} stats={stats} dataset={D} />
          <Fig2Baselines paper={P} />
        </div>
      </section>

      {/* 5. Interpretation */}
      <section className="bg-white border border-[#dcd7ca] p-5 sm:p-8 lg:p-10">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12 items-start">
          <div className="lg:col-span-4 space-y-5">
            <div>
              <span className="section-label">Interpretation</span>
              <h2 className="section-title">What the Results Do and Do Not Show</h2>
              <p className="head-desc">Implications for evaluation on this benchmark, and the limits of the evidence.</p>
            </div>
            <p className="text-sm text-[#4a4740] font-sans leading-relaxed">
              LEN-Small was constructed as the smallest LEN graphs by node count, yet comparison events in it remain several times larger than campaign events (median {Math.round(D.nodes.comparison.median).toLocaleString("en-US")} vs {Math.round(D.nodes.campaign.median).toLocaleString("en-US")} nodes).
            </p>
            <div className="space-y-2 pt-1 text-xs font-mono" role="tablist" aria-label="Interpretation topics">
              {[
                { id: "takeaway", label: "1. Main Takeaway" },
                { id: "implications", label: "2. Implications for Evaluation" },
                { id: "limitations", label: "3. Limitations" },
              ].map((tab) => (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => setActiveInterpretationTab(tab.id)}
                  role="tab"
                  aria-selected={activeInterpretationTab === tab.id}
                  className={`w-full text-left px-4 py-3 border transition-colors ${
                    activeInterpretationTab === tab.id
                      ? "bg-[#15263a] text-white border-[#15263a] font-medium shadow-xs"
                      : "bg-[#faf8f5] text-[#3c3a37] border-[#d8d3c5] hover:bg-[#ede9df]"
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>

          <div className="lg:col-span-8 flex flex-col gap-6">
            <div role="tabpanel" className="bg-[#fbfaf6] border border-[#e5e0d4] p-5 sm:p-8 text-[15px] font-sans text-[#3c3a37] leading-relaxed space-y-4">
              {activeInterpretationTab === "takeaway" && (
                <>
                  <div className="font-mono font-bold text-xs uppercase tracking-wider text-[#15263a] pb-3 border-b border-[#e5e0d4]">
                    Counts Carry Most of the Decision-Relevant Signal
                  </div>
                  <p>
                    Counts reach most of the balanced accuracy reached by the evaluated models, and richer features did not produce a detectable improvement in classification decisions. They did improve probability quality and ranking (log loss {f3(lr.M0q.log_loss)} → {f3(lr.M4.log_loss)}; AUC {f3(lr.M0q.roc_auc_ll_fit)} → {f3(lr.M4.roc_auc_ll_fit)}), but the source of this gain is not isolated: neither arrangement beyond degree nor content alone reproduces it.
                  </p>
                  <p>
                    Under restricted observation, a single view was not detectably less informative than the full graph with the same features. Much of that information is size-like: the number of distinct endpoints a view touches is strongly associated with the full graph's node count and mean degree, and is itself closely encoded by the structural features. A model needs to be trained on observations like those it will see: frozen transfer from full graphs loses accuracy at small budgets, while averaging many views adds almost nothing.
                  </p>
                </>
              )}
              {activeInterpretationTab === "implications" && (
                <>
                  <div className="font-mono font-bold text-xs uppercase tracking-wider text-[#15263a] pb-3 border-b border-[#e5e0d4]">
                    Recommendations for Evaluation on LEN-Small
                  </div>
                  <p><strong>1. Report a count-only baseline.</strong> Reported accuracy should be read against a model given only node and edge counts (BA {f3(lr.M0.balanced_accuracy)} here).</p>
                  <p><strong>2. Separate decision and probability metrics.</strong> Features that leave balanced accuracy unchanged can still improve probability scores (log loss, a proper scoring rule that reflects both calibration and discrimination; calibration was not assessed separately), which matters when thresholds are chosen after deployment.</p>
                  <p><strong>3. Match training to the observation regime.</strong> At K = 250, training on single views instead of full graphs raised single-view BA by {f3(rt.ba.delta)} with the same structural features, events and folds.</p>
                </>
              )}
              {activeInterpretationTab === "limitations" && (
                <>
                  <div className="font-mono font-bold text-xs uppercase tracking-wider text-[#15263a] pb-3 border-b border-[#e5e0d4]">
                    Limits of the Evidence
                  </div>
                  <p><strong>1. Sample size.</strong> With {D.n_events} events, null BA results are inconclusive. Paired intervals exclude refitting and split variability; the primary split shows the smallest C1 BA gain of the {SP.n_splits} splits. Hyperparameter selection in small inner folds was sensitive to row order and, for log loss, to the width of the regularization grid.</p>
                  <p><strong>2. Provenance.</strong> The archive differs from the official release for an unknown reason. Labels come from file names; account identifiers and campaign subtypes are not available, so dependence between events through shared accounts and subtype heterogeneity cannot be assessed. Repeated hashtags: {V.n_repeated_hashtag_pairs} campaign hashtags each appear as two events on nearby dates ({V.n_repeated_hashtag_pairs_split_across_folds} pair split across folds). LEN-Small is selected by node count, so size–label associations here need not hold in the full LEN dataset. Timestamp semantics are unverified, so no temporal features are used.</p>
                  <p><strong>3. Null model and matching.</strong> Rewiring mixes incompletely in hub-dominated graphs (median {Math.round(100 * NM.frac_edges_unchanged_quantiles[2])}% of non-loop edges unmoved), leaves the median core number almost unchanged and uses only {NM.realizations} realizations. Matching keeps {MT.node_only.n_pairs_range[0]}–{MT.node_only.n_pairs_range[1]} pairs, is exploratory and is reported without sampling intervals.</p>
                  <p><strong>4. Scope.</strong> Only LR and HGBT on hand-crafted features were evaluated; graph neural networks and the LEN and DECODE methods were not re-run, and published LEN-Small accuracies use a different protocol and metric. Uniform edge sampling is one observation mechanism among many, and the Study 2 contrasts are exploratory ({V.study2_n_bootstrap.toLocaleString("en-US")} bootstrap resamples, no multiplicity correction). Nothing here establishes that any model detects coordinated behavior, accounts or intent, or any causal effect.</p>
                </>
              )}
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <button
                type="button"
                onClick={() => setActiveTab("explorer")}
                className="inline-flex items-center gap-2 px-4 py-2.5 bg-[#15263a] text-white text-xs font-medium tracking-wide hover:bg-[#23527c] transition-colors shadow-2xs"
              >
                <span>Explore Matching & Edge-Budget Results</span>
                <ArrowRight size={13} />
              </button>
              <button
                type="button"
                onClick={() => setActiveTab("methods")}
                className="inline-flex items-center gap-2 px-4 py-2.5 bg-white border border-[#15263a] text-[#15263a] text-xs font-medium tracking-wide hover:bg-[#f2eee5] transition-colors"
              >
                <FileText size={13} />
                <span>Read Methods & Reproducibility</span>
              </button>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

// Landing-page entry to the dataset explorer: one row per event, placed by node count (log scale)
function DatasetInvite({ eventPoints, onOpen }) {
  const W = 560, H = 64;
  const xs = eventPoints.map((e) => e.log_nodes);
  const lo = Math.min(...xs), hi = Math.max(...xs);
  const X = (v) => 6 + ((v - lo) / (hi - lo)) * (W - 12);
  const ticks = [100, 300, 1000, 3000].filter((t) => Math.log1p(t) >= lo && Math.log1p(t) <= hi);
  return (
    <div className="pt-8 mt-4 border-t border-[#dcd7ca] max-w-[64ch]">
      <div className="flex items-baseline justify-between gap-4">
        <span className="section-label !mb-0">Explore the dataset</span>
        <span className="text-[11px] font-mono text-[#757065]">{eventPoints.length} engagement graphs</span>
      </div>
      <p className="mt-3 font-serif text-[22px] sm:text-2xl leading-snug text-[#15263a]">
        Go beyond the findings. Explore actual engagement networks, compare events, and investigate how graph structure changes under fixed-budget sampling.
      </p>
      <svg viewBox={`0 0 ${W} ${H}`} className="mt-5 w-full h-auto" role="img" aria-label="Every event in the archive, placed by node count; campaign events above, comparison events below">
        <line x1="0" x2={W} y1={H / 2 - 4} y2={H / 2 - 4} stroke="#dcd7ca" />
        {eventPoints.map((e) => (
          <line key={e.event_id} x1={X(e.log_nodes)} x2={X(e.log_nodes)}
            y1={e.label === 1 ? 6 : H / 2} y2={e.label === 1 ? H / 2 - 8 : H - 18}
            stroke={e.label === 1 ? "#8f2626" : "#23527c"} strokeOpacity="0.55" strokeWidth="1.5" />
        ))}
        {ticks.map((t) => (
          <text key={t} x={X(Math.log1p(t))} y={H - 4} textAnchor={X(Math.log1p(t)) < 40 ? "start" : X(Math.log1p(t)) > W - 40 ? "end" : "middle"} fontSize="10" fill="#757065" fontFamily="var(--font-mono)">{t >= 1000 ? `${t / 1000}k` : t} nodes</text>
        ))}
      </svg>
      <div className="mt-2 flex flex-wrap items-center justify-between gap-x-6 gap-y-3">
        <div className="flex gap-4 text-[11px] font-mono text-[#5e5a52]">
          <span className="inline-flex items-center gap-1.5"><span className="w-3 h-[2px] bg-[#8f2626]" />campaign</span>
          <span className="inline-flex items-center gap-1.5"><span className="w-3 h-[2px] bg-[#23527c]" />comparison</span>
        </div>
        <button type="button" onClick={onOpen}
          className="inline-flex items-center gap-2 px-4 py-2.5 bg-[#15263a] text-white text-xs font-medium tracking-wide hover:bg-[#23527c] transition-colors">
          <span>Explore LEN-Small</span>
          <ArrowRight size={13} />
        </button>
      </div>
    </div>
  );
}
