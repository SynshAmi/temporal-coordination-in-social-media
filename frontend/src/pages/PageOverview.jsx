import React from "react";
import { ArrowRight, FileText } from "lucide-react";
import Authors from "../components/Authors";
import NK from "../components/NK";
import { f2, f3, sg, ci, pct, int } from "../lib/fmt";
import { pdfHref } from "../lib/results";

export default function PageOverview({ data, setActiveTab }) {
  const P = data.paper, A = data.audit;
  const D = P.dataset, lr = P.study1.performance.logreg, LC = P.study1.confirmatory.logreg;
  const C = A.study1_20_partitions.contrasts, X = A.text_retention;
  const E = A.edge_limited_token_std, V = E.contrasts.primary.KK;
  const r2 = P.study2.mechanism_r2_K250;
  const nkAUC = [250, 500, 1000].map((k) => f3(E.performance[`K${k}`].KK.A.auc));
  const C1 = LC.C1;

  return (
    <div className="space-y-14 lg:space-y-20">
      {/* Hero: the paper, its question and its one visual */}
      <section className="grid grid-cols-1 lg:grid-cols-12 gap-12 xl:gap-16 items-center">
        <div className="lg:col-span-6 space-y-6">
          <span className="section-label">Research paper</span>
          <h1 className="font-serif text-[44px] sm:text-[60px] lg:text-[68px] leading-[1.1] text-[#15263a]">
            {data.metadata.paper_title}
          </h1>
          <p className="text-[18px] sm:text-[19px] leading-[1.55] text-[#3c3a37] max-w-[36rem]">
            Engagement graphs are used to tell coordinated campaigns apart from organic activity. We measure how much of their
            predictive signal needs anything beyond a graph's node and edge counts, on full graphs and on fixed-size samples of edges.
          </p>
          <Authors />
          <div className="flex flex-wrap gap-3 pt-2">
            <a href={pdfHref(data)} className="btn-primary">
              <FileText size={16} strokeWidth={1.5} />
              Read the paper
            </a>
            <button type="button" onClick={() => setActiveTab("results")} className="btn-secondary">
              See the results
              <ArrowRight size={16} strokeWidth={1.5} />
            </button>
          </div>
        </div>

        <figure className="lg:col-span-6 bg-white border border-[#dcd7ca] rounded-[12px] p-6 sm:p-8">
          <SizeStrip points={data.event_points} medians={{ 1: D.nodes.campaign.median, 0: D.nodes.comparison.median }} />
          <figcaption className="mt-5 pt-4 border-t border-[#ece6d8] text-[15px] leading-relaxed text-[#3c3a37]">
            Every one of the {D.n_events} event graphs, placed by node count. Comparison graphs (median {int(D.nodes.comparison.median)} nodes)
            are several times larger than campaign graphs (median {int(D.nodes.campaign.median)}). Logistic regression given only node
            and edge counts reaches balanced accuracy <span className="font-mono tabular">{f3(lr.M0.balanced_accuracy)}</span> and AUC{" "}
            <span className="font-mono tabular">{f3(lr.M0.roc_auc_ll_fit)}</span>.
          </figcaption>
        </figure>
      </section>

      {/* Motivation and the question */}
      <section className="grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-16">
        <div className="lg:col-span-4">
          <h2 className="section-title">Why ask this</h2>
        </div>
        <div className="lg:col-span-8 reading-prose">
          <p>
            Benchmarks such as the Large Engagement Networks (LEN) release label each Twitter event graph as campaign-associated or
            comparison, and graph-learning methods are evaluated on them. A high score invites the reading that a model has learned
            something about how campaigns spread. That reading depends on what the labels can be predicted from.
          </p>
          <p>
            Simple baselines often match elaborate graph models, and engagement graphs give a specific reason to expect it here:
            the two classes differ strongly in size. Full graphs are also not the only way such data are seen. Fixing the number of
            observed edges looks like a way to hold size constant, but sampling changes what graph statistics measure.
          </p>
          <blockquote className="mt-8 border-l-2 border-[#15263a] pl-6 font-serif text-[22px] leading-snug text-[#15263a] not-italic">
            How well can the campaign label be predicted from node and edge counts, and what, if anything, adds to that prediction?
          </blockquote>
        </div>
      </section>

      {/* The two studies */}
      <section>
        <div className="section-head">
          <h2 className="section-title">Two studies</h2>
          <span className="section-head-meta">Same events, same folds, paired comparisons</span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <StudyCard
            n="Study 1"
            title="Full observation"
            text={<>Nested logistic-regression models add degree concentration, higher-order arrangement and message content to the counts.
              Three contrasts were specified in advance; a degree-preserving rewiring null tests arrangement, and {A.study1_20_partitions.n_partitions} repartitions
              of the events test how much the answer depends on one partition into folds.</>}
          />
          <StudyCard
            n="Study 2"
            title="Edge-limited observation"
            text={<>Each graph is reduced to K = 250, 500 or 1000 uniformly sampled edges, ten times. In a K-edge view the edge count is fixed,
              so the count that still varies is the view's node count <NK />. We ask what structural and message-level statistics add to it,
              and how models trained on views compare with full-graph models applied to them.</>}
          />
        </div>
      </section>

      {/* Findings */}
      <section>
        <div className="section-head">
          <h2 className="section-title">What we found</h2>
          <span className="section-head-meta">Grouped by the strength of the evidence</span>
        </div>
        <FindingGroup title="Prespecified comparisons" note="Fixed before the final analysis; Holm-adjusted">
          <Finding
            i="1"
            title="Counts alone predict the label well"
            body={<>Node and edge counts reach balanced accuracy {f3(lr.M0.balanced_accuracy)}, AUC {f3(lr.M0.roc_auc_ll_fit)} and log loss {f3(lr.M0.log_loss)} on the
              prespecified partition. Any richer feature has to be judged against this baseline.</>}
          />
          <Finding
            i="2"
            title="More features improve probabilistic prediction, without a detectable gain in decisions"
            body={<>Adding every other feature changed log loss by {sg(C1.log_loss.delta_logloss)} {ci(C1.log_loss.delta_logloss_ci)} (Holm-adjusted
              p = {f3(C1.log_loss.p_holm)}), but balanced accuracy showed no detectable gain ({sg(C1.ba.delta_ba)} {ci(C1.ba.delta_ba_ci)}).</>}
            note={<>Sensitivity analysis: over {A.study1_20_partitions.n_partitions} repartitions of the same events the log-loss difference was {sg(C.C1.dLL)}{" "}
              {ci(C.C1.dLL_ci)}, in the same direction in {C.C1.repeats_favouring_A_LL} of {C.C1.n_repeats}.</>}
          />
        </FindingGroup>
        <FindingGroup title="Exploratory analyses" note="Planned, outside the prespecified family">
          <Finding
            i="3"
            title="A fixed edge budget does not remove size"
            body={<>The view's node count <NK /> alone reaches AUC {nkAUC.join(", ")} at K = 250, 500 and 1000. Its expectation depends only on the budget and
              the full graph's degree sequence; node count and mean degree explain {pct(r2["log N + log mean degree"])}% of its variation at K = 250, and the
              structural features of a view largely track it.</>}
            note={<>Under full observation, no feature family detectably improved on the counts by itself; structural features helped only alongside
              content ({sg(C.E2.dLL)} {ci(C.E2.dLL_ci)}, unadjusted).</>}
          />
        </FindingGroup>
        <FindingGroup title="Post-hoc analyses" note="Chosen after inspecting these data; a lead, not a result">
          <Finding
            i="4"
            title="One edge-by-edge statistic is worth testing"
            body={<>Token-count dispersion, the spread of message lengths in whitespace tokens, estimates the same quantity at every budget. Added to <NK />{" "}
              and structure at K = 1000 it was associated with lower log loss ({sg(V["D-C"].K1000.dLL)} {ci(V["D-C"].K1000.dLL_ci)}), the only one of the six
              dispersion contrasts to survive Holm adjustment.</>}
            note={<>Added to <NK /> alone, the estimates favoured it at every budget, with intervals that include zero or do not survive adjustment. It needs
              testing on independent events.</>}
          />
        </FindingGroup>
      </section>

      {/* Abstract */}
      <section className="grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-16">
        <div className="lg:col-span-4 space-y-3">
          <h2 className="section-title">Abstract</h2>
          <a href={pdfHref(data)} className="inline-flex items-center gap-2 text-[16px] text-[#23527c] underline decoration-[#b5ad9e] underline-offset-4 hover:text-[#15263a]">
            <FileText size={16} strokeWidth={1.5} />
            Full paper, PDF
          </a>
        </div>
        <div className="lg:col-span-8 reading-prose">
          <p>
            Engagement graphs, built from the retweets, replies and quotes that link accounts, are used to distinguish coordinated campaigns
            from organic activity. A model that classifies them well is easily read as having learned how campaigns spread, so the source of its
            predictive signal matters. How much of that signal can simple graph measurements capture, and what do structural and content features
            add? We study {D.n_events} Twitter event graphs from the Large Engagement Networks (LEN) project archive. We first compare node and edge
            counts with models adding degree concentration, higher-order arrangement and message content on complete graphs, and then ask what
            remains informative when only a fixed number of edges is observed, as in sampled engagement data.
          </p>
          <p>
            Node and edge counts alone separate campaign from comparison events well (balanced accuracy {f3(lr.M0.balanced_accuracy)}). The other
            features improved probabilistic predictions, lowering log loss in the prespecified comparison and in {C.C1.repeats_favouring_A_LL} of{" "}
            {C.C1.n_repeats} repartitions, but classification decisions showed no detectable improvement, and no feature family alone detectably
            improved on the counts. Under a fixed edge budget, the number of distinct nodes a sample reaches remained highly informative, because it
            is largely set by the full graph's size and degree sequence. An edge-by-edge statistic, the dispersion of message token counts, measured
            the same quantity at every budget, yet its added predictive value, identified post hoc, was uncertain: measurement stability and
            additional predictive value are different questions. Complex features should therefore be judged against simple baselines, and stable
            measurements should not be read as additional predictive information.
          </p>
        </div>
      </section>

      {/* Data and provenance */}
      <section className="grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-16">
        <div className="lg:col-span-4">
          <h2 className="section-title">The data</h2>
          <p className="head-desc">What every claim on this site applies to.</p>
        </div>
        <div className="lg:col-span-8 space-y-6">
          <dl className="grid grid-cols-1 sm:grid-cols-2 gap-x-10 gap-y-5 text-[16px]">
            <Fact term="Archive" value={`Obtained from the LEN project website: ${D.archive_json_files} graph files, ${D.duplicates_removed} exact duplicate removed, ${D.n_events} unique graphs (${D.n_campaign} campaign, ${D.n_comparison} comparison)`} />
            <Fact term="Relation to LEN-Small" value={`Distinct from the LEN paper's published LEN-Small description (${D.official_len_small.n_graphs} graphs, ${D.official_len_small.n_campaign}/${D.official_len_small.n_noncampaign})`} />
            <Fact term="Message text" value={`${pct(X.null_share)}% of ${int(X.links_total)} edge texts are null; mean usable share ${f2(X.usable_share_mean_campaign)} in campaign and ${f2(X.usable_share_mean_comparison)} in comparison graphs; ${X.events_without_usable_text} campaign graphs have none`} />
            <Fact term="Not available" value="Account identifiers, campaign subtypes and verified timestamp semantics, so account overlap and temporal features are out of scope" />
          </dl>
          <p className="text-[16px] text-[#5e5a52] max-w-[70ch]">
            Labels come from the dataset's file names and are not independently verified. The results describe this archive and need not hold for
            other LEN data.
          </p>
        </div>
      </section>

      {/* Limitations */}
      <section className="grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-16">
        <div className="lg:col-span-4">
          <h2 className="section-title">Limits of the evidence</h2>
        </div>
        <ul className="lg:col-span-8 space-y-4 text-[17px] leading-relaxed text-[#2f2d2a] max-w-[70ch]">
          <li>With {D.n_events} events ({P.eligibility["1000"].total_eligible} at K = 1000), intervals are wide; no detectable difference is not evidence of equivalence.</li>
          <li>Bootstrap intervals exclude refitting variability, which the repartitions show to be of comparable size. Repartitions and sampling seeds reuse the same events.</li>
          <li>Token-count dispersion was chosen after inspecting these events and is computed on retained text, whose availability differs by class.</li>
          <li>Budget is confounded with cohort composition in the edge-limited analysis, and only uniform edge sampling was studied.</li>
          <li>Only logistic regression and gradient-boosted trees on hand-crafted features were evaluated. Nothing here detects coordinating accounts, intent or causal effects.</li>
        </ul>
      </section>

      {/* Continue */}
      <section className="border-t border-[#15263a] pt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
        {[
          ["results", "Results", "Both studies, their figures and comparisons, grouped by the strength of the evidence"],
          ["methods", "Methods", "Features, models, uncertainty, reproduction commands and references"],
          ["dataset", "Dataset", "Open any of the event graphs and see what a sample of edges keeps"],
        ].map(([id, title, text]) => (
          <button key={id} type="button" onClick={() => setActiveTab(id)} className="group text-left py-2">
            <span className="flex items-center gap-2 font-serif text-xl text-[#15263a] group-hover:text-[#23527c]">
              {title}
              <ArrowRight size={16} strokeWidth={1.5} className="transition-transform group-hover:translate-x-0.5" />
            </span>
            <span className="block mt-1 text-[16px] text-[#5e5a52]">{text}</span>
          </button>
        ))}
      </section>
    </div>
  );
}

function StudyCard({ n, title, text }) {
  return (
    <div className="border border-[#dcd7ca] bg-white rounded-[12px] p-6 sm:p-8">
      <div className="text-[15px] font-mono text-[#8f2626]">{n}</div>
      <h3 className="mt-2 font-serif text-2xl text-[#15263a]">{title}</h3>
      <p className="mt-3 text-[17px] leading-relaxed text-[#3c3a37]">{text}</p>
    </div>
  );
}

function FindingGroup({ title, note, children }) {
  return (
    <div className="mt-8 first:mt-0">
      <div className="evidence-head">
        <h3>{title}</h3>
        <p>{note}</p>
      </div>
      <ol className="divide-y divide-[#ece6d8]">{children}</ol>
    </div>
  );
}

function Finding({ i, title, body, note }) {
  return (
    <li className="grid grid-cols-[32px_1fr] sm:grid-cols-[52px_1fr] gap-x-4 py-5 first:pt-1">
      <span className="font-serif text-[30px] leading-none text-[#9a948a] tabular">{i}</span>
      <div className="min-w-0 max-w-[82ch]">
        <h4 className="font-serif text-[25px] leading-snug text-[#15263a]">{title}</h4>
        <p className="mt-1.5 text-[17.5px] leading-relaxed text-[#2f2d2a]">{body}</p>
        {note && <p className="mt-2 text-[16.5px] leading-relaxed text-[#5e5a52] italic">{note}</p>}
      </div>
    </li>
  );
}

function Fact({ term, value }) {
  return (
    <div>
      <dt className="text-[15px] font-medium text-[#15263a]">{term}</dt>
      <dd className="mt-1 text-[#3c3a37] leading-relaxed tabular">{value}</dd>
    </div>
  );
}

// The hero's one visual: every event placed by node count (log scale), campaign above, comparison below
function SizeStrip({ points, medians }) {
  const W = 480, H = 160;
  const xs = points.map((e) => e.log_nodes);
  const lo = Math.min(...xs), hi = Math.max(...xs);
  const X = (v) => 8 + ((v - lo) / (hi - lo)) * (W - 16);
  const ticks = [100, 300, 1000, 3000, 10000].filter((t) => Math.log1p(t) >= lo && Math.log1p(t) <= hi);
  const med = (lab) => Math.log1p(medians[lab]);  // stored class medians (paper Table I)
  const rows = [[1, "#8f2626", "Campaign", 22, 60], [0, "#23527c", "Comparison", 82, 120]];
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto" role="img" aria-label="Every event placed by node count; campaign events above, comparison events below">
      {rows.map(([lab, color, name, y1, y2]) => (
        <g key={lab}>
          <text x={8} y={y1 - 7} fontSize="14" fill={color} fontFamily="var(--font-sans)">{name}</text>
          {points.filter((e) => e.label === lab).map((e) => (
            <line key={e.event_id} x1={X(e.log_nodes)} x2={X(e.log_nodes)} y1={y1} y2={y2} stroke={color} strokeOpacity="0.5" strokeWidth="1.5" />
          ))}
          <line x1={X(med(lab))} x2={X(med(lab))} y1={y1 - 2} y2={y2 + 2} stroke={color} strokeWidth="3" />
        </g>
      ))}
      <line x1="0" x2={W} y1={132} y2={132} stroke="#dcd7ca" />
      {ticks.map((t) => (
        <text key={t} x={Math.max(X(Math.log1p(t)), 12)} y={152} textAnchor="middle" fontSize="13" fill="#757065" fontFamily="var(--font-mono)">{t >= 1000 ? `${t / 1000}k` : t}</text>
      ))}
    </svg>
  );
}
