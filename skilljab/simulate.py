"""Generate a miniature dataset with a planted truth.

spec.yaml:
  generator: tabular_regression | tabular_classification | two_group_lift
  n: 400            # rows at size 1x
  seed: 42
  sizes: [1, 3, 10] # multipliers used for timing runs
  features: {numeric: 4, categorical: 1, categories: 3}
  truth:            # generator-specific, see below
  tolerance: {relative: 0.25, absolute: 0.1}

The pipeline under test must end by writing result.json: {"estimates": {estimand: value}}.
truth.json lists the same estimand names with the planted values.
"""
from __future__ import annotations
import numpy as np, pandas as pd, pathlib
from .util import read_yaml, write_json

GENERATORS = {}

def generator(name):
    def deco(fn): GENERATORS[name] = fn; return fn
    return deco

def _features(rng, n, spec):
    f = spec.get("features", {})
    k = int(f.get("numeric", 4)); kc = int(f.get("categorical", 0)); ncat = int(f.get("categories", 3))
    X = rng.normal(size=(n, k))
    df = pd.DataFrame(X, columns=[f"x{i+1}" for i in range(k)])
    for j in range(kc):
        df[f"cat{j+1}"] = rng.choice([f"c{i}" for i in range(ncat)], size=n)
    return df

@generator("tabular_regression")
def tabular_regression(rng, n, spec):
    """y = intercept + sum(beta_i * x_i) + noise. Estimands: beta_<feature>."""
    t = spec.get("truth", {})
    df = _features(rng, n, spec)
    effects = t.get("effects") or {"x1": 0.8, "x2": -0.5}
    y = float(t.get("intercept", 0.0)) + rng.normal(scale=float(t.get("noise_sd", 1.0)), size=n)
    for col, b in effects.items():
        y = y + float(b) * df[col].to_numpy()
    df["y"] = y
    return df, {f"beta_{c}": float(b) for c, b in effects.items()}

@generator("tabular_classification")
def tabular_classification(rng, n, spec):
    """logit(p) = intercept + sum(beta_i x_i). Estimands: beta_<feature>, prevalence."""
    t = spec.get("truth", {})
    df = _features(rng, n, spec)
    effects = t.get("effects") or {"x1": 1.0, "x2": -0.7}
    eta = float(t.get("intercept", 0.0)) + np.zeros(n)
    for col, b in effects.items():
        eta = eta + float(b) * df[col].to_numpy()
    p = 1 / (1 + np.exp(-eta))
    df["y"] = (rng.uniform(size=n) < p).astype(int)
    truth = {f"beta_{c}": float(b) for c, b in effects.items()}
    truth["prevalence"] = float(p.mean())
    return df, truth

@generator("two_group_lift")
def two_group_lift(rng, n, spec):
    """A/B style: outcome ~ base_rate, treatment lifts it by `lift` (absolute). Estimands: lift, base_rate."""
    t = spec.get("truth", {})
    base = float(t.get("base_rate", 0.10)); lift = float(t.get("lift", 0.03))
    df = _features(rng, n, spec)
    df["group"] = rng.choice(["A", "B"], size=n)
    p = np.where(df["group"] == "B", base + lift, base)
    df["y"] = (rng.uniform(size=n) < p).astype(int)
    return df, {"lift": lift, "base_rate": base}

def simulate(spec_path, out_dir, size_mult: float = 1.0, seed: int | None = None):
    spec = read_yaml(spec_path)
    gen = GENERATORS.get(spec.get("generator", "tabular_regression"))
    if gen is None:
        raise SystemExit(f"unknown generator {spec.get('generator')!r}; known: {sorted(GENERATORS)}")
    n = max(10, int(round(int(spec.get("n", 400)) * size_mult)))
    rng = np.random.default_rng(spec.get("seed", 42) if seed is None else seed)
    df, estimands = gen(rng, n, spec)
    out = pathlib.Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / "data.csv", index=False)
    truth = {"generator": spec.get("generator", "tabular_regression"), "n": n, "size_mult": size_mult,
             "estimands": estimands, "tolerance": spec.get("tolerance", {"relative": 0.25, "absolute": 0.1})}
    write_json(out / "truth.json", truth)
    return out / "data.csv", truth
