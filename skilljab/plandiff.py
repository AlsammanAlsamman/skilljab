"""Diff N independent plans -> divergence map.

plan.json (one per planner session):
  {"name": "plan_a", "persona": "statistician", "stages": [{"id": "qc", "name": "...", "tool": "plink2", ...}],
   "decisions": [{"id": "ld_pruning_threshold", "choice": "r2<0.2", "why": "..."}],
   "assumptions": ["..."]}
Consensus is low information; divergence marks decision points -> aim probes and stones there.
"""
from __future__ import annotations
from collections import defaultdict
from .util import read_json

def diff(plans: list[dict]) -> dict:
    names = [p.get("name", f"plan_{i+1}") for i, p in enumerate(plans)]
    decisions = defaultdict(lambda: defaultdict(list))
    for n, p in zip(names, plans):
        for d in p.get("decisions", []):
            decisions[d["id"]][str(d.get("choice"))].append(n)
    dec_out = {}
    for did, choices in decisions.items():
        missing = [n for n in names if n not in {x for v in choices.values() for x in v}]
        dec_out[did] = {"choices": dict(choices), "divergent": len(choices) > 1 or bool(missing),
                        "not_addressed_by": missing, "n_options": len(choices)}
    stage_sets = {n: [s["id"] for s in p.get("stages", [])] for n, p in zip(names, plans)}
    all_stages = sorted({s for v in stage_sets.values() for s in v}, key=lambda s: min(v.index(s) if s in v else 99 for v in stage_sets.values()))
    stage_out = {s: {"present_in": [n for n, v in stage_sets.items() if s in v]} for s in all_stages}
    for s, rec in stage_out.items():
        rec["divergent"] = len(rec["present_in"]) != len(names)
    assumptions = defaultdict(list)
    for n, p in zip(names, plans):
        for a in p.get("assumptions", []):
            assumptions[a.strip().lower()].append(n)
    hot = sorted([d for d, r in dec_out.items() if r["divergent"]], key=lambda d: -dec_out[d]["n_options"])
    return {"plans": names, "decisions": dec_out, "stages": stage_out,
            "assumptions": {a: v for a, v in assumptions.items()},
            "unique_assumptions": {a: v for a, v in assumptions.items() if len(v) == 1},
            "hotspots": hot + [s for s, r in stage_out.items() if r["divergent"]]}

def diff_cli(paths):
    return diff([read_json(p) for p in paths])
