#!/usr/bin/env python3
"""Checker example: fire if any predictor correlates > 0.9 with the outcome (leakage smell)."""
import sys, json, pandas as pd, numpy as np
df = pd.read_csv(sys.argv[1])
if "y" not in df.columns:
    print(json.dumps({"fired": False, "message": "no outcome column"})); sys.exit(0)
y = pd.to_numeric(df["y"], errors="coerce")
bad = []
for c in df.columns:
    if c == "y": continue
    v = pd.to_numeric(df[c], errors="coerce")
    if v.notna().sum() > 10 and abs(np.corrcoef(v.fillna(v.mean()), y.fillna(y.mean()))[0, 1]) > 0.9:
        bad.append(c)
fired = bool(bad)
print(json.dumps({"fired": fired, "message": f"predictors nearly identical to outcome: {bad}" if fired else "ok"}))
sys.exit(1 if fired else 0)
