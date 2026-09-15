# Marketing-mix ROI — the live test of the explainer

*Second domain, and the first time the wake-up step ran blind.* Everything in this folder was produced on 2026-09-15 by the engine plus a **fresh explainer agent** that had no access to the design discussion, the churn example, or any antibody written before. Its log is in [`EXPLAINER_LOG.md`](EXPLAINER_LOG.md), untouched; the checkers in [`checks/`](checks/) are the files it wrote.

Nothing here is about biology. That is deliberate — SkillJab is for any analysis with a number at the end.

## The prompt

> *"Here's our weekly marketing data — one row per region per week: spend on TV, paid search, social and email, the discount we ran, the region and the quarter, and the revenue that week. Build a model that tells me which channels actually drive revenue and what the return per dollar is for each one."*

Claude's pipeline ([`prepare.py`](prepare.py) → [`fit.py`](fit.py)): drop incomplete weeks, one-hot the region and quarter, fit a linear regression of revenue on everything, report each channel's coefficient as return per dollar. Clean, idiomatic, the thing a marketing analyst would ship.

**The planted truth** ([`spec.yaml`](spec.yaml)): search $4.00 per $1, TV $2.50, social $1.50, email $0.50, and $3k per point of discount. On clean data the pipeline recovers all five (R² 0.78, ranking right). Nothing looks wrong.

## Rounds 1–9: the pipeline as the AI wrote it

| what a real marketing table does | what the pipeline reported | warned? |
|---|---|:---:|
| the attribution tool's `attributed_revenue` column in the feed | R² 0.94; every channel's ROI cut by 70–80% (search $4.00 → $1.17) | ❌ |
| one region reports TV spend in dollars, not $k | TV's return $2.50 → $0.0004 — "TV does nothing" | ❌ |
| a few Black-Friday-scale revenue weeks (3.6%) | R² 0.08; four of five coefficients off, discount's ROI overstated 33% | ❌ |
| a hidden market: pricier search *and* higher revenue, unlabelled | search's return $4.00 → $7.11 — the budget would move to search | ❌ |
| discount exported with stray whitespace | `get_dummies` shredded it into 576 columns; discount coefficient **`null`** | ❌ |
| email counts from a noisy ESP log | email's return 54% too small | ❌ |
| agency never reports its biggest social weeks | fine | harmless |
| search spend + clicks + impressions | fine | harmless |
| promo-calendar join duplicated weeks | fine (point estimates) | harmless |

**Six of nine silent**, R² healthy in five of them. Same shape as the churn test, different field.

## The explainer, blind — first pass

The agent was given the plugin's own [`explainer.md`](../../plugin/agents/explainer.md) instructions, the folder, and the round numbers. It had to write its two "wake-up" sentences **before** reading the stone's hint. Verbatim, from the log:

- *Leak* — "an ad-platform export (Google/Meta attribution) tacks on an `attributed_revenue` field … really next week's outcome wearing a feature's clothes."
- *Unit mix* — "a media-buying platform export where some rows report raw dollars and others report thousands of dollars (a '$k' unit that someone forgot to normalize for one region)."
- *Outliers* — "a week where a refund reversal, a promo credit, or a duplicate transaction batch is added into that week's revenue total."
- *Hidden batch* — "Google Ads switching from net-of-fees to gross billed spend, or a currency/tax adjustment applied to about half the weeks."
- *Type corruption* — "someone typing '10%' instead of '10', a stray currency symbol, a locale using commas instead of decimal points."
- *Measurement error* — "an ESP rounding or batching send counts … classic errors-in-variables: attenuation bias on that channel only."

Every one was right before the hint. Then it wrote five checkers, tested each against the round's data *and* the clean baseline, and for the hidden batch it tried four detection methods (magnitude ratio, skew/kurtosis, grouping by region/quarter/row order, 1-vs-2 Gaussian mixture), found none that separated the shift from sampling noise, and **declared it unguardable** — naming the column the feed would need (a batch id, source flag, or ingestion timestamp).

Same nine stones again (rounds 10–18): **5 caught, 1 silent** — the declared one.

## Hold-out 1: nine perturbations it was never shown

| perturbation | first pass | after second pass |
|---|:---:|:---:|
| a noisier leak (`last_click_revenue`, 0.8 sd) | ❌ silent | ✅ |
| search spend ×100 for some rows | ✅ | ✅ |
| impossible *social spend* values (not revenue) | ❌ silent | ✅ |
| TV spend exported as text | ✅ | ✅ |
| revenue missing for the best weeks | ❌ silent | ✅ |
| TV GRPs + TV impressions copies | harmless | harmless |
| $k mix-up introduced *after* `prepare` | ❌ silent | ✅ |
| noisy discount (not a count, so the integer check has no foothold) | ❌ silent | ✅ |
| hidden batch on discount | ❌ silent | ❌ declared unguardable |

First pass: **2 caught, 6 silent.** The first-pass antibodies were narrow — a leak threshold of 0.9, an outlier scan on `revenue` only, a "must be an integer" check tied to one column, and everything registered at the `prepare` checkpoint only. That is a real finding about how an AI writes checkers, and it is the reason the plugin's `improve` loop re-tests and sends the explainer back.

**Second pass** (same agent, given only the verdicts). Still wake-up before hint, still tested against baseline and now against all 27 rounds for false alarms. It:
- measured the highest correlation any *legitimate* column ever reached (0.64) and lowered the leak threshold to 0.75;
- generalized the outlier scan from `revenue` to every numeric column;
- found the **timing gap** — a stone landing after `prepare` is invisible to a checker that runs at `prepare` — and registered `unit_mix.py` at both `prepare` and `fit`;
- built an observable-footprint test for outcome MNAR (missing-revenue weeks have ~1 sd higher spend than reporting weeks) that does *not* fire on the harmless social-spend missingness;
- generalized "counts are integers" into "spend and discount cannot be negative";
- re-ran its four tests on the discount batch, got the same answer, and updated the unguardable antibody to say *any channel* rather than adding a duplicate.

Hold-out 1 again (rounds 28–36): **7 caught, 1 harmless, 1 silent** (declared).

## Hold-out 2: never seen by either pass

| perturbation | result |
|---|:---:|
| a *very* noisy leak (`conversion_rate`, 1.2 sd) — social's ROI 32% off | ❌ silent |
| revenue spikes introduced *after* `prepare` | ❌ silent |
| heavy-tailed revenue noise | ✅ in the live run · ❌ in the replay (seed-dependent; social/email 30–49% off) |
| email sends ×10 for some rows (small factor) | ✅ |
| revenue itself exported as text | ✅ |
| search spend missing for the biggest weeks | false alarm — check fired on a genuinely blanked column; the estimates survived |

**3 caught, 1 false alarm, 2 silent** (3 silent in the replay). The two misses say something precise: the explainer learned the timing lesson for `unit_mix.py` but **did not generalize it to the other checkers** — `outlier_spike.py` is still registered at `prepare` only, so revenue spikes landing at `fit` sail through. And a leak at 1.2 sd correlates below any threshold that stays clear of legitimate columns; at that noise it is barely a leak, and it moved one coefficient by 32%.

## What this shows, and what it does not

**Shown, live and blind:**
1. The wake-up is real. A fresh agent with no hints named the domain mechanism for six of six silent failures before being told what the stone was.
2. It writes checkers that work, tests them, and — the part that matters most — refuses to write one when the data cannot support it, and says what data would.
3. The loop finds holes in its own defences: hold-out 1 went from 2/9 to 7/9 caught in one `improve` cycle, and hold-out 2 exposed a new, specific hole (checkpoint registration) for the next cycle.

**Not shown:**
- Anything about a real dataset nobody planted anything in. Still the test that matters most.
- The saboteur and analyst agents were not part of this run; the stones were chosen by hand and the pipeline was run by the engine. Only the explainer was tested live.
- One antibody (`email_sends_not_integer.py`) detects the simulation's fingerprint — fractional counts — more than the real-world failure (a noisy ESP log would still report whole numbers). The second pass added a bound check beside it (`negative_spend_or_discount.py`) that is not tied to the stone; the integer check stays as written, because that is what was written.

## Replay

```bash
./run_demo.sh     # ~3.5 min: baseline → 9 stones → the explainer's final antibodies → re-test → hold-out 1 → hold-out 2 → sweeps → report
open .claude/skills/marketing_mix/history/report.html
cat  .claude/skills/marketing_mix/SKILL.md
```

The replay installs the *final* antibodies, so hold-out 1 is caught on the first try there; the two-pass history above is in `EXPLAINER_LOG.md`. Rendered copies of the report and the skill are in [`docs/demo/marketing_mix/`](../../docs/demo/marketing_mix/).

## Files

```
PROMPT.md            the request as a user would type it
pipeline.yaml        two stages: prepare → fit
prepare.py fit.py    the pipeline Claude writes for that prompt
spec.yaml            the miniature: 600 region-weeks, planted return per dollar
checks/              the seven checkers the explainer wrote (final versions)
antibodies/          the eight antibodies, one file each, in the order they were added
graveyard.json       the twelve graveyard entries it filed
EXPLAINER_LOG.md     its verbatim log — wake-up before hint, hint, revision, test results
run_demo.sh          replays everything
```
