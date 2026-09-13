"""Add a feature that is a noisy copy of the outcome, named like an ordinary feature."""
import numpy as np
from ._common import outcome_col

def apply(df, rng, noise_sd=0.2, name="x_score"):
    df = df.copy(); y = outcome_col(df)
    v = df[y].to_numpy(dtype=float); sd = np.nanstd(v) or 1.0
    df[name] = v + rng.normal(scale=noise_sd * sd, size=len(df))
    return df, {"leak_col": name, "from": y}
