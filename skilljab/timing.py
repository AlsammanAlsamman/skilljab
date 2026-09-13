"""Fit a scaling law per stage from runs at several sizes and extrapolate to the real N.

Models: const, linear, nlogn, quadratic. Chosen by least squares on (n, seconds); the
prediction carries a range from the fit residuals. Extrapolation is the least trustworthy
number in the whole report, and it is labelled that way.
"""
from __future__ import annotations
import math
import numpy as np
from .util import read_json

MODELS = {
    "const":     lambda n: np.ones_like(n, dtype=float),
    "linear":    lambda n: n.astype(float),
    "nlogn":     lambda n: n * np.log(np.maximum(n, 2)),
    "quadratic": lambda n: n.astype(float) ** 2,
}

def _fit(ns, ts):
    ns = np.asarray(ns, dtype=float); ts = np.asarray(ts, dtype=float)
    best = None
    for name, f in MODELS.items():
        X = np.column_stack([np.ones_like(ns), f(ns)]) if name != "const" else np.ones((len(ns), 1))
        coef, *_ = np.linalg.lstsq(X, ts, rcond=None)
        pred = X @ coef; rss = float(((ts - pred) ** 2).sum())
        # penalize the extra parameter a little so const wins on flat data
        k = X.shape[1]; n = len(ns)
        score = n * math.log(max(rss, 1e-12) / n) + 2 * k
        if best is None or score < best[0]:
            best = (score, name, coef, rss)
    _, name, coef, rss = best
    resid_sd = math.sqrt(rss / max(1, len(ns) - len(coef)))
    return name, coef, resid_sd

def _predict(name, coef, n):
    n = np.asarray([n], dtype=float)
    if name == "const": return float(coef[0])
    return float(coef[0] + coef[1] * MODELS[name](n)[0])

def fit_runs(runs: list[dict], target_n: int, ram_mb: float | None = None) -> dict:
    """runs: run.json dicts (each has n_rows and stages[].seconds/peak_mem_mb)."""
    runs = sorted([r for r in runs if r.get("n_rows")], key=lambda r: r["n_rows"])
    if len(runs) < 2:
        raise ValueError("need runs at >= 2 sizes to fit a scaling law (3 recommended)")
    ns = [r["n_rows"] for r in runs]
    stages = [s["id"] for s in runs[0]["stages"]]
    out = {"target_n": target_n, "sizes": ns, "stages": {}, "low_confidence": len(runs) < 3}
    total_lo = total = total_hi = 0.0
    for sid in stages:
        ts = [next((s["seconds"] for s in r["stages"] if s["id"] == sid), np.nan) for r in runs]
        ms = [next((s.get("peak_mem_mb") or np.nan for s in r["stages"] if s["id"] == sid), np.nan) for r in runs]
        name, coef, sd = _fit(ns, ts)
        # never predict less than the slowest measured run: bigger N cannot be faster
        pred = max(float(np.nanmax(ts)), _predict(name, coef, target_n))
        growth = (target_n / ns[-1])
        # range: residual noise scaled by extrapolation distance, at least +/-30%
        spread = max(0.3 * pred, sd * growth)
        mname, mcoef, msd = _fit(ns, ms) if not any(np.isnan(ms)) else ("const", [float(np.nanmax(ms) if ms else 0)], 0.0)
        mem = max(float(np.nanmax(ms)) if not any(np.isnan(ms)) else 0.0, _predict(mname, mcoef, target_n))
        rec = {"model": name, "seconds": round(pred, 2), "seconds_range": [round(max(0, pred - spread), 2), round(pred + spread, 2)],
               "measured": dict(zip(ns, [round(float(t), 4) for t in ts])), "peak_mem_mb": round(mem, 1), "mem_model": mname,
               "superlinear": name in ("quadratic",), "flags": []}
        if name == "quadratic": rec["flags"].append(f"quadratic: {growth:.0f}x more rows -> ~{growth**2:.0f}x slower")
        if ram_mb and mem > 0.5 * ram_mb: rec["flags"].append(f"predicted peak memory {mem:.0f} MB is within 2x of {ram_mb:.0f} MB RAM")
        out["stages"][sid] = rec
        total += pred; total_lo += rec["seconds_range"][0]; total_hi += rec["seconds_range"][1]
    out["total_seconds"] = round(total, 2); out["total_range"] = [round(total_lo, 2), round(total_hi, 2)]
    # where to put a checkpoint: just before the first stage that costs > 25% of total
    cum = 0.0
    for sid in stages:
        s = out["stages"][sid]["seconds"]
        if total > 0 and s > 0.25 * total:
            out["checkpoint_before"] = sid; out["checkpoint_reason"] = f"{sid} is {s/total:.0%} of predicted runtime; a cheap check before it saves the most time"
            break
        cum += s
    return out

def fit_cli(run_paths, target_n, ram_mb=None):
    return fit_runs([read_json(p) for p in run_paths], int(target_n), ram_mb)

def human(seconds: float) -> str:
    if seconds < 60: return f"{seconds:.0f}s"
    if seconds < 3600: return f"{seconds/60:.0f}m"
    return f"{seconds/3600:.1f}h"
