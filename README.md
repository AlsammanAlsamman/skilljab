<p align="center">
  <img src="https://raw.githubusercontent.com/AlsammanAlsamman/skilljab/main/assets/icon/skilljab-icon-512.png" alt="SkillJab mascot — a winking syringe with a boxing glove, jabbing a bar chart" width="240">
</p>

<h1 align="center">SkillJab</h1>

<p align="center"><b>Immunize an analysis by sabotaging it before it sees real data — and keep the antibodies as a skill.</b></p>

<p align="center">
  <code>pipx install skilljab</code> · Claude Code plugin · Python 3.10+ · MIT
</p>

---

Every analyst has the same scar: a pipeline that ran for six hours and was wrong the whole time, because of something that was public knowledge — the dense-LD region, the leaked column, the duplicated join key, the spreadsheet that wrote `1,234`. AI assistants make this *worse*: they write clean, competent, silently wrong code, and the code looks so good you trust it.

SkillJab is a **jab** — a small controlled hit, like a vaccine shot or a sparring punch — delivered to a *miniature* of your analysis before the real run:

1. **Plant a truth.** Generate a tiny dataset where you know the answer.
2. **Prove recovery.** If the pipeline can't find a truth you planted, it's wrong before any real data.
3. **Throw stones.** Drop generic perturbations into the miniature — the Ghost (missing-not-at-random), the Clique (correlated block), the Time Traveler (leakage), the Twin (duplicates), the Drifter (batch shift)…
4. **Find the silent failures.** The result moved *and no check fired*. That's the only thing you see.
5. **Wake up the AI.** Each silent failure forces an explanation — which is when the model remembers the thing it knew but wasn't applying ("oh — this is the HLA region").
6. **Keep the antibody.** Explanation → checker + mitigation + heads-up → rendered into a per-pipeline `SKILL.md` that Claude loads every time it touches that analysis.

The skill is the accumulated antibodies. The report is a crash test.

## What it looks like

```
$ skilljab round run --skill .claude/skills/gwas
{ "class": "silent", "worst_rel_err": 0.9, "checks_fired": [] }
```

> **Round 1: The Time Traveler (target_leakage) hit stage `clean` — `beta_x1` moved 90% from the planted truth and nothing warned you.**

…then after `/skilljab:improve`:

```
$ skilljab round run --skill .claude/skills/gwas
{ "class": "caught", "checks_fired": [{"script": "checks/no_leaky_columns.py", "message": "predictors nearly identical to outcome: ['x_score']"}] }
$ skilljab status --skill .claude/skills/gwas
{ "jabbed": true, "reason": "clean", "skill_version": 1, "n_antibodies": 1 }
```

The report (`history/report.html`, self-contained, no external requests) shows star ratings per stage, a twin-result slider (drag the dose, watch your own estimates move), breaking-point curves, a stone × stage fragility matrix, predicted lap times at your real N, and a vaccination card of rounds × stones turning from red to green.

## Two halves

| | **Engine** — `skilljab` CLI (Python) | **Plugin** — Claude Code |
|---|---|---|
| does | simulate, inject, run, grade, sweep, diff plans, build the decision tree, score the lineup, predict time, render `SKILL.md` and the report | interview, plan ×N, elicit, judge, sabotage, analyze blind, explain, write antibodies |
| never | calls an LLM, decides what a failure *means* | touches data, computes a verdict, grades itself |

The engine grades; the AI reasons. Any fact that could come from either comes from the engine — that's what keeps the skill honest.

### Blind roles

Five subagents, each with only the files it's allowed to see:

- **planner ×N** — different persona + constraint each (statistician, domain expert, cluster admin, Reviewer 2, an outsider from another field…); never sees the other plans.
- **judge** — runs the *lineup*: "one of these plans failed — which, and why?" Never sees stone results, so its hit rate can be measured; sometimes a known culprit is planted to calibrate it.
- **saboteur** — picks and doses stones; writes `private/stones.json`.
- **analyst** — runs the pipeline blind with the current skill loaded; forbidden from opening `private/`.
- **explainer** — the only role that sees what was planted; does the wake-up, writes the antibody.

### The funnel

Search wide and cheap, prove narrow and expensive:

0. **Divergence map** — diff N plans; where they disagree is where uncertainty lives.
1. **Déjà vu** — `skilljab graveyard search` shows *setups* of similar past failures; predict the outcome, then reveal.
2. **Blurry-friend probe** — describe a symptom badly ("slow at step 3, warned about a parameter"); the model enumerates the neighbourhood; the user *recognizes* what they couldn't recall.
3. **Stones** — build, dose, run; only silent failures survive.

Elicitation proposes; simulation disposes. Nothing reaches the skill without a stone or a user's "that one."

## Install

SkillJab is a command-line tool, so install it with **pipx** (isolated, on your PATH, no fight with your system Python — on Debian/Ubuntu plain `pip install` is blocked by PEP 668):

```bash
# from PyPI (once published)
pipx install skilljab

# from GitHub, before/without PyPI
pipx install git+https://github.com/AlsammanAlsamman/skilljab.git

# from a local checkout (add -e to develop against it)
pipx install .
```

No pipx? `sudo apt install pipx && pipx ensurepath` (Debian/Ubuntu), `brew install pipx` (macOS), or use a venv: `python3 -m venv ~/.skilljab && ~/.skilljab/bin/pip install skilljab`.

Then the Claude Code plugin — point Claude at the plugin directory:

```bash
claude --plugin-dir /path/to/skilljab/plugin      # this session only
```

Requires Python ≥ 3.10. `/usr/bin/time` (GNU time) is used for per-stage peak memory when present; otherwise a coarser fallback.

## Quick start (Claude Code)

```
/skilljab:build   examples/toy_regression/pipeline.yaml
/skilljab:test
/skilljab:improve
/skilljab:report
```

or the whole vaccine in one go: `/skilljab:jab`. When you half-remember something odd from a past run: `/skilljab:recall`.

## Quick start (CLI only)

```bash
cd examples/toy_regression
skilljab init     --name toy --pipeline pipeline.yaml --spec spec.yaml --skill-dir .claude/skills/toy
skilljab baseline --skill .claude/skills/toy --target-n 200000       # proves clean recovery, fits timing
skilljab round new    --skill .claude/skills/toy
skilljab round stones --skill .claude/skills/toy target_leakage outliers --level 0.6
skilljab round run    --skill .claude/skills/toy                      # -> "silent"
skilljab sweep  --skill .claude/skills/toy --stone outliers --levels 5
skilljab report --skill .claude/skills/toy                            # history/report.html
```

## Your pipeline's contract

A `pipeline.yaml` of stages as shell commands — any language, any tool:

```yaml
name: gwas
stages:
  - id: qc      cmd: "plink2 --bfile {in} --geno 0.02 --make-bed --out {out}"   out: qc.csv
  - id: prune   cmd: "Rscript prune.R {in} {out}"                              out: pruned.csv
  - id: fit     cmd: "python fit.py {in} {out}"                                 out: result.json
```

The last stage writes `result.json = {"estimates": {"beta_x1": 0.79, ...}}` with the same estimand names as the planted truth in `sim/spec.yaml`. Checkers are scripts called at stage boundaries — `python3 check.py <stage_output>` — that exit `1` (or print `{"fired": true, "message": "..."}`) when they fire.

Three generators ship (`tabular_regression`, `tabular_classification`, `two_group_lift`); adding one is a function that returns `(DataFrame, {estimand: truth})`.

## The stones

| character | stone | what it does |
|---|---|---|
| The Clique | `correlated_block` | near-identical copies of a feature |
| The Ghost | `mnar_missing` | blanks the top values (missing-not-at-random) |
| The Twin | `duplicates` | re-appends rows |
| The Spike | `outliers` | a few impossible values |
| The Drifter | `batch_shift` | a hidden batch confounded with the outcome |
| The Blur | `measurement_error` | noise in a predictor (attenuation) |
| The Time Traveler | `target_leakage` | a feature computed from the outcome |
| The Metric Martian | `unit_mix` | two units in one column |
| The Long Tail | `heavy_tails` | Student-t noise |
| The Unicorn | `rare_category` | a level with almost no support |
| The Typo | `type_corruption` | `'1,234'`, `' 12 '`, `'NA'` in a numeric column |

They're deliberately domain-neutral. A generic stone is enough to make the model's own knowledge do the specialization: "a correlated block broke PCA" becomes "exclude chr6:25–35Mb before PCA" in the explainer's hands.

## Layout

```
skilljab/            engine (pip package): simulate · stones/ · inject · runner · check · project ·
                     plandiff · tree · lineup · timing · render_skill · graveyard · report · pack/
plugin/              Claude Code plugin: commands/ · agents/ · skills/skilljab-core · hooks/
examples/            toy_regression — a naive OLS pipeline that SkillJab breaks in four ways
tests/               47 tests: every stone, the full loop, helpers, CLI, plugin, hook
docs/DESIGN.md       the design and the thinking behind it
docs/sessions/       transcripts of the design discussions
```

Per pipeline, in *your* repo:

```
.claude/skills/<name>/
├── SKILL.md            rendered — never hand-edit
├── antibodies.json     source of truth, with provenance and evidence class
├── tree.json           decisions with evidence on the edges
├── checks/             the antibodies' checkers
├── sim/spec.yaml       how to build this pipeline's miniature
└── history/            baseline · sizes · round-NNN · sweeps · timing · lineup log · graveyard · report
```

## Honest limits

- **Miniatures can lie.** Some failures only appear at scale (memory cliffs, rare variants, convergence). The timing page extrapolates from three sizes and says so; treat ranges as optimistic.
- **Simulation only helps where you can plant a truth.** Quantitative analyses, yes. Design and strategy, no — there the simulation would just be the model's own assumptions fed back to itself.
- **Stones must bite.** A stone dosed too gently on a tiny miniature proves nothing; use `skilljab sweep` to find the knee.
- **The graveyard is local** in this version. A shared, anonymized one is the obvious next step and the one thing that would make déjà vu real rather than manufactured.

## Development

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
python -m pytest -q                      # 47 tests, ~35 s
claude plugin validate plugin --strict
python scripts/export_session.py         # save the current Claude Code session into docs/sessions/

pipx run build && pipx run twine check dist/*     # build + verify the wheel and sdist
pipx run twine upload dist/*                      # publish to PyPI (needs an API token)
```

## Author

**Alsamman M. Alsamman** — aalsamman100@gmail.com · [github.com/AlsammanAlsamman](https://github.com/AlsammanAlsamman)

## Why the name

A *jab* is a vaccine shot and a boxing punch. Both are a small, deliberate hit that makes you stronger before the real fight. Read the design notes in [`docs/DESIGN.md`](docs/DESIGN.md) for the whole argument — the pre-mortem, the recoverability test, why generic stones beat a hand-written pitfall library, the lineup, and the tricks for making an AI say "oh yeah, I should have told you."
