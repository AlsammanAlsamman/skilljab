"""antibodies.json -> SKILL.md. The skill is rendered, never hand-edited.

antibodies.json:
{"name": "toy_regression", "version": 3, "description": "...", "pipeline": "pipeline.yaml",
 "antibodies": [{
   "id": "ab-003", "title": "Leaked score column", "stage": "fit", "node": "feature_selection",
   "trigger": "a predictor correlates > 0.9 with the outcome",
   "headsup": "...one paragraph the user reads before running...",
   "mitigation": "...what to do...",
   "check": {"stage": "clean", "script": "checks/no_leaky_columns.py"},
   "evidence": "simulated|user_recognized|elicited_unverified",
   "provenance": {"round": 2, "stone": "target_leakage", "trick": "stone", "worst_rel_err": 0.79}
 }]}
"""
from __future__ import annotations
import pathlib
from .util import read_json, write_json, now
from . import tree as T

EVIDENCE_LABEL = {"simulated": "proven by simulation", "user_recognized": "reported by the user (not yet simulated)",
                  "elicited_unverified": "hypothesis only — not verified"}

def render(ab: dict, tree: dict | None = None, lineup_stats: dict | None = None) -> str:
    name = ab.get("name", "pipeline"); ver = ab.get("version", 0)
    desc = ab.get("description") or f"Heads-ups, checks and decisions for the {name} pipeline, earned by sabotaging miniature runs."
    L = ["---", f"name: {name}-jabbed", f"description: {desc} Use whenever writing, editing, reviewing or running the {name} analysis, or when the user mentions {name}.", "---", "",
         f"# {name} — jabbed skill v{ver}", "",
         "This skill was **rendered by SkillJab** from `antibodies.json`. Do not edit by hand; run `/skilljab:improve` or `/skilljab:recall` instead.",
         "Every line below traces to a round, a stone, or something the user recognized.", ""]
    groups = {"simulated": [], "user_recognized": [], "elicited_unverified": []}
    for a in ab.get("antibodies", []):
        groups.setdefault(a.get("evidence", "elicited_unverified"), []).append(a)
    L += ["## Before you run: heads-ups", ""]
    if not any(groups.values()):
        L += ["_No antibodies yet. Run `/skilljab:test` to start a round._", ""]
    for key in ("simulated", "user_recognized", "elicited_unverified"):
        items = groups.get(key, [])
        if not items: continue
        L += [f"### {EVIDENCE_LABEL[key]}", ""]
        for a in items:
            prov = a.get("provenance", {})
            src = f"round {prov.get('round')}" if prov.get("round") is not None else prov.get("trick", "")
            if prov.get("stone"): src += f", stone `{prov['stone']}`"
            if prov.get("worst_rel_err") is not None: src += f", worst error {prov['worst_rel_err']:.0%}"
            L += [f"**{a.get('id','?')} · {a.get('title','(untitled)')}** — stage `{a.get('stage','?')}`" + (f" · decision `{a['node']}`" if a.get("node") else "") + (f" · _{src}_" if src else ""), ""]
            if a.get("trigger"): L += [f"- **Trigger:** {a['trigger']}"]
            if a.get("headsup"): L += [f"- **Heads-up:** {a['headsup']}"]
            if a.get("mitigation"): L += [f"- **Do:** {a['mitigation']}"]
            if a.get("check", {}).get("script"): L += [f"- **Check:** `{a['check']['script']}` runs after stage `{a['check'].get('stage','?')}`"]
            L += [""]
    checks = [a for a in ab.get("antibodies", []) if a.get("check", {}).get("script")]
    L += ["## Checks that run at stage boundaries", ""]
    L += [f"- after `{a['check'].get('stage','?')}`: `{a['check']['script']}` — {a.get('title','')}" for a in checks] or ["_none yet_"]
    L += [""]
    if tree and tree.get("nodes"):
        L += ["## Decisions and what the evidence says", ""] + T.summary(tree) + [""]
    if lineup_stats and lineup_stats.get("n_scored"):
        L += ["## Judge calibration", "", f"Lineup hit rate: {lineup_stats['hits']}/{lineup_stats['n_scored']} ({lineup_stats['hit_rate']:.0%}). Trust the judge's rankings accordingly.", ""]
    L += ["## How to use this skill", "",
          "1. Read the heads-ups before writing or running the pipeline; apply the **Do** lines.",
          "2. Keep the checks in place; they are the antibodies.",
          "3. If you change the pipeline, run `/skilljab:test` again — the skill is only as current as its last clean round.",
          "4. If you remember something odd from a past run, describe it badly to `/skilljab:recall`.", "",
          f"_Rendered {now()} by SkillJab._", ""]
    return "\n".join(L)

def render_cli(skill_dir):
    d = pathlib.Path(skill_dir)
    ab = read_json(d / "antibodies.json")
    tree = read_json(d / "tree.json") if (d / "tree.json").exists() else None
    from .lineup import stats
    ls = stats(read_json(d / "history" / "lineup_log.json")) if (d / "history" / "lineup_log.json").exists() else None
    md = render(ab, tree, ls)
    (d / "SKILL.md").write_text(md)
    return d / "SKILL.md"
