---
name: churn-jabbed
description: Churn model (logistic regression on a customer table), jabbed: 8 silent failures found, 6 now guarded by checks, 2 need data the table does not carry. Use whenever writing, editing, reviewing or running the churn analysis, or when the user mentions churn.
---

# churn — jabbed skill v1

This skill was **rendered by SkillJab** from `antibodies.json`. Do not edit by hand; run `/skilljab:improve` or `/skilljab:recall` instead.
Every line below traces to a round, a stone, or something the user recognized.

## Before you run: heads-ups

### proven by simulation

**ab-001 · A hidden batch with its own churn rate** — stage `train` · decision `feature_selection` · _round 6, stone `batch_shift`, worst error 167%_

- **Trigger:** no cheap check from the data alone — needs a source/region/channel column
- **Heads-up:** One acquisition channel had both higher charges and a much higher churn rate. With no channel column in the model, the price coefficient absorbed the channel effect: every coefficient was off by ~100%. Nothing in the data as delivered can reveal this — the batch label is missing by construction.
- **Do:** Ask for the provenance columns (region, channel, plate, site, export batch) and include them; compare the churn rate per source before modelling. Until then, treat coefficients as confounded.

**ab-002 · Three columns that are the same column** — stage `prepare` · decision `feature_selection` · _round 9, stone `correlated_block`, worst error 127%_

- **Trigger:** any predictor pair with |corr| > 0.9
- **Heads-up:** The table carried monthly_charges together with derived copies (charges with tax, annualised charges, last-invoice amount). The model split the price effect arbitrarily across them; the reported coefficient for monthly_charges was 127% off and its sign is not stable between runs.
- **Do:** Keep one representative per group of near-duplicate predictors; check pairwise correlations before fitting.
- **Check:** `checks/collinear_predictors.py` runs after stage `prepare`

**ab-003 · Tenure is measured with noise** — stage `train` · decision `feature_selection` · _round 10, stone `measurement_error`, worst error 70%_

- **Trigger:** no check from the data alone — needs a gold-standard comparison
- **Heads-up:** tenure_months as recorded (derived from a first-invoice date) disagrees with true tenure by about a standard deviation. Classical measurement error attenuates the coefficient toward zero: the tenure effect came out 70% too small, and the report would rank it below factors it actually beats.
- **Do:** Validate derived fields against a source of truth on a sample; if noise is known, correct for attenuation or say the effect is a lower bound.

**ab-004 · dropna removed the churners** — stage `prepare` · decision `missing_handling` · _round 3, stone `mnar_missing`, worst error 67%_

- **Trigger:** missingness of any column differs by > 5 points between churned and not, or the stage drops > 5% of rows
- **Heads-up:** support_tickets was blank for the customers with the most tickets — because their ticket history is purged when an account closes. dropna therefore removed a biased slice of churners, and the effect of support tickets on churn came out 67% too small. Missingness that depends on the outcome is the norm in operational data, not the exception.
- **Do:** Report missingness per column split by outcome before dropping anything; use a missing indicator or imputation; never complete-case by default.
- **Check:** `checks/missingness_by_outcome.py` runs after stage `prepare`

**ab-005 · A few impossible bills** — stage `prepare` · decision `encoding` · _round 8, stone `outliers`, worst error 90%_

- **Trigger:** any value > 8 MAD from the column median
- **Heads-up:** ~50 rows had monthly_charges around ±$800 (a decimal slip). Logistic regression is not robust to them: the charges coefficient was off by 90%.
- **Do:** Range assertions at load; winsorize or drop documented impossible values; report how many.
- **Check:** `checks/scale_and_outliers.py` runs after stage `prepare`

**ab-006 · A column that already knows the answer** — stage `prepare` · decision `feature_selection` · _round 1, stone `target_leakage`, worst error 5767%_

- **Trigger:** a predictor with |corr| > 0.9 or single-feature AUC > 0.95 against churned
- **Heads-up:** The model swallowed a column named churn_score_v1 — a score from an earlier model, i.e. a column computed from the outcome. AUC jumped to ~1.0 and every real driver (tenure, tickets, contract) shrank toward zero: the report would have said 'nothing matters except the score'. Customer tables are full of these: retention_offer_sent, refund_issued, account_status, days_since_cancellation — all populated after the customer decided.
- **Do:** Whitelist predictors that existed before the churn decision; never 'use all columns'. Reject any feature whose single-feature AUC > 0.95.
- **Check:** `checks/no_leaky_columns.py` runs after stage `prepare`

**ab-007 · A number that arrived as text** — stage `prepare` · decision `encoding` · _round 2, stone `type_corruption`, worst error 728%_

- **Trigger:** one prefix spawned > 20 dummy columns, or prepared columns > 4x input columns
- **Heads-up:** monthly_charges came from a spreadsheet export with a few values like '1,234.50' and ' 89.9 '. pandas read the whole column as text, and get_dummies then one-hot encoded every distinct charge into ~1,400 columns. The model still ran, the coefficient for monthly_charges simply vanished, and every other coefficient was off by 2–7x.
- **Do:** Assert dtypes on load (pd.to_numeric with errors='raise' on known numeric columns); encode only an explicit list of categoricals with fixed levels, never 'every object column'.
- **Check:** `checks/dummy_explosion.py` runs after stage `prepare`

**ab-008 · Cents and dollars in the same column** — stage `prepare` · decision `encoding` · _round 5, stone `unit_mix`, worst error 100%_

- **Trigger:** |values| jump > 8x between neighbouring upper quantiles of a numeric column
- **Heads-up:** 15% of monthly_charges were recorded in cents (one billing region's export). The coefficient for charges collapsed to ~0 — the model concluded that price does not affect churn. No error, no warning, a clean AUC.
- **Do:** Assert a plausible range per numeric column at load; plot the distribution per data source before modelling.
- **Check:** `checks/scale_and_outliers.py` runs after stage `prepare`

## Checks that run at stage boundaries

- after `prepare`: `checks/collinear_predictors.py` — Three columns that are the same column
- after `prepare`: `checks/missingness_by_outcome.py` — dropna removed the churners
- after `prepare`: `checks/scale_and_outliers.py` — A few impossible bills
- after `prepare`: `checks/no_leaky_columns.py` — A column that already knows the answer
- after `prepare`: `checks/dummy_explosion.py` — A number that arrived as text
- after `prepare`: `checks/scale_and_outliers.py` — Cents and dollars in the same column

## Decisions and what the evidence says

- **What to do with incomplete rows?**
  - `dropna` — 1 vote(s), status *rejected*; evidence: stone:silent
  - `impute` — 1 vote(s), status *open*
  - `missing-indicator + report missingness by outcome` — 1 vote(s), status *default*; evidence: stone:caught
- **Which columns enter the model?**
  - `all columns` — 1 vote(s), status *rejected*; evidence: stone:silent
  - `drop post-outcome fields` — 1 vote(s), status *open*
  - `whitelist` — 1 vote(s), status *default*; evidence: stone:caught
- **How to encode categoricals?**
  - `get_dummies drop_first` — 1 vote(s), status *rejected*; evidence: stone:silent
  - `explicit levels` — 2 vote(s), status *default*; evidence: stone:caught
- **Check for duplicated customers?**
  - `no` — 1 vote(s), status *open*; evidence: stone:harmless
  - `dedupe on customer_id` — 2 vote(s), status *open*

## Judge calibration

Lineup hit rate: 1/1 (100%). Trust the judge's rankings accordingly.

## How to use this skill

1. Read the heads-ups before writing or running the pipeline; apply the **Do** lines.
2. Keep the checks in place; they are the antibodies.
3. If you change the pipeline, run `/skilljab:test` again — the skill is only as current as its last clean round.
4. If you remember something odd from a past run, describe it badly to `/skilljab:recall`.

_Rendered 2026-09-13T06:37:45 by SkillJab._
