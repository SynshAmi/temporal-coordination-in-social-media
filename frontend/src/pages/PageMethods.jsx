import React, { useState } from "react";
import { Copy, Check } from "lucide-react";
import Tex from "../components/Tex";
import NK from "../components/NK";
import REFERENCES from "../lib/references.json";
import { f2, int } from "../lib/fmt";

const REPO_URL = "https://github.com/SynshAmi/temporal-coordination-in-social-media";

const COMMANDS = [
  ["Run the full pipeline", "From the raw archive to every pipeline result, figure and website file, with fixed seeds; ends with the test suite (about 70 minutes).", "python run_pipeline.py"],
  ["Collect the audit values", "Gathers the repartition, exclusion, text-retention and token-count dispersion values from the stored outputs in research_audit/; nothing is refitted.", "python src/export_audit_results.py"],
  ["Run the tests", "Feature definitions, ingestion hashes, rewiring and sampling invariants, leakage guards, and agreement between the paper, the website and the results.", "python -m pytest"],
  ["Build the paper", "Regenerates the result macros and compiles the LaTeX source to the PDF served here.", "python paper/build.py"],
  ["Build the website", "Copies the current paper PDF and builds the static site.", "cd frontend && npm install && npm run build"],
];

function RefText({ text }) {
  return text.split(/\*([^*]+)\*/).map((part, i) => (i % 2 ? <span key={i} className="text-[#15263a]">{part}</span> : <React.Fragment key={i}>{part}</React.Fragment>));
}

export default function PageMethods({ data }) {
  const P = data.paper, A = data.audit;
  const D = P.dataset, EL = P.eligibility, NM = P.null_model, X = A.text_retention;
  const [copied, setCopied] = useState(null);
  const copy = (text, i) => {
    navigator.clipboard?.writeText(text);
    setCopied(i);
    setTimeout(() => setCopied(null), 1600);
  };

  return (
    <div className="space-y-10 lg:space-y-12">
      <header className="border-b border-[#15263a] pb-8 max-w-4xl">
        <span className="section-label">Methods</span>
        <h1 className="page-title">How the evidence was produced</h1>
        <p className="mt-5 text-[18px] text-[#3c3a37] leading-relaxed max-w-[64ch]">
          What was analysed, how each feature and comparison is defined, how uncertainty is stated, and how to reproduce every number from the repository.
        </p>
      </header>

      <Block n="1" title="Data and provenance">
        <p>
          The archive was obtained from the official LEN project website and holds {D.archive_json_files} NetworkX node-link files. Ingestion hashes
          every file with SHA-256 and removes {D.duplicates_removed} exact duplicate, a campaign graph whose two file names differ only in a Turkish
          dotless “ı” versus “i”. The remaining {D.n_events} unique graphs comprise {D.n_campaign} campaign and {D.n_comparison} comparison events,
          labelled from the file-name tokens campaign and noncampaign.
        </p>
        <p>
          This archive is distinct from the dataset described in the published LEN paper, which reports LEN-Small as {D.official_len_small.n_graphs}{" "}
          graphs ({D.official_len_small.n_campaign} campaign, {D.official_len_small.n_noncampaign} non-campaign) selected as the smallest by node count;
          the two differ in membership and graph sizes. Every result on this site describes the {D.n_events}-graph LEN project archive.
        </p>
        <p>
          The graphs are directed and simple, with {int(D.n_edges_total)} edges including {int(D.n_self_loops)} self-loops. Node identifiers are per-graph
          indices, so account overlap between events cannot be measured. {X.links_text_null.toLocaleString("en-US")} of {int(X.links_total)} edge texts are
          null; the mean usable share is {f2(X.usable_share_mean_campaign)} in campaign and {f2(X.usable_share_mean_comparison)} in comparison graphs, and{" "}
          {X.events_without_usable_text} campaign graphs have none. Timestamp semantics are unverified, so no temporal features are used.
        </p>
      </Block>

      <Block n="2" title="Features">
        <div className="overflow-x-auto not-prose">
          <table className="ieee-table">
            <thead>
              <tr><th>Feature</th><th>Models</th><th>In a K-edge view</th></tr>
            </thead>
            <tbody>
              {[
                ["Log node count", "all; A–D as log Nₖ", "depends on shared endpoints"],
                ["Log edge count", "M0–M4", "fixed at K"],
                ["Squares and product of the counts", "M0q–M4", "fixed or shared endpoints"],
                ["In- and out-degree Gini", "M1, M2, M4; C, D", "depends on shared endpoints"],
                ["Reciprocity; largest weakly connected component; median and maximum core number", "M2, M4; C, D", "depends on shared endpoints"],
                ["Exact-duplicate fraction; message-frequency Gini", "M3, M4", "depends on repeated texts"],
                ["Token-count dispersion", "M3, M4; B, D", "edge-by-edge average"],
              ].map((r) => (
                <tr key={r[0]}>{r.map((c, i) => <td key={i}>{c}</td>)}</tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="grid grid-cols-1 gap-4 not-prose">
          <Eq title="Degree concentration" tex={String.raw`G(x)=\frac{2\sum_{i=1}^{n} i\,x_{(i)}-(n+1)\sum_{i=1}^{n} x_{(i)}}{n\sum_{i=1}^{n} x_{(i)}}`}
            note="Gini coefficient of the in-degree and of the out-degree sequence, sorted ascending." />
          <Eq title="Token-count dispersion" tex={String.raw`s=\sqrt{\tfrac{1}{m-1}\textstyle\sum_{e=1}^{m}(t_e-\bar t)^2}`}
            note="Sample standard deviation of whitespace token counts t_e over the m usable texts, one per edge, repeats kept; 0 for one text, undefined (training-fold median) for none." />
        </div>
        <p>
          Texts are lower-cased, URLs are removed and whitespace is collapsed; null texts and texts empty after cleaning are dropped. Core numbers are computed
          on the simple undirected projection without self-loops. Density is a function of the counts and is used only in a diagnostic model. Recomputing the
          content features from the raw archive, independently of the pipeline code, reproduced the stored values exactly.
        </p>
      </Block>

      <Block n="3" title="Models, contrasts and metrics">
        <p>
          Study 1 compares nested feature sets on identical event-level folds: M0, counts; M0q, counts with squared and interaction terms; M1 = M0q + degree
          concentration; M2 = M1 + arrangement; M3 = M0q + content; M4 = M2 + content. Three contrasts were specified before the final run: C1 (M4 − M0q),
          C2 (M2 − M1) and C3 (M3 − M0q). They were not preregistered, and an earlier version of the study analysed the same archive.
        </p>
        <p>
          Logistic regression with median imputation, standardization and balanced class weights is the primary model; gradient-boosted trees are secondary.
          Hyperparameters are tuned by inner three-fold cross-validation within each of five stratified outer folds. Log loss and AUC come from fits tuned for
          log loss, balanced accuracy from fits tuned for balanced accuracy. Log loss leads every incremental comparison; both the log-loss and the balanced-accuracy
          tests of C1–C3 were prespecified, so leading with log loss is a presentation choice.
        </p>
      </Block>

      <Block n="4" title="Uncertainty and evidence">
        <p>
          Differences are estimated with an event-level paired bootstrap of fixed out-of-fold predictions ({int(P.study1.n_bootstrap)} resamples for Study 1, {int(data.revision.study2_n_bootstrap)} for Study 2,
          seed 7). Holm correction covers the three primary tests for each metric. Study 2 regime and feature contrasts carry Holm-adjusted p-values across the three budgets for each contrast and metric; the two token-count dispersion contrasts (B − A and D − C at three budgets) are adjusted together as one family of six, because they test one post-hoc question. The
          bootstrap intervals do not include refitting variability, so Study 1 was repeated over {A.study1_20_partitions.n_partitions} outer partitions (seeds
          42 and 1–19), with out-of-fold predictions averaged across partitions. Partitions and sampling seeds reuse the same events.
        </p>
        <dl className="grid grid-cols-1 sm:grid-cols-2 gap-x-10 gap-y-4 not-prose text-[17px]">
          {[
            ["Prespecified comparisons", "The paper's primary contrasts C1–C3, and the models they compare, on the prespecified partition; Holm-adjusted"],
            ["Sensitivity analyses", "The same question under other partitions, exclusions or fold grouping"],
            ["Exploratory analyses", "Planned, but outside the prespecified family; unadjusted unless stated"],
            ["Post-hoc analyses", "Chosen after inspecting results on these events; every analysis that isolates token-count dispersion"],
          ].map(([t, d]) => (
            <div key={t}><dt className="font-serif italic text-[18px] text-[#15263a]">{t}</dt><dd className="text-[#3c3a37] mt-1">{d}</dd></div>
          ))}
        </dl>
      </Block>

      <Block n="5" title="Degree-preserving null">
        <p>
          Each graph is rewired by directed double-edge swaps on non-loop edges, rejecting swaps that create self-loops or repeated edges, with {NM.swaps_per_edge}{" "}
          swaps per edge and {NM.realizations} realizations per event. This preserves every node's in- and out-degree exactly. M2 is refitted with
          arrangement features from the rewired graphs and compared with M2 on the real graphs. Because rewiring preserves the degree sequence, it preserves
          everything the degree sequence determines, including the expected node count of an edge sample; it rarely changes the median core number.
        </p>
      </Block>

      <Block n="6" title="Edge-limited design">
        <p>
          For K = 250, 500 and 1000, every event with at least K edges is reduced to K uniformly sampled edges with ten seeds (100–109), and every feature is
          recomputed from the sampled edges. Cohorts differ by budget: {[250, 500, 1000].map((k) => `${EL[k].total_eligible} events at K = ${k} (${EL[k].campaign_eligible}/${EL[k].comparison_eligible})`).join(", ")}.
          K = 2000 is infeasible because only {EL["2000"].campaign_eligible} campaign events have at least 2,000 edges. FF trains and evaluates on full graphs,
          FK applies the full-graph model to single views, each event scored by the fold model that held it out, and KK trains and evaluates on single views.
        </p>
        <div className="not-prose">
          <Eq title={<>Expected node count of a view, <NK /></>} tex={String.raw`\mathbb{E}[N_K]=\sum_{v\in V}\left[1-\binom{m-d_v}{K}\Big/\binom{m}{K}\right]`}
            note="Uniform sampling of K of the m edges without replacement; d_v is the number of distinct edges incident to v. It depends only on K and the incidence-degree sequence." />
        </div>
      </Block>

      <Block n="7" title="Reproducing the results">
        <p>
          The raw archive is not redistributed; download it from the LEN project and check its SHA-256 digest against the repository's data manifest. Every
          number in the paper and on this site is generated from stored results, and the tests fail if a value is typed by hand.
        </p>
        <ol className="not-prose">
          {COMMANDS.map(([title, desc, cmd], i) => (
            <li key={cmd} className="grid grid-cols-[40px_minmax(0,1fr)] gap-x-4 gap-y-2 py-4 border-b border-[#ece6d8] last:border-b-0">
              <span className="font-serif text-[30px] leading-none text-[#9a948a] tabular row-span-2">{i + 1}</span>
              <div>
                <div className="font-serif text-[21px] leading-snug text-[#15263a]">{title}</div>
                <p className="text-[17px] text-[#4a4740] mt-0.5 leading-relaxed">{desc}</p>
              </div>
              <div className="flex items-center justify-between gap-3 bg-[#15263a] text-[#ededed] rounded-[8px] pl-4 pr-2 h-11">
                <code className="font-code text-[15px] overflow-x-auto whitespace-nowrap no-scrollbar">{cmd}</code>
                <button type="button" onClick={() => copy(cmd, i)} aria-label={`Copy: ${cmd}`}
                  className="shrink-0 inline-flex items-center gap-1.5 h-8 px-3 rounded-[4px] text-[14px] text-[#c9c5bc] hover:bg-[#233b54] hover:text-white">
                  {copied === i ? <Check size={14} strokeWidth={1.5} /> : <Copy size={14} strokeWidth={1.5} />}
                  {copied === i ? "Copied" : "Copy"}
                </button>
              </div>
            </li>
          ))}
        </ol>
      </Block>

      <Block n="8" title="Code and data availability">
        <p>
          Code, configuration, tests, derived outputs and the audit record are at{" "}
          <a href={REPO_URL} target="_blank" rel="noopener noreferrer" className="underline decoration-[#b5ad9e] underline-offset-4 hover:text-[#23527c]">{REPO_URL.replace("https://", "")}</a>.
          An independent script recomputes all pipeline comparisons from the saved predictions ({P.verification.n_pass} of {P.verification.n_checks} checks pass),
          and a complete rerun reproduced every pipeline value on the original machine; other hardware has not been tested. The repository also documents two
          implementation errors in an earlier internal version, coreness on graphs with self-loops and fold assignment for frozen models, both fixed and covered by
          regression tests before these results were produced.
        </p>
        <p>
          LEN is released by its authors under a CC-BY licence. The repository shares derived files (event names, counts, file digests, features and predictions)
          and, for the dataset explorer, each event's graph structure without text or timestamps, with attribution and without endorsement by the LEN authors.
          The code is MIT-licensed; the paper and its figures are not.
        </p>
      </Block>

      <section>
        <div className="section-head">
          <h2 className="section-title">References</h2>
          <span className="section-head-meta">As cited in the paper</span>
        </div>
        <ol className="grid grid-cols-1 lg:grid-cols-2 gap-x-12 gap-y-5 text-[16px] leading-relaxed text-[#3c3a37]">
          {REFERENCES.map((ref, i) => (
            <li key={i} className="flex gap-4 pb-5 border-b border-[#e5e0d4]">
              <span className="shrink-0 font-mono text-[14px] text-[#8f2626] pt-0.5 tabular">[{i + 1}]</span>
              <span className="min-w-0 break-words"><RefText text={ref} /></span>
            </li>
          ))}
        </ol>
      </section>
    </div>
  );
}

function Block({ n, title, children }) {
  return (
    <section className="grid grid-cols-1 lg:grid-cols-12 gap-x-16 gap-y-4 pt-8 border-t border-[#dcd7ca] first-of-type:border-t-0 first-of-type:pt-0">
      <div className="lg:col-span-4 flex items-baseline gap-4">
        <span className="font-serif text-[46px] leading-none text-[#b5ad9e] tabular w-10 shrink-0">{n}</span>
        <h2 className="section-title">{title}</h2>
      </div>
      <div className="lg:col-span-8 space-y-4 text-[18px] leading-[1.7] text-[#2f2d2a] max-w-[74ch]">{children}</div>
    </section>
  );
}

function Eq({ title, tex, note }) {
  return (
    <div className="border border-[#dcd7ca] bg-white rounded-[12px] p-5">
      <div className="text-[15px] font-medium text-[#15263a]">{title}</div>
      <Tex display className="mt-3">{tex}</Tex>
      <p className="mt-3 text-[15px] text-[#5e5a52] leading-relaxed">{note}</p>
    </div>
  );
}
