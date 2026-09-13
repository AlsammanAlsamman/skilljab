"""Grade a run against the planted truth and the checkers -> verdict.json

Classes:
  crashed     pipeline did not produce a result
  silent      result degraded and NO checker fired   <- the only thing the user must see
  caught      result degraded and a checker fired
  false_alarm result fine but a checker fired
  harmless    result fine, nothing fired
"""
from __future__ import annotations
from .util import read_json, write_json

def grade(truth, run, baseline_run=None):
    tol = truth.get("tolerance", {}); rel_tol = float(tol.get("relative", 0.25)); abs_tol = float(tol.get("absolute", 0.1))
    est = (run.get("result") or {}).get("estimates", {}) if run.get("result") else {}
    per = {}
    degraded = False
    for name, tv in truth.get("estimands", {}).items():
        if run.get("crashed") or name not in est or est[name] is None:
            per[name] = {"truth": tv, "estimate": None, "abs_err": None, "rel_err": None, "degraded": True}
            degraded = True; continue
        ev = float(est[name]); ae = abs(ev - float(tv)); re = ae / (abs(float(tv)) if abs(float(tv)) > 1e-12 else 1.0)
        d = (ae > abs_tol) and (re > rel_tol)
        per[name] = {"truth": tv, "estimate": ev, "abs_err": round(ae, 6), "rel_err": round(re, 6), "degraded": d}
        degraded = degraded or d
    fired = [{"stage": s["id"], **c} for s in run.get("stages", []) for c in s.get("checks", []) if c.get("fired")]
    if run.get("crashed"):
        cls = "crashed"
    elif degraded and not fired:
        cls = "silent"
    elif degraded and fired:
        cls = "caught"
    elif fired:
        cls = "false_alarm"
    else:
        cls = "harmless"
    # per-stage time impact vs baseline
    time_impact = {}
    if baseline_run:
        base = {s["id"]: s["seconds"] for s in baseline_run.get("stages", [])}
        for s in run.get("stages", []):
            b = base.get(s["id"])
            if b and b > 0:
                time_impact[s["id"]] = round(s["seconds"] / b, 3)
    worst = max([p["rel_err"] for p in per.values() if p["rel_err"] is not None] or [None if run.get("crashed") else 0.0], key=lambda x: (x is not None, x))
    return {"class": cls, "degraded": degraded, "crashed": bool(run.get("crashed")), "worst_rel_err": worst,
            "estimands": per, "checks_fired": fired, "time_impact": time_impact,
            "stones": run.get("stones_applied", []), "n_rows": run.get("n_rows"), "label": run.get("label")}

def check_cli(truth_path, run_path, out_path, baseline_path=None):
    v = grade(read_json(truth_path), read_json(run_path), read_json(baseline_path) if baseline_path else None)
    write_json(out_path, v)
    return v
