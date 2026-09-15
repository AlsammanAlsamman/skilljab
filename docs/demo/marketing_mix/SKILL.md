---
name: marketing_mix-jabbed
description: Marketing-mix ROI regression, jabbed: 6 silent failures found; 5 guarded by checks, 1 (a hidden batch) declared unguardable without a source/batch column. Use whenever writing, editing, reviewing or running the marketing_mix analysis, or when the user mentions marketing_mix.
---

# marketing_mix — jabbed skill v1

This skill was **rendered by SkillJab** from `antibodies.json`. Do not edit by hand; run `/skilljab:improve` or `/skilljab:recall` instead.
Every line below traces to a round, a stone, or something the user recognized.

## Before you run: heads-ups

### proven by simulation

**ab-001 · Target leakage: a revenue-derived column left in the predictors** — stage `prepare` · _round 1, stone `target_leakage`, worst error 81%_

- **Trigger:** A numeric column other than revenue is almost a copy of revenue (e.g. an ad-platform 'attributed_revenue' or 'last_click_revenue' export field), so it dominates the fit and crushes every real channel coefficient toward zero.
- **Heads-up:** Before trusting the channel ROI numbers, make sure no column in the prepared data is secretly derived from revenue itself (platform exports sometimes bundle an 'attributed revenue', 'last-click revenue', or 'predicted revenue' field alongside the real outcome). If one slips in, the model will look like it fits great (high R2) while every channel's estimated return collapses toward zero -- the opposite of a broken pipeline, so it is easy to miss. UPDATED (round 19): a noisier leaked column (last_click_revenue, corr 0.78 with revenue) slipped past the original 0.9 correlation threshold, so the check's threshold was lowered to 0.75 -- checked against the correlation of every legitimate channel across 27 rounds (ceiling 0.64), so this stays safely clear of real channels.
- **Do:** Drop any column that is a near-duplicate or platform-computed version of the outcome before fitting; only keep genuine input/spend columns as predictors.
- **Check:** `checks/no_target_leakage.py` runs after stage(s) `prepare`

**ab-002 · Mixed units in a spend column (e.g. dollars vs thousands)** — stage `prepare` · _round 2, stone `unit_mix`, worst error 100%_

- **Trigger:** A minority of rows in a spend column are ~1000x (or 10x) the rest, as if that subset was recorded in a different unit (raw dollars instead of $k, or similar), producing a bimodal magnitude split.
- **Heads-up:** Check that every spend column is in one consistent unit across all rows. A regional export or a week's batch sometimes reports the same field in a different unit (e.g. raw dollars instead of the usual $k), and a handful of those rows become huge-variance outliers. The regression will let those rows dominate, and the affected channel's estimated return-per-dollar comes back near zero and unreliable, even though every other channel still looks fine. UPDATED (round 25): the same corruption can be injected into the already-prepared table (after the `prepare` step's own check already ran clean), not just the raw export -- so the script now scans every file path it's given and is registered at both the `prepare` and `fit` checkpoints, catching the corruption whichever point it actually lands at.
- **Do:** Find the rows with implausibly large values for that column, confirm the unit with the data source, and rescale (or exclude) them before fitting.
- **Check:** `checks/unit_mix.py` runs after stage(s) `prepare, fit`

**ab-003 · A handful of implausible revenue weeks drag the whole model** — stage `prepare` · _round 4, stone `outliers`, worst error 53%_

- **Trigger:** A small fraction of weeks have revenue OR any feature/spend column far outside the rest of the distribution (robust z-score using median/MAD far above normal), e.g. a refund reversal, duplicate transaction batch, promo-credit error, or a campaign budget-cap glitch/currency slip inflating that week's value.
- **Heads-up:** Scan revenue and every spend column for a handful of weeks that are wildly larger than the rest before trusting the coefficients. A least-squares fit cannot ignore even a few extreme weeks (about 3-4% here was enough); it lets them pull the intercept and several channel coefficients off target at once, in an uneven way that is easy to mistake for 'the model is just a bit noisy' rather than a data problem. UPDATED (round 21): the same spike stone can land on a feature column (social_spend) instead of revenue and pass through unnoticed if only revenue is scanned -- the script now checks every numeric feature column, not just the outcome.
- **Do:** Investigate the flagged weeks with the business (refunds, credits, duplicate postings, month-end corrections) and exclude or correct them before fitting; consider a robust regression if this is recurring.
- **Check:** `checks/outlier_spike.py` runs after stage(s) `prepare`

**ab-004 · An unlogged export/format change shifts one channel's baseline (undetectable from this data alone)** — stage `prepare` · _round 5, stone `batch_shift`, worst error 78%_

- **Trigger:** A batch of weeks (not tied to region, quarter, or row order) has a systematically higher/lower value for ANY channel column than the rest -- e.g. a media platform switching from net-of-fees to gross billed spend partway through the export, a discount-policy/pricing-system change applied to some weeks but not others, or a currency/tax adjustment applied to some rows but not others.
- **Heads-up:** There is currently no way to detect this from the data the pipeline receives: we tested a magnitude-ratio scan, skewness/kurtosis, grouping by region/quarter/row-order, and a 1-vs-2-component Gaussian-mixture fit on the affected column, and none of them separated the shifted rows from ordinary sampling noise, because the shift is spread across a large minority of rows and is small relative to that channel's natural spread. Confirmed twice now on two different columns (search_spend in round 5, discount_pct in round 27) -- this is a general property of the stone, not a quirk of one channel, so treat ANY channel's coefficient as potentially exposed to it. If a channel's estimated return per dollar looks off versus prior quarters with no other check firing, this silent batch/export shift is a real possibility -- ask the data source whether a reporting definition or platform changed mid-period. Detecting it would need an explicit batch id, data-source flag, export-version tag, or per-row ingestion timestamp added to the feed.
- **Do:** Add a batch/source/ingestion-date column to the export so shifts like this become checkable; in the meantime, cross-check channel spend/discount totals against the platform's or finance system's own record when a coefficient moves unexpectedly quarter over quarter.

**ab-005 · A numeric column gets mistaken for a category and shredded into hundreds of dummy columns** — stage `prepare` · _round 7, stone `type_corruption`, worst error 127%_

- **Trigger:** A numeric column (e.g. discount_pct) has whitespace, non-breaking-space padding, or blank/sentinel entries from a spreadsheet export, making pandas read it as text; the pipeline's 'one-hot encode every text column' rule then explodes it into hundreds of near-duplicate dummy columns instead of keeping it as one number.
- **Heads-up:** That channel effectively vanishes from the model -- it is not just noisy, its coefficient is completely absent from the results (discount_pct came back as null here) -- while everything else in the report still looks normal, which makes this the easiest failure to miss. Check that every column you expect to be numeric actually loaded as a number, not text, before trusting the coefficient table, especially after any spreadsheet round-trip.
- **Do:** Strip whitespace/non-breaking spaces and coerce the column to numeric (pd.to_numeric with errors handled) before deciding which columns are categorical for one-hot encoding.
- **Check:** `checks/numeric_column_exploded.py` runs after stage(s) `prepare`

**ab-006 · Fractional values in a send-count column signal injected measurement noise** — stage `prepare` · _round 9, stone `measurement_error`, worst error 54%_

- **Trigger:** email_sends (a count of thousands of emails sent) arrives with non-integer values -- a sign that continuous noise (e.g. an ESP reconciling 'queued' vs 'sent' counts, or a re-estimated send figure) has been mixed into what should be an exact count.
- **Heads-up:** This is the quiet failure: nothing crashes and R2 barely moves, but the noised channel's estimated return per dollar is pulled toward zero (classic errors-in-variables attenuation) while every other channel still reports correctly, so the report looks trustworthy at a glance. A simple sanity check -- email_sends should always be a whole number -- catches it immediately.
- **Do:** Confirm the send-count source before fitting; if there is genuine platform-level uncertainty in the count, model it explicitly (e.g. errors-in-variables regression) rather than ignoring it.
- **Check:** `checks/email_sends_not_integer.py` runs after stage(s) `prepare`

**ab-007 · Non-random missing revenue biases the whole model (rows silently dropped)** — stage `prepare` · _round 23, stone `mnar_missing`, worst error 30%_

- **Trigger:** revenue (or another column) is blank for a sizeable share of weeks, and the missingness is statistically associated with the other channel columns (e.g. missing-revenue weeks have systematically higher tv_spend/search_spend than reporting weeks) -- consistent with the outcome itself driving whether it got reported.
- **Heads-up:** The pipeline treats missing revenue as simply 'incomplete weeks' and drops them (dropna, 'complete weeks only'). If those weeks are missing because of their own value -- e.g. finance only finalizes/publishes revenue once it clears a threshold, or a region withholds an unusually high or low week for review -- the surviving weeks are a biased sample, not a random subset, and the channel coefficients (and the overall revenue picture) will be systematically off even though nothing looks broken and the row count just looks a bit smaller than expected.
- **Do:** Before dropping incomplete rows, check whether missingness correlates with the other observed columns. If it does, investigate why those specific weeks are missing (ask the data owner), and consider imputation or a missingness indicator instead of silently dropping the rows.
- **Check:** `checks/mnar_missing.py` runs after stage(s) `prepare`

**ab-008 · Negative values in a spend/discount column signal injected measurement noise** — stage `prepare` · _round 26, stone `measurement_error`, worst error 70%_

- **Trigger:** A spend, count, or discount-percentage column (tv_spend, search_spend, social_spend, email_sends, discount_pct) contains negative values -- structurally impossible in this domain, and a sign that continuous noise/jitter has been added to a column that should be bounded at zero.
- **Heads-up:** This is the same quiet failure family as round 9 (email_sends): nothing crashes and R2 barely moves, but the noised channel's estimated return per dollar is pulled toward zero (errors-in-variables attenuation) while every other channel still reports correctly, so the report looks trustworthy at a glance. This time it hit discount_pct instead of email_sends -- a simple sanity check (no spend/count/discount value should ever be negative) catches both cases and any future one.
- **Do:** Confirm the source of the noisy column before fitting; if there is genuine platform-level rounding/reconciliation uncertainty, model it explicitly (e.g. errors-in-variables regression) rather than ignoring it.
- **Check:** `checks/negative_spend_or_discount.py` runs after stage(s) `prepare`

## Checks that run at stage boundaries

- after `prepare`: `checks/no_target_leakage.py` — Target leakage: a revenue-derived column left in the predictors
- after `prepare, fit`: `checks/unit_mix.py` — Mixed units in a spend column (e.g. dollars vs thousands)
- after `prepare`: `checks/outlier_spike.py` — A handful of implausible revenue weeks drag the whole model
- after `prepare`: `checks/numeric_column_exploded.py` — A numeric column gets mistaken for a category and shredded into hundreds of dummy columns
- after `prepare`: `checks/email_sends_not_integer.py` — Fractional values in a send-count column signal injected measurement noise
- after `prepare`: `checks/mnar_missing.py` — Non-random missing revenue biases the whole model (rows silently dropped)
- after `prepare`: `checks/negative_spend_or_discount.py` — Negative values in a spend/discount column signal injected measurement noise

## How to use this skill

1. Read the heads-ups before writing or running the pipeline; apply the **Do** lines.
2. Keep the checks in place; they are the antibodies.
3. If you change the pipeline, run `/skilljab:test` again — the skill is only as current as its last clean round.
4. If you remember something odd from a past run, describe it badly to `/skilljab:recall`.

_Rendered 2026-09-15T03:29:31 by SkillJab._
