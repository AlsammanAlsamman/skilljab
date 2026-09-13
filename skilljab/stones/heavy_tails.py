"""Replace the outcome's noise with Student-t noise (df degrees of freedom) of matched scale."""
import numpy as np
from ._common import outcome_col

def apply(df, rng, df_t=2.5):
    df_t = float(df_t)
    df = df.copy(); y = outcome_col(df)
    if not np.issubdtype(df[y].dtype, np.floating):
        return df, {"skipped": "outcome not continuous"}
    v = df[y].to_numpy(dtype=float); sd = np.nanstd(v) or 1.0
    df[y] = v + rng.standard_t(df_t, size=len(df)) * sd * 0.5
    return df, {"col": y, "df": df_t}
