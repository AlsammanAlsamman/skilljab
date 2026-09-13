---
name: skilljab-core
description: The SkillJab discipline for any data analysis, data-mining or statistical pipeline - use when the user asks to make an analysis robust, to check a pipeline before a long run, to "jab", "immunize", "stress test", "sabotage", "pre-mortem" or "crash test" an analysis, or when planning any analysis whose mistakes would only surface after an expensive run. Also triggers on "what could go wrong with this pipeline".
---

# SkillJab core discipline

SkillJab makes the AI **prove** an analysis can recover a planted truth on a miniature, then **sabotages** the miniature with generic *stones*. A **silent failure** (result degraded, no checker fired) is the only thing that matters. Each one forces an explanation, which wakes up domain knowledge the model had but was not applying, and becomes an **antibody**: a checker + mitigation + heads-up, rendered into a per-pipeline `SKILL.md`.

Rules that must never be broken:

1. **The engine grades, the AI reasons.** Never compute a verdict yourself; run `skilljab` commands and read their JSON.
2. **Elicitation proposes, simulation disposes.** Anything a trick surfaces is a *hypothesis* until a stone reproduces it. Only `simulated` and `user_recognized` antibodies may claim to be true.
3. **Blindness is enforced by files.** The analyst never opens `private/stones.json` or any `--reveal` output. The judge never sees stone results. The saboteur never sees the analyst's context.
4. **Only silent failures reach the user.** A caught or harmless stone is a pass, not a warning.
5. **`SKILL.md` is rendered, never hand-edited.** Change `antibodies.json` through `skilljab antibody add` and `skilljab skill render`.

## The funnel (order of a round)
0. Divergence map (if several plans exist) marks decision points.
1. Déjà vu picks the *stage*: `skilljab graveyard search --shape a,b,c` shows setups of similar past failures; **predict the outcome before** running with `--reveal`.
2. Blurry-friend probe lists the *suspects*: `skilljab pack symptoms`, cross templates with stages, enumerate candidates.
3. Stones convict: pick from `skilljab stones list`, run a round, read the verdict.

## Commands
`/skilljab:build` → `/skilljab:test` → `/skilljab:improve` (loop) ; `/skilljab:jab` runs test+improve until clean ; `/skilljab:recall` for the user's half-memories ; `/skilljab:report` renders the crash-test page.

## Elicitation tricks (use inside build / improve / recall)
- **Name the assumption** per stage: what does it assume that the previous stage did not guarantee?
- **Prospective hindsight**: "It is later; this analysis was retracted. Write the retraction notice." Demand specifics.
- **Reviewer 2 / hostile panel**; **inversion** (write the most plausible *wrong* pipeline, diff it); **teach-back**; **the outsider** (reframe in another field); **fake figure first**; **the one-check question** ("6 hours of compute — check one thing before go").
- **Blurry-friend probe**: describe a symptom badly (symptom + location + one attribute) and enumerate the neighbourhood; let the user *recognize* rather than recall.
- **Lineup** (several plans): "one of these failed — which and why?" — and plant a known culprit sometimes to calibrate the judge (`skilljab lineup score`).

## Pipeline contract
`pipeline.yaml` lists stages as shell commands with `{in}` `{out}` `{pipeline_dir}` `{skill_dir}`; the last stage writes `result.json = {"estimates": {estimand: value}}` matching the estimands in `sim/spec.yaml`. Checkers: `python3 check.py <stage_output>` → exit 1 or JSON `{"fired": true, "message": ...}` to fire.
