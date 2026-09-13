"""Apply a stones manifest to a CSV.

stones.json: [{"stone_id": "target_leakage", "dose": {...}, "seed": 7, "after_stage": null|"<stage id>"}]
Entries with after_stage=None hit the input data; others are applied by the runner to that
stage's output before the next stage runs.
"""
from __future__ import annotations
import pandas as pd, numpy as np, pathlib, inspect
from . import stones as S
from .util import read_json, write_json

def _accepted(fn, dose):
    """Keep only the dose params the stone's apply() accepts (unless it takes **kwargs)."""
    sig = inspect.signature(fn)
    if any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()):
        return dict(dose), []
    ok = {k: v for k, v in dose.items() if k in sig.parameters and k not in ("df", "rng")}
    return ok, sorted(set(dose) - set(ok))

def apply_manifest(csv_in, csv_out, manifest, after_stage=None):
    """Apply every entry whose after_stage matches. Returns list of {stone_id, dose, info}."""
    entries = [m for m in manifest if (m.get("after_stage") or None) == after_stage]
    if not entries:
        if str(csv_in) != str(csv_out):
            pathlib.Path(csv_out).write_bytes(pathlib.Path(csv_in).read_bytes())
        return []
    df = pd.read_csv(csv_in)
    applied = []
    for m in entries:
        entry, fn = S.get(m["stone_id"])
        rng = np.random.default_rng(int(m.get("seed", 0)))
        dose, ignored = _accepted(fn, m.get("dose") or {})
        df, info = fn(df, rng, **dose)
        if ignored: info = {**info, "ignored_dose_params": ignored}
        applied.append({"stone_id": m["stone_id"], "character": entry.get("character"),
                        "dose": dose, "after_stage": after_stage, "info": info})
    pathlib.Path(csv_out).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(csv_out, index=False)
    return applied

def inject_cli(data, manifest_path, out, log=None):
    manifest = read_json(manifest_path)
    applied = apply_manifest(data, out, manifest, after_stage=None)
    if log:
        write_json(log, applied)
    return applied

def make_manifest(stone_ids, seed=0, level=None, after_stage=None):
    """Build a manifest with catalog-sampled doses (level: 0..1 or None for random)."""
    rng = np.random.default_rng(seed)
    out = []
    for i, sid in enumerate(stone_ids):
        entry, _ = S.get(sid)
        out.append({"stone_id": sid, "dose": S.sample_dose(entry, rng, level), "seed": int(seed + i),
                    "after_stage": after_stage})
    return out
