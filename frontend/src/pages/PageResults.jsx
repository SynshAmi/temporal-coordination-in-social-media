import React, { useEffect, useRef, useState } from "react";
import Fig1SizeConfounding from "../components/Fig1SizeConfounding";
import IntervalChart from "../components/IntervalChart";
import EdgeBudgetChart from "../components/EdgeBudgetChart";
import ResultsTable from "../components/ResultsTable";
import NK from "../components/NK";
import { f3, sg, ci, pct } from "../lib/fmt";
import { fullContrastRows, edgeSeries, edgeContrastRows, dispersionRows, cohorts, KS } from "../lib/results";

const METRIC_NAME = { log_loss: "Δ log loss", auc: "Δ AUC", ba: "Δ balanced accuracy" };

const SECTIONS = [
  ["study1", "Study 1: full observation"],
  ["full-comparisons", "Full-graph comparisons"],
  ["sensitivity", "Sensitivity and exploratory"],
  ["study2", "Study 2: edge-limited"],
  ["edge-comparisons", "Edge-limited comparisons"],
  ["dispersion", "Token-count dispersion"],
  ["table", "Results table"],
];

export default function PageResults({ data }) {
  const P = data.paper, A = data.audit;
  const LC = P.study1.confirmatory.logreg, lr = P.study1.performance.logreg;
  const C = A.study1_20_partitions.contrasts, nPart = A.study1_20_partitions.n_partitions;
  const E = A.edge_limited_token_std, H = A.study2_contrasts_holm.contrasts;
  const mech = P.study2.mechanism.K250, r2 = P.study2.mechanism_r2_K250, S = data.revision;
  const NM = P.null_model, X = A.text_retention;

  const [m1, setM1] = useState("log_loss");
  const [part, setPart] = useState("primary");
  const [m2, setM2] = useState("log_loss");
  const [kc, setKc] = useState(250);
  const [mc, setMc] = useState("log_loss");
  const [md, setMd] = useState("log_loss");
  const [cd, setCd] = useState("KK");

  return (
    <div>
      <header className="pb-6 max-w-4xl">
        <span className="section-label">Results</span>
        <h1 className="page-title">What the counts predict, and what adds to them</h1>
        <p className="mt-3 text-[18px] text-[#2f2d2a] leading-relaxed max-w-[72ch]">
          Log loss leads every comparison: it is a proper scoring rule and does not depend on a decision threshold. AUC is the ranking metric and
          balanced accuracy the decision metric. Results are grouped by the evidence behind them. <em>Prespecified comparisons</em> were fixed
          before the final analysis and are Holm-adjusted. <em>Sensitivity analyses</em> repeat a question under other partitions, event sets or
          baselines. <em>Exploratory analyses</em> were planned but sit outside the prespecified family. <em>Post-hoc analyses</em> were chosen
          after inspecting these data.
        </p>
      </header>

      <SectionNav />

      <div className="space-y-14 lg:space-y-16 pt-10">
        {/* ---------------- Study 1 ---------------- */}
        <Section id="study1" kicker="Study 1" title="Full observation" meta={`${P.dataset.n_events} events · logistic regression · 5-fold out-of-fold predictions`}>
          <div className="grid grid-cols-1 xl:grid-cols-12 gap-8">
            <div className="xl:col-span-7">
              <Fig1SizeConfounding eventPoints={data.event_points} stats={data.cohort_statistics} dataset={P.dataset} />
            </div>
            <div className="xl:col-span-5 space-y-5">
              <Note title="Counts alone">
                Logistic regression on log node and edge counts reaches log loss {f3(lr.M0.log_loss)}, AUC {f3(lr.M0.roc_auc_ll_fit)} and balanced
                accuracy {f3(lr.M0.balanced_accuracy)}; node count alone reaches balanced accuracy {f3(P.run_v2_metrics.B0a_log_node_logreg.balanced_accuracy)}.
                The classes overlap in the middle of the size range, which is why counts predict well but not perfectly.
              </Note>
              <Note title="All features">
                M4 adds degree concentration, arrangement and content: log loss {f3(lr.M4.log_loss)}, AUC {f3(lr.M4.roc_auc_ll_fit)}, balanced accuracy{" "}
                {f3(lr.M4.balanced_accuracy)}. Whether that difference is detectable is the question of the paired comparisons below.
              </Note>
            </div>
          </div>
        </Section>

        <Section id="full-comparisons" title="Full-graph model comparisons">
          <figure className="panel">
            <FigHead
              n="Figure 2"
              title="Paired contrasts under full observation"
              desc="Each row is the difference between two nested models on identical events, with a 95% event-level paired bootstrap interval."
            >
              <Segmented value={m1} onChange={setM1} options={[["log_loss", "Log loss"], ["auc", "AUC"], ["ba", "Balanced accuracy"]]} label="Metric" />
              <Segmented value={part} onChange={setPart} options={[["primary", "Prespecified partition"], ["twenty", `${nPart} partitions`]]} label="Partitioning" />
            </FigHead>
            <IntervalChart
              rows={fullContrastRows(data, m1, part)}
              xLabel={METRIC_NAME[m1]}
              better={m1 === "log_loss" ? "lower" : "higher"}
              extraLabel={part === "primary" ? (m1 === "auc" ? "" : "Holm-adjusted p") : "Partitions with lower log loss"}
              groupNotes={part === "primary"
                ? { primary: "Holm-adjusted over the three tests for each metric", exploratory: "Unadjusted" }
                : { primary: "Unadjusted over repartitions", exploratory: "Unadjusted", sensitivity: "Unadjusted", posthoc: "Unadjusted; chosen after inspecting these data" }}
              ariaLabel="Paired contrasts under full observation"
            />
            <figcaption className="fig-note">
              {part === "primary"
                ? "Sensitivity and post-hoc rows exist only for the repartitioned analysis; switch the partitioning to see them."
                : `Out-of-fold predictions are averaged across ${nPart} partitions before bootstrapping. The partitions reuse the same events and are not independent replications.`}
            </figcaption>
          </figure>
          <div className="mt-6 max-w-[80ch]">
            <Note title="Probabilistic gains, without a detectable gain in decisions">
              Adding every other feature to the counts (C1) changed log loss by {sg(LC.C1.log_loss.delta_logloss)} {ci(LC.C1.log_loss.delta_logloss_ci)}{" "}
              (Holm-adjusted p = {f3(LC.C1.log_loss.p_holm)}) and AUC by {sg(LC.C1.auc_ll_fit.delta_auc)} {ci(LC.C1.auc_ll_fit.delta_auc_ci)}, but balanced accuracy
              by only {sg(LC.C1.ba.delta_ba)} {ci(LC.C1.ba.delta_ba_ci)}. At the 0.5 threshold, the richer model classified {LC.C1.ba.mcnemar_a_right_b_wrong} events
              correctly that the count model missed and missed {LC.C1.ba.mcnemar_b_right_a_wrong} that it got right: it moves most predicted probabilities toward the
              correct class, but few of those moves change a decision.
            </Note>
          </div>
        </Section>

        <Section id="sensitivity" title="Sensitivity and exploratory analyses" meta="How firm the full-observation result is, and where it comes from">
          <EvidenceGroup title="Sensitivity analyses" note="The same question under other partitions, event sets or baselines; unadjusted">
            <Note title={`${nPart} repartitions`}>
              The prespecified interval omits partition variability, so the analysis was repeated over {nPart} outer partitions: C1 was {sg(C.C1.dLL)} {ci(C.C1.dLL_ci)},
              in the same direction in {C.C1.repeats_favouring_A_LL} of {C.C1.n_repeats}. The partitions reuse the same events.
            </Note>
            <Note title="Graphs without text">
              Without the {X.events_without_usable_text} campaign graphs that have no usable text, C1 was {sg(C.C1_text101.dLL)} {ci(C.C1_text101.dLL_ci)}: the same direction,
              with an interval that includes zero. The AUC difference ({sg(C.C1_text101.dAUC)} {ci(C.C1_text101.dAUC_ci)}) kept an interval excluding zero.
            </Note>
            <Note title="Flexible count baselines">
              Against a natural-spline count model, the gain was {sg(C.M4_minus_spline.dLL)} {ci(C.M4_minus_spline.dLL_ci)}; against quadratic discriminant analysis on
              the counts, {sg(C.M4_minus_QDA.dLL)} {ci(C.M4_minus_QDA.dLL_ci)}. None of the flexible-baseline comparisons survived Holm correction.
            </Note>
          </EvidenceGroup>
          <EvidenceGroup title="Exploratory analyses" note="Planned, outside the prespecified family; unadjusted">
            <Note title="Structure is conditional">
              Added to counts alone, the six structural features produced no detectable change ({sg(C.M2_minus_M0q.dLL)} {ci(C.M2_minus_M0q.dLL_ci)}); added to counts
              and content, they changed log loss by {sg(C.E2.dLL)} {ci(C.E2.dLL_ci)}. Logistic regression is additive, so this is not a modelled interaction, and it
              does not show that structure is uninformative.
            </Note>
            <Note title="Arrangement and its null">
              Arrangement features from real graphs did not detectably outperform the same features from degree-preserving rewired graphs (log loss{" "}
              {sg(NM.real_minus_null_logloss.delta_logloss)} {ci(NM.real_minus_null_logloss.delta_logloss_ci)}). Rewiring preserves everything the degree sequence
              determines, so this tests a narrow question.
            </Note>
          </EvidenceGroup>
          <EvidenceGroup title="Post-hoc analyses" note="Chosen after inspecting these data; a lead for independent testing, not a result">
            <Note title="One feature comes close to the full set">
              Token-count dispersion alone, added to the counts, changed log loss by {sg(C.tokenstd_beyond_counts.dLL)} {ci(C.tokenstd_beyond_counts.dLL_ci)}, and the full
              feature set did not detectably improve on counts plus this feature ({sg(C.M4_minus_counts_tokenstd.dLL)} {ci(C.M4_minus_counts_tokenstd.dLL_ci)}). Equivalence
              was not tested.
            </Note>
          </EvidenceGroup>
        </Section>

        {/* ---------------- Study 2 ---------------- */}
        <Section id="study2" kicker="Study 2" title="Edge-limited observation" meta="K = 250, 500, 1000 · ten sampling seeds · budget-specific cohorts">
          <p className="mb-6 max-w-[80ch] text-[17.5px] leading-relaxed text-[#2f2d2a]">
            Every edge-limited analysis is exploratory: it was planned, but no comparison in it belongs to the prespecified family. Analyses that single out
            token-count dispersion are post hoc and are reported separately below.
          </p>
          <figure className="panel">
            <FigHead n="Figure 3" title="Single-view performance by edge budget" desc="Means over ten sampling seeds. Cohorts differ by budget, so read the lines within a budget rather than across budgets.">
              <Segmented value={m2} onChange={setM2} options={[["log_loss", "Log loss"], ["auc", "AUC"], ["ba", "Balanced accuracy"]]} label="Metric" />
            </FigHead>
            <EdgeBudgetChart series={edgeSeries(data, m2)} metric={m2} cohorts={cohorts(data)} />
          </figure>
          <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-6">
            <Note title="The count that remains">
              In a K-edge view the edge count is fixed, but <NK /> alone reaches AUC {KS.map((k) => f3(E.performance[`K${k}`].KK.A.auc)).join(", ")} at the three
              budgets. Its expectation depends only on K and the full graph's degree sequence; it matches the observed mean within{" "}
              {pct(mech.max_abs_rel_error_expected_vs_observed)}% at K = 250, and node count and mean degree explain {pct(r2["log N + log mean degree"])}% of its
              variation. A fixed edge budget therefore does not hold size constant.
            </Note>
            <Note title="Structure tracks the count">
              Within views, the six structural features predict log <NK /> with cross-validated R² of{" "}
              {KS.map((k) => f3(S.structure_predicts_log_NK[`K${k}`].r2_event_grouped_cv)).join(", ")}, and adding them to <NK /> produced no detectable change in log
              loss at any budget. Frozen transfer of the full-graph <NK /> model keeps ranking (AUC {f3(P.study2.results.budget_specific_K250.conditions["FK|NK"].single_view_auc_mean)}{" "}
              at K = 250) but collapses decisions to one class (balanced accuracy {f3(P.study2.results.budget_specific_K250.conditions["FK|NK"].single_view_ba_mean)}),
              because a view's node count sits on a different scale.
            </Note>
          </div>
        </Section>

        <Section id="edge-comparisons" title="Edge-limited model comparisons">
          <figure className="panel">
            <FigHead n="Figure 4" title="Paired contrasts within one budget" desc="Regime and feature contrasts on the budget-specific cohort, with Holm-adjusted p-values.">
              <Segmented value={kc} onChange={setKc} options={KS.map((k) => [k, `K = ${k}`])} label="Budget" />
              <Segmented value={mc} onChange={setMc} options={[["log_loss", "Log loss"], ["ba", "Balanced accuracy"]]} label="Metric" />
            </FigHead>
            <IntervalChart
              rows={edgeContrastRows(data, kc, mc)}
              xLabel={METRIC_NAME[mc]}
              better={mc === "log_loss" ? "lower" : "higher"}
              extraLabel="Holm-adjusted p"
              groupNotes={{ exploratory: "Holm-adjusted across the three budgets for each contrast", posthoc: "Holm-adjusted across all six dispersion contrasts" }}
              ariaLabel="Edge-limited paired contrasts"
            />
            <figcaption className="fig-note">
              The view-minus-full-graph contrast has no stored p-value. Averaging ten views changed log loss by at most{" "}
              {f3(Math.max(...KS.map((k) => Math.abs(H.ensemble_vs_single_combined[`K${k}`].log_loss.delta))))}: detectable, but small. On the common cohort of the{" "}
              {P.eligibility["1000"].total_eligible} events eligible at every budget, the structure contrast at K = 250 changes sign (
              {sg(P.study2.contrasts.common_K250.structure_beyond_NK.log_loss.delta)} {ci(P.study2.contrasts.common_K250.structure_beyond_NK.log_loss.ci)}); its
              intervals include zero on both cohorts. In balanced accuracy, dispersion beyond <NK /> at K = 500 survives adjustment, but its AUC barely changes
              ({sg(A.edge_limited_token_std.contrasts.primary.KK["B-A"].K500.dAUC)} {ci(A.edge_limited_token_std.contrasts.primary.KK["B-A"].K500.dAUC_ci)}): a threshold
              effect rather than better ranking.
            </figcaption>
          </figure>
        </Section>

        <Section id="dispersion" title="Token-count dispersion" meta="Post-hoc analyses">
          <p className="mb-6 max-w-[80ch] text-[17.5px] leading-relaxed text-[#2f2d2a]">
            Token-count dispersion, the sample standard deviation of per-text whitespace token counts, was singled out after the full-observation results had been
            examined. Everything in this section is therefore post hoc: it shows a direction worth testing on independent events, not an established effect.
          </p>
          <figure className="panel">
            <FigHead n="Figure 5" title="Token-count dispersion added within views" desc="Computed edge by edge on the retained text of each view; Holm-adjusted across the six dispersion contrasts.">
              <Segmented value={md} onChange={setMd} options={[["log_loss", "Log loss"], ["auc", "AUC"]]} label="Metric" />
              <Segmented value={cd} onChange={setCd} options={[["KK", "Single views (KK)"], ["FF", "Full graphs (FF)"]]} label="Condition" />
            </FigHead>
            <IntervalChart rows={dispersionRows(data, md, cd)} xLabel={METRIC_NAME[md]} better={md === "log_loss" ? "lower" : "higher"}
              extraLabel="Holm-adjusted p" showGroups={false} ariaLabel="Token-count dispersion contrasts by budget" />
            <figcaption className="fig-note">
              After adjustment, only D − C at K = 1000 keeps a log-loss difference below 0.05. View values track full-graph values closely (Spearman ρ ≥{" "}
              {f3(E.spearman_view_vs_full_min)}), as expected for an average over hundreds of edges: a measurement check, not a finding. Model C has the highest log
              loss of the four at K = 1000 ({f3(E.performance.K1000.KK.C.log_loss)}), so D − C is measured against a poorly calibrated baseline, and cohorts change
              with K, so these results do not show a budget trend.
            </figcaption>
          </figure>
        </Section>

        <section id="table" className="scroll-mt-[var(--results-offset,140px)]">
          <ResultsTable experiments={data.experiments} />
        </section>
      </div>
    </div>
  );
}

// Sticky in-page navigation: stays under the site header and marks the section in view.
// Sections carry scroll-margin-top equal to the sticky header + bar, so a link can use the
// browser's own scrollIntoView. While a link-initiated scroll is running, the clicked section
// stays marked; the scroll position takes over again on "scrollend" or on any user scroll input.
function SectionNav() {
  const [active, setActive] = useState(SECTIONS[0][0]);
  const [top, setTop] = useState(64);
  const bar = useRef(null);
  const pending = useRef(null);

  useEffect(() => {
    // the site header's and the bar's heights change with the viewport and when the web fonts load
    const header = document.querySelector("header");
    if (!header || !bar.current) return undefined;
    const measure = () => {
      const h = header.getBoundingClientRect().height;
      setTop(h);
      document.documentElement.style.setProperty("--results-offset", `${Math.ceil(h + bar.current.offsetHeight + 12)}px`);
    };
    measure();
    const ro = new ResizeObserver(measure);
    ro.observe(header);
    ro.observe(bar.current);
    return () => { ro.disconnect(); document.documentElement.style.removeProperty("--results-offset"); };
  }, []);

  useEffect(() => {
    const fromPosition = () => {
      const line = top + (bar.current?.offsetHeight || 48) + 24;
      let current = SECTIONS[0][0];
      for (const [id] of SECTIONS) {
        const el = document.getElementById(id);
        if (el && el.getBoundingClientRect().top - line <= 0) current = id;
      }
      return current;
    };
    const onScroll = () => { if (!pending.current) setActive(fromPosition()); };
    const release = () => { if (pending.current) { pending.current = null; setActive(fromPosition()); } };
    const userInput = () => { pending.current = null; };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("scrollend", release);
    for (const ev of ["wheel", "touchstart", "keydown"]) window.addEventListener(ev, userInput, { passive: true });
    return () => {
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("scrollend", release);
      for (const ev of ["wheel", "touchstart", "keydown"]) window.removeEventListener(ev, userInput);
    };
  }, [top]);

  useEffect(() => {
    // keep the active link visible in the horizontally scrolling bar (mobile)
    const list = bar.current?.querySelector("ul");
    const link = bar.current?.querySelector(`[data-id="${active}"]`);
    if (list && link) list.scrollTo({ left: link.offsetLeft - 16, behavior: "auto" });
  }, [active]);

  const go = (id) => {
    const el = document.getElementById(id);
    if (!el) return;
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    pending.current = id;
    setActive(id);
    el.scrollIntoView({ behavior: reduce ? "auto" : "smooth", block: "start" });
  };

  return (
    <nav ref={bar} aria-label="Results sections" style={{ top }} className="sticky z-20 bg-[#faf8f5] border-y border-[#dcd7ca]">
      <ul className="no-scrollbar flex gap-1 overflow-x-auto py-2">
        {SECTIONS.map(([id, label]) => (
          <li key={id} className="shrink-0">
            <button type="button" data-id={id} onClick={() => go(id)} aria-current={active === id ? "true" : undefined}
              className={`h-9 px-3 rounded-[4px] text-[15.5px] whitespace-nowrap ${active === id ? "bg-[#15263a] text-white" : "text-[#4a4740] hover:bg-[#ece6d8] hover:text-[#15263a]"}`}>
              {label}
            </button>
          </li>
        ))}
      </ul>
    </nav>
  );
}

function Section({ id, kicker, title, meta, children }) {
  return (
    <section id={id} className="scroll-mt-[var(--results-offset,140px)]">
      <div className="flex flex-wrap items-end justify-between gap-x-8 gap-y-1 pb-3 mb-5 border-b border-[#15263a]">
        <div>
          {kicker && <div className="text-[16px] text-[#8f2626]">{kicker}</div>}
          <h2 className="section-title">{title}</h2>
        </div>
        {meta && <span className="section-head-meta">{meta}</span>}
      </div>
      {children}
    </section>
  );
}

// A group of results that share an evidential status, under an italic running head
function EvidenceGroup({ title, note, children }) {
  return (
    <div className="mb-10 last:mb-0">
      <div className="evidence-head">
        <h3>{title}</h3>
        <p>{note}</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-6">{children}</div>
    </div>
  );
}

function Note({ title, children }) {
  return (
    <div className="text-[17.5px] leading-relaxed text-[#2f2d2a]">
      <h4 className="font-serif text-[21px] text-[#15263a] leading-snug mb-1">{title}</h4>
      <p>{children}</p>
    </div>
  );
}

function FigHead({ n, title, desc, children }) {
  return (
    <div className="pb-4 mb-4 border-b border-[#e5e0d4] flex flex-col lg:flex-row lg:items-end justify-between gap-4">
      <div className="min-w-0">
        <span className="section-label !mb-1">{n}</span>
        <h3 className="font-serif text-[24px] text-[#15263a] leading-snug">{title}</h3>
        <p className="head-desc !mt-1">{desc}</p>
      </div>
      <div className="flex flex-col sm:flex-row flex-wrap gap-2 shrink-0">{children}</div>
    </div>
  );
}

function Segmented({ value, onChange, options, label }) {
  return (
    <div role="radiogroup" aria-label={label} className="inline-flex border border-[#d8d3c5] rounded-[8px] p-1 bg-[#faf8f5] self-start">
      {options.map(([v, text]) => (
        <button key={v} type="button" role="radio" aria-checked={value === v} onClick={() => onChange(v)}
          className={`h-8 px-3 text-[16px] rounded-[4px] whitespace-nowrap ${value === v ? "bg-[#15263a] text-white" : "text-[#3c3a37] hover:bg-[#ece6d8]"}`}>
          {text}
        </button>
      ))}
    </div>
  );
}
