#!/usr/bin/env python3
"""Prepare customer data for modelling: drop incomplete rows, one-hot encode categoricals."""
import sys
import pandas as pd

df = pd.read_csv(sys.argv[1])
df = df.dropna()                                        # keep complete cases only
cat_cols = [c for c in df.columns if df[c].dtype == object]
df = pd.get_dummies(df, columns=cat_cols, drop_first=True, dtype=float)
df.to_csv(sys.argv[2], index=False)
