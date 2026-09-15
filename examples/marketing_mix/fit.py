#!/usr/bin/env python3
"""Regress revenue on every available column; report the coefficient per channel as return per dollar."""
import sys, json
import numpy as np, pandas as pd
from sklearn.linear_model import LinearRegression

df = pd.read_csv(sys.argv[1])
y = df["revenue"].to_numpy()
X = df.drop(columns=["revenue"])
model = LinearRegression().fit(X, y)
coef = dict(zip(X.columns, model.coef_))
est = {f"beta_{c}": float(v) for c, v in coef.items()}
r2 = float(model.score(X, y))
channels = [c for c in ("tv_spend", "search_spend", "social_spend", "email_sends", "discount_pct") if c in coef]
ranked = sorted(((c, coef[c]) for c in channels), key=lambda kv: -kv[1])
json.dump({"estimates": est, "r2": r2, "n": int(len(df)),
           "return_per_dollar": [{"channel": c, "roi": round(float(v), 3)} for c, v in ranked]},
          open(sys.argv[2], "w"), indent=2)
