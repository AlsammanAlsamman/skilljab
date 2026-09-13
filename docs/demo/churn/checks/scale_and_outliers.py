#!/usr/bin/env python3
"""Antibody: one column, two units (cents vs dollars) or a handful of impossible values.
Two units: a gap of > 8x between consecutive upper quantiles of |value| (two magnitude populations).
Outliers: any value > 8 MADs from the median."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, __import__("os").path.dirname(__file__)); from _lib import load, outcome, finish
out, inp = load(sys.argv); df = inp if inp is not None else out; y = outcome(df); msgs = []
for c in df.columns:
    if c == y: continue
    v = pd.to_numeric(df[c], errors="coerce").dropna()
    if len(v) < 20 or v.nunique() < 10: continue
    a = v.abs(); q = a.quantile([0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99]).to_numpy()
    gaps = [(q[i + 1] / q[i]) for i in range(len(q) - 1) if q[i] > 0]
    med = v.median(); mad = (v - med).abs().median() or 1e-9
    ext = int(((v - med).abs() / (1.4826 * mad) > 8).sum())
    if gaps and max(gaps) > 8: msgs.append(f"{c}: values jump {max(gaps):.0f}x between neighbouring quantiles (two units in one column?)")
    elif ext: msgs.append(f"{c}: {ext} value(s) > 8 MAD from the median (outliers)")
finish(msgs, "; ".join(msgs) if msgs else "ok")
