"""Re-append a random `frac` of rows."""
import pandas as pd

def apply(df, rng, frac=0.2):
    k = int(round(frac * len(df)))
    idx = rng.choice(len(df), size=k, replace=True) if k else []
    out = pd.concat([df, df.iloc[idx]], ignore_index=True)
    return out, {"n_duplicated": int(k)}
