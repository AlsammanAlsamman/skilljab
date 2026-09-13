"""skilljab - command line for the engine. Every subcommand prints JSON (or a path) so Claude
Code can read the result; nothing here calls an LLM."""
from __future__ import annotations
import argparse, json, sys, pathlib
from .util import read_json, write_json, read_yaml, pkg_path

def _out(obj):
    print(json.dumps(obj, indent=2, default=str))

def main(argv=None):
    ap = argparse.ArgumentParser(prog="skilljab", description="Immunize an analysis by sabotaging it before it sees real data.")
    sp = ap.add_subparsers(dest="cmd", required=True)

    # ---- project lifecycle
    p = sp.add_parser("init", help="scaffold a skill dir for a pipeline"); p.add_argument("--name", required=True); p.add_argument("--pipeline", required=True)
    p.add_argument("--skill-dir"); p.add_argument("--spec"); p.add_argument("--force", action="store_true")
    p = sp.add_parser("baseline", help="simulate, prove clean recovery, run at 3 sizes, fit timing"); p.add_argument("--skill", required=True)
    p.add_argument("--sizes", nargs="*", type=float); p.add_argument("--target-n", type=int); p.add_argument("--ram-mb", type=float)
    p = sp.add_parser("status", help="is this pipeline jabbed? (exit 1 if not)"); p.add_argument("--skill", required=True)
    r = sp.add_parser("round", help="rounds: new | stones | run | show").add_subparsers(dest="sub", required=True)
    q = r.add_parser("new"); q.add_argument("--skill", required=True)
    q = r.add_parser("stones", help="write private/stones.json for a round"); q.add_argument("--skill", required=True); q.add_argument("--round", type=int)
    q.add_argument("stones", nargs="+"); q.add_argument("--level", type=float); q.add_argument("--seed", type=int); q.add_argument("--after-stage"); q.add_argument("--dose", help='JSON {"stone_id": {"param": value}}')
    q = r.add_parser("run", help="run the pipeline blind on the round's stones and grade it"); q.add_argument("--skill", required=True); q.add_argument("--round", type=int)
    q = r.add_parser("show", help="verdict of a round"); q.add_argument("--skill", required=True); q.add_argument("--round", type=int); q.add_argument("--reveal", action="store_true", help="include the stones (explainer only)")
    p = sp.add_parser("sweep", help="dose-response curve for one stone"); p.add_argument("--skill", required=True); p.add_argument("--stone", required=True)
    p.add_argument("--levels", type=int, default=5); p.add_argument("--after-stage"); p.add_argument("--fixed", help="JSON of fixed dose params, e.g. {\"col\":\"x1\"}"); p.add_argument("--seed", type=int, default=11)

    # ---- stones & pack
    s = sp.add_parser("stones", help="list | show").add_subparsers(dest="sub", required=True)
    s.add_parser("list"); q = s.add_parser("show"); q.add_argument("stone"); q.add_argument("--hint", action="store_true", help="include the wake-up hint (explainer only)")
    q = s.add_parser("manifest", help="write a standalone manifest"); q.add_argument("stones", nargs="+"); q.add_argument("--out", required=True); q.add_argument("--level", type=float); q.add_argument("--seed", type=int, default=0); q.add_argument("--after-stage")
    p = sp.add_parser("pack", help="show symptoms | personas | catalog"); p.add_argument("what", choices=["symptoms", "personas", "catalog"])

    # ---- low-level engine
    p = sp.add_parser("simulate"); p.add_argument("--spec", required=True); p.add_argument("--out", required=True); p.add_argument("--size", type=float, default=1.0); p.add_argument("--seed", type=int)
    p = sp.add_parser("inject"); p.add_argument("--data", required=True); p.add_argument("--stones", required=True); p.add_argument("--out", required=True)
    p = sp.add_parser("run"); p.add_argument("--pipeline", required=True); p.add_argument("--data", required=True); p.add_argument("--out", required=True); p.add_argument("--skill"); p.add_argument("--stones"); p.add_argument("--label")
    p = sp.add_parser("check"); p.add_argument("--truth", required=True); p.add_argument("--run", required=True); p.add_argument("--out", required=True); p.add_argument("--baseline")

    # ---- reasoning-side helpers
    pl = sp.add_parser("plans", help="diff N plan.json files -> divergence map").add_subparsers(dest="sub", required=True)
    q = pl.add_parser("diff"); q.add_argument("plans", nargs="+"); q.add_argument("--out")
    t = sp.add_parser("tree", help="build | add-evidence | show").add_subparsers(dest="sub", required=True)
    q = t.add_parser("build"); q.add_argument("plans", nargs="+"); q.add_argument("--out", required=True)
    q = t.add_parser("add-evidence"); q.add_argument("--tree", required=True); q.add_argument("--node", required=True); q.add_argument("--choice", required=True)
    q.add_argument("--kind", required=True, choices=["stone", "lineup", "user_recognized", "elicited"]); q.add_argument("--summary", required=True); q.add_argument("--verdict"); q.add_argument("--round", type=int); q.add_argument("--status", choices=["default", "rejected", "open"])
    q = t.add_parser("show"); q.add_argument("--tree", required=True)
    lu = sp.add_parser("lineup", help="score | stats").add_subparsers(dest="sub", required=True)
    q = lu.add_parser("score"); q.add_argument("--skill", required=True); q.add_argument("--lineup", required=True)
    q = lu.add_parser("stats"); q.add_argument("--skill", required=True)
    tm = sp.add_parser("timing", help="fit scaling laws").add_subparsers(dest="sub", required=True)
    q = tm.add_parser("fit"); q.add_argument("runs", nargs="+"); q.add_argument("--target-n", type=int, required=True); q.add_argument("--ram-mb", type=float); q.add_argument("--out")
    sk = sp.add_parser("skill", help="render | bump").add_subparsers(dest="sub", required=True)
    q = sk.add_parser("render"); q.add_argument("--skill", required=True)
    q = sk.add_parser("bump"); q.add_argument("--skill", required=True); q.add_argument("--description")
    ab = sp.add_parser("antibody", help="add").add_subparsers(dest="sub", required=True)
    q = ab.add_parser("add"); q.add_argument("--skill", required=True); q.add_argument("--json"); q.add_argument("--file")
    g = sp.add_parser("graveyard", help="search | add").add_subparsers(dest="sub", required=True)
    q = g.add_parser("search"); q.add_argument("--skill"); q.add_argument("--shape", required=True, help="comma-separated stage ids"); q.add_argument("--data-type"); q.add_argument("-k", type=int, default=5); q.add_argument("--reveal", action="store_true")
    q = g.add_parser("add"); q.add_argument("--skill", required=True); q.add_argument("--json"); q.add_argument("--file")
    p = sp.add_parser("report", help="render the crash-test report"); p.add_argument("--skill", required=True); p.add_argument("--out")
    sp.add_parser("version")

    a = ap.parse_args(argv)
    from . import project as P

    if a.cmd == "version":
        from . import __version__; print(__version__); return 0
    if a.cmd == "init":
        d = P.init(a.name, a.pipeline, a.skill_dir, a.spec, a.force); _out({"skill_dir": str(d), "next": f"skilljab baseline --skill {d}"}); return 0
    if a.cmd == "baseline":
        r = P.baseline(a.skill, a.sizes, a.target_n, a.ram_mb)
        ok = r["baseline"]["class"] in ("harmless", "false_alarm")
        _out({"recovered_planted_truth": ok, "baseline_class": r["baseline"]["class"], "estimands": r["baseline"]["estimands"],
              "timing_total_seconds": (r["timing"] or {}).get("total_seconds"), "checkpoint_before": (r["timing"] or {}).get("checkpoint_before"),
              "message": "clean recovery proven; proceed to rounds" if ok else "STOP: the pipeline cannot recover the planted truth on clean data. Fix the pipeline or the spec before any sabotage."})
        return 0 if ok else 1
    if a.cmd == "status":
        s = P.status(a.skill); _out(s); return 0 if s.get("jabbed") else 1
    if a.cmd == "round":
        if a.sub == "new": rd = P.new_round(a.skill); _out({"round_dir": str(rd), "round": int(rd.name.split("-")[1])}); return 0
        if a.sub == "stones":
            doses = json.loads(a.dose) if a.dose else None
            m = P.write_stones(a.skill, a.stones, a.round, a.level, a.seed, a.after_stage, doses); _out({"written": len(m), "stones": [x["stone_id"] for x in m]}); return 0
        if a.sub == "run":
            v = P.run_round(a.skill, a.round); pub = {k: v[k] for k in ("class", "degraded", "crashed", "worst_rel_err", "estimands", "checks_fired", "time_impact", "n_rows")}
            _out(pub); return 0
        if a.sub == "show":
            rd = P.round_dir(a.skill, a.round); v = read_json(rd / "verdict.json") if (rd / "verdict.json").exists() else {"error": "round not run yet"}
            if not a.reveal: v = {k: x for k, x in v.items() if k != "stones"}
            _out(v); return 0
    if a.cmd == "sweep":
        r = P.sweep(a.skill, a.stone, a.levels, a.after_stage, json.loads(a.fixed) if a.fixed else None, a.seed)
        _out({"stone": r["stone"], "knee_level": r["knee_level"], "knee_dose": r["knee_dose"], "levels": [{k: l[k] for k in ("level", "worst_rel_err", "class")} for l in r["levels"]]}); return 0
    if a.cmd == "stones":
        from . import stones as S
        if a.sub == "list": _out([{k: s[k] for k in ("id", "character", "applies_to", "symptom")} for s in S.catalog()]); return 0
        if a.sub == "show":
            e, _ = S.get(a.stone); e = dict(e)
            if not a.hint: e.pop("wakeup_hint", None)
            _out(e); return 0
        if a.sub == "manifest":
            from .inject import make_manifest; m = make_manifest(a.stones, a.seed, a.level, a.after_stage); write_json(a.out, m); _out(m); return 0
    if a.cmd == "pack":
        f = {"symptoms": pkg_path("pack", "symptoms.yaml"), "personas": pkg_path("pack", "diversity", "personas.yaml"), "catalog": pkg_path("stones", "catalog.yaml")}[a.what]
        print(f.read_text()); return 0
    if a.cmd == "simulate":
        from .simulate import simulate; csv, truth = simulate(a.spec, a.out, a.size, a.seed); _out({"data": str(csv), "truth": truth}); return 0
    if a.cmd == "inject":
        from .inject import inject_cli; _out(inject_cli(a.data, a.stones, a.out)); return 0
    if a.cmd == "run":
        from .runner import run_pipeline; r = run_pipeline(a.pipeline, a.data, a.out, a.skill, a.stones, label=a.label)
        _out({"crashed": r["crashed"], "total_seconds": r["total_seconds"], "stages": [{k: s.get(k) for k in ("id", "returncode", "seconds", "peak_mem_mb")} for s in r["stages"]], "run_json": str(pathlib.Path(a.out) / "run.json")}); return 0
    if a.cmd == "check":
        from .check import check_cli; _out(check_cli(a.truth, a.run, a.out, a.baseline)); return 0
    if a.cmd == "plans":
        from .plandiff import diff_cli; d = diff_cli(a.plans)
        if a.out: write_json(a.out, d)
        _out(d); return 0
    if a.cmd == "tree":
        from . import tree as T
        if a.sub == "build": t = T.build([read_json(p) for p in a.plans]); write_json(a.out, t); _out({"nodes": len(t["nodes"]), "out": a.out}); return 0
        if a.sub == "add-evidence":
            t = read_json(a.tree); ev = {"kind": a.kind, "summary": a.summary}
            if a.verdict: ev["verdict"] = a.verdict
            if a.round is not None: ev["round"] = a.round
            T.add_evidence(t, a.node, a.choice, ev, a.status); write_json(a.tree, t); _out({"ok": True}); return 0
        if a.sub == "show": print("\n".join(T.summary(read_json(a.tree)))); return 0
    if a.cmd == "lineup":
        from . import lineup as L; log = pathlib.Path(a.skill) / "history" / "lineup_log.json"
        if a.sub == "score": s = L.score(read_json(a.lineup)); L.append_log(log, s); _out({"hit": s["hit"], **L.stats(read_json(log))}); return 0
        if a.sub == "stats": _out(L.stats(read_json(log)) if log.exists() else {"n_scored": 0}); return 0
    if a.cmd == "timing":
        from .timing import fit_cli; t = fit_cli(a.runs, a.target_n, a.ram_mb)
        if a.out: write_json(a.out, t)
        _out(t); return 0
    if a.cmd == "skill":
        if a.sub == "render": from .render_skill import render_cli; _out({"rendered": str(render_cli(a.skill))}); return 0
        if a.sub == "bump": _out({"version": P.bump(a.skill, a.description)}); return 0
    if a.cmd == "antibody":
        body = json.loads(a.json) if a.json else read_json(a.file); _out(P.add_antibody(a.skill, body)); return 0
    if a.cmd == "graveyard":
        from . import graveyard as G; local = (pathlib.Path(a.skill) / "history" / "graveyard.json") if a.skill else None
        if a.sub == "search": _out(G.search([x.strip() for x in a.shape.split(",")], a.data_type, local, a.k, a.reveal)); return 0
        if a.sub == "add": body = json.loads(a.json) if a.json else read_json(a.file); _out(G.add(local, body)); return 0
    if a.cmd == "report":
        from .report import render; out = render(a.skill, a.out); _out({"report": str(out)}); return 0
    ap.error("unknown command"); return 2

if __name__ == "__main__":
    sys.exit(main())
