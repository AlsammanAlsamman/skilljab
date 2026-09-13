"""Stones: generic perturbations dropped into the miniature.

Each stone module exposes  apply(df, rng, **dose) -> (df, info)  and the catalog
describes when it applies, dose ranges, the symptom, and the wake-up hint that is
shown to the explainer ONLY after a silent failure.
"""
from __future__ import annotations
import importlib
from ..util import read_yaml, pkg_path

def catalog():
    return read_yaml(pkg_path("stones", "catalog.yaml"))["stones"]

def get(stone_id):
    for s in catalog():
        if s["id"] == stone_id:
            mod = importlib.import_module(f".{stone_id}", __package__)
            return s, mod.apply
    raise KeyError(f"unknown stone {stone_id!r}; run `skilljab stones list`")

def sample_dose(entry, rng, level: float | None = None):
    """Pick a dose inside the catalog ranges. level in [0,1] interpolates low->high; None = random."""
    dose = {}
    for k, v in (entry.get("dose") or {}).items():
        if isinstance(v, list) and len(v) == 2 and all(isinstance(x, (int, float)) for x in v):
            lo, hi = v
            u = rng.uniform() if level is None else float(level)
            val = lo + (hi - lo) * u
            dose[k] = int(round(val)) if isinstance(lo, int) and isinstance(hi, int) else float(val)
        else:
            dose[k] = v
    return dose
