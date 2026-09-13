"""plandiff, tree, lineup, timing, render_skill, graveyard, report, CLI."""
import json, subprocess, sys, pathlib
import numpy as np, pytest
from skilljab import plandiff, tree as T, lineup as L, timing, graveyard as G, render_skill as R
from skilljab.util import write_json, read_json

PLANS = [
    {"name": "plan_a", "stages": [{"id": "qc"}, {"id": "prune"}, {"id": "pca"}],
     "decisions": [{"id": "ld_threshold", "choice": "r2<0.2", "why": "standard"}, {"id": "mhc", "choice": "exclude", "why": "long-range LD"}],
     "assumptions": ["variants are independent after pruning"]},
    {"name": "plan_b", "stages": [{"id": "qc"}, {"id": "prune"}, {"id": "pca"}],
     "decisions": [{"id": "ld_threshold", "choice": "r2<0.5"}, {"id": "mhc", "choice": "keep"}],
     "assumptions": ["variants are independent after pruning", "build is hg38"]},
    {"name": "plan_c", "stages": [{"id": "qc"}, {"id": "pca"}],
     "decisions": [{"id": "ld_threshold", "choice": "r2<0.2"}],
     "assumptions": []},
]

def test_plandiff_marks_divergence_and_hotspots():
    d = plandiff.diff(PLANS)
    assert d["decisions"]["ld_threshold"]["divergent"] and d["decisions"]["ld_threshold"]["n_options"] == 2
    assert d["decisions"]["mhc"]["not_addressed_by"] == ["plan_c"]
    assert d["stages"]["prune"]["divergent"] and not d["stages"]["qc"]["divergent"]
    assert "build is hg38" in d["unique_assumptions"]
    assert d["hotspots"][0] in ("ld_threshold", "mhc") and "prune" in d["hotspots"]

def test_tree_build_and_evidence():
    t = T.build(PLANS)
    node = next(n for n in t["nodes"] if n["id"] == "ld_threshold")
    br = next(b for b in node["branches"] if b["choice"] == "r2<0.2")
    assert br["votes"] == 2 and set(br["plans"]) == {"plan_a", "plan_c"}
    T.add_evidence(t, "mhc", "keep", {"kind": "stone", "verdict": "silent", "round": 2, "summary": "PC1 = MHC"}, status="rejected")
    keep = next(b for n in t["nodes"] if n["id"] == "mhc" for b in n["branches"] if b["choice"] == "keep")
    assert keep["status"] == "rejected" and keep["evidence"][0]["verdict"] == "silent"
    T.add_evidence(t, "new_node", "x", {"kind": "user_recognized", "summary": "s"})
    assert any(n["id"] == "new_node" for n in t["nodes"])
    assert any("rejected" in line for line in T.summary(t))

def test_lineup_scoring_and_stats(tmp_path):
    log = tmp_path / "lineup_log.json"
    L.append_log(log, L.score({"round": 1, "judge_pick": "plan_b", "culprit": "plan_b"}))
    L.append_log(log, L.score({"round": 2, "judge_pick": "plan_a", "culprit": "plan_c"}))
    L.append_log(log, L.score({"round": 3, "judge_pick": "plan_a", "culprit": None}))
    s = L.stats(read_json(log))
    assert s == {"n_scored": 2, "hits": 1, "hit_rate": 0.5, "n_unscored": 1}

def _runs(ns, secs_fn, mem=50.0):
    return [{"n_rows": n, "stages": [{"id": "a", "seconds": secs_fn(n), "peak_mem_mb": mem}, {"id": "b", "seconds": 0.5, "peak_mem_mb": mem}]} for n in ns]

def test_timing_picks_quadratic_and_flags_it():
    t = timing.fit_runs(_runs([100, 300, 1000], lambda n: 1e-5 * n * n + 0.01), target_n=100000)
    assert t["stages"]["a"]["model"] == "quadratic" and t["stages"]["a"]["superlinear"]
    assert t["stages"]["a"]["seconds"] > 1e4 and t["stages"]["b"]["model"] == "const"
    assert t["checkpoint_before"] == "a" and t["low_confidence"] is False

def test_timing_linear_and_ram_flag():
    t = timing.fit_runs(_runs([100, 300, 1000], lambda n: 0.002 * n + 0.1, mem=100.0), target_n=10000, ram_mb=150)
    assert t["stages"]["a"]["model"] == "linear" and 19 < t["stages"]["a"]["seconds"] < 21
    lo, hi = t["stages"]["a"]["seconds_range"]; assert lo <= t["stages"]["a"]["seconds"] <= hi
    with pytest.raises(ValueError):
        timing.fit_runs(_runs([100], lambda n: 1.0), 1000)

def test_timing_never_predicts_below_measured():
    t = timing.fit_runs(_runs([100, 200], lambda n: 0.9 if n == 100 else 0.3), target_n=5000)  # noisy: bigger was faster
    assert t["stages"]["a"]["seconds"] >= 0.9

def test_render_skill_groups_by_evidence():
    ab = {"name": "p", "version": 2, "antibodies": [
        {"id": "ab-001", "title": "Sim", "stage": "s", "evidence": "simulated", "headsup": "H1", "mitigation": "M1", "check": {"stage": "s", "script": "checks/a.py"}, "provenance": {"round": 1, "stone": "outliers", "worst_rel_err": 0.4}},
        {"id": "ab-002", "title": "User", "stage": "s", "evidence": "user_recognized", "headsup": "H2"},
        {"id": "ab-003", "title": "Guess", "stage": "s", "evidence": "elicited_unverified"}]}
    md = R.render(ab, T.build(PLANS), {"n_scored": 4, "hits": 3, "hit_rate": 0.75})
    assert md.index("proven by simulation") < md.index("reported by the user") < md.index("hypothesis only")
    assert "name: p-jabbed" in md and "checks/a.py" in md and "worst error 40%" in md and "3/4 (75%)" in md
    assert "ld_threshold" in md
    empty = R.render({"name": "e", "version": 0, "antibodies": []})
    assert "No antibodies yet" in empty

def test_graveyard_seed_search_and_local_add(tmp_path):
    hits = G.search(["qc", "ld_prune", "pca", "assoc"], data_type="genotype")
    assert hits and hits[0]["id"] == "seed-001" and "explanation" not in hits[0]        # setup only
    assert "explanation" in G.search(["qc", "ld_prune", "pca"], reveal=True)[0]      # predict-then-reveal
    local = tmp_path / "g.json"
    G.add(local, {"shape": ["load", "weird"], "stage": "weird", "failure": "f", "explanation": "e"})
    got = G.search(["weird"], local_path=local, reveal=True)
    assert got and got[0]["failure"] == "f" and got[0]["id"].startswith("g-")

def test_report_renders_from_history(skill):
    from skilljab import project as P
    from skilljab.report import render, collect
    P.new_round(skill); P.write_stones(skill, ["target_leakage"], level=0.6); P.run_round(skill)
    P.sweep(skill, "outliers", levels=2)
    out = render(skill)
    html = out.read_text(); data = collect(skill)
    assert out.exists() and "SkillJab crash test" in html and "/*__SKILLJAB_DATA__*/null" not in html
    assert data["headline"].startswith("Round 1") and "nothing warned you" in data["headline"]
    assert data["stages"]["clean"]["silent"] == 1 and data["stages"]["clean"]["stars"] == 1
    assert data["sweeps"][0]["stone"] == "outliers" and data["timing"]["target_n"] == 50000
    js = html.split("<script>")[1].split("</script>")[0]
    node = __import__("shutil").which("node")
    if node:
        subprocess.run([node, "-e", "new Function(process.argv[1])", js], check=True)

def test_cli_smoke(skill, example):
    env = {**__import__("os").environ, "PYTHONPATH": str(pathlib.Path(__file__).resolve().parent.parent)}
    def cli(*args):
        p = subprocess.run([sys.executable, "-m", "skilljab.cli", *args], capture_output=True, text=True, cwd=example, env=env)
        return p.returncode, p.stdout
    rc, out = cli("stones", "list"); assert rc == 0 and "correlated_block" in out
    rc, out = cli("stones", "show", "outliers"); assert rc == 0 and "wakeup_hint" not in out
    rc, out = cli("stones", "show", "outliers", "--hint"); assert "wakeup_hint" in out
    rc, out = cli("pack", "symptoms"); assert rc == 0 and "senior_frowned" in out
    rc, out = cli("status", "--skill", str(skill)); assert rc == 1 and json.loads(out)["reason"] == "no rounds yet"
    rc, out = cli("round", "new", "--skill", str(skill)); assert rc == 0 and json.loads(out)["round"] == 1
    rc, out = cli("round", "stones", "--skill", str(skill), "outliers", "--level", "0.9", "--dose", '{"outliers": {"scale": 30}}'); assert rc == 0
    rc, out = cli("round", "run", "--skill", str(skill)); assert rc == 0 and json.loads(out)["class"] in ("silent", "harmless")
    rc, out = cli("round", "show", "--skill", str(skill)); assert "stone_id" not in out
    rc, out = cli("round", "show", "--skill", str(skill), "--reveal"); assert "outliers" in out
    for p in PLANS: write_json(example / f"{p['name']}.json", p)
    rc, out = cli("plans", "diff", *[str(example / f"{p['name']}.json") for p in PLANS]); assert rc == 0 and "hotspots" in out
    rc, out = cli("tree", "build", *[str(example / f"{p['name']}.json") for p in PLANS], "--out", str(skill / "tree.json")); assert json.loads(out)["nodes"] == 2
    rc, out = cli("tree", "add-evidence", "--tree", str(skill / "tree.json"), "--node", "mhc", "--choice", "keep", "--kind", "stone", "--summary", "s", "--verdict", "silent", "--status", "rejected"); assert rc == 0
    write_json(example / "lineup.json", {"round": 1, "judge_pick": "plan_b", "culprit": "plan_b"})
    rc, out = cli("lineup", "score", "--skill", str(skill), "--lineup", str(example / "lineup.json")); assert json.loads(out)["hit"] is True
    rc, out = cli("antibody", "add", "--skill", str(skill), "--json", '{"title": "t", "stage": "clean", "evidence": "user_recognized"}'); assert json.loads(out)["id"] == "ab-001"
    rc, out = cli("skill", "bump", "--skill", str(skill), "--description", "d"); assert json.loads(out)["version"] == 1
    rc, out = cli("graveyard", "search", "--skill", str(skill), "--shape", "clean,fit"); assert rc == 0
    rc, out = cli("report", "--skill", str(skill)); assert rc == 0 and pathlib.Path(json.loads(out)["report"]).exists()
    rc, out = cli("version"); assert out.strip() == "0.1.1"
