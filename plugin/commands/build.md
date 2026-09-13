---
description: Build a jabbed skill for an analysis pipeline - interview, N diverse plans, divergence map, lineup, miniature with planted truth, clean-recovery proof, SKILL.md v0.
argument-hint: [pipeline.yaml or a description of the analysis]
---

# /skilljab:build $ARGUMENTS

Follow the SkillJab core discipline (skill `skilljab-core`). Confirm `skilljab version` works; if not, tell the user to `pip install skilljab` and stop.

## 1. Interview (short)
Ask only what you cannot infer: the analysis goal in one sentence, the data type (tabular / genotype / counts / timeseries), what the final deliverable is, the real N, the compute budget, and the machine's RAM. If `$ARGUMENTS` points at an existing `pipeline.yaml`, read it and the scripts it calls.

## 2. Plans ×N (3–5)
Read `skilljab pack personas`. Spawn N `planner` subagents **in parallel**, each with a different persona + constraint and an output path `history/round-000/plans/plan_<persona>.json` (create the dir). Never pass one planner another planner's output.

## 3. Divergence map and lineup
`skilljab plans diff <plans...> --out history/round-000/divergence.json`. Then spawn one `judge` with the plans and the divergence map; it writes `lineup.json`. Record it: `skilljab lineup score --skill <dir> --lineup history/round-000/lineup.json` (no culprit yet; that's fine).

## 4. Merge and tree
Merge into one plan, taking each decision from the branch with the strongest reasoning (not the most votes). `skilljab tree build <plans...> --out <skill_dir>/tree.json`. Write or update `pipeline.yaml` for the merged plan (stages as shell commands; last stage writes `result.json`).

## 5. Elicitation pass on the hotspots
For each divergence hotspot and each planner's `one_check` and `retraction_notice`: name the assumption, run the blurry-friend grammar (`skilljab pack symptoms`) on that stage, and write `history/round-000/candidates.json` = `[{hypothesis, stage, source, proposed_stone}]`. Do not tell the user about these yet — they are hypotheses.

## 6. Miniature and proof
`skilljab init --name <name> --pipeline pipeline.yaml --skill-dir .claude/skills/<name>` (add `--spec` if you wrote one). Edit `sim/spec.yaml` so the planted truth matches the deliverable's estimands, then `skilljab baseline --skill <dir> --target-n <real N> --ram-mb <RAM>`.
- If it returns `recovered_planted_truth: false` → **STOP**. Show the estimands vs truth and fix the pipeline or the spec with the user. No sabotage on a pipeline that fails clean.
- Otherwise report the predicted runtime and the checkpoint suggestion.

## 7. Antibodies v0
Turn the merged plan's named assumptions into baseline checkers where cheap (row counts, dtypes, uniqueness of join keys, no |corr|>0.9 with the outcome). `skilljab antibody add ... --json` with `evidence: "elicited_unverified"` for anything not yet reproduced. `skilljab skill bump --skill <dir> --description "<one line>"`.

Finish: tell the user the skill path, the clean-recovery result, predicted runtime, and that the next step is `/skilljab:test`.
