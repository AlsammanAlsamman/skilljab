<p align="center">
  <img src="https://raw.githubusercontent.com/AlsammanAlsamman/skilljab/main/assets/icon/skilljab-icon-circle-512-ring.png" alt="SkillJab mascot — a winking syringe with a boxing glove, jabbing a bar chart" width="200">
</p>

<h1 align="center">SkillJab</h1>

<p align="center">
  <b>Your AI writes the analysis. SkillJab makes sure it's right before you spend the six hours finding out.</b>
</p>

<p align="center">
  <a href="https://pypi.org/project/skilljab/"><img alt="PyPI" src="https://img.shields.io/pypi/v/skilljab?color=ff5a4e&label=pypi"></a>
  <a href="https://pypi.org/project/skilljab/"><img alt="Python" src="https://img.shields.io/pypi/pyversions/skilljab?color=1b2a4a"></a>
  <img alt="Claude Code plugin" src="https://img.shields.io/badge/Claude%20Code-plugin-1b2a4a">
  <img alt="tests" src="https://img.shields.io/badge/tests-47%20passing-2fa36b">
  <a href="LICENSE"><img alt="MIT" src="https://img.shields.io/badge/license-MIT-lightgrey"></a>
</p>

<p align="center">
  <code>pipx install skilljab</code> &nbsp;·&nbsp; <code>claude --plugin-dir ./plugin</code> &nbsp;·&nbsp; <code>/skilljab:jab</code>
</p>

<p align="center">
  <a href="#-see-it-work">See it work</a> ·
  <a href="#-why">Why</a> ·
  <a href="#-how-it-works">How it works</a> ·
  <a href="#-the-report">The report</a> ·
  <a href="#-install">Install</a> ·
  <a href="#-what-you-get">What you get</a> ·
  <a href="#-under-the-hood">Under the hood</a> ·
  <a href="#-the-stones">The stones</a> ·
  <a href="#-limits">Limits</a>
</p>

---

**SkillJab** is a Claude Code plugin and CLI for people who do data analysis with an AI at their side. It builds a *miniature* of your analysis with a **planted truth**, sabotages it with realistic perturbations, and shows you the failures **nothing would have warned you about** — then turns every one of them into a checker, a fix, and a heads-up inside a `SKILL.md` that Claude loads whenever it touches that analysis again.

- 🧪 **Proves** your pipeline can recover a truth you planted — before any real data
- 🥊 **Finds the silent failures** — the result moved and no check fired
- 🧬 **Keeps the antibodies** — your AI gets better at *your* pipeline, permanently, with the reason on record
- 📊 **Crash-test report** — where it's strong, where it's fragile, how long it will take at full size

<br>

## 🎯 See it work

> **The prompt:** *"Here's a CSV of our customers — tenure, monthly charges, support tickets, contract, plan, churned. Build a churn model and tell me which factors matter."*

Claude wrote `dropna` → `get_dummies` → logistic regression on every column. Clean, idiomatic code. On clean data it recovers every planted effect — AUC 0.73, factors ranked correctly. **Nothing looks wrong.**

Then SkillJab threw ten stones at it, one per round, each a thing that happens to real customer tables. **Eight broke the answer, and nothing warned anyone:**

| what a real table does | what the AI's pipeline reported | warned? |
|---|---|:---:|
| a `churn_score_v1` column from an earlier model | AUC 1.0 — "nothing matters except the score" | ❌ |
| `monthly_charges` exported as text (`'1,234.50'`) | `get_dummies` made 1,400 columns; the price coefficient vanished | ❌ |
| support history purged for closed accounts | `dropna` removed the churners; ticket effect 67% too small | ❌ |
| one billing region in cents | "price doesn't affect churn" | ❌ |
| one acquisition channel pricier and churnier, unlabelled | every coefficient ~100% off | ❌ |
| ~50 bills at ±$800 (decimal slip) | price effect 90% off | ❌ |
| charges + charges-with-tax + annual charges | price effect split three ways, sign unstable | ❌ |
| tenure derived from a noisy invoice date | tenure effect 70% too small, mis-ranked | ❌ |
| billing join duplicated rows | estimates fine | harmless |
| a new `enterprise` plan with two customers | fine | harmless |

<p align="center"><img src="https://raw.githubusercontent.com/AlsammanAlsamman/skilljab/main/assets/report/churn/01-headline-and-stars.png" alt="Report headline: Round 1: The Time Traveler (target_leakage) hit stage prepare — beta_contract_one_year moved 5767% from the planted truth and nothing warned you. Star rating: prepare 3 stars, train 5 stars." width="880"></p>

**Then the antibodies.** For each silent failure the explainer wrote *why* in the domain's own words, a checker at the stage boundary, and a heads-up. Same ten stones again: **six caught**; two still silent — and for those two the skill says plainly that the data as delivered cannot reveal them, and which columns to ask for.

**Then the hold-out** — the part that makes it evidence. Ten perturbations the checkers were *never written for*: tenure in years, a different column going missing, a *very* noisy leak, the outcome itself missing, a stone dropped *between* stages… **Nine of ten flagged** by antibodies written for something else; the one miss is the batch the skill already declares unguardable. The first pass of that hold-out exposed two real holes in the antibodies — and fixing them is in the replay too.

<p align="center">
  <a href="examples/churn_ai_pipeline/"><b>Full write-up, the pipeline, and a 4-minute replay script →</b></a> &nbsp;·&nbsp;
  <a href="docs/demo/churn/">the rendered report and the skill it produced →</a>
</p>

<br>

## 💡 Why

You ask Claude to write your pipeline. It writes clean, competent code. You run it on the real data, wait hours, and the result is wrong — because of something that was *known*: the region where every variant is correlated, the column secretly computed from the outcome, the join that doubled half the rows, the spreadsheet that exported `1,234` as text.

The AI knew about all of these. It didn't apply them, because nothing reminded it at the moment it was writing that step. You didn't catch it, because the code looked right. And by the time the mistake was visible, the compute was spent.

**SkillJab gives the AI the scars before you pay for them.** The name says the mechanism: a *jab* is a vaccine shot and a boxing punch — a small, deliberate hit that makes you stronger before the real fight.

<br>

## ⚙️ How it works

<p align="center"><img src="https://raw.githubusercontent.com/AlsammanAlsamman/skilljab/main/assets/flowchart/skilljab-loop.png" alt="The SkillJab loop: plan it N ways, plant a truth, prove recovery → throw stones → did the result move with no check firing? → silent failure → explain (the AI wakes up), antibody, SKILL.md → run the real thing; next round, harder stones" width="1000"></p>

1. **Plan it several ways.** Planners with different personas — a statistician, a domain veteran, the person who runs the cluster, Reviewer 2 — each write a plan. Where they *disagree* is where the risk lives.
2. **Plant a truth and prove recovery.** A tiny dataset with a known answer, the whole pipeline run on it. If the answer doesn't come back, the pipeline is wrong before any real data.
3. **Throw stones.** Generic perturbations, dosed to bite. Only **silent failures** are reported — the result moved *and* nothing fired.
4. **Explain.** Each silent failure forces the AI to say *why*, which is when it recalls the domain knowledge it had but wasn't using.
5. **Keep the antibody.** Explanation → checker + mitigation + heads-up → rendered into `SKILL.md`, with provenance.
6. **Repeat** until a round is clean. Then run the real thing — with a hook that warns you if the skill has gone stale.

Every step is a slash command:

| command | what it does |
|---|---|
| `/skilljab:build` | interview → plans ×N → divergence map → lineup → miniature → clean-recovery proof → `SKILL.md` v0 |
| `/skilljab:test` | one sabotage round; you see only the silent failures |
| `/skilljab:improve` | turn them into antibodies; re-test until the round is clean |
| `/skilljab:jab` | test + improve, looped — the whole vaccine in one command |
| `/skilljab:recall` | *"describe something odd from a past run, badly"* — it lists what it could have been; what you recognize becomes an antibody |
| `/skilljab:report` | the crash-test page |

<br>

## 📊 The report

One sentence at the top tells you the worst thing it found; everything below shows where and how much. A single self-contained HTML file — no server, no external requests, safe to email. These are from the churn test.

<table>
<tr><td width="50%" valign="top">

<img src="https://raw.githubusercontent.com/AlsammanAlsamman/skilljab/main/assets/report/churn/02-twin-result.png" alt="Twin result: your estimates against the planted truth, with a dose slider">

**Slow-motion replay** — your own estimates against the planted truth, with a slider for the dose. Watch the coefficient leave the green band and see the point where nothing would have told you.

</td><td width="50%" valign="top">

<img src="https://raw.githubusercontent.com/AlsammanAlsamman/skilljab/main/assets/report/churn/03-breaking-points.png" alt="Breaking-point curves: dose against error for seven stones, with the tolerance line">

**Where it breaks** — dose against error per stone; the knee is the fragility. "How much missingness can I survive?" gets a number, not a warning. Green dots: a check caught it.

</td></tr>
<tr><td width="50%" valign="top">

<img src="https://raw.githubusercontent.com/AlsammanAlsamman/skilljab/main/assets/report/churn/04-fragility-matrix.png" alt="Fragility matrix: stone by stage, colored by worst outcome">

**Impact points** — stone × stage, colored by the worst outcome ever seen: red silent, green caught, grey harmless. The reds that remain are the ones the skill says it cannot guard without more columns.

</td><td width="50%" valign="top">

<img src="https://raw.githubusercontent.com/AlsammanAlsamman/skilljab/main/assets/report/churn/05-lap-times.png" alt="Lap times: predicted runtime per stage at N = 2,000,000">

**Lap times** — predicted runtime per stage at your *real* N, extrapolated from three miniature sizes, with ranges, a flag for anything superlinear, and where to put a cheap check so a bad input dies at minute two instead of hour six.

</td></tr>
</table>

<p align="center"><img src="https://raw.githubusercontent.com/AlsammanAlsamman/skilljab/main/assets/report/churn/06-immunity-record.png" alt="Vaccination card: rounds by stones, red turning green as antibodies were added" width="880"></p>

**Immunity record** — rounds × stones; red turning green is the skill learning. Below it, every antibody with its provenance, and how often the judge picked the right plan in the lineup.

<br>

## 🚀 Install

```bash
pipx install skilljab                                  # the engine — a CLI, so pipx (no fight with system Python)
git clone https://github.com/AlsammanAlsamman/skilljab
claude --plugin-dir ./skilljab/plugin                  # the Claude Code side
```

<details>
<summary>No pipx? Other ways to install</summary>

```bash
sudo apt install pipx && pipx ensurepath        # Debian / Ubuntu
brew install pipx                               # macOS
python3 -m venv ~/.skilljab && ~/.skilljab/bin/pip install skilljab && export PATH=~/.skilljab/bin:$PATH   # plain venv
pipx install git+https://github.com/AlsammanAlsamman/skilljab.git   # bleeding edge
```

Requires Python ≥ 3.10. GNU `time` (`/usr/bin/time`) is used for per-stage peak memory when present.
</details>

### Quick start — in Claude Code

```
/skilljab:build  pipeline.yaml
/skilljab:jab
/skilljab:report
```

### Quick start — CLI only

<details>
<summary>Replay the churn test (4 minutes)</summary>

```bash
cd skilljab/examples/churn_ai_pipeline
./run_demo.sh                                         # baseline, 30 rounds, 7 sweeps, report
open .claude/skills/churn/history/report.html
cat  .claude/skills/churn/SKILL.md
```
</details>

<details>
<summary>Drive the engine by hand on your own pipeline</summary>

```bash
skilljab init     --name mine --pipeline pipeline.yaml --spec spec.yaml --skill-dir .claude/skills/mine
skilljab baseline --skill .claude/skills/mine --target-n 2000000     # proves clean recovery, fits timing
skilljab round new    --skill .claude/skills/mine
skilljab round stones --skill .claude/skills/mine target_leakage mnar_missing --level 0.6
skilljab round run    --skill .claude/skills/mine                     # -> silent | caught | harmless | …
skilljab sweep  --skill .claude/skills/mine --stone mnar_missing --levels 6
skilljab antibody add --skill .claude/skills/mine --file antibody.json
skilljab report --skill .claude/skills/mine                           # history/report.html
skilljab status --skill .claude/skills/mine                           # jabbed: true/false, and why
```
</details>

<br>

## 📦 What you get

In *your* repo, per pipeline:

```
.claude/skills/<your-pipeline>/
├── SKILL.md            what Claude reads before touching this analysis — rendered, never hand-edited
├── antibodies.json     every entry traces to a round, a stone, or something you recognized
├── tree.json           the decisions the planners disagreed on, with the evidence on each branch
├── checks/             the checkers that now run at every stage boundary
└── history/            rounds · sweeps · timing · lineup log · graveyard · the report
```

A heads-up in the skill reads like this:

> **ab-004 · dropna removed the churners** — stage `prepare` · decision `missing_handling` · *round 3, stone `mnar_missing`, worst error 67%*
> - **Trigger:** missingness of any column differs by > 5 points between churned and not
> - **Heads-up:** `support_tickets` was blank for the customers with the most tickets — their ticket history is purged when an account closes. `dropna` removed a biased slice of churners, and the effect of support tickets came out 67% too small.
> - **Do:** report missingness per column split by outcome before dropping anything; use a missing indicator or imputation.
> - **Check:** `checks/missingness_by_outcome.py` runs after stage `prepare`

Three evidence classes, kept apart: **proven by simulation** · **reported by you** · **hypothesis only**.

<br>

## 🔬 Under the hood

Two halves, and each fact lives in exactly one:

| | **Engine** — `skilljab` CLI · Python · no AI inside | **Plugin** — Claude Code |
|---|---|---|
| does | plant the truth, inject stones, run stages, grade, sweep doses, diff plans, predict time, render the skill and the report | interview, plan ×N, judge, sabotage, analyze, explain, write antibodies |
| never | decide what a failure *means* | compute a verdict, or grade itself |

**Five blind roles.** Subagents that cannot see each other's files: **planners** (one per persona) · a **judge** that runs the lineup — *"one of these plans failed; which?"* — and is scored against planted culprits so you know how much to trust it · a **saboteur** that picks stones · a blind **analyst** that runs the pipeline with the current skill loaded · an **explainer**, the only one allowed to see what was planted.

**The funnel.** Search wide and cheap, prove narrow and expensive:

| step | technique | what it gives |
|---|---|---|
| 0 | **divergence map** — diff N plans | where the plans disagree = where uncertainty lives |
| 1 | **déjà vu** — `skilljab graveyard search` | setups of similar past failures; predict the outcome, *then* reveal |
| 2 | **blurry-friend probe** — describe a symptom badly | the model enumerates the neighbourhood; you *recognize* what you couldn't recall |
| 3 | **stones** — build, dose, run | only silent failures survive |

*Elicitation proposes; simulation disposes.* The AI can suspect anything; only a stone that breaks the miniature — or something you recognized yourself — earns a place in the skill.

<br>

## 🪨 The stones

Deliberately domain-neutral. A generic stone is enough to make the AI's own knowledge do the specialization: *"a correlated block broke PCA"* becomes *"exclude chr6:25–35 Mb before PCA"* in the explainer's hands.

| character | stone | what it does to the miniature |
|---|---|---|
| 🕰️ The Time Traveler | `target_leakage` | adds a feature computed from the outcome |
| 👻 The Ghost | `mnar_missing` | blanks the top values — missing-not-at-random |
| 👥 The Clique | `correlated_block` | near-identical copies of a feature |
| 🌊 The Drifter | `batch_shift` | a hidden batch confounded with the outcome |
| 👯 The Twin | `duplicates` | re-appends rows |
| 📈 The Spike | `outliers` | a few impossible values |
| 🌫️ The Blur | `measurement_error` | noise in a predictor (attenuation) |
| 👽 The Metric Martian | `unit_mix` | two units in one column |
| 🦎 The Long Tail | `heavy_tails` | Student-t noise |
| 🦄 The Unicorn | `rare_category` | a category level with almost no support |
| ⌨️ The Typo | `type_corruption` | `'1,234'`, `' 12 '`, `'NA'` in a numeric column |

<br>

## 🔌 Your pipeline's contract

Stages as shell commands — any language, any tool — and a last stage that writes the estimates:

```yaml
name: gwas
stages:
  - id: qc      cmd: "plink2 --bfile {in} --geno 0.02 --make-bed --out {out}"   out: qc.csv
  - id: prune   cmd: "Rscript prune.R {in} {out}"                              out: pruned.csv
  - id: fit     cmd: "python fit.py {in} {out}"                                 out: result.json
```

`result.json = {"estimates": {"beta_x1": 0.79, ...}}`, with the same names as the planted truth in `sim/spec.yaml`. Checkers are scripts called at stage boundaries — `python3 check.py <stage_output> <stage_input>` — that exit `1` or print `{"fired": true, "message": "..."}`.

Three generators ship: `tabular_regression`, `tabular_classification`, `two_group_lift` — with named features, categorical effects, and a planted intercept. Adding one is a function that returns `(DataFrame, {estimand: truth})`.

<br>

## ⚠️ Limits

- **Miniatures can lie.** Some failures only appear at scale. The timing page extrapolates and says so; treat ranges as optimistic.
- **You need a truth to plant.** Quantitative analyses, yes. Design and strategy, no — there the simulation would just be the AI's own assumptions fed back to itself.
- **Stones are stones.** The churn test proves the mechanism and its generalization; it has not yet caught a problem in a real dataset that nobody planted. That's the next test, and the one that matters most.
- **The graveyard is local.** A shared, anonymized graveyard of real past failures is the obvious next step.

<details>
<summary>Roadmap</summary>

- A genotype generator with real LD structure (the HLA region as a stone), and a counts generator for RNA-seq
- Adapters that read estimands out of common outputs (regression summaries, GWAS sumstats, DE tables) instead of a hand-written `result.json`
- The twin view on the user's *real* final figure, not a proxy
- A shared graveyard
- Snakemake / Nextflow / Makefile pipeline adapters
</details>

<br>

## 🛠️ Development

```bash
git clone https://github.com/AlsammanAlsamman/skilljab && cd skilljab
python3 -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]"
python -m pytest -q                              # 47 tests, ~35 s
claude plugin validate plugin --strict
```

```
skilljab/            engine: simulate · stones/ · inject · runner · check · project · plandiff · tree · lineup · timing · render_skill · graveyard · report · pack/
plugin/              Claude Code plugin: commands/ · agents/ · skills/skilljab-core · hooks/
examples/            churn_ai_pipeline — the test above, replayable · toy_regression — the minimal example the tests use
assets/flowchart/    the loop diagram — hand-drawn SVG in JavaScript, rendered to PNG by scripts/render_flowchart.sh
docs/DESIGN.md       the design and the reasoning behind every choice
docs/sessions/       transcripts of the design discussions
```

The thinking — the pre-mortem, the recoverability test, why generic stones beat a hand-written pitfall library, the lineup, the tricks for making an AI say *"oh yeah, I should have told you"* — is in [`docs/DESIGN.md`](docs/DESIGN.md).

<br>

<p align="center">
  <b>Alsamman M. Alsamman</b> · aalsamman100@gmail.com · <a href="https://github.com/AlsammanAlsamman">github.com/AlsammanAlsamman</a> · MIT
</p>
