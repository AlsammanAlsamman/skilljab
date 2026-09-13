#!/usr/bin/env python3
"""Antibody: a predictor that is nearly the outcome (a score from an earlier model, a post-cancellation
flag, a refund field) — |corr| > 0.9 or single-feature AUC > 0.95 with the outcome."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, __import__("os").path.dirname(__file__)); from _lib import load, outcome, finish
out, _ = load(sys.argv); y = outcome(out)
if y is None: finish(False, "no outcome column")
yy = out[y].to_numpy(dtype=float); bad = []
for c in out.columns:
    if c == y: continue
    v = pd.to_numeric(out[c], errors="coerce")
    if v.notna().sum() < 20 or v.std() == 0: continue
    v = v.fillna(v.mean()).to_numpy(dtype=float)
    r = abs(np.corrcoef(v, yy)[0, 1])
    # single-feature AUC via rank statistic (binary outcome only)
    auc = None
    if set(np.unique(yy)) <= {0.0, 1.0} and 0 < yy.mean() < 1:
        ranks = pd.Series(v).rank().to_numpy(); n1 = yy.sum(); n0 = len(yy) - n1
        auc = (ranks[yy == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0); auc = max(auc, 1 - auc)
    if r > 0.9 or (auc is not None and auc > 0.95): bad.append(f"{c} (corr {r:.2f}" + (f", AUC {auc:.2f})" if auc else ")"))
finish(bad, f"predictors that are nearly the outcome — leakage: {bad}" if bad else "ok")
