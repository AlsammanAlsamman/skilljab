from __future__ import annotations
import numpy as np, pandas as pd

OUTCOME_NAMES = ("y", "outcome", "target", "label", "churned", "churn", "response", "converted", "event")

def outcome_col(df, col=None):
    if col in df.columns: return col
    for c in OUTCOME_NAMES:
        if c in df.columns: return c
    return df.columns[-1]

def numeric_cols(df: pd.DataFrame, exclude=()):
    y = outcome_col(df)
    return [c for c in df.columns if c != y and c not in exclude and pd.api.types.is_numeric_dtype(df[c])]

def pick_col(df, rng, col=None, exclude=()):
    cols = numeric_cols(df, exclude)
    if not cols:
        raise ValueError("no numeric column to perturb")
    return col if col in cols else str(rng.choice(cols))

def as_float(df, col):
    """Integer columns cannot hold shifted/outlying values; promote to float in place."""
    if pd.api.types.is_integer_dtype(df[col]):
        df[col] = df[col].astype(float)
    return df
