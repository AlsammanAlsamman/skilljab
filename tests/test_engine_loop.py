"""End-to-end on the toy pipeline: clean recovery, stones bite, antibody flips silent -> caught."""
import json, shutil, pathlib, pytest
from skilljab import project as P
from skilljab.util import read_json
from skilljab.check import grade
from skilljab.runner import run_pipeline

def test_init_creates_scaffold(example):
    d = P.init("toy", example / "pipeline.yaml", example / ".claude/skills/toy", spec=example / "spec.yaml")
    for f in ("antibodies.json", "tree.json", "SKILL.md", "sim/spec.yaml", "history/state.json"):
        assert (d / f).exists(), f
    assert read_json(d / "antibodies.json")["antibodies"] == []
    with pytest.raises(SystemExit):
        P.init("toy", example / "pipeline.yaml", d, spec=example / "spec.yaml")   # refuses to clobber

def test_baseline_proves_recovery_and_fits_timing(skill):
    st = P.load_state(skill)
    assert st["baseline_ok"] and st["baseline_class"] == "harmless"
    t = read_json(skill / "history" / "timing.json")
    assert set(t["stages"]) == {"clean", "fit"} and t["target_n"] == 50000 and t["total_seconds"] > 0
    assert t["low_confidence"] is True   # only 2 sizes in the fixture
    v = read_json(skill / "history" / "baseline" / "verdict.json")
    assert all(not e["degraded"] for e in v["estimands"].values())

def test_baseline_stops_when_pipeline_cannot_recover(example):
    # sabotage the pipeline itself: fit returns garbage
    (example / "fit.py").write_text('import sys, json\njson.dump({"estimates": {"beta_x1": 99, "beta_x2": 99, "beta_x3": 99}}, open(sys.argv[2], "w"))\n')
    d = P.init("bad", example / "pipeline.yaml", example / ".claude/skills/bad", spec=example / "spec.yaml")
    r = P.baseline(d, sizes=[1, 2])
    assert r["baseline"]["class"] == "silent" and r["timing"] is None
    assert P.load_state(d)["baseline_ok"] is False

def test_round_silent_then_caught_after_antibody(skill):
    rd = P.new_round(skill); assert rd.name == "round-001"
    P.write_stones(skill, ["target_leakage"], level=0.6)
    v = P.run_round(skill)
    assert v["class"] == "silent" and v["estimands"]["beta_x1"]["degraded"]
    assert P.status(skill)["jabbed"] is False
    # explainer adds the checker + antibody
    shutil.copy(pathlib.Path(__file__).parent.parent / "examples/toy_regression/checks/no_leaky_columns.py", skill / "checks")
    P.add_antibody(skill, {"title": "Leaked score", "stage": "clean", "trigger": "corr>0.9", "headsup": "h", "mitigation": "m",
                           "check": {"stage": "clean", "script": "checks/no_leaky_columns.py"}, "evidence": "simulated",
                           "provenance": {"round": 1, "stone": "target_leakage", "trick": "stone", "worst_rel_err": v["worst_rel_err"]}})
    assert P.bump(skill) == 1
    P.new_round(skill); P.write_stones(skill, ["target_leakage"], level=0.6)
    v2 = P.run_round(skill)
    assert v2["class"] == "caught" and v2["checks_fired"][0]["script"].endswith("no_leaky_columns.py")
    s = P.status(skill); assert s["jabbed"] is True and s["skill_version"] == 1 and s["n_antibodies"] == 1
    md = (skill / "SKILL.md").read_text()
    assert "proven by simulation" in md and "no_leaky_columns.py" in md and "v1" in md

def test_status_detects_pipeline_change(skill, example):
    P.new_round(skill); P.write_stones(skill, ["duplicates"], level=0.3); P.run_round(skill)
    assert P.status(skill)["jabbed"] is True
    (example / "fit.py").write_text((example / "fit.py").read_text() + "\n# edited\n")
    s = P.status(skill); assert s["jabbed"] is False and s["pipeline_changed"] is True

def test_checker_on_baseline_does_not_false_alarm(skill):
    shutil.copy(pathlib.Path(__file__).parent.parent / "examples/toy_regression/checks/no_leaky_columns.py", skill / "checks")
    P.add_antibody(skill, {"title": "Leaked score", "stage": "clean", "check": {"stage": "clean", "script": "checks/no_leaky_columns.py"}, "evidence": "simulated"})
    r = P.baseline(skill, sizes=[1, 2]); assert r["baseline"]["class"] == "harmless"

def test_after_stage_stone_lands_on_intermediate(skill):
    P.new_round(skill); P.write_stones(skill, ["target_leakage"], level=0.5, after_stage="clean")
    v = P.run_round(skill)
    run = read_json(skill / "history" / "round-001" / "run.json")
    assert run["stages"][0]["stones_applied"] and run["stages"][0]["stones_applied"][0]["after_stage"] == "clean"
    assert v["class"] == "silent"

def test_crash_is_classified(skill, example):
    (example / "clean.py").write_text("import sys; sys.exit(3)\n")
    P.new_round(skill); P.write_stones(skill, ["duplicates"], level=0.2)
    v = P.run_round(skill); assert v["class"] == "crashed" and v["crashed"]

def test_sweep_finds_knee(skill):
    s = P.sweep(skill, "target_leakage", levels=3)
    assert len(s["levels"]) == 3 and s["knee_level"] == 0.0 and s["silent_from"] == 0.0 and all(l["class"] == "silent" for l in s["levels"])
    s2 = P.sweep(skill, "duplicates", levels=3)
    assert s2["knee_level"] is None and (skill / "history" / "sweeps" / "duplicates.json").exists()

def test_grade_classes_directly():
    truth = {"estimands": {"b": 1.0}, "tolerance": {"relative": 0.2, "absolute": 0.05}}
    ok = {"result": {"estimates": {"b": 1.05}}, "stages": [{"id": "s", "checks": []}]}
    assert grade(truth, ok)["class"] == "harmless"
    bad = {"result": {"estimates": {"b": 0.5}}, "stages": [{"id": "s", "checks": []}]}
    assert grade(truth, bad)["class"] == "silent"
    bad_fired = {"result": {"estimates": {"b": 0.5}}, "stages": [{"id": "s", "checks": [{"script": "c", "fired": True}]}]}
    assert grade(truth, bad_fired)["class"] == "caught"
    ok_fired = {"result": {"estimates": {"b": 1.0}}, "stages": [{"id": "s", "checks": [{"script": "c", "fired": True}]}]}
    assert grade(truth, ok_fired)["class"] == "false_alarm"
    assert grade(truth, {"crashed": True, "stages": []})["class"] == "crashed"
    # tiny truths use the absolute tolerance
    t0 = {"estimands": {"b": 0.0}, "tolerance": {"relative": 0.2, "absolute": 0.1}}
    assert grade(t0, {"result": {"estimates": {"b": 0.05}}, "stages": []})["class"] == "harmless"
    assert grade(t0, {"result": {"estimates": {"b": 0.5}}, "stages": []})["class"] == "silent"
