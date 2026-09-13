"""Run a pipeline.yaml on one dataset, stage by stage, with checkers at every boundary and
stones (if a manifest is given) applied at the boundaries they name.

pipeline.yaml:
  name: toy
  stages:
    - id: clean
      cmd: "python {pipeline_dir}/clean.py {in} {out}"
      out: clean.csv              # filename for this stage's output (in the work dir)
      checks: [checks/rowcount.py] # optional, relative to the skill dir
    - id: fit
      cmd: "python {pipeline_dir}/fit.py {in} {out}"
      out: result.json
Placeholders: {in} {out} {workdir} {pipeline_dir} {skill_dir}
The last stage's output must be result.json = {"estimates": {estimand: value}}.

Check script contract: `python check.py <stage_output> <stage_input>`; exit 0 = pass; exit 1 = FIRED
(stdout is the message); anything else = check error. A JSON stdout {"fired":..,"message":..}
is honoured too.
"""
from __future__ import annotations
import subprocess, time, pathlib, shlex, json, resource, shutil, os
from .util import read_yaml, read_json, write_json, now
from .inject import apply_manifest

def _peak_mb_wrapper():
    return shutil.which("time") if pathlib.Path("/usr/bin/time").exists() else None

def _run_cmd(cmd, cwd, timeout):
    """Run a shell command; return (rc, seconds, peak_mb, stdout_tail, stderr_tail)."""
    t0 = time.perf_counter()
    gnu_time = pathlib.Path("/usr/bin/time")
    if gnu_time.exists():
        full = f"/usr/bin/time -f '__SKILLJAB_RSS__ %M' bash -c {shlex.quote(cmd)}"
    else:
        full = cmd
    try:
        p = subprocess.run(full, shell=True, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        rc, out, err = p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired as e:
        rc, out, err = 124, (e.stdout or ""), (e.stderr or "") + "\n[timeout]"
        out = out.decode() if isinstance(out, bytes) else out
        err = err.decode() if isinstance(err, bytes) else err
    secs = time.perf_counter() - t0
    peak_mb = None
    if "__SKILLJAB_RSS__" in err:
        lines = [l for l in err.splitlines() if "__SKILLJAB_RSS__" in l]
        try: peak_mb = round(int(lines[-1].split()[-1]) / 1024, 1)
        except (ValueError, IndexError): peak_mb = None
        err = "\n".join(l for l in err.splitlines() if "__SKILLJAB_RSS__" not in l)
    if peak_mb is None:
        peak_mb = round(resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss / 1024, 1)
    return rc, round(secs, 4), peak_mb, out[-2000:], err[-2000:]

def _run_check(script, target, skill_dir, cwd, timeout, stage_input=None):
    path = pathlib.Path(script)
    if not path.is_absolute():
        path = pathlib.Path(skill_dir) / script
    if not path.exists():
        return {"script": str(script), "fired": False, "error": "check script not found"}
    argv = f"python3 {shlex.quote(str(path))} {shlex.quote(str(target))}" + (f" {shlex.quote(str(stage_input))}" if stage_input else "")
    rc, secs, _, out, err = _run_cmd(argv, cwd, timeout)
    msg = out.strip()
    try:
        j = json.loads(msg); fired = bool(j.get("fired")); msg = j.get("message", msg)
    except (json.JSONDecodeError, AttributeError):
        fired = rc == 1
    rec = {"script": str(script), "fired": fired or rc == 1, "message": msg[-500:], "seconds": secs}
    if rc not in (0, 1):
        rec["error"] = f"rc={rc}: {err.strip()[-300:]}"
    return rec

def _checks_from_antibodies(skill_dir):
    p = pathlib.Path(skill_dir) / "antibodies.json"
    if not p.exists():
        return {}
    by_stage = {}
    for a in read_json(p).get("antibodies", []):
        c = a.get("check")
        if c and c.get("script") and c["script"] not in by_stage.setdefault(c.get("stage"), []):
            by_stage[c.get("stage")].append(c["script"])
    return by_stage

def run_pipeline(pipeline_yaml, data_csv, out_dir, skill_dir=None, stones_manifest=None, timeout=1800, label=None):
    pipeline_yaml = pathlib.Path(pipeline_yaml).resolve()
    spec = read_yaml(pipeline_yaml)
    pipeline_dir = pipeline_yaml.parent
    out_dir = pathlib.Path(out_dir).resolve(); work = out_dir / "work"; work.mkdir(parents=True, exist_ok=True)
    skill_dir = pathlib.Path(skill_dir).resolve() if skill_dir else out_dir
    manifest = read_json(stones_manifest) if stones_manifest else []
    ab_checks = _checks_from_antibodies(skill_dir)

    # stage 0: input (stones with after_stage=None land here)
    current = work / "input.csv"
    applied = apply_manifest(data_csv, current, manifest, after_stage=None)
    run = {"pipeline": spec.get("name", pipeline_yaml.stem), "pipeline_yaml": str(pipeline_yaml), "data": str(data_csv),
           "label": label, "started": now(), "stones_applied": applied, "stages": [], "crashed": False, "result": None}
    try:
        import pandas as pd; run["n_rows"] = int(len(pd.read_csv(current)))
    except Exception:
        run["n_rows"] = None

    stages = spec.get("stages", [])
    for i, st in enumerate(stages):
        out_name = st.get("out") or (f"{st['id']}.csv" if i < len(stages) - 1 else "result.json")
        out_path = work / out_name
        cmd = st["cmd"].format(**{"in": str(current), "out": str(out_path), "workdir": str(work),
                                  "pipeline_dir": str(pipeline_dir), "skill_dir": str(skill_dir)})
        rc, secs, peak, so, se = _run_cmd(cmd, str(pipeline_dir), st.get("timeout", timeout))
        rec = {"id": st["id"], "cmd": cmd, "returncode": rc, "seconds": secs, "peak_mem_mb": peak,
               "out": str(out_path), "stdout_tail": so[-800:], "stderr_tail": se[-800:], "checks": []}
        if rc != 0 or not out_path.exists():
            rec["crashed"] = True; run["crashed"] = True; run["stages"].append(rec); break
        # checkers for this stage: pipeline.yaml + antibodies
        for script in dict.fromkeys(list(st.get("checks") or []) + ab_checks.get(st["id"], [])):
            rec["checks"].append(_run_check(script, out_path, skill_dir, str(pipeline_dir), 300, stage_input=current))
        # stones landing after this stage
        if out_path.suffix == ".csv":
            rec["stones_applied"] = apply_manifest(out_path, out_path, manifest, after_stage=st["id"])
            run["stones_applied"] += rec["stones_applied"]
        run["stages"].append(rec)
        current = out_path

    if not run["crashed"] and current.suffix == ".json" and current.exists():
        try:
            run["result"] = read_json(current)
        except json.JSONDecodeError as e:
            run["crashed"] = True; run["result_error"] = str(e)
    run["finished"] = now()
    run["total_seconds"] = round(sum(s["seconds"] for s in run["stages"]), 4)
    write_json(out_dir / "run.json", run)
    return run
