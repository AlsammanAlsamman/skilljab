from __future__ import annotations
import numpy as np, pandas as pd

def numeric_cols(df: pd.DataFrame, exclude=("y",)):
    return [c for c in df.columns if c not in exclude and pd.api.types.is_numeric_dtype(df[c])]

def pick_col(df, rng, col=None, exclude=("y",)):
    cols = numeric_cols(df, exclude)
    if not cols:
        raise ValueError("no numeric column to perturb")
    return col if col in cols else str(rng.choice(cols))

def outcome_col(df, col=None):
    return col if col in df.columns else ("y" if "y" in df.columns else df.columns[-1])
