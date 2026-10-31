# SUPERSEDED RUN: historical record only

**Do not cite or reuse these numbers.** This is the original run (config `configs/final.yaml`), produced before two defects were corrected:

1. Every graph contains self-loops, which the core-number routine rejects; this run silently set both coreness features to zero.
2. Frozen full-graph models were assigned to sampled events by a budget-specific fold split, so some events were scored by a model trained on their own full graph.

It is kept unchanged for the paper's correction history. For example, its combined-model balanced accuracy of 0.923 is 0.894 after correction. The only value read from here is that historical 0.923 (`superseded_run_final` in `outputs/run_v2/paper_results.json`).

Current, verified results: `outputs/run_v2/`, summarised in `outputs/run_v2/paper_results.json`.
