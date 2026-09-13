"""Add `n_rows` rows carrying a never-before-seen category level."""
import pandas as pd

def apply(df, rng, n_rows=2, level="zz_rare"):
    cats = [c for c in df.columns if df[c].dtype == object or str(df[c].dtype) == "category"]
    if not cats:
        return df, {"skipped": "no categorical column"}
    c = cats[0]
    rows = df.sample(n=int(n_rows), replace=True, random_state=int(rng.integers(1 << 30))).copy()
    rows[c] = level
    return pd.concat([df, rows], ignore_index=True), {"col": c, "level": level, "n_rows": int(n_rows)}
