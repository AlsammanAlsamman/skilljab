<p align="center">
  <img src="https://raw.githubusercontent.com/AlsammanAlsamman/skilljab/main/assets/icon/skilljab-icon-512.png" alt="SkillJab mascot — a winking syringe with a boxing glove, jabbing a bar chart" width="220">
</p>

<h1 align="center">SkillJab</h1>

<p align="center"><b>Your AI writes the analysis. SkillJab makes sure it's right before you spend the six hours finding out.</b></p>

<p align="center">
  <a href="https://pypi.org/project/skilljab/"><code>pipx install skilljab</code></a> · a Claude Code plugin + CLI · for people who do data analysis with an AI at their side
</p>

---

## The problem you already have

You ask Claude to write your pipeline. It writes clean, competent code. You run it on the real data, wait hours, and the result is wrong — because of something that was *known*: the region where every variant is correlated, the column that was secretly computed from the outcome, the join that doubled half the rows, the spreadsheet that exported `1,234` as text.

The AI knew about all of these. It didn't apply them, because nothing reminded it at the moment it was writing that step. You didn't catch it, because the code looked right. And by the time the mistake was visible, the compute was spent.

**SkillJab gives the AI the scars before you pay for them.**

## What it does for you

SkillJab is a **jab** — a small controlled hit, like a vaccine shot or a sparring punch — delivered to a *miniature* of your analysis before the real run. Inside Claude Code, it makes the AI:

1. **Plan the analysis several ways at once**, with different personas (a statistician, a domain veteran, the person who runs the cluster, Reviewer 2), and shows you *where the plans disagree* — that is where the risk lives.
2. **Prove the pipeline can recover a truth you planted.** It generates a tiny dataset with a known answer and runs the whole pipeline on it. If the answer doesn't come back, the pipeline is wrong before any real data touches it.
3. **Attack the miniature with "stones"** — missing-not-at-random values, a hidden batch, a leaked column, duplicated rows, two units in one column — and report only the **silent failures**: the result moved *and nothing warned you*.
4. **Explain every silent failure**, which is the moment the AI says *"oh — this is the HLA region"* or *"that score column is computed from the outcome"*: the knowledge it had but wasn't using.
5. **Keep what it learned as a skill.** Every explanation becomes a checker, a fix, and a heads-up in a `SKILL.md` that Claude loads automatically every time it touches that analysis again. Your AI gets better at *your* pipeline, permanently, with a record of why.

And it hands you a **crash-test report** so you can see, in one page, where your analysis is strong and where it is fragile.

## The report

The report is what you'll actually look at. One sentence at the top tells you the worst thing it found; everything below shows where and how much.

<p align="center"><img src="https://raw.githubusercontent.com/AlsammanAlsamman/skilljab/main/assets/report/01-headline-and-stars.png" alt="Headline: Round 1: The Time Traveler (target_leakage) hit stage clean — beta_x1 moved 90% from the planted truth and nothing warned you. Star rating per stage." width="880"></p>

**Star rating per stage** — which step of your pipeline is weak, in two seconds. A stage loses stars for every stone that broke the result without any check firing.

<p align="center"><img src="https://raw.githubusercontent.com/AlsammanAlsamman/skilljab/main/assets/report/02-twin-result.png" alt="Twin result: drag the dose and watch your estimates move relative to the planted truth" width="880"></p>

**Slow-motion replay** — your own estimates against the planted truth, with a slider for the dose. You watch the number leave the green band and see the point where nothing would have told you.

<p align="center"><img src="https://raw.githubusercontent.com/AlsammanAlsamman/skilljab/main/assets/report/03-curves-and-matrix.png" alt="Breaking-point curves (dose vs error, with the tolerance line) and the fragility matrix (stone × stage)" width="880"></p>

**Where it breaks** — dose against error for each stone; the knee is the fragility. It answers "how much missingness can I survive?" with a number instead of a warning. **Impact points** — stone × stage, colored by the worst outcome seen: red is silent, green is caught, grey is harmless.

<p align="center"><img src="https://raw.githubusercontent.com/AlsammanAlsamman/skilljab/main/assets/report/04-lap-times-and-immunity.png" alt="Lap times: predicted runtime per stage at the real N, with ranges and a checkpoint suggestion; the vaccination card: rounds × stones turning from red to green" width="880"></p>

**Lap times** — predicted runtime per stage at your *real* N, extrapolated from three miniature sizes, with the range, a flag for anything superlinear, and where to place a cheap check so a bad input dies at minute two instead of hour six. **Immunity record** — rounds × stones; red turning green is the skill learning.

The report is a single self-contained HTML file. No server, no external requests, safe to email. See a real one from the toy example: [`docs/demo/report.html`](docs/demo/report.html).

## What you get, in your repo

```
.claude/skills/<your-pipeline>/
├── SKILL.md            what Claude reads before touching this analysis: heads-ups, fixes, checks
├── antibodies.json     every entry traces to a round, a stone, or something you recognized
├── tree.json           the decisions the planners disagreed on, with the evidence on each branch
├── checks/             the checkers that now run at every stage boundary
└── history/            rounds, sweeps, timing, the report
```

The skill says *why*. A heads-up reads like: *"stage `clean` · proven by simulation, round 1, stone `target_leakage`, worst error 90% — Selecting every x\* column swallows any column derived from the outcome. Whitelist predictors explicitly; assert no predictor has |corr| > 0.9 with y before fitting. Check: `checks/no_leaky_columns.py`."* Three evidence classes, kept apart: **proven by simulation**, **reported by you**, **hypothesis only**.

## Quick start

```bash
pipx install skilljab                                  # the engine (Debian/Ubuntu: sudo apt install pipx first)
git clone https://github.com/AlsammanAlsamman/skilljab
claude --plugin-dir ./skilljab/plugin                  # the Claude Code side
```

Then, in Claude Code, on any analysis:

```
/skilljab:build   pipeline.yaml        plans ×N, divergence map, lineup, miniature, clean-recovery proof, SKILL.md v0
/skilljab:test                         one sabotage round; you see only the silent failures
/skilljab:improve                      turn them into antibodies; re-test until the round is clean
/skilljab:jab                          test + improve looped — the whole vaccine in one command
/skilljab:recall                       "describe something odd from a past run, badly" — it lists what it could have been
/skilljab:report                       the crash-test page
```

Try it on the shipped example first — a deliberately naive regression that SkillJab breaks four different ways:

```bash
cd skilljab/examples/toy_regression
skilljab init     --name toy --pipeline pipeline.yaml --spec spec.yaml --skill-dir .claude/skills/toy
skilljab baseline --skill .claude/skills/toy --target-n 200000
skilljab round new    --skill .claude/skills/toy
skilljab round stones --skill .claude/skills/toy target_leakage --level 0.6
skilljab round run    --skill .claude/skills/toy          # → "silent": beta_x1 off by 90%, no check fired
skilljab report --skill .claude/skills/toy                # → history/report.html
```

## How it stays honest

Two halves, and each fact lives in exactly one:

| | **Engine** — `skilljab` CLI (Python, no AI inside) | **Plugin** — Claude Code |
|---|---|---|
| does | plant the truth, inject stones, run stages, grade, sweep doses, diff plans, predict time, render the skill and the report | interview, plan ×N, judge, sabotage, analyze, explain, write antibodies |
| never | decide what a failure *means* | compute a verdict or grade itself |

Five subagents that cannot see each other's files: **planners** (one per persona), a **judge** that runs a lineup — "one of these plans failed; which?" — and is scored against planted culprits so you know how much to trust it, a **saboteur** that picks stones, a blind **analyst** that runs the pipeline with the current skill loaded, and an **explainer**, the only one allowed to see what was planted.

*Elicitation proposes; simulation disposes.* The AI can suspect anything; only a stone that actually breaks the miniature — or something you recognized yourself — earns a place in the skill.

## The stones

Deliberately domain-neutral. A generic stone is enough to make the AI's own knowledge do the specialization.

| character | stone | what it does to the miniature |
|---|---|---|
| The Time Traveler | `target_leakage` | adds a feature computed from the outcome |
| The Ghost | `mnar_missing` | blanks the top values — missing-not-at-random |
| The Clique | `correlated_block` | near-identical copies of a feature |
| The Drifter | `batch_shift` | a hidden batch confounded with the outcome |
| The Twin | `duplicates` | re-appends rows |
| The Spike | `outliers` | a few impossible values |
| The Blur | `measurement_error` | noise in a predictor (attenuation) |
| The Metric Martian | `unit_mix` | two units in one column |
| The Long Tail | `heavy_tails` | Student-t noise |
| The Unicorn | `rare_category` | a category level with almost no support |
| The Typo | `type_corruption` | `'1,234'`, `' 12 '`, `'NA'` in a numeric column |

## Your pipeline's contract

Stages as shell commands — any language, any tool — and a last stage that writes the estimates:

```yaml
name: gwas
stages:
  - id: qc      cmd: "plink2 --bfile {in} --geno 0.02 --make-bed --out {out}"   out: qc.csv
  - id: prune   cmd: "Rscript prune.R {in} {out}"                              out: pruned.csv
  - id: fit     cmd: "python fit.py {in} {out}"                                 out: result.json
```

`result.json = {"estimates": {"beta_x1": 0.79, ...}}`, with the same names as the planted truth in `sim/spec.yaml`. Checkers are scripts called at stage boundaries — `python3 check.py <stage_output>` — that exit `1` or print `{"fired": true, "message": "..."}`.

## Honest limits

- **Miniatures can lie.** Some failures only appear at scale. The timing page extrapolates and says so; treat ranges as optimistic.
- **You need a truth to plant.** Quantitative analyses, yes; design and strategy, no — there the simulation is just the AI's own assumptions fed back to itself.
- **Three generators ship** (`tabular_regression`, `tabular_classification`, `two_group_lift`). A genotype generator with real LD structure and a counts generator are the next ones.
- **The graveyard is local.** A shared, anonymized graveyard of real past failures is the obvious next step.

## Development

```bash
git clone https://github.com/AlsammanAlsamman/skilljab && cd skilljab
python3 -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]"
python -m pytest -q                              # 47 tests, ~35 s
claude plugin validate plugin --strict
```

Design notes and the reasoning behind every choice — the pre-mortem, the recoverability test, why generic stones beat a hand-written pitfall library, the lineup, the tricks for making an AI say "oh yeah, I should have told you" — are in [`docs/DESIGN.md`](docs/DESIGN.md).

## Author

**Alsamman M. Alsamman** — aalsamman100@gmail.com · [github.com/AlsammanAlsamman](https://github.com/AlsammanAlsamman) · MIT

*A jab is a vaccine shot and a boxing punch. Both are a small, deliberate hit that makes you stronger before the real fight.*
