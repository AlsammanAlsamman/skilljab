"""Missing-not-at-random: blank the top `frac` of a column's values (or of y)."""
import numpy as np
from ._common import pick_col, outcome_col

def apply(df, rng, frac=0.15, col=None, target="outcome"):
    df = df.copy()
    c = outcome_col(df) if target == "outcome" else pick_col(df, rng, col)
    v = df[c].to_numpy(dtype=float); k = int(round(frac * len(df)))
    idx = np.argsort(v)[-k:] if k > 0 else []
    df.loc[df.index[idx], c] = np.nan
    return df, {"col": c, "n_blanked": int(k)}
