"""Add n_copies near-duplicates of one feature (correlation rho). Named like features so a
'use every x* column' pipeline swallows them; coefficients split across the block."""
import numpy as np
from ._common import pick_col

def apply(df, rng, n_copies=4, rho=0.95, col=None):
    df = df.copy(); col = pick_col(df, rng, col)
    base = df[col].to_numpy(dtype=float); sd = np.nanstd(base) or 1.0
    noise_sd = sd * np.sqrt(max(1e-9, 1 - rho**2)) / max(rho, 1e-9)
    added = []
    for i in range(int(n_copies)):
        name = f"{col}_b{i+1}"
        df[name] = base + rng.normal(scale=noise_sd, size=len(df)); added.append(name)
    return df, {"col": col, "added": added, "rho": rho}
