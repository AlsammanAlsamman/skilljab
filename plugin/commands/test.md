---
description: Run one sabotage round on the miniature - funnel (deja vu, blurry probe), saboteur picks stones, blind analyst runs, engine grades; report silent failures only.
argument-hint: [skill dir, default .claude/skills/<name>] [--stones id,id] [--level 0.6]
---

# /skilljab:test $ARGUMENTS

Follow the `skilljab-core` discipline. Locate the skill dir (argument, or the single dir under `.claude/skills/` with `antibodies.json`). Check `skilljab status --skill <dir>`; if `baseline_ok` is false, run `/skilljab:build` first.

## Funnel
1. **Déjà vu.** `skilljab graveyard search --skill <dir> --shape <stage ids>`. For each hit, *predict* the failure in one line, then re-run with `--reveal` and note where you were wrong — those stages are where you aim.
2. **Blurry probe.** For the 1–2 stages picked above, take 3 templates from `skilljab pack symptoms`, enumerate candidates, and append to `history/round-N/candidates.json` (`[{hypothesis, stage, source: "blurry", proposed_stone}]`).
3. **Round.** `skilljab round new --skill <dir>` → N. Spawn the `saboteur` with the skill dir, round N, the candidates and the divergence map (if any). If the user passed `--stones`/`--level`, hand those to the saboteur as constraints.
4. **Blind run.** Spawn the `analyst` with the skill dir and round N only. Do not relay anything the saboteur said beyond "stones written".
5. **Grade.** Read `skilljab round show --skill <dir> --round N` (no `--reveal` in this context).

## Report to the user — silent failures only
- If class is `silent` or `crashed`: one paragraph per degraded estimand in plain words (what moved, by how much, that nothing warned), then "Run `/skilljab:improve` to turn this into an antibody."
- If class is `caught`, `false_alarm` or `harmless`: one line. Suggest `skilljab sweep --skill <dir> --stone <id>` for stones that were near the tolerance, and a higher `--level` next round.
Never list the stones or doses unless the round is finished and the user asks.
