"""
s00_engine.py — shared code for the Study 1 robustness phase (s02, s03). Not run on its own.

Re-implements the paper's Study 1 logistic-regression procedure exactly (src/train.run_cv and
tune_logreg_C): rows in the order of outputs/run_v2/study1/full_graph_features.parquet; outer folds
from src/splits.make_event_folds(manifest, 5, seed); inside each training fold, C is chosen from
{0.01, 0.1, 1, 10} by StratifiedKFold(3, shuffle, random_state 0) cross_val_score (first maximum wins)
for the given objective; pipeline = median imputation -> [optional count basis] -> standardisation
-> LogisticRegression(lbfgs, max_iter 1000, class_weight balanced, random_state 42).
Every preprocessing step is fitted on the training fold only.

Count bases (applied to columns 0-1, which are always log(1+|V|), log(1+|E|)):
  "lr"     none (the paper's models; quadratic count terms are explicit columns)
  "spline" additive cubic B-splines, 4 quantile knots per count (5 basis functions each),
           linear extrapolation; still regularised by the tuned C
  "poly3"  all monomials of the two log counts up to degree 3 (9 terms), tuned C
  "qda"    quadratic discriminant analysis on the standardised counts (no tuning; reference only)

Uncertainty: event bootstrap (2,000 resamples, seed 7) of repeat-averaged quantities. Per-event log
loss is averaged over repeats; AUC and BA are computed per repeat and averaged, with the same
resampled events in every repeat. Repeats re-partition the same events and are not replicates.
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import rankdata
from sklearn.compose import ColumnTransformer
from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import PolynomialFeatures, SplineTransformer, StandardScaler

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from splits import make_event_folds  # noqa: E402

OUT = ROOT / "research_audit/outputs"
GRID = [0.01, 0.1, 1.0, 10.0]
EPS = 1e-6
SCORING = {"ll": "neg_log_loss", "ba": "balanced_accuracy"}
SEEDS = [42, 1, 2, 3, 4, 5, 6, 7, 8, 9] + list(range(10, 20))  # first 10 = the paper's split seeds

SCALE = ["log_node_count", "log_edge_count"]
QUAD = ["log_n_sq", "log_e_sq", "log_n_x_log_e"]
DEGREE = ["indegree_gini", "outdegree_gini"]
ARRANGE = ["reciprocity", "largest_wcc_fraction", "coreness_median", "coreness_max"]
CONTENT = ["exact_dup_proportion", "text_concentration", "msg_length_dispersion"]
LEVELS = {"M0": SCALE, "M0q": SCALE + QUAD, "M1": SCALE + QUAD + DEGREE, "M2": SCALE + QUAD + DEGREE + ARRANGE,
          "M3": SCALE + QUAD + CONTENT, "M4": SCALE + QUAD + DEGREE + ARRANGE + CONTENT}


def load():
    F = pd.read_parquet(ROOT / "outputs/run_v2/study1/full_graph_features.parquet")
    F["log_n_sq"], F["log_e_sq"] = F.log_node_count ** 2, F.log_edge_count ** 2
    F["log_n_x_log_e"] = F.log_node_count * F.log_edge_count
    t = pd.read_csv(OUT / "s01_content_verification.csv", index_col="event_id")
    F["usable_text_share"] = t.loc[F.index, "usable_text_share"].values
    F["no_text"] = (t.loc[F.index, "n_usable_text"].values == 0).astype(float)
    man = pd.read_parquet(ROOT / "data/manifests/manifest.parquet")
    return F, man


def make_pipe(kind, C=1.0):
    steps = [("imputer", SimpleImputer(strategy="median"))]
    if kind == "qda":
        return Pipeline(steps + [("scaler", StandardScaler()), ("clf", QuadraticDiscriminantAnalysis())])
    if kind == "spline":
        steps.append(("basis", ColumnTransformer([("s", SplineTransformer(n_knots=4, degree=3, knots="quantile",
                                                                           extrapolation="linear", include_bias=False), [0, 1])],
                                                 remainder="passthrough")))
    elif kind == "poly3":
        steps.append(("basis", ColumnTransformer([("p", PolynomialFeatures(3, include_bias=False), [0, 1])], remainder="passthrough")))
    return Pipeline(steps + [("scaler", StandardScaler()),
                             ("clf", LogisticRegression(C=C, max_iter=1000, solver="lbfgs", class_weight="balanced", random_state=42))])


def oof(F, cols, kind, fold_map, objective):
    """Out-of-fold P(campaign) for the rows of F (in F's order), as src/train.run_cv."""
    X, y = F[cols].to_numpy(float), F.label.to_numpy().astype(int)
    f = np.array([fold_map[e] for e in F.index])
    p = np.full(len(y), np.nan)
    for k in range(5):
        tr, te = f != k, f == k
        if not te.any():
            continue
        if kind == "qda":
            pipe = make_pipe("qda")
        else:
            cvs = max(2, min(3, int(np.bincount(y[tr]).min())))
            best_C, best = GRID[0], -np.inf
            for C in GRID:
                s = cross_val_score(make_pipe(kind, C), X[tr], y[tr], cv=StratifiedKFold(cvs, shuffle=True, random_state=0),
                                    scoring=SCORING[objective]).mean()
                if s > best:
                    best, best_C = s, C
            pipe = make_pipe(kind, best_C)
        p[te] = pipe.fit(X[tr], y[tr]).predict_proba(X[te])[:, 1]
    return p


def fold_maps(man, seeds=SEEDS):
    return {s: make_event_folds(man, 5, s) for s in seeds}


def loss(y, P):
    P = np.clip(P, EPS, 1 - EPS)
    return -(y * np.log(P) + (1 - y) * np.log(1 - P))


def auc_rows(y, P):
    """AUC of each row of P (repeats x events); ties get average ranks."""
    P = np.atleast_2d(P)
    r = rankdata(P, axis=1)
    n1 = int(y.sum())
    n0 = len(y) - n1
    return (r[:, y == 1].sum(1) - n1 * (n1 + 1) / 2) / (n1 * n0)


def ba_rows(y, P):
    H = np.atleast_2d(P) >= 0.5
    return 0.5 * (H[:, y == 1].mean(1) + (~H[:, y == 0]).mean(1))


def pct_p(d):
    return float(min(1.0, 2 * min((d <= 0).mean(), (d >= 0).mean())))


def contrast(y, PA, PB, BA_A=None, BA_B=None, n_boot=2000, seed=7):
    """A - B on identical events. PA, PB: repeats x events (log-loss-tuned fits); BA_A, BA_B: BA-tuned fits."""
    PA, PB = np.atleast_2d(PA), np.atleast_2d(PB)
    dl_ev = (loss(y, PA) - loss(y, PB)).mean(0)          # per-event, repeat-averaged
    dl_rep = (loss(y, PA) - loss(y, PB)).mean(1)         # per repeat
    da_rep = auc_rows(y, PA) - auc_rows(y, PB)
    out = {"dLL": float(dl_ev.mean()), "dAUC": float(da_rep.mean())}
    has_ba = BA_A is not None
    if has_ba:
        db_rep = ba_rows(y, BA_A) - ba_rows(y, BA_B)
        out["dBA"] = float(db_rep.mean())
    rng = np.random.default_rng(seed)
    bl, ba_, bb = [], [], []
    for _ in range(n_boot):
        i = rng.integers(0, len(y), len(y))
        yi = y[i]
        if yi.min() == yi.max():
            continue
        bl.append(dl_ev[i].mean())
        ba_.append((auc_rows(yi, PA[:, i]) - auc_rows(yi, PB[:, i])).mean())
        if has_ba:
            bb.append((ba_rows(yi, BA_A[:, i]) - ba_rows(yi, BA_B[:, i])).mean())
    bl, ba_ = np.array(bl), np.array(ba_)
    out |= {"dLL_ci": np.percentile(bl, [2.5, 97.5]).tolist(), "p_LL": pct_p(bl), "dLL_event_sd": float(bl.std(ddof=1)),
            "dAUC_ci": np.percentile(ba_, [2.5, 97.5]).tolist(), "p_AUC": pct_p(ba_),
            "repeat_dLL_mean": float(dl_rep.mean()), "repeat_dLL_sd": float(dl_rep.std(ddof=1)) if len(dl_rep) > 1 else 0.0,
            "repeat_dLL_min": float(dl_rep.min()), "repeat_dLL_max": float(dl_rep.max()),
            "repeats_favouring_A_LL": int((dl_rep < 0).sum()), "repeats_favouring_A_AUC": int((da_rep > 0).sum()),
            "n_repeats": int(len(dl_rep)), "events_improved_LL": int((dl_ev < 0).sum()), "n_events": int(len(y))}
    if has_ba:
        bb = np.array(bb)
        out |= {"dBA_ci": np.percentile(bb, [2.5, 97.5]).tolist(), "p_BA": pct_p(bb),
                "repeats_favouring_A_BA": int((db_rep > 0).sum()), "repeats_tied_BA": int((db_rep == 0).sum()),
                "repeat_dBA_min": float(db_rep.min()), "repeat_dBA_max": float(db_rep.max())}
    return out


def holm(p):
    items = sorted(p.items(), key=lambda kv: kv[1])
    m, out, run = len(items), {}, 0.0
    for r, (k, v) in enumerate(items):
        run = max(run, min(1.0, (m - r) * v))
        out[k] = run
    return out
