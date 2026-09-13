#!/usr/bin/env python3
"""Stage 2: OLS of y on every column starting with 'x'. Writes result.json."""
import sys, json, numpy as np, pandas as pd
df = pd.read_csv(sys.argv[1])
xcols = [c for c in df.columns if c.startswith("x")]
X = np.column_stack([np.ones(len(df))] + [pd.to_numeric(df[c], errors="coerce").to_numpy(dtype=float) for c in xcols])
y = df["y"].to_numpy(dtype=float)
ok = ~np.isnan(X).any(axis=1) & ~np.isnan(y)
beta, *_ = np.linalg.lstsq(X[ok], y[ok], rcond=None)
est = {f"beta_{c}": float(b) for c, b in zip(xcols, beta[1:])}
json.dump({"estimates": est, "n_used": int(ok.sum()), "columns": xcols}, open(sys.argv[2], "w"), indent=2)
