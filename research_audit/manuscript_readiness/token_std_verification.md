# token_std verification

`token_std` is the stored feature `msg_length_dispersion`. It is called *lensd* in earlier audit files.

- **Scope.** This is verification only. No model was fitted, no resampling was drawn and no pipeline code was changed.
- **Status.** The predictive role of `token_std` is **Exploratory-post-hoc** throughout. It was singled out after the Study 1 results had been examined on these same 103 events. Measurement agreement (this file) and predictive utility (other files) are separate questions.

## 1. Had token_std been independently recomputed from raw text before this task?

| Object | Earlier check | From raw archive? | Result |
|---|---|---|---|
| Full graphs (103 events) | `research_audit/scripts/s01_content_verification.py` → `research_audit/outputs/s01_content_verification.json` | **Yes**: read `small_encoder_final.tar` directly, own implementation | max abs diff 0.0, identical NaN pattern |
| Sampled views (2,730) | `research_audit/scripts/v01_view_text_availability.py` → `research_audit/outputs/v01_view_text.json` | **No**: views were regenerated from the processed `data/processed/edges.parquet` with the original sampler | max abs diff 0.0, identical NaN pattern |
| Ledger entry | `INVESTIGATION_LEDGER.md` #7: "Content features not independently checked" | — | **Stale.** It predates s01. The ledger was not edited, per instructions. |

The sampled-view values had therefore not been recomputed from the raw archive, so the single permitted verification was run:

- **Script:** `research_audit/manuscript_readiness/t01_token_std_raw_verification.py`
- **Outputs:** `t01_full.csv`, `t01_views.csv`, `t01_summary.json` and `t01.log`, all in the same directory.
- **Independence:**
  - It imports no `src/` code.
  - It reads link texts straight from the raw tar, in file order.
  - For views, it applies the **stored** sampled-edge positions (`frontend/public/data/len/samples/eNNN.json`, ten seeds per budget) to those raw links. It does not rerun the sampler.
  - It compares the results with `data/processed/sampled_views_v2.parquet` and `outputs/run_v2/study1/full_graph_features.parquet`.

**Command (from the project root, about 2 minutes, reads the 5.4 GB tar):**

```
python research_audit/manuscript_readiness/t01_token_std_raw_verification.py
```

## 2. Exact definition

| Item | Rule (identical in the pipeline `src/features.extract_content_features`, s01, v01 and t01) |
|---|---|
| Unit | One directed edge (link). Each edge contributes its own text. |
| Per edge or per unique text | **Per edge.** Repeated texts are kept, so an identical message on *k* edges contributes *k* token counts. (Unique texts are used only by the separate duplicate and concentration features.) |
| Missing text | Null or non-string text is dropped. The raw archive has 79,271 null texts out of 288,540 links. The key is never absent, and no text is empty before cleaning (`s01_content_verification.json`). |
| Cleaning | Lower-case (Python `str.lower`); remove every match of `https?://\S+`; collapse whitespace runs to one space; strip. Texts empty after cleaning are dropped. |
| Tokenisation | Whitespace split (`str.split()`). The token count is the number of resulting tokens. Mentions, hashtags and punctuation are not treated specially. |
| Statistic | Sample standard deviation (ddof = 1) of the token counts of the usable texts. |
| Edge cases | Exactly one usable text gives 0. No usable text gives undefined (NaN). |
| `m` / `m_K` | The number of usable texts in the graph or the K-edge view. |
| Undefined values in models | Training-fold median imputation inside `train.make_logreg_pipeline`. No missing-value indicator is used. |

Small implementation differences, none of which affects any value:
- The pipeline maps a missing `text` key to `""`, which is then dropped. t01 drops it as a non-string. No key is missing in the archive.

## 3. Comparison with stored values (t01)

| Object | n | Max abs diff | Values with diff > 1e-9 | NaN pattern identical | Undefined |
|---|---|---|---|---|---|
| Full graphs | 103 | 0.0 | 0 | yes | 2 |
| Sampled views | 2,730 (all stored views) | 3.6 × 10⁻¹⁵ | 0 | yes | 50 |

**Discrepancies:** none. The 3.6 × 10⁻¹⁵ difference is floating-point summation order.

## 4. Usable texts per view (m_K), by class and K

Source: `t01_summary.json`. These match `v01_view_text.json`.

| K | Class | Events | Views | Min | Median | Max | Views with m_K = 0 | Views with m_K = 1 | Views with m_K < 10 |
|---|---|---|---|---|---|---|---|---|---|
| 250 | campaign | 51 | 510 | 0 | 158 | 247 | 20 | 0 | 30 |
| 250 | comparison | 51 | 510 | 58 | 207 | 248 | 0 | 0 | 0 |
| 500 | campaign | 48 | 480 | 0 | 312.5 | 494 | 20 | 0 | 29 |
| 500 | comparison | 50 | 500 | 143 | 408 | 495 | 0 | 0 | 0 |
| 1000 | campaign | 28 | 280 | 0 | 530 | 974 | 10 | 0 | 10 |
| 1000 | comparison | 45 | 450 | 298 | 811 | 977 | 0 | 0 | 0 |

Campaign views estimate `token_std` from fewer texts, and a few campaign views from fewer than 10. No view has exactly one usable text, so the "0 if one text" rule is never triggered in views.

## 5. Are the undefined events the same at every budget?

**Yes, wherever they are eligible.** Undefined values come only from two campaign events (label 1 in the manifest and in the full-graph features) that have no usable text anywhere in the archive:

| Event | Edges | K = 250 | K = 500 | K = 1000 |
|---|---|---|---|---|
| `Tapuma_YapıKayıt___2023-04-19_campaign_fulldata` | 1,186 | 10/10 views undefined | 10/10 | 10/10 |
| `YapıKayıt_YoksaOyyok___2023-05-01_campaign_fulldata` | 546 | 10/10 | 10/10 | not eligible (fewer than 1,000 edges) |

Their full-graph `token_std` is also undefined, and no other event or view is undefined. The difference at K = 1000 is due to eligibility, not to different missingness.

## 6. What this verification does and does not establish

- **Establishes:** the stored `token_std` values, full-graph and sampled-view, are exactly the stated definition applied to the raw archive texts.
- **Does not establish:**
  - that `token_std` measures coordination, templating or any linguistic property;
  - that it is independent of text availability (`final_diagnostics/FINAL_TWO_DIAGNOSTICS.md`, Check 1: moderate negative within-class association in comparison events);
  - anything about predictive value.
- **On the view-to-full agreement** (Spearman ≥ 0.995, `v02_results.json`): this is an expected sampling property of a per-edge average-type statistic estimated from hundreds of edges. At K = 1000 a view also covers most of the edges of many campaign graphs (campaign median edge count 1,078, manuscript Table I). It is a measurement check, not evidence of a mechanism.
