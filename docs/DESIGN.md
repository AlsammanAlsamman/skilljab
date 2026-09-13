# SkillJab — design notes

*Status: **v0.1.0 built and tested** (2026-09-13) — engine, plugin, example, 47 tests. See README.md for usage; this file keeps the reasoning. Distilled from the 2026-09-13 brainstorm — full transcript in `sessions/2026-09-13-skillaid-brainstorm.md` (working name was SkillAid for most of the session). Re-export a session with `scripts/export_session.py`.*

## One-line pitch

**Immunize an analysis by sabotaging it before it sees real data — and keep the antibodies as a skill.**

SkillJab makes the AI *prove* an analysis pipeline can recover a planted truth on a miniature dataset, then attacks that miniature with "stones" (controlled perturbations). Every silent failure — the result degrades and no check fires — forces the AI to explain why, which wakes up domain knowledge it had but wasn't applying (the HLA moment), and crystallizes it into a checker + mitigation + heads-up inside a persistent `SKILL.md`. The skill is the accumulated antibodies.

## Audience

First: people doing **data analysis and data mining** — anyone who can run methods but can't independently verify them, which in 2026 is most people using AI to write analyses. The failure mode targeted is *plausible but silently wrong* pipelines discovered only after long runs.

Later, maybe: other quantitative fields. **Not** judgment domains (design, strategy) — simulation there is circular (the AI simulating its own assumptions).

## Origin story (why this exists)

In genomics, the HLA/MHC region (chr6:25–35Mb) has dense long-range LD that breaks PCA, LD pruning, PRS, fine-mapping. The knowledge is public and old (Price et al. 2008). Users still get burned after hours of compute because nobody told them *at the moment they wrote that step*. AI assistants make it worse: they write clean, competent, wrong code. The problem is timing, not knowledge.

## Core mechanisms

1. **Pre-mortem.** The AI writes the final deliverable first (the figure, the table, the sentence in the paper), then works backwards: what would make this wrong?
2. **Recoverability test.** Generate a tiny dataset with planted known truth (effect size, clusters, lift…). Run the planned pipeline. If it can't recover a truth you planted, it's wrong before any real data. Also: reproduce a known public result before running on your own data.
3. **Miniature end-to-end run.** Whole pipeline including the final plot, on a subset. Checkers built at every stage boundary.
4. **Stones in the pipe (chaos / mutation testing for the science).** Inject generic perturbations into the miniature: correlated block, missing-not-at-random, duplicates, outliers, distribution shift, label noise, time leakage, class imbalance, mixed date formats, silently changed units, heavy tails, non-stationarity, rare category level. Half from a catalog matched to the data type, half random-dosed (unknown unknowns).
5. **Silent failures only.** A stone the pipeline handles is a pass. A stone that degrades the result with no checker firing is what gets reported. This keeps the output short enough to be read.
6. **Wake-up.** For each silent failure the AI must explain it. Generic stone → latent domain knowledge → "this is the HLA region; exclude chr6:25–35Mb before PCA."
7. **Antibodies.** Each explanation becomes: a checker script, a mitigation, a heads-up in `SKILL.md`, an entry in the history. Re-test until the round is clean; bump the skill version.
8. **Blind saboteur / analyst.** Separate contexts (Claude Code subagents). The saboteur writes `stones.json`; the engine applies it; the analyst only sees the perturbed data. The engine, not either agent, does the comparison. Otherwise the AI "knows" the stone and trivially handles it.

### Why generic stones solve the domain-density problem

A hand-written per-domain pitfall library never gets dense enough. But "a dense block of highly correlated features" is domain-neutral; when it breaks PCA in the mini-run, the LLM's own knowledge does the specialization. ~30–50 generic stones + latent model knowledge scales in a way a pitfall library doesn't.

## Elicitation tricks (how to make the AI "remember")

An LLM never forgets; it lacks the *cue*. Every trick below plants a cue. Rule: **elicitation proposes, simulation disposes** — every elicited concern becomes a targeted stone; only silent failures in the miniature run reach the user or the skill. Models confabulate when told "something went wrong here," so nothing elicited is trusted un-stoned.

- **Stone (symptom cue).** A failure in the mini-run is the strongest cue; symptom → cause is a well-trodden path. Already core.
- **Déjà vu, form 1 — predict-then-reveal.** Retrieve past cases with the same pipeline shape (user's `history/`, later a shared cross-user corpus of silent failures). Show only the setup, make the AI predict where/why it failed, then reveal. Generation + hypercorrection effects: wrong predictions stick and mark gaps → stones + antibodies.
- **Déjà vu, form 2 — prospective hindsight.** State the failure as already happened and demand specifics: "write the retraction notice," "write Reviewer 2's fatal comment," "write the Slack message after the 6-hour run." (Mitchell, Russo & Pennington 1989: ~30% more reasons than "what could go wrong.") Stronger than the pre-mortem.
- **Name the assumption.** Per step: what does it assume that the previous step didn't guarantee? (HLA = independence assumption violated.) Cheapest trick.
- **Reviewer 2 / hostile panel.** Role-shift: meanest domain reviewer, statistician, cluster admin. The helper persona is the worst at surfacing pitfalls.
- **Inversion.** Write the most plausible *wrong* pipeline a smart person would ship; diff against the real one.
- **Teach-back.** Explain the step to a new grad student including what they'll get wrong; pulls "common mistake" patterns.
- **The outsider.** Reframe as time-series / epidemiology / factory QC; cross-domain cues (autocorrelation ↔ LD).
- **Fake figure first.** Generate the plausible final plot before running; "what here would make an expert suspicious?" Twin view as elicitation.
- **One-check question.** "Run costs 6h; check one thing before go." Forces ranking; what it doesn't worry about is also signal.
- **Blurry-friend probe (differential diagnosis from a vague cue).** Describe a symptom *badly* — "slow at step 3, warned about an input parameter" — and the model must enumerate the neighborhood (window size, r² threshold, unsorted input, chr naming, dense region → HLA). Vagueness is the feature: precise cues retrieve one thing, blurry cues retrieve the cluster. Works for business/math/procedures ("finance said one input assumption was off" → seasonality, churn definition, currency, fiscal calendar). **Bidirectional:** the enumeration lets the *user* recognize what they can't recall ("that one!") — recognition beats recall. In `/skilljab:build` ask "ever seen something odd here? describe it badly." Systematize with a domain-neutral symptom grammar × stages: *slow at {step}*; *warning mentioning {input|parameter|shape|memory|convergence}*; *result looks {too clean|too good|flipped|noisy}*; *numbers changed after {rerun|reorder|subset|colleague ran it}*; *someone senior frowned at {figure|table|count}*. Candidates → targeted stones (makes the saboteur aim instead of spray). Blur is a dose: sweet spot ≈ symptom + location + one attribute. Two evidence classes in SKILL.md, labelled separately: *simulated* (stone proved it) vs *user-recognized* (real, not yet reproduced).
- **Blind disagreement.** Two fresh contexts, different framings; disagreement = low certainty = aim stones there.

Long-term: the shared graveyard of real past failures is the only déjà vu that isn't manufactured.

### Multi-plan tricks (comparison — information no single plan contains)

- **Divergence map.** N sessions plan independently; diff the plans. Consensus = low information; *divergence* (A prunes at r²=0.2, B at 0.5, C excludes MHC first, D never mentions it) = decision points = where to aim probes and stones. Picks the stage before any `history/` exists. **Diversity must be forced** — same model + same prompt collapses to the same popular plan. Vary persona (statistician / domain expert / cluster admin), constraint ("1h compute", "R only", "don't trust the reference panel"), or outsider framing.
- **The lineup.** A judge session reads all plans and is told "one of these failed — which and why?" Forced ranking: it must find the weakest point in every plan and compare. Refinements: (a) run both ways — also "one worked far better — which?"; the asymmetry shows what it thinks matters; (b) **plant a known culprit** — include a plan already proven (by stones) to have a silent failure, unannounced; whether the judge catches it calibrates how much to trust its rankings. Vaccinates the judge itself. Without (b) the lineup is confident confabulation.
- **Decision tree with evidence on edges.** Merge the N plans into a tree: node = decision, branch = a choice some session made, edge carries evidence (votes, lineup prediction, stone results, user-recognized). `SKILL.md` becomes "at this node choose X because Y failed under stone Z in round 3" — a skill that explains itself. Same structure feeds the report's lineage view. Over rounds it's a tournament: survivors' choices → defaults, losers' failures → antibodies. Keep N = 3–5; prune with divergence + lineup before stoning (stoning is N× compute).

Prior art: Delphi method × witness lineup, applied to plans. The planted-culprit calibration is the unseen part.

### The funnel (how a `/skilljab:test` round should be ordered)

Not "all stones at every stage." Techniques at decreasing width:
0. **Divergence map** (when several plans exist) marks the decision points.
1. **Déjà vu** picks the *stage* — which neighborhoods are worth looking at (past cases with this shape).
2. **Blurry-friend probe** lists the *suspects* at that stage — one sentence → six candidates, cheap.
3. **Stone** convicts *one* — build, dose, run on the miniature; only silent failures survive.

Search wide and cheap, prove narrow and expensive. Elicitation aims the saboteur; simulation is the only thing allowed to write antibodies.

**Open question — seeding déjà vu before any user has a `history/`:** (a) hand-seed a small graveyard from the author's own scars (GWAS / data mining), (b) let the AI synthesize past cases (weak, immediate), (c) skip in v1 and grow from real runs. Leaning (a) + (c).

## Architecture (refined 2026-09-13 — built as described; deviations noted below)

**Python only for v1.** SkillJab runs miniatures; the heavy compute is the user's pipeline. C++/Rust perturbation core only if profiling ever demands it.

### The split

| Layer | Does | Never does |
|---|---|---|
| **Engine** (Python CLI, `pip install skilljab`) | simulate, inject, run, measure, check, diff plans, merge tree, score lineup, predict time, render report + SKILL.md, store history | call an LLM; decide what a failure *means* |
| **Plugin** (Claude Code) | interview, plan ×N, elicit, judge, sabotage, analyze blind, explain, write antibodies | touch data; compute a verdict; grade itself |
| **Per-pipeline artifact** (user's repo) | `SKILL.md` + antibodies + tree + checks + spec + history | — |

Shared **knowledge pack** shipped with the plugin: stone catalog, symptom grammar, diversity packs (personas / constraints / outsider framings), seed graveyard.

Rule: the engine grades, the AI reasons. Any fact that could come from either comes from the engine.

### Contracts (JSON between the two sides)

```
plan.json        stages[] {id, name, cmd, lang, inputs, outputs, params,
                            assumptions[], decisions[] {id, choice, alternatives[]}}
tree.json        nodes[] {decision, branches[] {choice, votes, evidence[]}}
spec.yaml        generator, planted_truth, sizes:[1x,3x,10x], seed
truth.json       what was planted
candidates.json  [{hypothesis, stage, source: blurry|dejavu|reviewer2|..., proposed_stone}]
stones.json      [{stone_id, stage, dose, seed}]            <- analyst never sees this
run.json         per stage: outputs, time, peak_mem, checker results, log tail
verdict.json     per stone: error_vs_truth, checker_fired, downstream_error[],
                  class: caught|silent|harmless, time_impact
lineup.json      judge picks + planted_culprit + hit/miss
antibodies.json  [{id, node, trigger, check, mitigation, headsup,
                   evidence: simulated|user_recognized|elicited_unverified,
                   provenance: {round, stone, trick}}]
graveyard/*.json {shape_signature, stage, failure, explanation}   (anonymized)
```

`antibodies.json` is the source; `SKILL.md` is **rendered** from it by the engine (never hand-edited). Every line in the skill traces to a round, a stone, or a user's "that one."

### Roles (Claude Code subagents, separate contexts)

- **planner ×N** — each gets a different diversity pack; never sees the other plans.
- **judge** — sees all plans, runs the lineup; never sees stone results (so it can be calibrated).
- **saboteur** — sees plan + candidates + catalog; picks and doses stones.
- **analyst** — sees only the perturbed data path and the current `SKILL.md`; runs the pipeline.
- **explainer** — sees the engine's verdict; does the wake-up; writes antibodies.

Blindness is enforced by which files each role is handed, not by prompting.

### Commands (lifecycle order)

```
/skilljab:build     interview -> planner xN -> engine: diff -> divergence map
                    -> judge: lineup -> merged plan + tree v0
                    -> elicitation pass on decision points -> candidates
                    -> spec.yaml -> engine: simulate -> clean run at 3 sizes
                    -> engine: recovery proof (STOP if it fails)
                    -> antibodies v0 (named assumptions -> baseline checks) -> SKILL.md v0

/skilljab:recall    blurry-friend interview on demand ("describe it badly")
                    -> candidates; user-recognized ones -> antibodies directly

/skilljab:test      funnel: divergence + deja vu pick stages -> blurry probe -> candidates
                    -> saboteur: stones (targeted + random) -> engine: inject
                    -> analyst: blind run -> engine: check -> verdict.json
                    -> report (silent failures only)

/skilljab:improve   explainer: per silent failure -> antibody + tree-edge evidence
                    -> engine: render SKILL.md, bump version
                    -> re-run test until clean -> graveyard entry

/skilljab:jab       test + improve looped until clean (the whole vaccine)
/skilljab:report    render the crash-test report from history/
```

**Hook — "not jabbed":** before the real pipeline runs, warn if the last round wasn't clean or the pipeline changed since. Ignorable; exists so nobody runs the 6-hour job on a stale skill.

### Running the user's pipeline

`pipeline.yaml` — stages as commands with inputs/outputs (a deliberately tiny Snakemake). Language-agnostic: C, R, Python, plink, anything with a CLI. Checkers are Python scripts the runner calls at stage boundaries with that stage's outputs. Adapters for Snakemake / Nextflow / Makefile later; v1 = "give me the stage commands."

```yaml
stages:
  - id: qc      cmd: "plink2 --bfile {in} --geno 0.02 --out {out}"
  - id: prune   cmd: "Rscript prune.R {in} {out}"
  - id: pca     cmd: "python pca.py {in} {out}"
```

### Per-pipeline artifact

```
.claude/skills/<pipeline>/
├── SKILL.md              rendered — do not hand-edit
├── antibodies.json       source of truth
├── tree.json             decisions + evidence on edges
├── checks/               generated checkers
├── pipeline.yaml
├── sim/spec.yaml
└── history/
    └── round-003/        plans/, candidates.json, stones.json, run.json,
                          verdict.json, lineup.json, report.html
```

### Repo layout

```
skilljab/
├── engine/        cli.py simulate.py inject.py runner.py check.py plandiff.py
│                  tree.py lineup.py timing.py render_skill.py report/ (JS assets)
├── plugin/        .claude-plugin/plugin.json
│                  commands/ build.md recall.md test.md improve.md jab.md report.md
│                  agents/   planner.md judge.md saboteur.md analyst.md explainer.md
│                  skills/skilljab-core/SKILL.md
│                  hooks/hooks.json            (not-jabbed gate)
└── pack/          stones/catalog.yaml + modules, symptoms.yaml, diversity/, graveyard/seed/
```

### As built (v0.1.0) — deviations from the plan above
- Stones perturb the *input* by default; `after_stage` lands one on an intermediate CSV so stage attribution is real. Non-CSV intermediates cannot receive stones yet.
- Timing: needs ≥2 sizes, prefers 3; predictions are clamped to the slowest measured run; `low_confidence` flag when only 2 sizes.
- `pipeline_hash` covers `pipeline.yaml` + scripts in its dir (hidden dirs and `history/` excluded) and is refreshed at **baseline**, so "pipeline changed" means "changed since the clean-recovery proof".
- The twin view is the proxy version (recovered estimate vs planted, per estimand, driven by sweeps). Real-figure capture is not built.
- Hook is `PreToolUse` on Bash: adds a warning as `additionalContext` when a command mentions a jabbed pipeline's scripts and the skill is stale. Never blocks.
- Verdict classes: crashed · silent · caught · false_alarm · harmless. Only silent/crashed count against `jabbed`.

### The churn demo (2026-09-13) — first real test
`examples/churn_ai_pipeline/`: the pipeline Claude writes for "build a churn model, which factors matter" (dropna → get_dummies → logistic regression on everything). Clean recovery passes (AUC 0.73). Ten stones, one per round: **8 silent failures** (leak, numeric-as-text one-hot explosion, MNAR on support tickets, cents/dollars, hidden batch, outliers, collinear copies, noisy tenure); 2 harmless (duplicates, rare level). Six antibody checkers written; re-test: 6 caught, 2 remain silent by nature (hidden batch, measurement error) — the skill says which columns to ask for. Engine changes this forced: named features + categorical effects in the simulator, checkers receive the stage input as argv[2], outcome-aware stones, batch_shift preserves prevalence on binary outcomes, type_corruption copy bug, absolute tolerance is a floor (spec must set it below the smallest coefficient), sweep "knee" = first degradation (silent_from separately), shared checkers deduped. Replay: `run_demo.sh` (~4 min). Report + skill copies in `docs/demo/churn/`.

**Hold-out (rounds 21–30, same day):** ten perturbations the checkers were never written for. First pass: 5 caught, 1 false alarm, 2 silent (a *very noisy* leak — leak threshold corr>0.9/AUC>0.95 too strict; cents/dollars introduced between stages — no guard at `train`), 2 engine crashes (stones on int64 columns). Fixes: leak check AUC>0.8 (clean features top out ~0.63, a model-wrecking leak sits ~0.89); antibody checks may declare `stages: [prepare, train]`; checkers tolerate a JSON stage output; five stones promote int columns to float. Second pass: 6 caught, 3 false alarm (check fired on a genuinely bad column, estimates survived that seed), 1 silent (the declared-unguardable batch). This is the evidence that antibodies generalize beyond the stone they were written for — and that the loop finds holes in its own defenses.

### Open (deliberately)

- `spec.yaml` generators: hand-written per data type, or AI-drafted + engine-validated (planted truth must be recoverable in a clean run)? Leaning AI-drafted + validated.
- Graveyard sharing: local only in v1; cross-user needs anonymization + consent.
- Twin view real-figure capture (see Report) — still the biggest report decision.

## The report (JavaScript, self-contained HTML, JSON embedded, no server)

**Principle:** show nothing the user could draw themselves. A flowchart shows structure they already know; the simulation's only new output is *behavior under stress*.

**Data:** dose sweeps (each stone at 4–6 doses) produce a fragility tensor:
`(stage, stone, dose) → error vs planted truth, checker fired?, downstream error per stage, time, memory`.
Python computes; JS only paints.

**Frame: a crash test.** Dummies, impact points, star ratings, slow-motion replay.

- **Top of page:** the **twin result** — the user's real final figure (fallback: recovered parameter vs planted) with a scrub slider morphing clean → stoned; red band where no checker would fire. Plus one sentence: *"at 8% missing-not-at-random your effect estimate flips sign and nothing warns you."*
- **Star rating per stage** — where it's weak, in 2 seconds.
- **Stones as characters** — the Ghost (missingness), the Clique (correlated block), the Twin (duplicates), the Time Traveler (leakage), the Drifter (shift). Memorable, not silly.
- **Breaking-point curves** — per stage, dose vs error; the knee is the fragility. Drag the dose, the twin updates. Answers "how much missingness can I survive?" with a number.
- **Fragility matrix** — stage × stone, color = worst error, border = caught / silent / harmless. Click → curve + twin. Second dimension: slowdown.
- **Propagation ribbons** — a stone hits stage k; ribbon width = error downstream. Shows which stages amplify vs absorb.
- **Vaccination card** — rounds × stones, cells flipping red → green with the skill version at each flip. This is "how the skill moved."

**Predicted time per step** — run each stage at 3 miniature sizes, fit the scaling law (linear / n log n / quadratic / flat), extrapolate to real N *as a range*. Show: cost of each silent failure ("you'd have found this after ~6h 20m"), stones that break the schedule not the result, where to place checkers (just before expensive stages), superlinear warnings, predicted peak memory vs machine RAM. Label I/O-bound / external-tool stages "measured, low confidence"; memory cliffs are binary — say when within 2× of the limit; parallel stages: per-core, user enters core count.

## Naming

**Chosen: SkillJab** (decided 2026-09-13). A *jab* is both a vaccine shot (small deliberate dose of the threat so you build immunity) and a quick boxing punch (a sparring partner's hit that finds your openings). Both map directly onto the mechanism; it's a verb ("jab it before you run it"); it's playful, matching the crash-test report tone.

Availability check on 2026-09-13: PyPI `skilljab` free, npm `skilljab` free, GitHub user `skilljab` free, zero GitHub repos matching, no DNS on skilljab.com/.io/.dev/.ai/.app. **To do: register the GitHub org + PyPI name.**

Rejected:
- **SkillDrill** — liked, but SkillDrill.ai is a live company with mail configured, skilldrill.io/.com/.dev/.app all in use, 67 GitHub repos. Collision risk too high.
- **SkillBee** (original folder name) — checked 2026-09-13: npm `skillbee` taken by a "skill manager, catalog, and deployment toolkit for AI coding CLIs" (v1.0.0, May 2026 — same shelf as this tool), GitHub org `skillbee` taken since 2019, skillbee.com is a live job-vacancy site, skillbee.ai registered, 76 GitHub repos. Not usable.
- **SkillAid** — working name during the brainstorm; fine, but SkillJab carries the mechanism better.
- Others considered: SkillGym, SkillProof, SkillStrainer, FireDrill, Achilles, Strain, Grit, Sting.

## Icon / mascot

`assets/icon/skilljab-mascot-v1.jpeg` (Gemini, 2026-09-13): a winking syringe wearing a doctor's head mirror and one red boxing glove, jabbing a small bar chart. Chosen because it shows both meanings of "jab" (shot + punch), the wink says "painless," and the chart says "data." Sticker style, thick outlines, light-blue background.

To do before use: transparent-background PNG, a cropped head-only version for the 16–32 px favicon, and a monochrome variant for terminal/dark themes. The bar chart in v1 is slightly smudged at the top-left — regenerate or clean up when making the final.

## Innovation assessment (honest)

**Not new:** fake-data simulation with planted truth (Gelman's Bayesian workflow, SBC); chaos data engineering (infra failures, not science); mutation/metamorphic testing; data validation (Great Expectations, Deepchecks); LLM-agent robustness benchmarks (test the AI).

**Not found anywhere:**
1. Sabotage used to *elicit latent domain knowledge from the model* and write it down — direction reversed from "test the AI" to "extract from the AI."
2. Output is a persistent, versioned, shareable skill (antibodies), not a pass/fail.
3. Dose-response fragility of an analysis *conclusion*, with the twin-result view.
4. Blind saboteur/analyst as a design principle for AI-driven analysis.

The defensible core is 1 + 2. If it becomes "chaos testing for pandas with a nice report," it loses on maturity to existing tools. Keep skill-as-antibodies central.

## Risks / open questions

- **Stones must bite** in a small miniature (a 20-SNP LD block in 10k SNPs may not move PCA). Dosing is a design problem; prototype this first — if stones don't bite, nothing else works.
- **Miniatures can lie** — some problems only appear at scale (memory, rare-variant counts, convergence). The report must state which pitfalls the miniature can't catch.
- **Warning fatigue** — only silent failures get reported.
- **Twin view:** render the user's real plot (powerful, fiddly — must capture and re-run their figure code) or a generic proxy (always works, less visceral)? Aim: real when possible, proxy fallback. Biggest engineering decision in the report.
- **Domain seeds** (generators, known public results) are 80% of the work; the engine is 20%.
- Dropped from v1: performance / language-choice optimization (C, R, Python routing). Wrong answers burn people, not slow ones.

## Cheapest first experiment (before writing any real code)

Take one small pipeline you already trust. Session A plants three stones in its input without telling you which. Fresh session B runs the pipeline and reports. Does B notice on its own, only when asked "what could be wrong?", or never? That single experiment measures how real the wake-up effect is.
