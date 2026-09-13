"""Replace `frac` of a column with values `scale` standard deviations away."""
import numpy as np
from ._common import pick_col, outcome_col

def apply(df, rng, frac=0.02, scale=10.0, col=None, target="outcome"):
    df = df.copy()
    c = outcome_col(df) if target == "outcome" else pick_col(df, rng, col)
    v = df[c].to_numpy(dtype=float); sd = np.nanstd(v) or 1.0; mu = np.nanmean(v)
    k = max(1, int(round(frac * len(df))))
    idx = rng.choice(len(df), size=k, replace=False)
    df.loc[df.index[idx], c] = mu + rng.choice([-1, 1], size=k) * scale * sd
    return df, {"col": c, "n_outliers": int(k)}
