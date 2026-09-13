#!/usr/bin/env python3
"""Antibody: near-duplicate predictors (charges, charges_with_tax, annual_charges...) — coefficients
split arbitrarily across the block. Fires on any predictor pair with |corr| > 0.9."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, __import__("os").path.dirname(__file__)); from _lib import load, outcome, finish
out, _ = load(sys.argv); y = outcome(out)
num = out.drop(columns=[y] if y else []).apply(pd.to_numeric, errors="coerce")
num = num.loc[:, num.std() > 0]
pairs = []
if num.shape[1] > 1:
    corr = num.corr().abs().to_numpy(); cols = list(num.columns)
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            if corr[i, j] > 0.9: pairs.append(f"{cols[i]}~{cols[j]} ({corr[i, j]:.2f})")
finish(pairs, f"near-duplicate predictors: {pairs}" if pairs else "ok")
