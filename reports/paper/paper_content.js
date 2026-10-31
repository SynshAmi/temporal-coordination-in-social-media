// Paper content: every number is read from outputs/run_v2/paper_results.json.
// Loaded by build_paper.js, which supplies the template helpers in `h`.
module.exports = function buildContent(h, R) {
  const { P, H1, H2, bullet, figure, table, eq, runs, Paragraph, TextRun } = h;
  const minus = (t) => t.replace(/^-/, "\u2212");
  const f3 = (v) => (v == null ? "—" : minus(Number(v).toFixed(3)));
  const f2 = (v) => minus(Number(v).toFixed(2));
  const pct = (v) => (100 * v).toFixed(1);
  const sg = (v) => (Math.abs(v) < 0.0005 ? "0.000" : (v > 0 ? "+" : "\u2212") + Math.abs(v).toFixed(3));
  const ci = (a) => `[${sg(a[0])}, ${sg(a[1])}]`;
  const ciu = (a) => `[${f3(a[0])}, ${f3(a[1])}]`;
  const pv = (p) => (p < 0.001 ? "<0.001" : f3(p));
  const int = (v) => Math.round(v).toLocaleString("en-US");

  // ---- citations: numbered in order of first appearance -------------------------
  const REFS = {
    len: `A. A. Gopalakrishnan, J. Hossain, T. Elmas, and A. E. Sarıyüce, "Large engagement networks for classifying coordinated campaigns and organic Twitter trends," in *Proc. Int. AAAI Conf. Web and Social Media (ICWSM)*, vol. 19, no. 1, pp. 688–702, 2025, doi: 10.1609/icwsm.v19i1.35839.`,
    decode: `A. A. Gopalakrishnan, J. Hossain, T. Elmas, and A. E. Sarıyüce, "Density-aware walks for coordinated campaign detection," in *Proc. European Conf. Machine Learning and Principles and Practice of Knowledge Discovery in Databases (ECML PKDD)*, 2025, pp. 283–298, arXiv:2506.13912.`,
    repo: `"LEN: Large Engagement Networks," dataset repository. [Online]. Available: https://erdemub.github.io/large-engagement-network/`,
    li: `Z. Li, Y. Cao, K. Shuai, Y. Miao, and K. Hwang, "Rethinking the effectiveness of graph classification datasets in benchmarks for assessing GNNs," in *Proc. Int. Joint Conf. Artificial Intelligence (IJCAI)*, 2024, pp. 2144–2152, doi: 10.24963/ijcai.2024/237.`,
    coupette: `C. Coupette, J. Wayland, E. Simons, and B. Rieck, "No metric to rule them all: Toward principled evaluations of graph-learning datasets," in *Proc. Int. Conf. Machine Learning (ICML)*, PMLR, vol. 267, 2025, pp. 11405–11434.`,
    errica: `F. Errica, M. Podda, D. Bacciu, and A. Micheli, "A fair comparison of graph neural networks for graph classification," in *Proc. Int. Conf. Learning Representations (ICLR)*, 2020.`,
    jacobs: `A. Z. Jacobs and H. Wallach, "Measurement and fairness," in *Proc. ACM Conf. Fairness, Accountability, and Transparency (FAccT)*, 2021, pp. 375–385, doi: 10.1145/3442188.3445901.`,
    leskovec: `J. Leskovec and C. Faloutsos, "Sampling from large graphs," in *Proc. ACM SIGKDD Int. Conf. Knowledge Discovery and Data Mining*, 2006, pp. 631–636, doi: 10.1145/1150402.1150479.`,
    maslov: `S. Maslov and K. Sneppen, "Specificity and stability in topology of protein networks," *Science*, vol. 296, no. 5569, pp. 910–913, 2002.`,
    varoquaux: `G. Varoquaux, "Cross-validation failure: Small sample sizes lead to large error bars," *NeuroImage*, vol. 180, pp. 68–77, 2018.`,
    holm: `S. Holm, "A simple sequentially rejective multiple test procedure," *Scandinavian J. Statistics*, vol. 6, no. 2, pp. 65–70, 1979.`,
    efron: `B. Efron and R. J. Tibshirani, *An Introduction to the Bootstrap*. New York, NY, USA: Chapman & Hall, 1993.`,
    austin: `P. C. Austin, "Balance diagnostics for comparing the distribution of baseline covariates between treatment groups in propensity-score matched samples," *Statistics in Medicine*, vol. 28, no. 25, pp. 3083–3107, 2009, doi: 10.1002/sim.3697.`,
    stuart: `E. A. Stuart, "Matching methods for causal inference: A review and a look forward," *Statistical Science*, vol. 25, no. 1, pp. 1–21, 2010.`,
    sklearn: `F. Pedregosa et al., "Scikit-learn: Machine learning in Python," *J. Mach. Learn. Res.*, vol. 12, pp. 2825–2830, 2011.`,
    nx: `A. A. Hagberg, D. A. Schult, and P. J. Swart, "Exploring network structure, dynamics, and function using NetworkX," in *Proc. 7th Python in Science Conf. (SciPy)*, 2008, pp. 11–15.`,
  };
  const order = [];
  const c = (...keys) => keys.map((k) => { if (!REFS[k]) throw new Error(`unknown ref ${k}`); if (!order.includes(k)) order.push(k); return `[${order.indexOf(k) + 1}]`; }).join(", ");

  // ---- data -------------------------------------------------------------------------
  const D = R.dataset, S1 = R.study1, S2 = R.study2, NM = R.null_model, MT = R.matching, EL = R.eligibility;
  const lr = S1.performance.logreg, hg = S1.performance.hgbt, LC = S1.confirmatory.logreg;
  const rep = S1.repeated_splits_lr, ro = S1.row_order_sensitivity, X = S1.hgbt_vs_best_count_baseline;
  const B0a = R.run_v2_metrics.B0a_log_node_logreg;
  const cond = (k, key) => S2.results[`budget_specific_K${k}`].conditions[key];
  const con = (k, name) => S2.contrasts[`budget_specific_K${k}`][name];
  const conC = (k, name) => S2.contrasts[`common_K${k}`][name];
  const r2 = S2.mechanism_r2_K250, mech = S2.mechanism;
  const nE = D.n_events;
  const baMaxHi = Math.max(...["C1", "C2", "C3"].map((k) => LC[k].ba.delta_ba_ci[1]));
  const body = [];

  // ---- abstract / keywords ------------------------------------------------------------
  body.push(
    new Paragraph({ style: "Abstract", children: [
      new TextRun({ text: "Abstract", italics: true, bold: true }), new TextRun({ text: "—", bold: true }),
      ...runs(`LEN-Small is a benchmark of Twitter engagement graphs labeled as campaign-associated or comparison events. We ask what its labels can be predicted from. On a distributed archive of ${nE} canonical event graphs, three more than the official 100-graph release, logistic regression given only node and edge counts reaches a balanced accuracy of ${f3(lr.M0.balanced_accuracy)}. Adding degree, higher-order arrangement and content features did not detectably improve balanced accuracy in paired event-level comparisons (difference ${sg(LC.C1.ba.delta_ba)}, 95 percent interval ${sg(LC.C1.ba.delta_ba_ci[0])} to ${sg(LC.C1.ba.delta_ba_ci[1])}), but improved log loss by ${f3(-LC.C1.log_loss.delta_logloss)} and ranking quality by ${f3(LC.C1.auc_ll_fit.delta_auc)} in area under the curve. The arrangement features did not outperform the same features computed on degree-preserving rewired graphs. In fixed-budget edge samples, a single view retains strong label information, carried largely by the number of distinct sampled endpoints, whose expectation is strongly associated with full-graph node count and mean degree. Training on observations of the kind being scored matters far more than averaging repeated views. The results describe what the released labels are predictable from; they do not detect coordinating accounts.`, { bold: true }),
    ] }),
    new Paragraph({ style: "Keywords", children: [
      new TextRun({ text: "Keywords", italics: true, bold: true }), new TextRun({ text: "—", bold: true }),
      new TextRun({ text: "benchmark validity, graph classification, coordinated campaigns, paired evaluation, probabilistic evaluation, degree-preserving null model, graph sampling", bold: true, italics: true }),
    ] }),
  );

  // ---- I. Introduction ----------------------------------------------------------------
  body.push(H1("Introduction"),
    P(`Coordinated campaigns on social media, such as organized efforts to push a hashtag into a platform's trending list, are often studied through engagement graphs, in which accounts are nodes and retweets, replies or quotes are directed edges. The Large Engagement Networks (LEN) benchmark ${c("len")} releases such graphs with event-level labels, and later work proposes graph-learning methods on it ${c("decode")}. A high benchmark score is usually read as evidence that a model has learned something about coordination. Whether that reading is justified depends on what the labels can be predicted from: a construct question, not only a performance question ${c("jacobs")}.`),
    P(`LEN-Small is constructed as the 100 smallest LEN graphs by node count ${c("len")}, and comparison events in it are several times larger than campaign events. Simple graph properties are known to rival learned models on many graph benchmarks ${c("li", "errica", "coupette")}. We therefore ask two questions of the released archive. *RQ1 (incremental information):* what do degree concentration, higher-order arrangement and retained content add beyond node and edge counts? *RQ2 (restricted observation):* how much label information survives in a single fixed-size sample of edges, what does the sampling mechanism make predictive, and how much does training on matching observations change performance?`),
    P(`Our contributions are a reproducible predictive-information audit of the distributed LEN-Small archive with three findings. First, counts alone reach most of the attainable balanced accuracy; combined features improve probability quality and ranking but show no reliable gain in classification decisions. Second, the tested arrangement features did not outperform their degree-preserving rewired counterparts. Third, at fixed edge budgets a single view remains highly predictive, largely through the number of distinct endpoints it touches, and observation-matched training dominates ensembling. The unit of analysis is the event graph throughout; we make no claims about individual accounts, bots, intent or causal effects.`),
  );

  // ---- II. Related work ---------------------------------------------------------------
  body.push(H1("Related Work"),
    P(`LEN ${c("len")} provides 314 engagement graphs (179 campaign, 135 non-campaign) with campaign subtypes, and LEN-Small, the 100 smallest graphs by node count (51 campaign, 49 non-campaign), distributed through the project repository ${c("repo")}. Its authors note that comparison events tend to produce larger networks. DECODE ${c("decode")} adds density-aware random-walk embeddings built on degree, core and truss numbers. We do not propose a detector or re-evaluate these models; we characterize the label signal they are evaluated against.`),
    P(`Benchmark-effectiveness studies show that structure-agnostic or simple-property baselines can match graph neural networks ${c("li", "errica")}, and that dataset quality can be assessed by perturbing graph structure and features ${c("coupette")}. Degree-preserving rewiring is a standard null model for separating degree-sequence effects from higher-order arrangement ${c("maslov")}, and graph sampling is known to distort graph statistics ${c("leskovec")}. Small-sample cross-validation produces wide error bars ${c("varoquaux")}. Our contribution is the application of paired, estimand-specific evaluation, a degree-preserving null and a single-view observation design to one released benchmark, with an explicit account of what each analysis can and cannot show.`),
  );

  // ---- III. Data and provenance -------------------------------------------------------
  body.push(H1("Data and Provenance"),
    H2("Archive, Labels and Canonical Cohort"),
    P(`The analysed archive contains ${D.archive_json_files} NetworkX node-link JSON files. Ingestion computes a SHA-256 digest of every file; ${D.duplicates_removed} byte-identical duplicate, a campaign graph whose two file names differ only in a Turkish dotless "ı" versus ASCII "i", is removed, leaving ${nE} canonical events (${D.n_campaign} campaign, ${D.n_comparison} comparison). Labels are read from the file-name tokens _campaign_ and _noncampaign_. **This archive does not match the official release.** The LEN paper describes LEN-Small as ${D.official_len_small.n_graphs} graphs (${D.official_len_small.n_campaign} campaign, ${D.official_len_small.n_noncampaign} non-campaign), the smallest 100 of 314 by node count ${c("len")}. We could not determine why the archive holds three additional events, and we make no claim of equivalence to the official selection; all results refer to the ${nE}-event archive.`),
    P(`Graphs are directed and simple (no repeated directed pairs), with ${int(D.n_edges_total)} edges in total, including ${int(D.n_self_loops)} self-loops that occur in every event. Node identifiers are per-graph indices (0 to N−1); the release contains no account identifiers, so cross-event account overlap cannot be measured. Pretrained text and profile embeddings attached to nodes and edges are excluded to keep the analysis interpretable and avoid unexplained representation effects. Edge timestamps are present, but whether they record the engagement action or the engaged-with post is not verified, so no temporal features are used. Table I summarizes the cohort, and Fig. 1 shows the size difference between classes: the signed standardized mean difference (SMD) of log node count is ${f2(D.smd_log_nodes_full_cohort)}.`),
    ...table("TABLE I.\tArchive and Cohort", ["Item", "Value"], [
      ["Archive JSON files", `${D.archive_json_files} (${D.duplicates_removed} SHA-256 duplicate removed)`],
      ["Canonical events", `${nE} (${D.n_campaign} campaign / ${D.n_comparison} comparison)`],
      ["Official LEN-Small", `${D.official_len_small.n_graphs} (${D.official_len_small.n_campaign} / ${D.official_len_small.n_noncampaign}); smallest 100 of 314 by node count`],
      ["Nodes, median [IQR]", `campaign ${int(D.nodes.campaign.median)} [${int(D.nodes.campaign.q25)}–${int(D.nodes.campaign.q75)}]; comparison ${int(D.nodes.comparison.median)} [${int(D.nodes.comparison.q25)}–${int(D.nodes.comparison.q75)}]`],
      ["Edges, median [IQR]", `campaign ${int(D.edges.campaign.median)} [${int(D.edges.campaign.q25)}–${int(D.edges.campaign.q75)}]; comparison ${int(D.edges.comparison.median)} [${int(D.edges.comparison.q25)}–${int(D.edges.comparison.q75)}]`],
      ["Edges / self-loops", `${int(D.n_edges_total)} / ${int(D.n_self_loops)} (all ${D.events_with_self_loops} events)`],
      ["Account identifiers", "none (per-graph node indices)"],
    ], [1500, 3540]),
    ...figure("fig1_size_distributions.png", `Fig. 1.\tEvent-graph size by class on a logarithmic axis. Left: node count; right: edge count. Boxes show interquartile ranges and medians; points are events (comparison n = ${D.n_comparison}, campaign n = ${D.n_campaign}).`),
  );

  // ---- IV. Methods ----------------------------------------------------------------------
  body.push(H1("Methods"),
    H2("Features and Conventions"),
    P(`All features are computed per event graph G = (V, E) with NetworkX ${c("nx")}. *Counts:* log(1+|V|) and log(1+|E|). *Degree concentration:* Gini coefficients of the in-degree and out-degree sequences, where for a non-negative vector x sorted ascending`),
    eq(null, 1),
    P(`*Arrangement:* reciprocity, the fraction of nodes in the largest weakly connected component, and the median and maximum core number. Core numbers are computed on the simple undirected projection with self-loops removed ({u, v} is an edge if (u, v) or (v, u) is, u ≠ v); a node whose only edges are self-loops has core number 0. *Content:* exact-duplicate fraction of cleaned message texts, a Gini coefficient over message frequencies, and the standard deviation of message token counts. Density |E|/(|V|(|V|−1)) is a deterministic function of the counts; we therefore treat it as scale-encoding, not as topology, and use it only in a diagnostic model.`),
    H2("Study 1: Nested Models and Paired Inference"),
    P(`Seven nested feature levels share identical event-level folds: M0 counts; M0q counts with squared and interaction terms as a nonlinear count control; M1 = M0q + degree Gini; M2 = M1 + arrangement; M3 = M0q + content; M4 = M2 + content; and a diagnostic M4 + density. Three contrasts are confirmatory: C1 (M4 vs M0q, anything beyond counts), C2 (M2 vs M1, arrangement beyond degree concentration) and C3 (M3 vs M0q, content beyond counts). Other contrasts are exploratory.`),
    P(`Logistic regression (LR, median imputation, standardization, balanced class weights) is the primary model ${c("sklearn")}; gradient-boosted trees (HGBT) are secondary. All hyperparameters are tuned by inner three-fold cross-validation inside each outer training fold. Balanced accuracy (BA) and log loss are distinct estimands with separately tuned fits: BA uses fits tuned for BA, log loss uses fits tuned for log loss, and area under the ROC curve (AUC) is secondary. Differences are estimated on identical events with an event-level paired bootstrap of fixed out-of-fold predictions ${c("efron")} (${S1.n_bootstrap} resamples), with Holm correction applied separately to the three BA and the three log-loss confirmatory tests ${c("holm")}. These intervals do not include refitting or split variability ${c("varoquaux")}; we report that separately from ${S1.n_split_seeds} re-drawn fold splits, which are not independent replicates.`),
    H2("Degree-Preserving Null"),
    P(`To test arrangement beyond degree ${c("maslov")}, each graph is rewired by directed double-edge swaps (a, b), (c, d) → (a, d), (c, b) on non-loop edges, rejecting swaps that create self-loops or repeated edges. Self-loops are held fixed. This preserves every node's in- and out-degree, |V|, |E|, density and the degree Gini coefficients exactly, while randomizing reciprocity, connectivity and core structure. Directed double-edge swaps do not reach every digraph with the given degrees, so this is a degree-preserving null rather than a uniform sample. We use ${NM.swaps_per_edge} swaps per edge and ${NM.realizations} realizations per event, refit M2 with arrangement features from the rewired graphs, and compare it with M2 on the real graphs. Realizations are nested within events and are not independent samples.`),
    H2("Exploratory Size Matching"),
    P(`Campaign and comparison events are matched one-to-one on log node count with a caliper of ${MT.caliper_sd_fraction} standard deviations ${c("austin", "stuart")}, giving ${MT.primary_pairs} pairs (32 events; signed SMD ${f3(MT.smd_before)} → ${f3(MT.smd_after)}, i.e. |SMD| ${f2(Math.abs(MT.smd_before))} → ${f2(Math.abs(MT.smd_after))}). Because greedy matching depends on visiting order and node-only matching does not balance edge counts, we repeat it over ${MT.node_only.n_order_seeds} visiting orders, with and without edge counts as a second matching variable, keeping pairs in the same fold. With about 16 pairs, this analysis is exploratory.`),
    H2("Study 2: Single-View Observation Design"),
    P(`For K ∈ {250, 500, 1000}, eligible events (at least K edges) are reduced to K uniformly sampled edges, with ten sampling seeds per event, and every feature is recomputed from the sampled edges only. All conditions at a given K use the same events, the full-cohort folds restricted to those events, and the same feature definitions: *FF*, a model trained and evaluated on full graphs; *FK*, the full-graph model applied to single K-edge views (frozen transfer); and *KK*, a model trained and evaluated on single K-edge views from the same seed. Feature sets are the sampled endpoint count N~K~ alone, six structural features (degree Gini, reciprocity, largest component, coreness), N~K~ plus structure, and N~K~ plus structure plus content. Density is excluded because at fixed K it is determined by N~K~:`),
    eq(null, 2),
    P(`The primary estimand is single-view performance, computed per sampling seed and averaged over seeds; the ensemble that averages probabilities over the ten views is reported separately. We report budget-specific cohorts (K = 250: ${EL["250"].total_eligible} events, ${EL["250"].campaign_eligible}/${EL["250"].comparison_eligible}; K = 500: ${EL["500"].total_eligible}, ${EL["500"].campaign_eligible}/${EL["500"].comparison_eligible}; K = 1000: ${EL["1000"].total_eligible}, ${EL["1000"].campaign_eligible}/${EL["1000"].comparison_eligible}) and a common cohort of the ${EL["1000"].total_eligible} events eligible at every budget. K = 2000 is infeasible for five-fold stratified evaluation because only ${EL["2000"].campaign_eligible} campaign events have at least 2,000 edges. To explain the sampled endpoint count, we use its expectation under uniform sampling of K of the m = |E| edges without replacement, where d~v~ is the number of distinct edges incident to v:`),
    eq(null, 3),
  );

  // ---- V. Results ------------------------------------------------------------------------
  const levelRows = ["M0", "M0q", "M1", "M2", "M3", "M4", "M4d"].map((lv) => [
    lv === "M4d" ? "M4 + density" : lv,
    f3(lr[lv].balanced_accuracy), f3(lr[lv].log_loss), f3(lr[lv].roc_auc_ll_fit),
    f3(hg[lv].balanced_accuracy), f3(hg[lv].log_loss), f3(hg[lv].roc_auc_ll_fit)]);
  const conRows = ["C1", "C2", "C3"].map((k) => [
    `${k}: ${LC[k].a} vs ${LC[k].b}`,
    `${sg(LC[k].ba.delta_ba)} ${ci(LC[k].ba.delta_ba_ci)} (${pv(LC[k].ba.p_holm)})`,
    `${sg(LC[k].log_loss.delta_logloss)} ${ci(LC[k].log_loss.delta_logloss_ci)} (${pv(LC[k].log_loss.p_holm)})`,
    `${sg(LC[k].auc_ll_fit.delta_auc)} ${ci(LC[k].auc_ll_fit.delta_auc_ci)}`]);
  body.push(H1("Results"),
    H2("Counts and Incremental Information (RQ1)"),
    P(`Table II reports out-of-fold performance by feature level. Node and edge counts alone (M0, LR) reach BA ${f3(lr.M0.balanced_accuracy)} (node count alone: ${f3(B0a.balanced_accuracy)}). The full feature set M4 reaches BA ${f3(lr.M4.balanced_accuracy)}, log loss ${f3(lr.M4.log_loss)} and AUC ${f3(lr.M4.roc_auc_ll_fit)}, against ${f3(lr.M0q.log_loss)} and ${f3(lr.M0q.roc_auc_ll_fit)} for the count model.`),
    P(`The confirmatory contrasts (Table III, Fig. 2) separate the three measures. **For classification decisions, no contrast shows a detectable gain:** C1, the difference in BA between all features and counts, is ${sg(LC.C1.ba.delta_ba)} ${ci(LC.C1.ba.delta_ba_ci)}, with ${LC.C1.ba.mcnemar_a_right_b_wrong} events classified correctly only by M4 and ${LC.C1.ba.mcnemar_b_right_a_wrong} only by the count model. C2 and C3 are also indistinguishable from zero. These are inconclusive results, not evidence of equivalence: the intervals admit gains of up to about ${f2(baMaxHi)}. **For probability quality and ranking, the combined features help:** C1 improves log loss by ${f3(-LC.C1.log_loss.delta_logloss)} ${ci(LC.C1.log_loss.delta_logloss_ci)} (Holm p = ${pv(LC.C1.log_loss.p_holm)}) and AUC by ${f3(LC.C1.auc_ll_fit.delta_auc)} ${ci(LC.C1.auc_ll_fit.delta_auc_ci)}. Neither arrangement beyond degree (C2) nor content alone (C3) accounts for this gain. Log loss is a proper scoring rule that reflects both calibration and discrimination; calibration was not assessed separately.`),
    ...table("TABLE II.\tOut-of-Fold Performance by Feature Level (N = 103)", ["Level", "LR BA", "LR log loss", "LR AUC", "HGBT BA", "HGBT log loss", "HGBT AUC"], levelRows,
      [760, 713, 713, 713, 713, 714, 714], "BA from BA-tuned fits; log loss and AUC from log-loss-tuned fits."),
    ...table("TABLE III.\tConfirmatory Paired Contrasts, LR (Δ [95% CI] (Holm p))", ["Contrast", "Δ BA", "Δ log loss", "Δ AUC"], conRows, [1100, 1330, 1330, 1280]),
    ...figure("fig2_study1_contrasts.png", `Fig. 2.\tConfirmatory paired contrasts (LR, N = ${nE}). Points are differences A − B on identical events; bars are 95% event-level paired bootstrap intervals of fixed out-of-fold predictions. Filled red points exclude zero. Lower log loss is better.`),
    P(`These conclusions are stable in direction but not in magnitude. Across ${S1.n_split_seeds} re-drawn fold splits, the C1 BA difference ranged from ${sg(rep.C1.dBA_min)} to ${sg(rep.C1.dBA_max)}, the C1 log-loss difference from ${sg(rep.C1.dLL_min)} to ${sg(rep.C1.dLL_max)}, and the C1 AUC difference from ${sg(rep.C1.dAUC_min)} to ${sg(rep.C1.dAUC_max)}. Hyperparameter selection was also sensitive to the order of events: re-running with permuted rows moved the C1 BA difference from ${sg(ro["ba:C1"].delta_study_order)} to ${sg(ro["ba:C1"].delta_permuted_order)} and the C3 BA difference from ${sg(ro["ba:C3"].delta_study_order)} to ${sg(ro["ba:C3"].delta_permuted_order)}, while the C1 log-loss difference was unchanged (${sg(ro["ll:C1"].delta_study_order)}). HGBT is secondary: its own count model is weak (BA ${f3(hg.M0q.balanced_accuracy)}), so within-HGBT gains are inflated. Against the best count model (LR M0q), HGBT M4 changes BA by ${sg(X.HGBT_M4_vs_LR_M0q_ba.delta_ba)} ${ci(X.HGBT_M4_vs_LR_M0q_ba.delta_ba_ci)} and AUC by ${sg(X.HGBT_M4_vs_LR_M0q_ba.delta_auc)} ${ci(X.HGBT_M4_vs_LR_M0q_ba.delta_auc_ci)}, and its log loss (${f3(hg.M4.log_loss)}) is worse than LR's.`),
    H2("Arrangement Beyond Degree"),
    P(`Real graphs differ strongly from their rewired counterparts (median observed-minus-null z-scores for reciprocity of ${f2(NM.observed_vs_null_median_z.reciprocity.median_z_campaign)} in campaign and ${f2(NM.observed_vs_null_median_z.reciprocity.median_z_comparison)} in comparison events, and about ${f2(NM.observed_vs_null_median_z.largest_wcc_fraction.median_z_campaign)} for the largest-component fraction). However, this arrangement did not carry label information beyond the degree sequences: M2 on real graphs reached BA ${f3(NM.M2_real_ba)}, and M2 with arrangement features from rewired graphs reached ${f3(NM.M2_null_ba_mean)} on average (range ${f3(NM.M2_null_ba_range[0])}–${f3(NM.M2_null_ba_range[1])}); the paired difference was ${sg(NM.real_minus_null_ba.delta_ba)} ${ci(NM.real_minus_null_ba.delta_ba_ci)} for BA and ${sg(NM.real_minus_null_logloss.delta_logloss)} ${ci(NM.real_minus_null_logloss.delta_logloss_ci)} for log loss (Table IV). This shows only that the tested arrangement features did not outperform their degree-preserving counterparts under this null; it does not show that topology is uninformative. Mixing was limited: about ${Math.round(100 * NM.frac_edges_unchanged_quantiles[2])}% of non-loop edges per graph could not be moved (median), a plateau reached by five swaps per edge and concentrated in hub-dominated graphs, and the median core number showed no variation across realizations in ${Math.round(100 * NM.share_events_zero_null_variance.coreness_median)}% of events.`),
    ...table("TABLE IV.\tDegree-Preserving Null (LR, N = 103)", ["Quantity", "Value"], [
      ["M1 (counts + degree), BA", f3(NM.M1_ba)],
      ["M2 real arrangement, BA", f3(NM.M2_real_ba)],
      [`M2 rewired arrangement, BA (mean over ${NM.realizations})`, `${f3(NM.M2_null_ba_mean)} [${f3(NM.M2_null_ba_range[0])}–${f3(NM.M2_null_ba_range[1])}]`],
      ["Real − rewired, Δ BA [95% CI]", `${sg(NM.real_minus_null_ba.delta_ba)} ${ci(NM.real_minus_null_ba.delta_ba_ci)}`],
      ["Real − rewired, Δ log loss [95% CI]", `${sg(NM.real_minus_null_logloss.delta_logloss)} ${ci(NM.real_minus_null_logloss.delta_logloss_ci)}`],
      ["Unmoved non-loop edges, median [IQR]", `${f2(NM.frac_edges_unchanged_quantiles[2])} [${f2(NM.frac_edges_unchanged_quantiles[1])}–${f2(NM.frac_edges_unchanged_quantiles[3])}]`],
    ], [3000, 2040]),
    H2("Exploratory Size Matching"),
    P(`Across ${MT.node_only.n_order_seeds} visiting orders, node-only matching retained ${MT.node_only.n_pairs_range[0]}–${MT.node_only.n_pairs_range[1]} pairs but left edge counts imbalanced (|SMD| of log edge count ${f2(MT.node_only.smd_log_edges_range[0])}–${f2(MT.node_only.smd_log_edges_range[1])}). Within matched cohorts, the count model fell to near chance (median BA ${f3(MT.node_only.ba.M0.median)}), while content stayed above chance in every ordering (median ${f3(MT.node_only.ba.M3.median)}, range ${f3(MT.node_only.ba.M3.min)}–${f3(MT.node_only.ba.M3.max)}; Table V). With 15–17 pairs these estimates are imprecise, and matching changes the evaluated population; they are sensitivity evidence only.`),
    ...table("TABLE V.\tExploratory Matching Sensitivity, LR BA (Median [Range] Over Visiting Orders)", ["Matching", "Pairs", "M0 counts", "M3 content", "M4 all"], ["node_only", "node_edge"].map((k) => [
      k === "node_only" ? "Log node count" : "Log node + edge count", `${MT[k].n_pairs_range[0]}–${MT[k].n_pairs_range[1]}`,
      ...["M0", "M3", "M4"].map((lv) => `${f3(MT[k].ba[lv].median)} [${f3(MT[k].ba[lv].min)}–${f3(MT[k].ba[lv].max)}]`)]),
      [1180, 560, 1100, 1100, 1100]),
  );

  const s2rows = [["FF|struct6", "FF: full → full, structure"], ["FK|struct6", "FK: full → view, structure"], ["KK|struct6", "KK: view → view, structure"],
    ["KK|NK", "KK: N~K~ only"], ["KK|NK_struct6", "KK: N~K~ + structure"], ["KK|combined", "KK: N~K~ + structure + content"]]
    .map(([key, label]) => [label, ...[250, 500, 1000].map((k) => f3(cond(k, key).single_view_ba_mean))])
    .concat([["KK: all, 10-view ensemble", ...[250, 500, 1000].map((k) => f3(cond(k, "KK|combined").ensemble_ba))]]);
  const s2con = [["retrain_effect_struct6", "Retraining (KK − FK), structure"], ["transfer_loss_struct6", "Transfer (FK − FF), structure"],
    ["structure_beyond_NK", "Structure beyond N~K~ (KK)"], ["content_beyond_NK_struct", "Content beyond N~K~ + structure"],
    ["ensemble_vs_single_combined", "Ensemble − single view (KK, all)"]]
    .map(([n, label]) => [label, ...[250, 500, 1000].map((k) => `${sg(con(k, n).ba.delta)} ${ci(con(k, n).ba.ci)}`)]);
  const rt = con(250, "retrain_effect_struct6");
  body.push(
    H2("Restricted Observation (RQ2)"),
    P(`Table VI and Fig. 3 report single-view BA. A model trained on single K-edge views (KK) remains highly predictive at every budget: with N~K~ alone it reaches ${f3(cond(250, "KK|NK").single_view_ba_mean)}, ${f3(cond(500, "KK|NK").single_view_ba_mean)} and ${f3(cond(1000, "KK|NK").single_view_ba_mean)} at K = 250, 500 and 1000, and adding structure and content raises this to ${f3(cond(250, "KK|combined").single_view_ba_mean)}, ${f3(cond(500, "KK|combined").single_view_ba_mean)} and ${f3(cond(1000, "KK|combined").single_view_ba_mean)}. Structure did not detectably improve on N~K~ at any budget (Table VII), and content added at most a few points, with intervals that mostly include zero.`),
    P(`Training regime matters far more than feature choice. With the same six structural features, events and folds, training on single views instead of full graphs raised single-view BA at K = 250 (budget-specific cohort, n = ${S2.results.budget_specific_K250.n_events}) by ${f3(rt.ba.delta)} ${ciu(rt.ba.ci)}, and by ${f3(con(500, "retrain_effect_struct6").ba.delta)} and ${f3(con(1000, "retrain_effect_struct6").ba.delta)} at K = 500 and 1000. Applying the full-graph model to views lost ${f3(-con(250, "transfer_loss_struct6").ba.delta)} BA at K = 250 relative to full graphs, a loss that shrinks to intervals including zero at larger budgets. Averaging the ten views changed BA by at most ${f3(Math.max(...[250, 500, 1000].map((k) => Math.abs(con(k, "ensemble_vs_single_combined").ba.delta))))}, so ensembling contributes little. The common cohort gives the same directions for all primary contrasts (e.g. a K = 250 retraining effect of ${f3(conC(250, "retrain_effect_struct6").ba.delta)}); an exploratory diagnostic of density in frozen models changed sign between cohorts and is not interpreted.`),
    ...table("TABLE VI.\tSingle-View Balanced Accuracy (Budget-Specific Cohorts)", ["Condition (feature set)", "K = 250", "K = 500", "K = 1000"], s2rows, [2240, 933, 933, 934],
      "Mean over 10 sampling seeds; last row averages probabilities over the 10 views."),
    ...figure("fig3_study2_single_view.png", "Fig. 3.\tSingle-view balanced accuracy by edge budget (budget-specific cohorts). Points are means over 10 sampling seeds and bars span the minimum and maximum over seeds; they are not confidence intervals. All conditions at a given K share events, folds and feature definitions."),
    ...table("TABLE VII.\tStudy 2 Paired Contrasts, Single-View Δ BA [95% CI]", ["Contrast", "K = 250", "K = 500", "K = 1000"], s2con, [1640, 1133, 1133, 1134]),
    H2("What the Sampled Endpoint Count Reflects"),
    P(`The expectation in (3) matches the observed mean N~K~ within ${pct(mech.K250.max_abs_rel_error_expected_vs_observed)}% at K = 250 and agrees with Monte Carlo simulation. Its label information is high: at K = 250 its AUC is ${f3(mech.K250.auc_expectedNK_label)}, compared with ${f3(mech.K250.auc_log_N_full_label)} for full-graph log node count. The expected number of distinct endpoints in a fixed-budget edge sample is strongly associated with full-graph node count and mean degree. Together, these variables explain ${pct(r2["log N + log mean degree"])}% of its variation at K = 250 in the analysed archive (node count alone ${pct(r2["log N only"])}%). Adding in/out-degree Gini provides no measurable additional explanatory power (${pct(r2["size + degree concentration"])}% with it). Because (3) depends on the full incidence-degree distribution, these aggregates describe, but do not completely determine, the quantity (Fig. 4).`),
    ...figure("fig4_endpoint_mechanism.png", `Fig. 4.\tExpected distinct endpoints in a 250-edge sample, from (3), against full-graph node count for the ${EL["250"].total_eligible} eligible events. Inset: variance of log E[N~K~] explained by log node count, by log node count and log mean degree, and additionally by in/out-degree Gini.`),
  );

  // ---- VI. Discussion -------------------------------------------------------------------
  body.push(H1("Discussion"),
    P(`On this archive, the released labels are predictable to a large degree from how large an event graph is. Counts reach most of the attainable BA, and richer features did not produce a detectable improvement in classification decisions. They did improve probability quality and ranking, which matters for uses that rely on probability scores or on thresholds chosen after deployment, but the source of this gain is not isolated by our contrasts: neither arrangement beyond degree nor content alone reproduces it. For anyone using LEN-Small as a benchmark, reported accuracy should be read against a count-only baseline, and probabilistic metrics should be reported separately.`),
    P(`The null-model result is narrow by design. The real graphs are far from degree-preserving random graphs, so their arrangement is not random; it is simply not label-informative beyond the degree sequences for the features and model we tested. Other arrangement statistics, other null models or larger cohorts could change this.`),
    P(`Under restricted observation, most label information in a single view is carried by the number of distinct endpoints it touches, a quantity strongly associated with the full graph's node count and mean degree. A model needs to be trained on observations like those it will see: frozen transfer from full graphs loses accuracy at small budgets, while averaging many views adds almost nothing.`),
    P(`These results do not establish that any model detects coordinated behavior, accounts or intent, that size is the only relevant property, or any causal effect. They concern one released archive, which differs from the official release.`),
  );

  // ---- VII. Limitations ------------------------------------------------------------------
  body.push(H1("Limitations"),
    P(`*Sample size and uncertainty.* With ${nE} events, null BA results are inconclusive rather than evidence of equivalence. Paired intervals resample fixed out-of-fold predictions and exclude refitting and split variability; re-drawn splits show C1 differences that vary in magnitude. Hyperparameter selection in small inner folds was sensitive to row order.`),
    P(`*Provenance.* The archive has ${nE} events rather than the official 100, for an unknown reason. Labels come from file names; account identifiers and campaign subtypes are not available, so dependence between events through shared accounts and subtype heterogeneity cannot be assessed. Timestamp semantics are unverified, so temporal features are excluded.`),
    P(`*Null model and matching.* Rewiring mixes incompletely in hub-dominated graphs and uses five realizations. Matching keeps 15–17 pairs, changes the evaluated population and does not balance all size measures.`),
    P(`*Scope of models and observations.* Only LR and HGBT on hand-crafted features were evaluated; graph neural networks and the methods of ${c("len", "decode")} were not re-run, and published LEN-Small accuracies use a different protocol and metric. Uniform edge sampling is one observation mechanism among many ${c("leskovec")}.`),
  );

  // ---- VIII. Reproducibility and corrections --------------------------------------------
  body.push(H1("Reproducibility and Correction History"),
    P(`All parameters are read from one configuration file, and every number in this paper is generated from a single results file produced by the pipeline; an independent verification script recomputes all reported comparisons from the saved predictions (${R.verification.n_pass}/${R.verification.n_checks} checks passed), including tests that permuting held-out labels does not change tuned hyperparameters. A complete rerun from the raw archive into a separate directory reproduced every reported value on the same machine; reproduction on other machines has not been tested. Seeds are fixed for folds, matching, edge sampling, rewiring and bootstrap. Source code, configuration, tests and derived outputs accompany the paper; the raw archive is not redistributed and is available from the LEN project ${c("repo")}.`),
    P(`Two defects in an earlier version of this analysis were found and corrected. First, every graph contains self-loops, which the core-number routine rejects; the earlier code silently set both coreness features to zero, so its structural results used five effective features. Second, an earlier frozen-model evaluation assigned sampled events to fold models using a budget-specific split, so some events were scored by a model trained on their own full graph. Both are fixed and covered by regression tests, the earlier outputs are archived unchanged, and all results reported here come from the corrected run. For example, logistic regression on all twelve features in the base experiment grid reported BA ${f3(R.superseded_run_final.A_combined_logreg_ba)} in the earlier run and reaches ${f3(R.run_v2_metrics.A_combined_logreg.balanced_accuracy)} after correction; ${f3(R.superseded_run_final.A_combined_logreg_ba)} is a superseded value, not a result of this paper.`),
  );

  // ---- IX. Conclusion -------------------------------------------------------------------
  body.push(H1("Conclusion"),
    P(`LEN-Small's labels, as distributed in the analysed archive, are largely predictable from graph counts. Additional degree, arrangement and content features improve probability quality and ranking but did not reliably improve classification decisions, and the tested arrangement features did not outperform a degree-preserving null. Single fixed-budget views retain strong label information, carried largely by the number of distinct endpoints sampled, and observation-matched training matters far more than ensembling. Evaluations on this benchmark should report count-only baselines, separate decision and probability metrics, and match training to the observation regime. Natural next steps are obtaining the official release and account-level data to test provenance and dependence, and evaluating learned graph models under the same paired protocol.`),
  );

  // ---- References ---------------------------------------------------------------------------
  const unused = Object.keys(REFS).filter((k) => !order.includes(k));
  if (unused.length) throw new Error(`uncited references: ${unused.join(", ")}`);
  body.push(new Paragraph({ style: "Heading5", children: [new TextRun("References")] }),
    ...order.map((k) => new Paragraph({ style: "references", numbering: { reference: "refs", level: 0 }, children: runs(REFS[k]) })));
  return body;
};
