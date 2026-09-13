"""Multiply a `frac` of one feature's rows by `factor` (two units in one column)."""
from ._common import as_float, pick_col

def apply(df, rng, frac=0.1, factor=100.0, col=None):
    df = df.copy(); c = pick_col(df, rng, col); as_float(df, c)
    mask = rng.uniform(size=len(df)) < frac
    df.loc[mask, c] = df.loc[mask, c] * factor
    return df, {"col": c, "n_rescaled": int(mask.sum()), "factor": factor}
