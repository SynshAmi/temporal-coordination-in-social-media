# Claude Code Execution Prompt — LEN-Small Research Advancement

You are the implementation, repository-audit, reproducibility and cross-verification agent for our LEN-Small research project.

## Read first
1. Read `LEN_SMALL_CONSOLIDATED_RESEARCH_ROADMAP.md` completely.
2. Read the latest authoritative research paper in the project (identify it; do not assume a filename).
3. Inspect the repository, source code, experiment scripts, outputs, tests, configs, website and paper-generation workflow.
4. The roadmap consolidates two independent research reviews (ChatGPT Astra and Gemini Argon). Treat it as a plan to verify—not unquestionable truth.

Our goal is to strengthen the scientific paper with a small number of defensible experiments, revise the paper in clean IEEE style, update the website consistently, and leave the project folder reproducible and ready for us to initialize Git. We will exclude the dataset from Git. **Do not run `git init`, add, commit or push.**

## Operating principles
- Be rigorous, skeptical and efficient.
- Do not invent results, sources, data semantics or novelty.
- Do not blindly implement every suggestion in the roadmap.
- Verify claims against actual code, data, outputs and primary literature where relevant.
- Do not start random investigations or repeatedly reopen settled decisions.
- Do not redesign the website for aesthetics; update only where research content/results changed.
- Preserve the existing project, raw dataset and original artifacts.
- Never overwrite the only copy of the current paper, source data or experiment outputs.
- Ask us only when a genuine ambiguity changes scientific validity, data interpretation, scope or implementation.
- If blocked, explain the exact blocker, why it matters, options and your recommended choice. Do not ask about minor choices you can safely resolve and document.
- No unbounded loops of issue hunting. Resolve a check, record it and move on.

## Phase 1 — Evidence and repository audit (do not modify results yet)

Inspect the project and produce a concise audit containing:

1. Current folder tree and identification of authoritative paper, website, scripts, data, outputs and tests.
2. Claim-to-evidence matrix for every headline paper result:
   - claim/number;
   - exact script/function/config;
   - exact output artifact;
   - independently reproduced?;
   - discrepancy/caveat;
   - action.
3. Verify, where source data exists:
   - archive file count, duplicate identity/hash, canonical event count and labels;
   - official 100-event vs local 103-event discrepancy;
   - node/edge count summaries and medians;
   - feature definitions, especially density, degree, core and component features;
   - edge-budget eligibility at K=250/500/1000 and common N≈73 cohort;
   - D1/D2 feature, cohort, training and aggregation differences;
   - ten-view probability aggregation vs single-view estimates;
   - timestamp count (reported 288,540), units, semantics, missingness, ties and whether timestamps describe interaction actions or referenced posts;
   - account overlap (reported 92.7%), exact calculation, identity comparability and overlap distribution;
   - subtype map and reported 16 Reform events;
   - existing leakage correction, split alignment and tests.
4. Verify claims about original LEN, DECODE, published GNN results and LEN-Small selection from primary sources.
5. Classify roadmap suggestions as already implemented, feasible, infeasible, redundant or scientifically unsafe.

Do not assume a dataset exists because a path is mentioned. If missing, do not download multiple gigabytes without asking; state exactly what is missing and what we need to provide.

At the end of Phase 1, report only:
- critical blockers;
- corrections required before new experiments;
- short execution plan in priority order;
- decisions that genuinely require our input.

Do not modify paper, website or experiment results in this phase. You may create a new audit note under `reports/audit/` or `docs/`, but do not overwrite existing files.

## Phase 2 — Freeze protocol and implement primary studies

Proceed after the audit. If no material blocker exists, use the roadmap priorities and document reasonable choices. Ask us only where a decision changes the scientific question or invalidates an assumption.

### Study 1: Incremental information beyond scale and degree
Implement nested levels:
- M0 counts/scale: log(1+|V|), log(1+|E|), justified nonlinear count controls if needed.
- M1 degree sequence/concentration.
- M2 higher-order arrangement beyond degree.
- M3 retained content summaries.
- M4 combined.

Required:
1. Density D=E/[V(V−1)] is determined by V and E. Do not claim it is independent topology. Keep it only as an explicitly scale-encoding diagnostic if useful.
2. Fit residualization and learned transforms inside training folds only.
3. Use overlap weighting only if estimand, support, weight stability and effective sample size are defensible. It is not causal deconfounding. If overlap is poor, report that; do not force the method.
4. Implement directed degree-preserving rewiring only after validating graph semantics and invariants. Check in/out-degree sequence, |V|, |E|, density, self-loop/multiedge constraints and mixing. Recompute features on null graphs. Describe exactly what the null changes/preserves. Null realizations are nested within events, not independent samples.
5. Same event-level outer folds and same events for nested models; save event-level out-of-fold predictions.
6. Paired event/group-level uncertainty for BA/log-loss differences; AUC secondary. Distinguish fixed-OOF uncertainty from refitting/model-selection uncertainty. Do not use p>0.05 as equivalence.
7. Keep current 16-pair matching as exploratory. Add node+edge matching, optimal matching or seed sensitivity only if it adds clear value. Do not run 1,000 seeds by default.
8. Treat matched HGBT constant prediction as a configuration problem; tune inside training folds or omit from tiny sensitivity.

### Study 2: Single-view retained-observation validity
At K=250, 500, 1000:
1. Make frozen and observation-trained conditions comparable: same eligible events, outer folds, feature sets and estimands.
2. Add log(1+|V_K|)-only baseline.
3. Include structural-7 and density-removed/endpoint-count-controlled structural set.
4. Include content-only/combined only where feature definitions are consistent and valid.
5. Recompute every feature from sampled edges. Never use original full-graph counts, cached k-core or full-graph features as restricted-view inputs.
6. Primary single-view estimate: metric/loss per sampled view, summarized within original event.
7. Report probability-averaged multi-view ensemble separately. Never label it single-view performance.
8. Report budget-specific cohorts and constant cohort eligible across all budgets (reported N≈73; verify).
9. Keep every view of an event in the same fold.
10. Account-oriented edge loss, if used, is a modeled missingness stress test, not observed platform behavior.

### Conditional extensions
- Chronological prefixes only if timestamp semantics support actual relevant chronology. Otherwise omit “early detection” and document why.
- Random-walk sampling is an established sampler; novelty is the label-information comparison, not the sampler.
- Full-LEN comparison only with compatible verified data/labels; not a blocker.
- Subtype/Reform analysis descriptive unless support permits stronger inference.
- Temporal burstiness only after timestamp validation.
- GIN/GraphSAGE is low priority and requires a specific reviewer-facing reason.

### Dependence audit
Verify 92.7% overlap. Compute overlap matrix, Jaccard and overlap relative to smaller event. Determine stable IDs and whether overlap is ubiquitous users or repeated participants. Compare standard event splits with grouped/event-family sensitivity only if groups are defensible without outcome-driven thresholds and enough independent groups remain. Report residual cross-fold overlap. Do not call overlap “leakage” by itself. If grouping is infeasible, document the limit.

## Phase 3 — Revise research paper

Only after experiments and outputs are validated:

1. Revise title, abstract, RQs, contributions, methods, results, discussion and limitations to match actual findings.
2. Use precise target wording: classification of retained engagement graphs associated with campaign-labeled versus comparison events. Do not claim direct detection of coordinating accounts, bots, intent or real-time campaigns.
3. Generate all tables, figures and metrics from machine-readable outputs; no hand-entered stale numbers.
4. Include verified provenance and 100-vs-103 discrepancy, duplicate audit, selection context, feature hierarchy/density relationship, paired comparisons/uncertainty, null-model diagnostics if run, single-view vs ensemble, cohort eligibility, overlap sensitivity and honest limitations.
5. Remove superseded claims and contradictory values throughout paper and site.
6. Distinguish confirmatory, exploratory and conditional analyses.
7. No “first,” “unique,” or “verified novel” without focused literature verification. State bounded differences from closest work.
8. Reassess venue fit after the contribution is clear.

### IEEE formatting
- Use the appropriate official IEEE conference template and current requirements for the target venue.
- Correct title/author/affiliation block, abstract, index terms, section hierarchy, equations, figure/table captions, references and citation numbering.
- Ensure figures/tables are legible and referenced in text.
- Avoid generic AI-looking layout, oversized headings, excessive whitespace and decorative charts.
- Apply venue page/reference limits only after target venue selection.
- Provide editable Word source and final PDF.
- If the current build depends on Microsoft Word, document that dependency rather than silently changing it.
- Visually inspect every PDF page and compare against editable source.
- Preserve existing verified author names, registration numbers and affiliation unless we explicitly change them.

## Phase 4 — Update website
Preserve the existing editorial research-journal identity and current routes (Overview, Results Explorer, Methods & Reproducibility). Update:
- research question and contribution;
- dataset/provenance notes;
- methods and experimental design;
- results, charts, tables and uncertainty;
- single-view vs ensemble distinction;
- limitations and conditional analyses;
- citations/references;
- verified latest paper download.

Every number and claim must match the final paper and generated outputs. Remove stale metrics, obsolete interpretations, broken links and outdated downloads. Keep production build working. No gratuitous redesign or feature additions.

## Phase 5 — Clean and make reproducible / Git-ready
Leave the folder ready for us to initialize Git ourselves.

1. Inspect before deleting. Preserve raw dataset, original paper, source outputs and anything whose role is unclear.
2. Create/update README: purpose, architecture, environment, dataset acquisition, checksum verification, exact reproduction commands, outputs and limitations.
3. Add/update `.gitignore`: raw data, large derived data, secrets, credentials, local env files, caches, temp files, build artifacts and machine-specific files. Dataset will be excluded by us.
4. Keep a small data manifest: source URL, version, expected/actual bytes, checksums, archive inventory, label provenance, license/attribution. Do not commit dataset.
5. Pin dependencies and include a lock or existing reproducible mechanism.
6. Replace absolute local paths with relative/configured paths.
7. Document one sequence to validate data, run experiments, generate tables/figures, build site and export PDF.
8. Trace outputs to run IDs/configs and dataset hashes.
9. Add tests for ingestion, sampling invariants, feature leakage, split isolation, prediction alignment and result-generation consistency.
10. Remove stale/dead scripts and duplicate generated files only after proving superseded; archive useful historical artifacts.
11. Remove secrets and local credentials; never print them.
12. Do not run `git init`, add, commit or push.

## Phase 6 — Final verification and handoff
- Run relevant tests.
- Run clean reproduction where feasible.
- Run website production build and verify paper download.
- Confirm Word/PDF consistency and inspect every PDF page.
- Confirm all site/paper metrics derive from final outputs.
- Confirm dataset is excluded from clean source package.
- Confirm no absolute local paths or secrets remain.
- Provide concise handoff: changes, experiments, key findings, tests, reproduction commands, limitations, files and manual steps.

## Questions and blockers
Ask only if:
- field semantics change the scientific claim;
- data/version discrepancy cannot be resolved;
- two defensible methods imply different estimands;
- data is missing or download is large;
- author/affiliation is ambiguous;
- venue template choice is needed;
- implementation would materially alter results/scope.

When asking, give exact blocker, why it matters, options/consequences and recommendation. Otherwise make a conservative documented choice and proceed. Do not repeatedly revisit resolved questions.

## Definition of done
- Current work audited against evidence.
- Selected primary experiments implemented and validated, or specifically documented as blocked.
- Paper revised to verified results and formatted cleanly in IEEE style.
- Website matches paper.
- Folder clean, documented, reproducible and Git-initialization-ready.
- Raw dataset excluded from source package.
- Final Word/PDF and concise handoff provided.

Start with Phase 1. After the audit, continue without waiting if there are no material blockers; if there are material blockers, ask concise targeted questions and wait.
