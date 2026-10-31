# LEN-Small Research Advancement Roadmap
## Consolidated Astra + Gemini Argon audit and execution priorities

**Purpose:** Strengthen the existing LEN-Small empirical paper through defensible experiments, revise the IEEE-style paper and website, and leave a reproducible, Git-initialization-ready project folder.

**Status:** This is a proposed plan. All results, data semantics, literature claims and novelty claims must be verified against the actual repository, raw data and primary sources before implementation or publication.

## 0. Executive decision

The independent reviews converge on a stronger central question:

> Which properties of retained engagement graphs predict LEN-Small's campaign-associated versus comparison-event labels, and which conclusions survive controls for graph scale, degree concentration, event dependence and observation mechanism?

Build the paper around two connected studies:

1. **Incremental information beyond scale and degree:** quantify what counts, degree concentration, higher-order arrangement and content summaries add in a controlled paired evaluation; use degree-preserving rewiring as a topology null only where technically valid.
2. **Single-view retained-observation validity:** determine what one K-edge observation preserves, separate single-view from multi-view ensemble performance, and isolate training-regime effects using identical features, events, folds and budgets.

A cross-event account-dependence audit is a required validity sensitivity. LEN-Small truncation/selection is an important conditional explanatory extension if the original selection mechanism and full-LEN data can be verified. Chronological/timestamp experiments are conditional—not a core dependency—until timestamp semantics are proven.

Do not pre-commit to a negative result. A robust incremental topology signal would contradict a strong size-dominance interpretation and could strengthen the paper. An inconclusive result must be reported as inconclusive, not as proof of no effect.

---

## 1. What Astra contributed

Astra recommended two focused questions:

- What predictive information remains beyond graph size and degree concentration?
- What information does a genuinely restricted observation preserve, and what does the sampling procedure itself make predictive?

Its key observations:

- The reported LR gain may be meaningful: node-count BA 0.8739 to combined BA 0.9229 is +0.0490; node+edge BA 0.8837 to combined is +0.0392. Combined AUC is reported as 0.9857 versus 0.9340 for node count. These are point-estimate differences, not paired evidence.
- Density D=E/[N(N−1)] is determined by node and edge counts. It can provide a nonlinear transformation to a model, but it is not independent topology evidence.
- Component fractions, degree Gini and core statistics can also depend on graph size.
- Matching changes the evaluated population, training-set size, class-conditional distributions, topics/subtypes and potentially account overlap. Matching only on node count does not balance edge count. A small mean SMD does not prove full distributional balance.
- The matched HGBT collapse is likely a configuration problem on a tiny cohort (leaf-size constraints), not evidence that nonlinear learning fails.
- Averaging predicted probabilities over ten sampled views is an ensemble estimand, not expected performance from one K-edge observation.
- 92.7% cross-event account overlap does not automatically prove leakage. Investigate what accounts overlap and define the intended generalization target.
- The task is narrower than direct coordination detection: classification of retained engagement graphs associated with documented astroturfing-promoted trends versus selected comparison trends.
- Embeddings are not automatically leakage. Exclusion needs a precise rationale (interpretability, dimensionality, provenance/fitting leakage), not a blanket claim.
- Timestamp use remains conditional on field semantics. Chronological sorting cannot recover deleted or discarded interactions.

Astra's ranking:
1. Incremental information beyond scale and degree concentration.
2. Genuine single-view observation-budget analysis.
3. Event/ecosystem dependence analysis.
4. LEN-Small size-selection/truncation audit, conditional on full-LEN access.

Astra's principal reviewer risks:
- The main conclusion does not follow from current experiments.
- The work may look like generic benchmark auditing applied to 103 events.
- Current evaluation does not establish the claimed population/observation regime.

## 2. What Gemini Argon contributed

Gemini independently identified:

- Full-cohort deconfounding and paired inference are needed; the N=32 / 16-pair matched analysis is too small and only balances node count.
- Density embeds inverse node scale. At fixed K, D_K=K/[N_K(N_K−1)] is a deterministic function of sampled endpoint count N_K.
- D1 (frozen 7-feature structural model) versus D2 (retrained 12-feature combined model) confounds feature set and training regime.
- Ten-view probability averaging must be separated from single-view performance.
- The archive is reported to contain 288,540 timestamped edges and 92.7% cross-event user overlap. Both are leads to verify from raw files, not facts to assume.
- LEN-Small was reportedly constructed by selecting the 100 smallest graphs from the larger LEN collection. Paper/repository counts differ (e.g. 314 vs 305 full graphs; 100 vs this archive's 103 canonical events). Verify the exact release/selection mechanism from primary sources.
- Gemini proposes comparing our scale baseline with published LEN-Small GNN results. This is useful context, but our balanced accuracy must not be directly compared with published accuracy as if they were the same metric/protocol.
- It highlights subtype heterogeneity, especially 16 Reform campaign graphs and their high degree/edge characteristics. Subtype results may explain heterogeneity, but small subgroups warrant descriptive treatment.
- It proposes chronological prefixes and random-walk samples in addition to uniform edge samples. This is conditional on timestamp semantics and does not reconstruct deleted or discarded interactions.
- Full-LEN replication is a conditional external validation, not a prerequisite.
- Lightweight GIN/GraphSAGE Sum-vs-Mean readout is optional and low priority.
- Gemini's proposed 1,000 matching seeds, 20 repeated 5-fold CV splits, 10,000 bootstrap resamples and multiple tests are candidate settings, not automatically correct. Repeated splits/views do not create independent events.

Gemini's five directions:
1. Full-cohort scale/degree/topology controls plus degree-preserving rewiring.
2. Uniform fixed-K vs chronological prefix vs random-walk observation regimes.
3. Cross-event user overlap and event-family dependence.
4. Subtype heterogeneity and conditional temporal burstiness.
5. Full-LEN versus LEN-Small truncation/selection audit.

---

## 3. Existing paper: reported facts and defensible interpretation

These are reported values from the current project context. Claude Code must trace every headline number to actual code/config/output before revising the paper.

### Dataset and provenance
- Archive: 104 graph JSON files; one byte-identical duplicate removed; 103 canonical events (52 campaign, 51 comparison).
- Official LEN-Small documentation: 100 events (51 campaign, 49 non-campaign). Discrepancy unresolved.
- Median node count: campaign ≈506; comparison ≈3,227.
- Reported cross-event account overlap: 92.7%.
- Reported timestamped edges: 288,540.
- Gemini reports 16 Reform campaign graphs; verify subtype mapping and counts.

### Classification results
- Node-count-only LR: BA 0.8739, macro-F1 0.8738, ROC-AUC 0.9340.
- Node+edge-count LR: BA 0.8837, macro-F1 0.8835, ROC-AUC 0.9306.
- Combined LR: BA 0.9229, macro-F1 0.9221, ROC-AUC 0.9857.
- Combined HGBT: BA 0.9319, macro-F1 0.9320, ROC-AUC 0.9578.

The combined model's point estimate is better. Whether the gain is reliable and attributable to topology/content remains untested by direct paired inference. Do not imply that overlapping marginal confidence intervals answer the paired question.

### Size matching
- 16 pairs / 32 events.
- Matching on log1p(node_count), nearest neighbour without replacement, caliper ≈0.25 SD.
- |SMD| reported from 2.24 to 0.10.
- Matched BA: scale .5938; content .7500; structure .6875; combined LR .7500; HGBT .5000 (constant-class behavior).

Interpret as an exploratory selected-population sensitivity. It is not a causal estimate of size's effect. It ignores edge-count balance and may depend on visitation order/seed. HGBT collapse is a configuration failure until proven otherwise.

### Edge-budget results
- K=250, 500, 1,000.
- Corrected frozen structural D1 BA: .598, .725, .746.
- Retrained combined D2 BA: .9412 (N=102), .9379 (N=98), .9063 (N=73).
- K=2,000 not pursued because only four campaign graphs had at least 2,000 edges.
- D1 is a frozen 7-feature structural model; D2 is a retrained 12-feature combined model. Their gap cannot isolate retraining.
- The current protocol averages probabilities across ten sampled views. This is an ensemble, not a one-view estimate.
- Earlier D1 leakage was corrected; verify current code/tests and fold alignment.
- K-specific eligible cohorts differ; Gemini reports N≈102, 98, 73 and a common cohort N≈73. Verify exact class composition.

### Other limitations
- Temporal features were disabled because timestamp semantics were uncertain.
- High-dimensional embeddings were excluded; justify this precisely. Pretrained embeddings are not automatically leakage.
- Confidence intervals may not capture refitting, matched-pair or shared-account dependence.
- Full raw 5.4 GB pipeline was not rerun after finalization (per prior project status); do not claim full end-to-end reproducibility until tested.

### Claims not established
Do not claim:
- LEN-Small is invalid, universally biased or useless.
- Combined-model performance is primarily caused by size.
- Higher-order topology is irrelevant.
- Matching proves a causal size effect.
- K observed edges suffice when probabilities are averaged over ten views.
- D1/D2 gap measures retraining alone.
- 92.7% overlap proves leakage or an effective sample size.
- Direct detection of coordination, bots, malicious intent, individual operators or real-time campaigns.
- Generalization to all campaigns/platforms/unseen ecosystems.
- First-ever, unique, novel detector or SOTA.

Use careful wording: **campaign-associated event labels**, **retained engagement graph**, and **comparison/non-campaign event**. Event-level provenance labels do not establish that every user or interaction is coordinated.

---

## 4. Literature positioning and novelty discipline

Verify exact titles, publication status, methods and overlaps before citing or making novelty claims.

| Work | What it establishes | Consequence for our claims |
|---|---|---|
| Gopalakrishnan et al., LEN, ICWSM 2025, https://arxiv.org/abs/2503.00599 | LEN/LEN-Small, graph/content baselines, size/selection context | Size-selection concern is not our discovery; test its consequences. |
| Gopalakrishnan et al., DECODE, ECML-PKDD 2025, https://arxiv.org/abs/2506.13912 | Density-aware walks, degree/core/truss signals | Density/core/walk features are established; ask whether they add beyond counts/degree. |
| Li et al., IJCAI 2024, https://www.ijcai.org/proceedings/2024/237 | Simple graph-property baselines and benchmark effectiveness | Generic “simple baseline challenges graph benchmark” novelty already exists. |
| Coupette et al., ICML 2025 RINGS, https://proceedings.mlr.press/v267/coupette25a.html | Graph dataset evaluation via perturbations/modes | Generic perturbation/null analysis is not novel by itself. |
| Errica et al., ICLR 2020, https://arxiv.org/abs/1912.09893 | Rigorous GNN comparisons and structure-agnostic baselines | Baseline discipline is established. |
| Yehudai et al., ICML 2021, https://proceedings.mlr.press/v139/yehudai21a.html | Graph-size shifts and generalization | Size/structure coupling is established broadly. |
| Leskovec & Faloutsos, KDD 2006, https://cs.stanford.edu/people/jure/pubs/sampling-kdd06.pdf | Graph sampling methods and property distortion | Random-walk sampling itself is not novel. |
| Pacheco et al., ICWSM 2021, https://arxiv.org/abs/2001.05658 | Coordination from behavioral traces | Their account-similarity networks differ from LEN event engagement graphs. |
| Jacobs & Wallach, FAccT 2021, https://arxiv.org/abs/1912.05511 | Measurement validity/construct interpretation | Prediction alone does not validate the construct. |
| Varoquaux, 2018, https://arxiv.org/abs/1706.07581 | Small-sample CV uncertainty | Important to our 103-event setting; not a new method. |
| Brekin et al., Oct 2026 preprint, https://arxiv.org/abs/2610.32611 | Local-evidence baselines, nuisance controls, topology augmentation | Close conceptual overlap with incremental structural value; inspect carefully. |
| Iannucci, Matakos & Kivelä, Oct 2026 preprint, https://arxiv.org/abs/2610.37970 | Coordination detectability vs density; null models and multi-modal operation analysis | Strong adjacent overlap; LEN event-level task/observation constraints may differ. |
| Not All Duplicates Are Coordination, 2026 preprint, https://arxiv.org/abs/2609.13671 | Semantic specificity of repeated content | Do not treat text duplication as an unqualified coordination signal. |
| Hossain, Soundarajan & Sarıyüce, GTA3/ICDM 2025, https://sariyuce.com/papers/icdmw25.pdf | Truss robustness under edge removal | Generic edge perturbation is not novel. |
| Iannucci et al., ICWSM 2026, https://ojs.aaai.org/index.php/ICWSM/article/view/42682 | Temporal/multiplex/shared-action analysis | Complete action histories may be required; LEN retained representation may not support them. |
| Li, Morgan & Zaslavsky, JASA 2018, https://arxiv.org/abs/1404.1785 | Overlap weighting | Statistical tool, not novelty. |

Broadly established: simple baselines can rival GNNs; graph properties correlate with labels; sampling changes graph statistics; size and local structure interact; accuracy does not prove construct validity; density/repetition alone do not establish coordination.

Potentially distinctive if supported by results:
- precise predictive-information audit of the distributed LEN-Small archive;
- separating scale, degree concentration, higher-order arrangement and text repetition;
- explaining fixed-edge performance through endpoint coverage / sampled node count / degree concentration;
- distinguishing single-view from ensemble robustness;
- testing event-family/account-overlap sensitivity;
- explaining LEN-Small size-selection consequences.

No model's “verified novel” label is proof. Run a focused literature check against the exact implemented protocol. Do not claim “first” or “unique.”

---

## 5. Primary Study 1 — Incremental information beyond scale and degree

**Priority: highest.**

### Research question
When node and edge counts are controlled, do degree-concentration features, higher-order arrangement features and content summaries add stable predictive information for the released event labels?

### Feature hierarchy
- **M0 counts/scale:** log(1+|V|), log(1+|E|), with nonlinear terms/splines only if justified.
- **M1 degree concentration:** average degree and in/out-degree summaries, in/out-degree Gini or other predeclared concentration measures.
- **M2 arrangement beyond degree:** reciprocity, component structure, coreness/core summaries and existing topology features after careful controls.
- **M3 content:** duplicate fraction, content concentration, token variability and existing content summaries. Interpret duplication cautiously.
- **M4 combined:** nested combinations to measure incremental contribution.

### Required corrections and controls
1. Density D=E/[V(V−1)] is determined by V and E. Do not call it independent topology. Average degree E/V is also determined by V/E; it is descriptive, not an independent variable.
2. Fit residualization and learned transforms inside training folds only. Consider nonlinear scale controls; a linear residualization alone may leave nonlinear dependence.
3. Overlap weighting based on e(x)=P(campaign label | scale covariates) is not automatically causal deconfounding because campaign status is the prediction outcome. Define the estimand as a weighted discrimination comparison over scale-covariate overlap. Report overlap, weight distribution, effective sample size, class support and sensitivity. If positivity/support is poor, do not force it.
4. Use directed degree-preserving rewiring only after validating directed graph semantics and algorithmic invariants. Directed double-edge swaps can preserve node set, edge count, in/out-degree sequence and therefore density/degree summaries, while altering selected higher-order arrangements. Verify self-loop/multiedge constraints, connectivity implications and mixing. Recompute all features on rewired graphs. Do not assume all motifs are destroyed or that rewiring isolates “coordination.”
5. Multiple rewired realizations are nested within events, not independent samples. Pilot mixing/convergence; do not blindly assume ten is enough.
6. Same event-level outer folds and same events for every nested model; save event-level OOF predictions.
7. Primary estimands: paired differences in BA and log loss; AUC difference secondary. Use event/group-level paired uncertainty.
8. McNemar may compare paired hard predictions on identical held-out events; thresholds must be selected using training data. DeLong is for correlated ROC curves; verify assumptions and dependence. Do not use tests as decoration.
9. Separate fixed-OOF uncertainty from refitting/model-selection uncertainty. Do not treat folds, repeated CV splits or null realizations as independent events. p>0.05 is not equivalence.
10. Multiplicity-control confirmatory secondary tests; mark exploratory work.

### Matching sensitivity
Keep the existing 16-pair result as exploratory. If useful, add:
- node+edge matching as a distinct sensitivity;
- optimal bipartite matching and seed/order sensitivity;
- retention, class support, full distributions and effective sample size;
- keep pairs in the same fold and resample pairs;
- do not call 1,000 seeds 1,000 independent datasets.
Tune HGBT only inside training folds; its current constant prediction is a configuration issue unless proven otherwise.

---

## 6. Primary Study 2 — Single-view retained-observation validity

**Priority: second main contribution.**

### Research question
At a fixed K-edge budget, what predictive information is present in one sampled view, what is introduced by the sampling mechanism, and how much does training on the same observation regime help?

### Fix current D1/D2 confound
D1 is frozen full-graph with 7 structural features; D2 is retrained on sampled graphs with 12 combined features. They differ in features and potentially cohorts/training conditions. Their difference cannot isolate retraining.

At K in {250, 500, 1,000}, use identical eligible events, outer folds and feature definitions:
- Full→Full reference.
- Full-trained→one K-view frozen transfer.
- K-view-trained→one K-view evaluation.
- Where feasible, frozen/retrained conditions for identical feature sets.

Feature families:
- log(1+|V_K|) only;
- structural-7 (density explicitly recognized as scale-encoding);
- density-removed / endpoint-count-controlled structural set;
- content-only;
- combined only when definitions are identical and valid.

### Mechanism controls
- Uniform random edge sampling is the primary baseline.
- Add sampled endpoint-count N_K and degree-concentration baselines.
- At fixed K, density D_K=K/[N_K(N_K−1)] is deterministic in N_K.
- For a graph with E directed edges and d_v^inc distinct edges incident to vertex v, expected endpoint count under uniform K-edge sampling without replacement is:
  E[N_K] = Σ_v [1 − C(E−d_v^inc, K)/C(E,K)].
  Verify graph conventions and incidence counting before using it.
- Optional degree-preserving null views use the same observation pipeline.
- Optional account-oriented edge loss removes outgoing edges of sampled source accounts at matched expected retention. Label this a modeled missingness stress test, not a real platform process.

### Single-view versus ensemble
- **Single-view:** compute metric/loss per sampled view, then summarize repetitions within original event.
- **Ensemble:** average probabilities across views, then classify; report separately.
- Never call ensemble performance “performance from K observed edges.”
- Repeated views do not increase independent N.

### Cohort controls
Report both:
- budget-specific eligible cohorts (reported N≈102, 98, 73; verify class counts);
- constant cohort eligible at every budget (reported N≈73; verify).

The common cohort isolates budget differences on the same events; budget-specific cohorts answer coverage questions. Neither replaces the other.

All views of an original event stay in one fold. Recompute every sampled feature. Never use original full-graph counts, cached k-core or full-graph features in a restricted-view predictor.

### Conditional chronological and random-walk extension
Gemini proposes Uniform vs Earliest-K chronological prefix vs Random-Walk subgraph. Only implement chronological prefix if timestamps are verified to represent the relevant interaction chronology, with units, timezone, missingness, ties and meaning checked. If timestamps are target-post timestamps rather than engagement-action timestamps, do not call it early detection. Even a valid chronological ordering of retained records cannot reconstruct deleted or discarded interactions. Random-walk sampling is established; novelty is the label-information comparison, not the sampler.

---

## 7. Required dependence audit — across both studies

Verify the reported 92.7% overlap from canonical graph files. Define calculation precisely.

Produce:
- 103×103 account-overlap matrix;
- Jaccard similarity and overlap relative to the smaller event;
- overlap by same/different class and verified subtype;
- whether overlap is dominated by ubiquitous public accounts or repeated participants;
- whether account IDs are stable/comparable across graphs.

Compare standard event-stratified CV with a defensible event-family/grouped sensitivity only if groups can be built without outcome-driven threshold selection and enough independent groups remain. Report residual cross-fold overlap. Shared accounts do not automatically prove leakage: unseen events with familiar users and unseen campaign ecosystems are different prediction targets. If grouping creates giant groups or too few groups, state that broader generalization cannot be estimated.

---

## 8. Conditional extensions and lower-priority ideas

### LEN-Small construction/truncation audit
Gemini reports LEN-Small selects the 100 smallest graphs from the larger collection. Verify the selection rule/version in the original paper, repository, metadata and history. The 314-vs-305 full-release and 100-vs-103 small-archive discrepancies must remain explicit until resolved. If compatible full-LEN data/labels can be obtained without derailing the project:
- compare class-conditional size distributions in full LEN and LEN-Small;
- rerun count-only and compact baselines;
- test whether selection changes size-label association and helps explain different published model scores.
This is potentially valuable but conditional—not a main-project blocker.

### Subtype / Reform
Verify the reported 16 Reform campaign events and subtype labels. Report counts, sizes, degree stats, errors and influence. Treat as descriptive unless support is sufficient.

### Temporal burstiness
Conditional on verified timestamp semantics. Do not infer scheduling/synchronization from ambiguous timestamps.

### Content repetition
Check whether repeated cleaned text means same target post, copied independent posts, URL/normalization collisions, or another mechanism. If source-post IDs are unavailable, say these cases cannot be separated. Do not treat duplicate fraction as an unqualified coordination measure.

### Optional GNN
A small GIN/GraphSAGE Sum-vs-Mean readout experiment is low priority. Published metrics are contextual only unless protocol/metrics align. Size-shift/OOD testing is established. Do not add a GNN merely for sophistication; require a reviewer-facing reason after primary studies.

---

## 9. Revised provisional paper framing

**Working title:** *What Does LEN-Small Measure? Predictive Information Beyond Scale in Retained Engagement Graphs.*

Alternative retaining continuity: *Beyond Graph Scale: Auditing Predictive Information and Retained-Observation Robustness in LEN-Small.*

**RQ1 — Incremental information:** What predictive information do degree concentration, higher-order graph arrangement and content summaries add beyond node and edge counts for classifying LEN-Small event labels?

**RQ2 — Observation validity:** Under fixed retained-edge budgets, how much predictive information is available from a single sampled view, what does the sampling mechanism make predictive, and how does observation-matched training change performance?

**RQ3 — Dependence sensitivity:** How sensitive are event-level results to repeated account participation or event-family dependence in the released archive?

Truncation/selection is a conditional explanatory extension until provenance/full data are verified.

**Provisional contribution statement (rewrite after results):**

This work provides a reproducible measurement audit of LEN-Small that (i) quantifies the predictive contribution of graph scale, degree concentration, higher-order arrangement and retained content using paired event-level evaluation; (ii) examines how fixed-budget graph observation changes information available to single-view and ensemble classifiers; and (iii) evaluates sensitivity to cross-event account overlap and archive provenance. It characterizes what the released event labels can be predicted from; it does not claim direct detection of coordinating accounts or causal proof of benchmark invalidity.

---

## 10. Reviewer objections to answer

1. **“Your conclusion does not follow.”** Paired incremental comparisons, nonlinear count controls, degree/arrangement nulls and uncertainty around differences.
2. **“This is generic benchmark auditing on 103 graphs.”** A specific LEN measurement mechanism and explanatory result, not just a baseline or standard rewiring.
3. **“Your evaluation does not represent the claimed population/observation regime.”** Explicit prediction target, dependence sensitivity, common-cohort comparisons, identical features/training conditions and single-view estimands.
4. **“You compare incomparable published results.”** Separate contextual published metrics from apples-to-apples experiments.
5. **“Timestamp/content semantics are unsupported.”** Provide field-level provenance or exclude the claim.
6. **“Uncertainty treats repeated views/folds as independent.”** Event/group-level inference.

---

## 11. Execution gates

### Gate 0 — Repository/data reality check
Inspect current paper, repository, scripts, outputs, tests, website and data. Trace every headline number to code/config/output. Verify archive count, duplicate, labels/subtypes, medians, timestamp count/meaning, overlap, feature definitions, edge-budget eligibility, D1/D2 differences and leakage correction. Produce a claim-to-evidence matrix. Do not edit paper/site/results yet.

### Gate 1 — Freeze minimal valid protocol
Freeze target, event unit, splits, feature hierarchy, estimands, null model, observation aggregation and uncertainty. Pilot residualization/overlap, one rewiring run, single-view/ensemble bookkeeping, timestamp semantics and runtime. Ask us only about material scientific blockers.

### Gate 2 — Run primary studies
Run Study 1 and Study 2, with dependence audit integrated. Only then consider truncation/subtype/temporal/GNN extensions.

### Gate 3 — Revise paper and site
Update research questions, contributions, methods, results, discussion and limitations from verified outputs. Rebuild tables/figures from machine-readable results. Update Overview, Results Explorer, Methods & Reproducibility, references and verified paper download. Preserve existing editorial visual identity; no gratuitous redesign. Ensure every website number matches the paper.

### Gate 4 — Reproducibility and Git readiness
Clean the folder after inspecting dependencies. Keep raw dataset out of Git; document official acquisition route, license/attribution, version, hashes, bytes and archive inventory. Add README, configs, scripts, tests, pinned dependencies/lock, `.gitignore`, relative paths and one reproduction sequence. Remove stale caches/temp/duplicate artifacts only when proven superseded. Preserve original paper/data/results. Do not run `git init`, add, commit or push; the team will do that.

### Gate 5 — Final paper and handoff
Return editable Word and final PDF in clean IEEE style using the appropriate official template/requirements. Correct author/affiliation block using existing verified details. Inspect every PDF page and source consistency. Run tests, clean reproduction where feasible, production website build and PDF download check. Provide concise changed-files, experiment, test, reproduction and unresolved-limitations handoff.

---

## 12. Statistical and scientific guardrails

- These are observational retrospective event-level analyses. Avoid causal language.
- Original event/group is the inference unit unless another unit is justified.
- Repeated seeds, views, rewired realizations and CV folds are not independent events.
- p>0.05 does not establish equivalence.
- Density is determined by V and E; fixed-K density is determined by sampled endpoint count.
- No cached full-graph features in restricted/null views.
- Single-view and ensemble results must be separate.
- Report budget-specific and common-cohort results.
- Define weighting/matching estimands and overlap/ESS; do not claim causal deconfounding.
- No metric mismatch when contextualizing published GNN scores.
- No novelty claim solely because a model says “verified novel.”
- No complex architecture for appearance.
- If the result contradicts the hypothesis, report it.
- Avoid unbounded issue hunting. Resolve each audit item once, record it, and proceed.

## 13. Candidate venues (not predictions)

Gemini named AAAI ICWSM, ACM WWW relevant short/workshop tracks, ECML-PKDD, ACM CIKM short/resource tracks, and NeurIPS/ICML/ICLR datasets-and-benchmarks or data-centric graph-learning workshops. Reassess after results, related-work verification, current calls, template and page limits. A focused workshop/short paper may be more realistic if the contribution remains a single-benchmark audit; a full paper needs a substantial explanatory result, meaningful replication, or reusable resource.

## 14. Final operating rule

The goal is not to prove LEN-Small invalid or maximize experiment count. The goal is a precise, falsifiable account of what the released labels are predictable from, what information survives restricted observation, and what the evaluation does or does not support.

Astra and Gemini provided independent research opinions. Claude Code is the implementation and cross-verification agent. Verify their suggestions against the actual repository, raw data and literature. Treat their novelty labels and projected outcomes as hypotheses, not facts.
