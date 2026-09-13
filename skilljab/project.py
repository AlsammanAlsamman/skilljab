"""Project-level orchestration over a skill dir:

<skill_dir>/
  antibodies.json  tree.json  SKILL.md  checks/  sim/spec.yaml  pipeline.yaml (path recorded in state)
  history/baseline/  history/sizes/<k>x/  history/timing.json
  history/round-NNN/{private/stones.json, run.json, verdict.json, ...}
  history/sweeps/<stone>.json  history/lineup_log.json  history/graveyard.json  history/state.json
"""
from __future__ import annotations
import pathlib, hashlib, shutil, re
import numpy as np
from .util import read_json, write_json, read_yaml, write_yaml, now, pkg_path
from .simulate import simulate
from .runner import run_pipeline
from .check import grade
from .inject import make_manifest
from .timing import fit_runs
from . import stones as S

def _state_path(skill): return pathlib.Path(skill) / "history" / "state.json"
def load_state(skill):
    p = _state_path(skill); return read_json(p) if p.exists() else {}
def save_state(skill, st):
    st["updated"] = now(); write_json(_state_path(skill), st); return st

def pipeline_hash(pipeline_yaml) -> str:
    p = pathlib.Path(pipeline_yaml).resolve(); h = hashlib.sha256(p.read_bytes())
    for f in sorted(p.parent.rglob("*")):
        rel = f.relative_to(p.parent).parts
        if any(part.startswith(".") or part in ("history", "__pycache__") for part in rel): continue   # skill dir, history, hidden
        if f.is_file() and f.suffix in (".py", ".R", ".r", ".sh", ".jl", ".yaml", ".yml", ".c", ".cpp"):
            h.update(f.name.encode()); h.update(f.read_bytes())
    return h.hexdigest()[:16]

def init(name, pipeline_yaml, skill_dir=None, spec=None, force=False):
    pipeline_yaml = pathlib.Path(pipeline_yaml).resolve()
    if not pipeline_yaml.exists(): raise SystemExit(f"pipeline.yaml not found: {pipeline_yaml}")
    skill = pathlib.Path(skill_dir) if skill_dir else pathlib.Path(".claude/skills") / name
    if skill.exists() and any(skill.iterdir()) and not force:
        raise SystemExit(f"{skill} exists and is not empty (use --force to overwrite the scaffold)")
    for sub in ("checks", "sim", "history"): (skill / sub).mkdir(parents=True, exist_ok=True)
    if spec: shutil.copy(spec, skill / "sim" / "spec.yaml")
    elif not (skill / "sim" / "spec.yaml").exists():
        write_yaml(skill / "sim" / "spec.yaml", {"generator": "tabular_regression", "n": 400, "seed": 42, "sizes": [1, 3, 10],
                   "features": {"numeric": 4, "categorical": 1, "categories": 3},
                   "truth": {"intercept": 1.0, "noise_sd": 1.0, "effects": {"x1": 0.8, "x2": -0.5, "x3": 0.0}},
                   "tolerance": {"relative": 0.25, "absolute": 0.1}})
    if not (skill / "antibodies.json").exists() or force:
        write_json(skill / "antibodies.json", {"name": name, "version": 0, "description": "", "pipeline": str(pipeline_yaml), "antibodies": []})
    if not (skill / "tree.json").exists() or force:
        write_json(skill / "tree.json", {"version": 1, "built": now(), "nodes": []})
    save_state(skill, {"name": name, "pipeline_yaml": str(pipeline_yaml), "pipeline_hash": pipeline_hash(pipeline_yaml),
                       "baseline_ok": False, "last_round": 0, "last_clean_round": None})
    from .render_skill import render_cli; render_cli(skill)
    return skill

def _pipeline(skill):
    st = load_state(skill)
    if not st.get("pipeline_yaml"): raise SystemExit("skill dir not initialised: run `skilljab init` first")
    return st["pipeline_yaml"]

def baseline(skill, sizes=None, target_n=None, ram_mb=None):
    skill = pathlib.Path(skill); h = skill / "history"; spec_p = skill / "sim" / "spec.yaml"; pipe = _pipeline(skill)
    spec = read_yaml(spec_p); sizes = sizes or spec.get("sizes", [1, 3, 10])
    csv, truth = simulate(spec_p, h / "baseline", size_mult=1.0)
    run = run_pipeline(pipe, csv, h / "baseline", skill_dir=skill, label="baseline")
    v = grade(truth, run); write_json(h / "baseline" / "verdict.json", v)
    st = load_state(skill); st["baseline_ok"] = v["class"] in ("harmless", "false_alarm"); st["baseline_class"] = v["class"]
    st["pipeline_hash"] = pipeline_hash(pipe)
    out = {"baseline": v, "timing": None}
    if not st["baseline_ok"]:
        save_state(skill, st); return out   # STOP: the pipeline cannot recover a planted truth on clean data
    runs = []
    for k in sizes:
        d = h / "sizes" / f"{k}x"; c, _ = simulate(spec_p, d, size_mult=float(k))
        runs.append(run_pipeline(pipe, c, d, skill_dir=skill, label=f"size {k}x"))
    if len(runs) >= 2:
        tn = int(target_n or spec.get("target_n") or truth["n"] * 100)
        t = fit_runs(runs, tn, ram_mb); write_json(h / "timing.json", t); out["timing"] = t
    save_state(skill, st); return out

def new_round(skill):
    skill = pathlib.Path(skill); st = load_state(skill); n = int(st.get("last_round", 0)) + 1
    rd = skill / "history" / f"round-{n:03d}"; (rd / "private").mkdir(parents=True, exist_ok=True); (rd / "plans").mkdir(exist_ok=True)
    st["last_round"] = n; save_state(skill, st); return rd

def round_dir(skill, n=None):
    skill = pathlib.Path(skill); n = n or load_state(skill).get("last_round", 0)
    rd = skill / "history" / f"round-{int(n):03d}"
    if not rd.exists(): raise SystemExit(f"no such round: {rd}")
    return rd

def write_stones(skill, stone_ids, n=None, level=None, seed=None, after_stage=None, doses=None):
    rd = round_dir(skill, n); seed = int(seed if seed is not None else int(re.sub(r"\D", "", rd.name)))
    m = make_manifest(stone_ids, seed=seed, level=level, after_stage=after_stage)
    for e in m:
        if doses and e["stone_id"] in doses: e["dose"].update(doses[e["stone_id"]])
    write_json(rd / "private" / "stones.json", m); return m

def run_round(skill, n=None):
    skill = pathlib.Path(skill); rd = round_dir(skill, n); h = skill / "history"; pipe = _pipeline(skill)
    truth = read_json(h / "baseline" / "truth.json"); base = read_json(h / "baseline" / "run.json")
    stones_p = rd / "private" / "stones.json"
    run = run_pipeline(pipe, h / "baseline" / "data.csv", rd, skill_dir=skill, stones_manifest=stones_p if stones_p.exists() else None, label=rd.name)
    v = grade(truth, run, base); write_json(rd / "verdict.json", v)
    st = load_state(skill); st["last_round_class"] = v["class"]
    if v["class"] in ("harmless", "caught", "false_alarm"): st["last_clean_round"] = int(re.sub(r"\D", "", rd.name))
    save_state(skill, st); return v

def sweep(skill, stone_id, levels=5, after_stage=None, fixed=None, seed=11):
    """Dose-response for one stone: run at `levels` doses from low to high -> history/sweeps/<stone>.json"""
    skill = pathlib.Path(skill); h = skill / "history"; pipe = _pipeline(skill)
    truth = read_json(h / "baseline" / "truth.json"); base = read_json(h / "baseline" / "run.json")
    entry, _ = S.get(stone_id); rng = np.random.default_rng(seed); out = {"stone": stone_id, "character": entry.get("character"), "after_stage": after_stage, "levels": []}
    for i, lv in enumerate(np.linspace(0.0, 1.0, int(levels))):
        dose = S.sample_dose(entry, rng, level=float(lv)); dose.update(fixed or {})
        d = h / "sweeps" / stone_id / f"L{i}"; d.mkdir(parents=True, exist_ok=True)
        write_json(d / "stones.json", [{"stone_id": stone_id, "dose": dose, "seed": seed + i, "after_stage": after_stage}])
        run = run_pipeline(pipe, h / "baseline" / "data.csv", d, skill_dir=skill, stones_manifest=d / "stones.json", label=f"sweep {stone_id} L{i}")
        v = grade(truth, run, base)
        out["levels"].append({"level": round(float(lv), 3), "dose": dose, "worst_rel_err": v["worst_rel_err"], "class": v["class"],
                              "estimands": {k: {"estimate": e["estimate"], "rel_err": e["rel_err"]} for k, e in v["estimands"].items()},
                              "time_impact": v["time_impact"]})
    knee = next((l["level"] for l in out["levels"] if l["class"] in ("silent", "crashed")), None)
    out["knee_level"] = knee; out["knee_dose"] = next((l["dose"] for l in out["levels"] if l["level"] == knee), None)
    write_json(h / "sweeps" / f"{stone_id}.json", out); return out

def status(skill):
    skill = pathlib.Path(skill); st = load_state(skill)
    if not st: return {"initialised": False, "jabbed": False, "reason": "not initialised"}
    cur = pipeline_hash(st["pipeline_yaml"]) if pathlib.Path(st["pipeline_yaml"]).exists() else None
    changed = cur != st.get("pipeline_hash")
    last = st.get("last_round", 0); clean = st.get("last_clean_round")
    jabbed = bool(st.get("baseline_ok")) and last > 0 and clean == last and not changed
    reason = ("pipeline changed since baseline — re-run baseline and a round" if changed else "no baseline" if not st.get("baseline_ok") else
              "no rounds yet" if last == 0 else f"last round ({last}) was not clean: {st.get('last_round_class')}" if clean != last else "clean")
    ab = read_json(skill / "antibodies.json") if (skill / "antibodies.json").exists() else {}
    return {"initialised": True, "name": st.get("name"), "jabbed": jabbed, "reason": reason, "pipeline_changed": changed,
            "baseline_ok": st.get("baseline_ok"), "last_round": last, "last_clean_round": clean, "last_round_class": st.get("last_round_class"),
            "skill_version": ab.get("version"), "n_antibodies": len(ab.get("antibodies", []))}

def add_antibody(skill, ab: dict):
    skill = pathlib.Path(skill); p = skill / "antibodies.json"; doc = read_json(p)
    ab.setdefault("id", f"ab-{len(doc['antibodies']) + 1:03d}"); ab.setdefault("evidence", "elicited_unverified"); ab.setdefault("added", now())
    doc["antibodies"].append(ab); write_json(p, doc)
    from .render_skill import render_cli; render_cli(skill); return ab

def bump(skill, description=None):
    skill = pathlib.Path(skill); p = skill / "antibodies.json"; doc = read_json(p)
    doc["version"] = int(doc.get("version", 0)) + 1
    if description: doc["description"] = description
    write_json(p, doc)
    from .render_skill import render_cli; render_cli(skill); return doc["version"]
