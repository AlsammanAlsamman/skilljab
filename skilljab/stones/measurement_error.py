"""Add classical measurement noise (sd in units of the column's sd) to one predictor."""
import numpy as np
from ._common import pick_col

def apply(df, rng, sd=0.8, col=None):
    df = df.copy(); c = pick_col(df, rng, col)
    xsd = np.nanstd(df[c].to_numpy(dtype=float)) or 1.0
    df[c] = df[c] + rng.normal(scale=sd * xsd, size=len(df))
    return df, {"col": c, "noise_sd": sd}
