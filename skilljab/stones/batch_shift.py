"""A hidden batch: shift one feature AND the outcome for a `frac` subgroup, so the batch is
confounded with the feature. No batch column is written (the whole point)."""
import numpy as np
from ._common import pick_col, outcome_col

def apply(df, rng, frac=0.3, shift=1.0, col=None):
    df = df.copy(); c = pick_col(df, rng, col); y = outcome_col(df)
    mask = rng.uniform(size=len(df)) < frac
    xsd = np.nanstd(df[c].to_numpy(dtype=float)) or 1.0
    # the batch moves the feature a little and the outcome a lot -> confounded
    df.loc[mask, c] = df.loc[mask, c] + 0.25 * shift * xsd
    if np.issubdtype(df[y].dtype, np.floating):
        ysd = np.nanstd(df[y].to_numpy(dtype=float)) or 1.0
        df.loc[mask, y] = df.loc[mask, y] + shift * ysd
    else:  # binary outcome: raise its rate in the batch
        flip = mask & (df[y] == 0) & (rng.uniform(size=len(df)) < min(0.9, 0.3 * shift))
        df.loc[flip, y] = 1
    return df, {"col": c, "n_in_batch": int(mask.sum()), "shift": shift}
