"""Collect everything in <skill_dir>/history into one JSON and render the crash-test report.

history/
  baseline/{truth.json, run.json}      clean run at 1x
  sizes/<k>x/run.json + timing.json    scaling runs and the fitted prediction
  round-NNN/{verdict.json, private/stones.json, lineup.json}
  sweeps/<stone>.json                  dose-response curves
  lineup_log.json, graveyard.json
"""
from __future__ import annotations
import pathlib, json, re
from .util import read_json, write_json, pkg_path, now
from . import stones as S
from .lineup import stats as lineup_stats

def _stage_of(stone_entry, stage_ids):
    a = stone_entry.get("after_stage")
    if a is None: return stage_ids[0] if stage_ids else "input"
    i = stage_ids.index(a) if a in stage_ids else -1
    return stage_ids[i + 1] if 0 <= i + 1 < len(stage_ids) else a

def collect(skill_dir) -> dict:
    d = pathlib.Path(skill_dir); h = d / "history"
    ab = read_json(d / "antibodies.json") if (d / "antibodies.json").exists() else {"name": d.name, "version": 0, "antibodies": []}
    truth = read_json(h / "baseline" / "truth.json") if (h / "baseline" / "truth.json").exists() else {}
    base = read_json(h / "baseline" / "run.json") if (h / "baseline" / "run.json").exists() else {}
    stage_ids = [s["id"] for s in base.get("stages", [])]
    chars = {s["id"]: s.get("character", s["id"]) for s in S.catalog()}
    rounds = []
    for rd in sorted(h.glob("round-*")):
        v = rd / "verdict.json"
        if not v.exists(): continue
        vj = read_json(v); n = int(re.sub(r"\D", "", rd.name) or 0)
        for st in vj.get("stones", []) or [{"stone_id": None}]:
            rounds.append({"round": n, "stone": st.get("stone_id"), "character": chars.get(st.get("stone_id"), st.get("stone_id")),
                           "dose": st.get("dose", {}), "stage": _stage_of(st, stage_ids) if st.get("stone_id") else None,
                           "class": vj["class"], "worst_rel_err": vj.get("worst_rel_err"),
                           "checks_fired": [c.get("script") for c in vj.get("checks_fired", [])],
                           "time_impact": vj.get("time_impact", {}), "estimands": vj.get("estimands", {})})
    sweeps = []
    for sp in sorted((h / "sweeps").glob("*.json")) if (h / "sweeps").exists() else []:
        sj = read_json(sp); sj["character"] = chars.get(sj.get("stone"), sj.get("stone")); sweeps.append(sj)
    timing = read_json(h / "timing.json") if (h / "timing.json").exists() else None
    ll = read_json(h / "lineup_log.json") if (h / "lineup_log.json").exists() else {"entries": []}
    # per-stage fragility: stones that landed on this stage
    stages = {}
    for sid in stage_ids:
        hits = [r for r in rounds if r["stage"] == sid and r["stone"]]
        silent = [r for r in hits if r["class"] == "silent"]; crashed = [r for r in hits if r["class"] == "crashed"]
        worst = max([r["worst_rel_err"] or 0 for r in hits] or [0])
        n = len(hits)
        bad = len(silent) + len(crashed)
        stars = 5 if n == 0 else max(1, round(5 * (1 - bad / n)))
        stages[sid] = {"n_stones": n, "silent": len(silent), "crashed": len(crashed), "caught": sum(r["class"] == "caught" for r in hits),
                       "harmless": sum(r["class"] == "harmless" for r in hits), "worst_rel_err": round(worst, 3), "stars": stars,
                       "baseline_seconds": next((s["seconds"] for s in base.get("stages", []) if s["id"] == sid), None)}
    silent_all = [r for r in rounds if r["class"] in ("silent", "crashed")]
    headline = None
    if silent_all:
        w = max(silent_all, key=lambda r: (r["class"] == "silent", r["worst_rel_err"] or 0))
        est = [(k, e) for k, e in w["estimands"].items() if e.get("degraded")]
        what = f"`{est[0][0]}` moved {est[0][1]['rel_err']:.0%} from the planted truth" if est and est[0][1].get("rel_err") is not None else "the pipeline crashed"
        headline = f"Round {w['round']}: {w['character']} ({w['stone']}) hit stage {w['stage']} — {what} and nothing warned you."
    elif rounds:
        headline = "Every stone so far was caught or harmless. Keep jabbing with new stones and higher doses."
    else:
        headline = "No rounds yet. Run /skilljab:test."
    return {"name": ab.get("name", d.name), "version": ab.get("version", 0), "generated": now(), "headline": headline,
            "stage_ids": stage_ids, "stages": stages, "rounds": rounds, "sweeps": sweeps, "timing": timing,
            "truth": truth.get("estimands", {}), "tolerance": truth.get("tolerance", {}),
            "baseline": {s["id"]: {"seconds": s["seconds"], "peak_mem_mb": s.get("peak_mem_mb")} for s in base.get("stages", [])},
            "antibodies": [{k: a.get(k) for k in ("id", "title", "stage", "evidence", "provenance")} for a in ab.get("antibodies", [])],
            "lineup": lineup_stats(ll), "stone_characters": chars,
            "stone_stages": sorted({r["stone"] for r in rounds if r["stone"]})}

def render(skill_dir, out_path=None) -> pathlib.Path:
    data = collect(skill_dir)
    tpl = pkg_path("report_assets", "report.html").read_text()
    html = tpl.replace("/*__SKILLJAB_DATA__*/null", json.dumps(data, default=str))
    out = pathlib.Path(out_path) if out_path else pathlib.Path(skill_dir) / "history" / "report.html"
    out.parent.mkdir(parents=True, exist_ok=True); out.write_text(html)
    write_json(out.with_suffix(".json"), data)
    return out
