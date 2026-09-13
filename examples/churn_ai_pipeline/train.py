#!/usr/bin/env python3
"""Fit a logistic regression for churn on every available feature; report coefficients and AUC."""
import sys, json
import numpy as np, pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

df = pd.read_csv(sys.argv[1])
y = df["churned"].to_numpy()
X = df.drop(columns=["churned"])
model = LogisticRegression(penalty=None, max_iter=2000)
model.fit(X, y)
coef = dict(zip(X.columns, model.coef_[0]))
est = {f"beta_{c}": float(v) for c, v in coef.items()}
est["prevalence"] = float(y.mean())
auc = float(roc_auc_score(y, model.predict_proba(X)[:, 1]))
ranked = sorted(coef.items(), key=lambda kv: -abs(kv[1]))
json.dump({"estimates": est, "auc": auc, "n": int(len(df)),
           "top_factors": [{"feature": c, "coef": round(float(v), 3)} for c, v in ranked[:5]]},
          open(sys.argv[2], "w"), indent=2)
