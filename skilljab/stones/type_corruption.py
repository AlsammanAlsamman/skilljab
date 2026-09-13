"""Turn a numeric column into object dtype with a `frac` of spreadsheet-style strings."""
import numpy as np
from ._common import pick_col

def apply(df, rng, frac=0.05, col=None):
    df = df.copy(); c = pick_col(df, rng, col)
    vals = df[c].astype(object).to_numpy()
    mask = rng.uniform(size=len(df)) < frac
    forms = [lambda v: f"{v:,.3f}", lambda v: f" {v:.3f} ", lambda v: "NA", lambda v: f"{v:.3f} "]
    for i in np.where(mask)[0]:
        try: vals[i] = forms[int(rng.integers(len(forms)))](float(vals[i]))
        except (TypeError, ValueError): vals[i] = "NA"
    df[c] = vals
    return df, {"col": c, "n_corrupted": int(mask.sum())}
