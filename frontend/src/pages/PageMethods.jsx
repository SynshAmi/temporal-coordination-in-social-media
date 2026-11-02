import React, { useState } from "react";
import { Terminal, Copy, Check, ShieldCheck, AlertTriangle, BookMarked, FileText, Layers, History } from "lucide-react";
import Tex from "../components/Tex";
import NK from "../components/NK";
import REFERENCES from "../lib/references.json";
import { f2, f3, int, sg, ci, ciu, con, pct0 } from "../lib/fmt";

const REPO_URL = "https://github.com/SynshAmi/temporal-coordination-in-social-media";

const commands = [
  {
    id: "c1",
    title: "Run the full pipeline",
    cmd: "python run_pipeline.py",
    note: "From the raw archive to every result: ingestion, matching, edge sampling, both studies, independent verification, result exports and tests.",
  },
  {
    id: "c2",
    title: "Run the test suite",
    cmd: "python -m pytest tests/ -v",
    note: "Ingestion and deduplication, fold leakage, sampling determinism, the coreness convention, degree preservation under rewiring, and agreement between the paper and this website.",
  },
  {
    id: "c4",
    title: "Run the revision analyses on their own",
    cmd: "python src/h1_c_grid.py && python src/revision_supplement.py",
    note: "The wider regularization search for the count model and the supplementary analyses. Both only read the verified run and write to the output.revision_* locations in the config; the full pipeline runs them as stage 11.",
  },
  {
    id: "c3",
    title: "Build the paper",
    cmd: "python paper/build.py",
    note: "Compiles the IEEE LaTeX paper (requires TeX Live or MiKTeX). Every number in it is generated from the pipeline's results.",
  },
];

// Shared header for each numbered methods section
function MethodsSectionHead({ icon: Icon, iconColor = "#15263a", children }) {
  return (
    <div className="flex items-center gap-3 pb-4 mb-8 border-b border-[#e5e0d4]">
      <Icon size={20} className="shrink-0" style={{ color: iconColor }} />
      <h2 className="section-title">{children}</h2>
    </div>
  );
}

// Term + typeset equation (KaTeX) rendered as a definition
function Definition({ term, tex, children }) {
  return (
    <div className="h-full bg-[#fbfaf6] border border-[#e5e0d4] px-4 py-3.5 sm:px-5 sm:py-4">
      <dt className="text-sm font-semibold text-[#15263a]">{term}</dt>
      {tex && (
        <dd className="mt-3 mb-1">
          <Tex display>{tex}</Tex>
        </dd>
      )}
      {children && <dd className="mt-2 text-[13px] text-[#4a4740] leading-relaxed">{children}</dd>}
    </div>
  );
}

// One feature group: heading + explanation (left) and definitions (right)
function FeatureGroup({ letter, title, subtitle, intro, children }) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-x-12 gap-y-5 py-8 first:pt-0 last:pb-0">
      <div className="lg:col-span-4">
        <div className="font-mono text-xs font-bold uppercase tracking-wider text-[#8f2626]">{letter}</div>
        <h3 className="subsection-title mt-2">{title}</h3>
        <div className="mt-1 text-xs font-mono text-[#757065]">{subtitle}</div>
        <p className="mt-3 text-sm text-[#4a4740] leading-relaxed">{intro}</p>
      </div>
      <dl className="lg:col-span-8 grid grid-cols-1 md:grid-cols-2 gap-3 content-start">{children}</dl>
    </div>
  );
}

function ProtocolBlock({ title, children }) {
  return (
    <div className="bg-[#fbfaf6] border border-[#e5e0d4] p-5 sm:p-6">
      <h3 className="subsection-title">{title}</h3>
      <div className="mt-3 text-sm text-[#3c3a37] leading-relaxed space-y-3">{children}</div>
    </div>
  );
}

// Reference text uses *...* for italics, as in the paper source
function RefText({ text }) {
  return text.split(/\*([^*]+)\*/).map((part, i) => (i % 2 ? <em key={i}>{part}</em> : <React.Fragment key={i}>{part}</React.Fragment>));
}

export default function PageMethods({ data }) {
  const P = data.paper, V = data.revision, CH = V.null_feature_change;
  const D = P.dataset, EL = P.eligibility, MT = P.matching, NM = P.null_model, S1 = P.study1;
  const [copiedCmd, setCopiedCmd] = useState(null);

  const copyToClipboard = (text, id) => {
    navigator.clipboard.writeText(text);
    setCopiedCmd(id);
    setTimeout(() => setCopiedCmd(null), 2000);
  };

  const protocolSteps = [
    { step: "Step 1", tag: "Ingestion", color: "#8f2626", title: "Canonical Ingestion & Deduplication",
      body: `SHA-256 digest of every archive file; ${D.duplicates_removed} byte-identical duplicate removed. Pretrained text and profile embeddings are excluded.`,
      output: `${D.n_events} canonical events (${D.n_campaign} / ${D.n_comparison})` },
    { step: "Step 2", tag: "Features", color: "#23527c", title: "Interpretable Graph & Content Features",
      body: "Counts, in/out-degree Gini, reciprocity, largest weakly connected component, coreness, and three content statistics. Density is treated as scale-encoding.",
      output: "Per-event feature table" },
    { step: "Step 3", tag: "Study 1", color: "#15263a", title: "Nested Models & Paired Contrasts",
      body: "Seven feature sets in two nested chains on identical event-level folds; three primary contrasts (C1–C3), specified before the corrected run but not preregistered; LR primary, HGBT secondary.",
      output: "Out-of-fold predictions for BA and log-loss fits" },
    { step: "Step 4", tag: "Null Model", color: "#8f2626", title: "Degree-Preserving Rewiring",
      body: `Directed double-edge swaps with self-loops held fixed; ${NM.swaps_per_edge} swaps per edge, ${NM.realizations} realizations per event.`,
      output: "Real vs rewired arrangement features" },
    { step: "Step 5", tag: "Study 2", color: "#23527c", title: "Single-View Observation Design",
      body: "K ∈ {250, 500, 1000} uniformly sampled edges, 10 seeds per event; full-graph (FF), frozen (FK) and retrained (KK) conditions.",
      output: "Single-view and ensemble predictions" },
    { step: "Step 6", tag: "Verification", color: "#15263a", title: "Independent Recomputation",
      body: "A separate script reimplements the evaluation and recomputes every reported comparison from saved predictions.",
      output: `${P.verification.n_pass}/${P.verification.n_checks} checks pass` },
  ];

  const panel = "bg-white border border-[#dcd7ca] p-5 sm:p-8 lg:p-10";

  return (
    <div className="space-y-16 lg:space-y-20">
      <header className="border-b border-[#15263a] pb-10 lg:pb-12">
        <span className="section-label">Methods & Reproducibility</span>
        <h1 className="page-title max-w-[32ch]">
          Study Design, Feature Definitions and Reproducibility
        </h1>
        <p className="mt-5 text-base sm:text-[17px] text-[#3c3a37] leading-relaxed max-w-[62ch]">
          How the archive was processed, how each feature and estimand is defined, how uncertainty is quantified, and how to reproduce every number.
        </p>
      </header>

      {/* Protocol overview */}
      <section className={panel}>
        <div className="panel-head">
          <span className="section-label">Study Protocol</span>
          <h2 className="section-title">Pipeline Overview</h2>
          <p className="head-desc">
            Six stages, all driven by one configuration file with fixed seeds for folds, matching, edge sampling, rewiring and bootstrap.
          </p>
        </div>
        <ol className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5 lg:gap-6">
          {protocolSteps.map((s) => (
            <li key={s.step} className="bg-[#fbfaf6] border border-[#e5e0d4] border-t-2 p-5 sm:p-6 flex flex-col" style={{ borderTopColor: s.color }}>
              <div className="flex items-center justify-between gap-3 font-mono text-xs" style={{ color: s.color }}>
                <span className="font-bold uppercase tracking-wider">{s.step}</span>
                <span>{s.tag}</span>
              </div>
              <h3 className="mt-3 font-serif text-lg font-medium leading-snug text-[#15263a]">{s.title}</h3>
              <p className="mt-2 text-sm text-[#4a4740] leading-relaxed">{s.body}</p>
              <div className="mt-auto pt-5">
                <div className="pt-3 border-t border-[#e5e0d4] text-xs font-mono text-[#5e5a52]">Output: {s.output}</div>
              </div>
            </li>
          ))}
        </ol>
      </section>

      {/* 1. Data */}
      <section className={panel}>
        <MethodsSectionHead icon={ShieldCheck}>1. Unit of Analysis & Data Provenance</MethodsSectionHead>
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 lg:gap-6">
          <div className="lg:col-span-5 xl:col-span-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-1 gap-5 lg:gap-6">
            <ProtocolBlock title="Unit of Analysis">
              <p>
                The unit of analysis is the event engagement graph: accounts are nodes and retweets, replies or quotes are directed edges. No account-level, bot, intent or causal inferences are made.
              </p>
            </ProtocolBlock>
            <ProtocolBlock title="Labels and Identifiers">
              <p>
                Labels are read from the file-name tokens <code className="font-mono text-[13px]">_campaign_</code> and <code className="font-mono text-[13px]">_noncampaign_</code>. Node identifiers are per-graph indices, so cross-event account overlap cannot be measured. Edge timestamps are present, but their semantics are unverified, so no temporal features are used.
              </p>
            </ProtocolBlock>
          </div>
          <div className="lg:col-span-7 xl:col-span-8 border border-[#e5e0d4] border-l-4 border-l-[#8f2626] bg-[#fbfaf6] p-5 sm:p-6 lg:p-8">
            <h3 className="subsection-title">Archive vs Official Release</h3>
            <p className="mt-3 text-sm text-[#3c3a37] leading-relaxed">
              <strong>This archive does not match the official release.</strong> The LEN paper describes LEN-Small as {D.official_len_small.n_graphs} graphs ({D.official_len_small.n_campaign} campaign, {D.official_len_small.n_noncampaign} non-campaign), the {D.official_len_small.selection_rule}. The analysed archive contains {D.archive_json_files} files; after removing {D.duplicates_removed} byte-identical duplicate (a campaign graph whose two file names differ only in a Turkish dotless <code className="font-mono text-[13px]">ı</code> versus ASCII <code className="font-mono text-[13px]">i</code>), {D.n_events} canonical events remain ({D.n_campaign} campaign, {D.n_comparison} comparison). We could not determine why the archive holds {D.n_events - D.official_len_small.n_graphs} additional events and make no claim of equivalence to the official selection.
            </p>
            <dl className="mt-6 grid grid-cols-1 sm:grid-cols-3 gap-px bg-[#e5e0d4] border border-[#e5e0d4] font-mono text-xs">
              <div className="bg-white px-4 py-3">
                <dt className="text-[11px] uppercase tracking-wider text-[#757065]">Edges / self-loops</dt>
                <dd className="mt-1 text-[#15263a] font-semibold">{int(D.n_edges_total)} / {int(D.n_self_loops)}</dd>
              </div>
              <div className="bg-white px-4 py-3">
                <dt className="text-[11px] uppercase tracking-wider text-[#757065]">Duplicates removed</dt>
                <dd className="mt-1 text-[#15263a] font-semibold">{D.duplicates_removed} file</dd>
              </div>
              <div className="bg-white px-4 py-3">
                <dt className="text-[11px] uppercase tracking-wider text-[#757065]">Canonical events</dt>
                <dd className="mt-1 text-[#15263a] font-semibold">{D.n_events} ({D.n_campaign} / {D.n_comparison})</dd>
              </div>
            </dl>
            <div className="mt-5">
              <div className="text-[11px] font-mono uppercase tracking-wider text-[#757065]">Duplicate SHA-256 digest</div>
              <code className="mt-2 block bg-white border border-[#e5e0d4] px-4 py-3 font-mono text-xs text-[#15263a] break-all leading-relaxed">
                {D.duplicate_sha256}
              </code>
            </div>
          </div>
        </div>
      </section>

      {/* 2. Features */}
      <section className={panel}>
        <MethodsSectionHead icon={FileText}>2. Feature Definitions</MethodsSectionHead>
        <div className="divide-y divide-[#e5e0d4]">
          <FeatureGroup letter="Counts" title="Graph Size" subtitle="Levels M0, M0q"
            intro="Log-transformed node and edge counts. M0q adds squared and interaction terms as a nonlinear count control.">
            <Definition term="Log node count" tex={String.raw`\ln\left(1 + |V|\right)`} />
            <Definition term="Log edge count" tex={String.raw`\ln\left(1 + |E|\right)`} />
          </FeatureGroup>

          <FeatureGroup letter="Degree & arrangement" title="Graph Structure" subtitle="Levels M1, M2"
            intro="Degree concentration (M1) and higher-order arrangement (M2), computed per event graph with NetworkX.">
            <div className="md:col-span-2">
              <Definition term="Degree concentration (Gini), Eq. (1)" tex={String.raw`G(x) = \frac{2 \sum_{i=1}^{n} i\, x_{(i)} \;-\; (n+1) \sum_{i=1}^{n} x_{(i)}}{n \sum_{i=1}^{n} x_{(i)}}`}>
                <Tex>{String.raw`x_{(1)} \le \dots \le x_{(n)}`}</Tex> is a non-negative vector sorted ascending; computed separately on in-degrees and out-degrees.
              </Definition>
            </div>
            <Definition term="Reciprocity" tex={String.raw`r = \frac{\lvert E \cap E^{\mathrm{rev}} \rvert}{|E|}`}>
              <Tex>{String.raw`E^{\mathrm{rev}} = \{(v,u) : (u,v) \in E\}`}</Tex>.
            </Definition>
            <Definition term="Largest WCC fraction" tex={String.raw`f_{\mathrm{WCC}} = \frac{\lvert V_{\max\mathrm{WCC}} \rvert}{|V|}`} />
            <div className="md:col-span-2">
              <Definition term="Coreness (median and maximum)" tex={String.raw`\operatorname*{median}_{v \in V} k(v), \qquad \max_{v \in V} k(v)`}>
                <Tex>k(v)</Tex> is the core number on the simple undirected projection with self-loops removed: <Tex>{String.raw`\{u, v\}`}</Tex> is an edge if <Tex>(u, v)</Tex> or <Tex>(v, u)</Tex> is, <Tex>{String.raw`u \neq v`}</Tex>. A node whose only edges are self-loops has core number 0.
              </Definition>
            </div>
          </FeatureGroup>

          <FeatureGroup letter="Content" title="Retained Message Text" subtitle="Level M3"
            intro="Message repetition statistics computed from cleaned message text, without semantic embeddings.">
            <div className="md:col-span-2">
              <Definition term="Exact-duplicate fraction" tex={String.raw`d_{\mathrm{dup}} = 1 - \frac{\lvert U_{\mathrm{text}} \rvert}{\lvert T_{\mathrm{text}} \rvert}`}>
                <Tex>{String.raw`T_{\mathrm{text}}`}</Tex> is the multiset of cleaned messages and <Tex>{String.raw`U_{\mathrm{text}}`}</Tex> its set of distinct messages.
              </Definition>
            </div>
            <Definition term="Text concentration" tex={String.raw`c_{\mathrm{text}} = G\bigl(\{\, f_u \,\}_{u \in U_{\mathrm{text}}}\bigr)`}>
              Gini coefficient over message frequencies <Tex>{String.raw`f_u`}</Tex>.
            </Definition>
            <Definition term="Message length dispersion" tex={String.raw`s_{\ell} = \operatorname{sd}\bigl(\{\ell_t\}_{t \in T_{\mathrm{text}}}\bigr)`}>
              Standard deviation of message token counts <Tex>{String.raw`\ell_t`}</Tex>.
            </Definition>
          </FeatureGroup>

          <FeatureGroup letter="Scale-encoding" title="Density and Sampled Views" subtitle="Diagnostic only; Study 2"
            intro="Density is a deterministic function of the counts, so it is used only in a diagnostic model (M4 + density). In a K-edge sample it is fixed by the endpoint count.">
            <Definition term="Density" tex={String.raw`\rho = \frac{|E|}{|V|\,\bigl(|V| - 1\bigr)}`} />
            <Definition term="Density of a K-edge view, Eq. (2)" tex={String.raw`D_K = \frac{K}{N_K\,(N_K - 1)}`}>
              <NK /> is the number of distinct endpoints in the sample.
            </Definition>
            <div className="md:col-span-2">
              <Definition term="Expected distinct endpoints, Eq. (3)" tex={String.raw`\mathbb{E}[N_K] = \sum_{v \in V} \left[ 1 - \binom{m - d_v}{K} \Big/ \binom{m}{K} \right]`}>
                Uniform sampling of K of the <Tex>m = |E|</Tex> edges without replacement; <Tex>d_v</Tex> is the number of distinct edges incident to <Tex>v</Tex>.
              </Definition>
            </div>
          </FeatureGroup>
        </div>
      </section>

      {/* 3. Evaluation */}
      <section className={panel}>
        <MethodsSectionHead icon={Layers}>3. Evaluation & Inference</MethodsSectionHead>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 lg:gap-6">
          <ProtocolBlock title="Cross-Validation & Tuning">
            <p>
              Event-level stratified 5-fold cross-validation; all sampled views of an event share its fold. Logistic regression (median imputation, standardization, balanced class weights, C ∈ &#123;{V.h1.original_grid.join(", ")}&#125;) and HGBT are tuned by inner 3-fold cross-validation inside each outer training fold. A wider grid ({V.h1.grid[0]} to {V.h1.grid[V.h1.grid.length - 1].toLocaleString("en-US")}) was examined as a sensitivity analysis.
            </p>
            <p>
              <strong>Separate estimands:</strong> balanced accuracy uses fits tuned for BA; log loss and AUC use fits tuned for log loss on the same outer folds.
            </p>
          </ProtocolBlock>
          <ProtocolBlock title="Paired Inference">
            <p>
              Differences are estimated on identical events with an event-level paired bootstrap of fixed out-of-fold predictions ({S1.n_bootstrap.toLocaleString("en-US")} resamples). Holm correction is applied separately to the three BA and the three log-loss primary tests. Study 2 contrasts are exploratory: an event-level bootstrap of the single-view estimand ({V.study2_n_bootstrap.toLocaleString("en-US")} resamples) with no multiplicity correction.
            </p>
            <p>
              These intervals exclude refitting and split variability, which is reported separately from {S1.n_split_seeds} re-drawn fold splits (not independent replicates). Hyperparameter selection was sensitive to row order (C1 ΔBA {sg(S1.row_order_sensitivity["ba:C1"].delta_study_order)} vs {sg(S1.row_order_sensitivity["ba:C1"].delta_permuted_order)} with permuted rows).
            </p>
          </ProtocolBlock>
          <ProtocolBlock title="Exploratory Size Matching">
            <p>
              1:1 greedy matching on log node count with a {MT.caliper_sd_fraction} SD caliper ({f3(MT.caliper_abs)}): {MT.primary_pairs} pairs, |SMD| {f2(Math.abs(MT.smd_before))} → {f2(Math.abs(MT.smd_after))}. Repeated over {MT.node_only.n_order_seeds} visiting orders, with and without log edge count.
            </p>
            <Tex display>{String.raw`\mathrm{SMD} = \frac{\bar{x}_{\mathrm{camp}} - \bar{x}_{\mathrm{comp}}}{\sqrt{\bigl(s^{2}_{\mathrm{camp}} + s^{2}_{\mathrm{comp}}\bigr)/2}}`}</Tex>
            <p>With about 16 pairs, results are point estimates without sampling intervals: sensitivity evidence only.</p>
          </ProtocolBlock>
        </div>
      </section>

      {/* 4. Null model and Study 2 conditions */}
      <section className={panel}>
        <MethodsSectionHead icon={AlertTriangle} iconColor="#8f2626">4. Null Model & Observation Conditions</MethodsSectionHead>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 lg:gap-6">
          <div className="bg-[#fbfaf6] border border-[#e5e0d4] border-t-2 border-t-[#8f2626] p-5 sm:p-6">
            <div className="font-mono text-xs font-bold uppercase tracking-wider text-[#8f2626]">Study 1</div>
            <h3 className="subsection-title mt-2">Degree-Preserving Rewiring</h3>
            <p className="mt-3 text-sm text-[#3c3a37] leading-relaxed">
              Directed double-edge swaps (a, b), (c, d) → (a, d), (c, b) on non-loop edges, rejecting swaps that create self-loops or repeated edges, preserve every node's in- and out-degree, |V|, |E|, density and the degree Gini coefficients exactly. Directed double-edge swaps do not reach every digraph with the given degrees, so this is not a uniform sample. It changed reciprocity in {pct0(CH.reciprocity.share_events_changed_in_some_realization)}% of events, the largest-component fraction in {pct0(CH.largest_wcc_fraction.share_events_changed_in_some_realization)}% and the maximum core number in {pct0(CH.coreness_max.share_events_changed_in_some_realization)}%, but the median core number in only {pct0(CH.coreness_median.share_events_changed_in_some_realization)}%, so it is a constrained comparison rather than a randomization of all structure. Real arrangement minus the rewired ensemble (probabilities of the {NM.realizations} rewired fits averaged per event): ΔBA {sg(NM.real_minus_null_ba.delta_ba)} {ci(NM.real_minus_null_ba.delta_ba_ci)}, Δ log loss {sg(NM.real_minus_null_logloss.delta_logloss)} {ci(NM.real_minus_null_logloss.delta_logloss_ci)}: no detectable improvement, which is not evidence of equivalence and does not show that topology is uninformative.
            </p>
          </div>
          <div className="bg-[#fbfaf6] border border-[#e5e0d4] border-t-2 border-t-[#23527c] p-5 sm:p-6">
            <div className="font-mono text-xs font-bold uppercase tracking-wider text-[#23527c]">Study 2</div>
            <h3 className="subsection-title mt-2">FF, FK and KK Conditions</h3>
            <p className="mt-3 text-sm text-[#3c3a37] leading-relaxed">
              <strong>FF</strong> trains and evaluates on full graphs; <strong>FK</strong> applies the full-graph model to single K-edge views (frozen transfer), scoring each event with the fold model that held it out; <strong>KK</strong> trains and evaluates on single views from the same sampling seed. All conditions at a given K share events, folds and feature definitions, so KK − FK isolates the effect of training on views. At K = 250 it is +{f3(con(P, 250, "retrain_effect_struct6").ba.delta)} {ciu(con(P, 250, "retrain_effect_struct6").ba.ci)} with the six structural features.
            </p>
          </div>
        </div>
        <div className="mt-6 p-5 sm:p-6 bg-[#f4efe6] border-l-4 border-[#8f2626] text-[13px] font-mono text-[#2a2825] leading-relaxed">
          <strong>Budget eligibility:</strong> K = 250: {EL["250"].total_eligible} events ({EL["250"].campaign_eligible}/{EL["250"].comparison_eligible}); K = 500: {EL["500"].total_eligible} ({EL["500"].campaign_eligible}/{EL["500"].comparison_eligible}); K = 1000: {EL["1000"].total_eligible} ({EL["1000"].campaign_eligible}/{EL["1000"].comparison_eligible}). K = 2000 is infeasible for five-fold stratified evaluation because only {EL["2000"].campaign_eligible} campaign events have at least 2,000 edges.
        </div>
      </section>

      {/* 5. Reproducibility and correction history */}
      <section className={panel}>
        <MethodsSectionHead icon={History}>5. Reproducibility & Methodological Corrections</MethodsSectionHead>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 lg:gap-6">
          <ProtocolBlock title="Code and Data Availability">
            <p>
              Source code, configuration, tests, derived event-level outputs and reproduction instructions are available on{" "}
              <a href={REPO_URL} target="_blank" rel="noopener noreferrer" className="underline decoration-[#b5ad9e] underline-offset-4 text-[#15263a] hover:text-[#23527c]">GitHub</a>. The code is released under the MIT licence, which does not extend to the paper, its figures or any data. One command runs the pipeline from the raw archive to every number, table and figure in the paper and on this website. An independent verification script recomputes all reported comparisons from the saved predictions ({P.verification.n_pass} of {P.verification.n_checks} checks pass), including checks that permuting held-out labels leaves the tuned hyperparameters unchanged.
            </p>
            <p>
              A complete rerun from the raw archive reproduced every reported value on the original machine; reproduction on other hardware has not been tested.
            </p>
            <p>
              LEN-Small is part of LEN (Large Engagement Networks; Gopalakrishnan, Hossain, Elmas and Sarıyüce, ICWSM 2025), which its authors release under a CC-BY licence. We do not redistribute the raw archive; it must be obtained from the LEN project. The repository's derived files (event names, counts, file digests, features and predictions) and the graph structure shown in the dataset explorer (node indices and directed edges, without message text or timestamps) are shared with attribution and are not endorsed by the LEN authors.
            </p>
          </ProtocolBlock>
          <ProtocolBlock title="Methodological Corrections">
            <p>
              Validation of an earlier version of this analysis identified two errors, both corrected before the reported results were produced.
            </p>
            <p>
              <strong>Coreness and self-loops.</strong> Every graph contains self-loops, which the core-number routine does not accept. The earlier implementation set both coreness features to zero instead of failing, so its arrangement features carried no coreness information. Core numbers are now computed on the undirected projection without self-loops. This affected every model that uses arrangement features.
            </p>
            <p>
              <strong>Fold assignment for frozen models.</strong> Sampled events were assigned to frozen fold models with a split specific to each edge budget, so some were scored by a model whose training data included their own full graph, which inflates frozen-transfer accuracy. Each sampled event is now scored only by the full-cohort fold model that held it out. This affected only the frozen-transfer condition.
            </p>
            <p>
              Both corrections are covered by regression tests, and every result shown here comes from the corrected pipeline. The superseded outputs are retained in the repository, with their values, for reference.
            </p>
          </ProtocolBlock>
        </div>
      </section>

      {/* 6. Commands */}
      <section className={panel}>
        <MethodsSectionHead icon={Terminal}>6. Reproducing the Results</MethodsSectionHead>
        <p className="-mt-4 mb-8 text-sm text-[#4a4740] leading-relaxed max-w-[80ch]">
          The raw LEN-Small archive must first be obtained from the LEN project and checked against its published SHA-256 digest. Setup, data provenance and the full workflow are documented in the{" "}
          <a href={REPO_URL} target="_blank" rel="noopener noreferrer" className="underline decoration-[#b5ad9e] underline-offset-4 text-[#15263a] hover:text-[#23527c]">repository README</a>.
        </p>
        <ol className="space-y-8">
          {commands.map((c, i) => (
            <li key={c.id} className="grid grid-cols-1 lg:grid-cols-12 gap-x-10 gap-y-4 items-start">
              <div className="lg:col-span-4 flex gap-4">
                <span className="shrink-0 w-8 h-8 flex items-center justify-center bg-[#15263a] text-white font-mono text-sm font-semibold">
                  {i + 1}
                </span>
                <div className="min-w-0">
                  <h3 className="text-[15px] font-sans font-semibold tracking-normal text-[#15263a] leading-snug">{c.title}</h3>
                  <p className="mt-1.5 text-sm text-[#5e5a52] leading-relaxed">{c.note}</p>
                </div>
              </div>
              <div className="lg:col-span-8 border border-[#15263a] min-w-0">
                <div className="flex items-center justify-between gap-3 pl-4 pr-2 py-1.5 bg-[#0d1a29] text-[11px] font-mono text-[#a9b4c2]">
                  <span>shell</span>
                  <button
                    type="button"
                    onClick={() => copyToClipboard(c.cmd, c.id)}
                    className="inline-flex items-center gap-1.5 px-2.5 py-1 text-[#d8dee6] hover:text-white hover:bg-white/10 transition-colors"
                    aria-label={`Copy command: ${c.title}`}
                  >
                    {copiedCmd === c.id ? <Check size={12} className="text-emerald-400" /> : <Copy size={12} />}
                    <span>{copiedCmd === c.id ? "Copied" : "Copy"}</span>
                  </button>
                </div>
                <pre className="bg-[#15263a] text-white px-4 py-4 sm:px-5 font-mono text-[13px] leading-relaxed whitespace-pre-wrap break-words [font-variant-ligatures:none]"><span className="text-[#8fa3b8] select-none">$ </span>{c.cmd}</pre>
              </div>
            </li>
          ))}
        </ol>
      </section>

      {/* 7. References */}
      <section className={panel}>
        <MethodsSectionHead icon={BookMarked}>7. References</MethodsSectionHead>
        <p className="-mt-4 mb-6 text-sm text-[#5e5a52]">Numbered as in the paper.</p>
        <ol className="grid grid-cols-1 lg:grid-cols-2 gap-x-12 gap-y-5 text-sm text-[#3c3a37] leading-relaxed">
          {REFERENCES.map((ref, i) => (
            <li key={i} className="flex gap-4 pb-5 border-b border-[#e5e0d4]">
              <span className="shrink-0 font-mono text-xs text-[#8f2626] font-semibold pt-0.5">[{i + 1}]</span>
              <span className="min-w-0 break-words"><RefText text={ref} /></span>
            </li>
          ))}
        </ol>
      </section>
    </div>
  );
}
