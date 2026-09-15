# Verbatim log written by the explainer agent during the live test of 2026-09-15 (see README.md).
# Nothing here was edited afterwards; the checker files in checks/ are the ones it wrote.

# Explainer log — marketing_mix

Summary: 6 silent rounds (1,2,4,5,7,9) explained. 5 got working checkers (fire on their round, not on baseline). Round 5 (batch_shift) genuinely undetectable from this data -- documented as headsup only, no checker. Skill version bumped 0 -> 1.


## Round 1 — stone: target_leakage, dose {noise_sd: 0.3, name: "attributed_revenue"}

### Wake-up sentences (written BEFORE reading hint)
In weekly marketing reporting, an "attributed_revenue" column is exactly the kind of field an ad-platform export (Google/Meta attribution) tacks onto a feed — it's revenue the platform itself already credited to campaigns, so it is really next week's outcome wearing a feature's clothes. If prepare.py or fit.py naively includes every numeric column as a regressor, this attributed-revenue field — being a near-copy of the true `revenue` target plus a little noise — would dominate the fit and crush all the real channel coefficients toward zero, exactly the "everything looks tiny" pattern in the verdict.

### Hint (read AFTER wake-up)
{
  "symptom": "one feature predicts the outcome almost perfectly; all other effects shrink toward zero",
  "wakeup_hint": "a column computed from the outcome, or from the future, leaked into the predictors"
}

### Revised explanation
Confirmed: `attributed_revenue` is a near-copy of `revenue` (corr 0.96 vs baseline max 0.62) accidentally left in the feed — the kind of "platform-attributed revenue" column an ads export bundles in alongside the real outcome. Because prepare.py keeps every numeric column, the regression leans on this near-duplicate target and every real channel coefficient collapses toward zero (all five betas degraded, worst_rel_err 0.81). The fix is a leakage check on the prepared data: flag any non-outcome numeric column whose correlation with revenue exceeds a safe threshold.

### Checker
File: checks/no_target_leakage.py — computes correlation of every non-`revenue` numeric column against `revenue` in the stage output; fires if any |corr| > 0.9.
Tested: fires on round-001 work/prepared.csv (attributed_revenue corr = 0.961); does NOT fire on baseline work/prepared.csv (max |corr| = 0.619, tv_spend).

## Round 2 — stone: unit_mix, dose {frac: 0.175, factor: 1000, col: "tv_spend"}

### Wake-up sentences (written BEFORE reading hint)
In weekly marketing spend feeds, `tv_spend` is exactly the kind of column that gets pulled from a media-buying platform export where some rows report raw dollars and others report thousands of dollars (a "$k" unit that someone forgot to normalize for one region or one week's batch) -- so a subset of rows end up 1000x too large. If ~17.5% of tv_spend values are inflated 1000x, those rows become enormous-variance outliers in the regression's design matrix, which would drag the tv_spend coefficient toward zero (as OLS tries to explain the huge swings with a tiny slope) while barely moving the other channels -- matching the verdict where beta_tv_spend collapsed to ~0.0004 and everything else stayed close to truth.

### Hint (read AFTER wake-up)
{
  "id": "unit_mix",
  "character": "The Metric Martian",
  "applies_to": [
    "tabular"
  ],
  "dose": {
    "frac": [
      0.05,
      0.3
    ],
    "factor": [
      10,
      1000
    ]
  },
  "symptom": "a feature has two populations of magnitudes; its coefficient becomes tiny and noisy",
  "wakeup_hint": "the same quantity recorded in two different units (mg vs g, cm vs inches, hg19 vs hg38 coordinates)"
}

### Revised explanation
Confirmed with the data: tv_spend is bimodal in round-002 -- 108/600 rows (18%) sit around 50,000-100,000 while the rest sit around 40-80 (median 56.8, baseline column has no such split). This is a classic "same metric, two units" mixup (e.g. one region/week's export reporting raw dollars instead of $k). The huge-variance rows swamp the regression and crush beta_tv_spend to ~0.0004 while leaving the other channels close to truth.

### Checker
File: checks/unit_mix.py -- for each numeric, non-dummy column, flags a column where a minority (2-45%) of positive values are >10x the column's median (a "two populations of magnitude" signature).
Tested: fires on round-002 work/prepared.csv (tv_spend: 108/600 rows >10x median 56.95); does NOT fire on baseline work/prepared.csv, and does not false-fire on any of rounds 1,3-9's prepared.csv either.

## Round 4 — stone: outliers, dose {frac: 0.0365, scale: 22, target: "outcome"}

### Wake-up sentences (written BEFORE reading hint)
In weekly revenue reporting, a scale-22 spike on the outcome column looks like a data-export glitch where a handful of weeks (about 3.6%) get double-counted or mis-summed revenue -- e.g. a week where a refund reversal, a promo credit, or a duplicate transaction batch is added into that week's revenue total, producing a handful of enormous revenue weeks. Because OLS minimizes squared error, a small number of huge-revenue outlier weeks can pull the fitted intercept/slopes around, inflating some channel coefficients (tv_spend, social_spend, discount_pct all came in high) while others barely move -- an uneven, "everything's a bit off in different directions" degradation rather than a clean shrink-to-zero pattern.

### Hint (read AFTER wake-up)
{
  "id": "outliers",
  "character": "The Spike",
  "applies_to": [
    "tabular",
    "timeseries"
  ],
  "dose": {
    "frac": [
      0.005,
      0.05
    ],
    "scale": [
      5,
      30
    ]
  },
  "symptom": "a few extreme points drag means and slopes; residual plots show a lone cluster",
  "wakeup_hint": "a handful of impossible values (unit slip, sensor glitch, typo) that a squared-error method cannot ignore"
}

### Revised explanation
Confirmed: revenue in round-004 has robust z-scores (median/MAD based) up to ~19.5 vs a baseline max of ~2.9, and 22/600 weeks (3.65%) sit far above the rest (max 2304 vs median 528). This matches the hint exactly -- a handful of impossible revenue weeks that OLS cannot ignore, pulling the intercept and several channel coefficients (tv_spend, social_spend, discount_pct) off target while leaving search_spend nearly untouched.

### Checker
File: checks/outlier_spike.py -- flags the revenue column when any week's modified z-score (median/MAD based) exceeds 6.
Tested: fires on round-004 work/prepared.csv (22/600 extreme weeks); does NOT fire on baseline, and does not false-fire on rounds 1,2,3,5-9.

## Round 5 — stone: batch_shift, dose {frac: 0.44, shift: 3.4, col: "search_spend"}

### Wake-up sentences (written BEFORE reading hint)
A "batch shift" on search_spend in weekly marketing data smells like a change in how a paid-search platform reports spend mid-quarter -- e.g. Google Ads switching from net-of-fees to gross billed spend, or a currency/tax adjustment applied to about half the weeks (44%) while the older export format continued for the rest, adding a constant offset to one batch. Because this offset only shifts a subset of rows by a constant rather than corrupting variance, OLS would try to explain the batch-level step as if it were part of search_spend's real effect, likely inflating beta_search_spend (matching the verdict: beta_search_spend jumped from truth 4.0 to estimate 7.1, the worst-degraded coefficient) while leaving other channels closer to truth.

### Hint (read AFTER wake-up)
{
  "id": "batch_shift",
  "character": "The Drifter",
  "applies_to": [
    "tabular",
    "timeseries",
    "genotype"
  ],
  "dose": {
    "frac": [
      0.2,
      0.5
    ],
    "shift": [
      1.0,
      4.0
    ]
  },
  "symptom": "a subgroup has a different baseline; effect estimates absorb the group difference",
  "wakeup_hint": "an unmodelled batch/plate/site/time effect that is confounded with the exposure"
}

### Revised explanation
The shift is real (search_spend mean 34.99 in round-005 vs 30.19 in baseline) but it is a *diffuse* additive shift applied to a random ~44% of rows, not tied to region, quarter, or row order (checked group means by region/quarter/contiguous chunks -- no clean split), and not large enough relative to the channel's natural spread to show up as bimodality: skew/kurtosis are nearly identical to baseline (0.029/-0.165 vs 0.030/-0.212), and a 2-component Gaussian mixture does not fit better than 1 component (BIC prefers 1 component for both round-005 and baseline). This is exactly the hint's "unmodelled batch/site/time effect confounded with the exposure": search_spend has no accompanying batch id, data-source flag, or ingestion-date column in the pipeline's input, so there is nothing in the data to key a check on. OLS absorbs the shifted subgroup's higher baseline into the search_spend slope itself (beta_search_spend inflated from truth 4.0 to 7.1).

### Checker: none written -- genuinely undetectable from the data the pipeline receives
Tried: (1) magnitude/ratio test (like unit_mix) -- shift (3.4) is far too small relative to the column's spread (sd ~12) to separate a subpopulation; (2) skew/kurtosis comparison -- essentially unchanged from baseline; (3) contiguous-row / region / quarter grouping -- no clean split found; (4) 1- vs 2-component Gaussian-mixture BIC test -- does not prefer 2 components even on the corrupted round. None fire reliably without false-alarming on ordinary sampling noise. Documented as a headsup instead of a check (see antibody below): would need an explicit batch/source id, an ingestion-date/version column, or a raw per-row timestamp to detect a batch-level shift like this.

## Round 7 — stone: type_corruption, dose {frac: 0.064, col: "discount_pct"}

### Wake-up sentences (written BEFORE reading hint)
A "type corruption" on discount_pct in a weekly marketing export smells like a spreadsheet or CSV formatting glitch -- someone typing "10%" instead of "10", a stray currency symbol, a locale using commas instead of decimal points, or a manual override note ("TBD"/"n/a") typed into a numeric discount field for about 6.4% of weeks. Since prepare.py does `df.dropna()` for "complete weeks only" but a corrupted string wouldn't necessarily become NaN on read (it could parse as a different value or force the whole column to load as text), this could either silently drop weeks or, worse, silently coerce the column so the model fits garbage numbers -- and the verdict shows discount_pct's estimate came back as `null` entirely, meaning the whole fit or that coefficient broke, consistent with a dtype/parsing failure rather than a smooth numeric drift.

### Hint (read AFTER wake-up)
{
  "id": "type_corruption",
  "character": "The Typo",
  "applies_to": [
    "tabular"
  ],
  "dose": {
    "frac": [
      0.01,
      0.1
    ]
  },
  "symptom": "a numeric column arrives as text ('1,234', ' 12 ', 'NA'); parsers coerce silently or crash",
  "wakeup_hint": "mixed types in one column (thousands separators, whitespace, sentinel strings) from a spreadsheet export"
}

### Revised explanation
Confirmed and worse than expected: 6.4% of discount_pct values were corrupted with whitespace/non-breaking-space padding (e.g. "9.871\xa0", " 9.357 ") or left blank. This made pandas read the whole discount_pct column as dtype=object (text). prepare.py's rule "any object-dtype column is categorical -> one-hot encode it" then exploded discount_pct into 576 separate dummy columns (one per distinct text value, e.g. "discount_pct_ 9.357 "), instead of keeping one numeric column. The real discount_pct channel effect is gone entirely from the fit (beta_discount_pct comes back null in the verdict), and 6 rows also got dropped by dropna(). This matches the hint precisely: "mixed types in one column... from a spreadsheet export."

### Checker
File: checks/numeric_column_exploded.py -- scans the prepared output's column names for a prefix that has been split into >=5 dummy columns whose suffixes are all numbers (e.g. "discount_pct_9.357"), which only happens when a numeric column was wrongly treated as categorical.
Tested: fires on round-007 work/prepared.csv (discount_pct exploded into 567 dummy columns); does NOT fire on baseline, and does not false-fire on rounds 1-6,8,9.

## Round 9 — stone: measurement_error, dose {sd: 1.02, col: "email_sends"}

### Wake-up sentences (written BEFORE reading hint)
Adding noise with sd~1.02 to email_sends (thousands of emails, spec mean 40/sd 15) sounds like the everyday imprecision of email-platform reporting -- e.g. an ESP (email service provider) rounding or batching send counts, or a delay between "emails queued" and "emails actually sent" being logged as a slightly different number each week -- a small, honest measurement wobble rather than a structural corruption. Classic errors-in-variables: this kind of noise on a predictor (not the outcome) biases that channel's own regression coefficient toward zero (attenuation bias) without doing much to the other channels, which matches the verdict -- beta_email_sends is the only badly degraded estimand (rel_err 0.54), while tv_spend, search_spend, and discount_pct are all close to truth.

### Hint (read AFTER wake-up)
{
  "id": "measurement_error",
  "character": "The Blur",
  "applies_to": [
    "tabular",
    "timeseries"
  ],
  "dose": {
    "sd": [
      0.3,
      1.5
    ]
  },
  "symptom": "effects attenuate toward zero; nothing crashes, everything looks a bit weaker",
  "wakeup_hint": "noise in a predictor (errors-in-variables) biases its coefficient toward zero"
}

### Revised explanation
Confirmed and even more specific than expected: email_sends is defined in spec.yaml as an integer count (thousands of emails). In the baseline, every value is a whole number. In round-009, 100% of rows are non-integer floats (e.g. 44.5003), because Gaussian noise (sd=1.02) was added directly to what must be a count. This is textbook errors-in-variables measurement noise on a predictor, which biases only that predictor's coefficient toward zero (attenuation bias) -- matching the verdict where beta_email_sends alone is badly degraded (rel_err 0.54) while the other channels stay close to truth.

### Checker
File: checks/email_sends_not_integer.py -- flags email_sends when >=5% of values are non-integer (it should always be a whole send count).
Tested: fires on round-009 work/prepared.csv (600/600 rows non-integer); does NOT fire on baseline, and does not false-fire on rounds 1-8.

## Second pass

Rounds 10-18 re-ran the same 9 stones through the round-1-9 antibodies: 5 caught, round 14 (batch_shift) silent as declared (unguardable from this data -- no new work needed, matches prior finding). Rounds 19-27 are 9 hold-out perturbations never shown before. Verdicts: 20 (unit_mix), 22 (type_corruption) caught; 24 (correlated_block) harmless; 19 (target_leakage), 21 (outliers), 23 (mnar_missing), 25 (unit_mix), 26 (measurement_error), 27 (batch_shift) silent -- addressed below.

## Round 19 — stone: target_leakage, dose {noise_sd: 0.8, name: "last_click_revenue"}

### Wake-up sentences (written BEFORE reading hint)
"last_click_revenue" is the same family of problem as round 1's "attributed_revenue" but from a different attribution model -- a last-click/last-touch revenue field a marketing analytics tool computes and exports alongside the true weekly revenue, still fundamentally a transformation of the outcome. This dose has more noise added (noise_sd 0.8 vs round 1's 0.3), so I expect the leaked column to correlate with revenue less strongly than round 1's ~0.96 -- likely why my existing no_target_leakage.py checker (threshold 0.9) missed it; the leak is real but noisier.

### Hint (read AFTER wake-up)
{
  "id": "target_leakage",
  "character": "The Time Traveler",
  "applies_to": [
    "tabular",
    "timeseries"
  ],
  "dose": {
    "noise_sd": [
      0.05,
      0.5
    ]
  },
  "symptom": "one feature predicts the outcome almost perfectly; all other effects shrink toward zero",
  "wakeup_hint": "a column computed from the outcome, or from the future, leaked into the predictors"
}

### Revised explanation
Confirmed: last_click_revenue correlates with revenue at 0.784 -- clearly a leak, but well under my round-1 threshold of 0.9 because of the higher injected noise (sd 0.8). Checked the correlation ceiling across every legit column in all 27 rounds + baseline: the highest any real channel ever reaches is 0.637 (round-008, tv_spend). So 0.75 sits safely between the legit ceiling (0.637) and the lowest leak signal seen so far (0.784).

### Checker: tightened existing checks/no_target_leakage.py
Change: lowered CORR_THRESHOLD from 0.9 to 0.75 (same script, same antibody family -- generalizes rather than adding a new checker).
Tested: fires on round-019 (last_click_revenue corr=0.784) and still fires on round-001/round-010 (attributed_revenue); swept all 27 rounds + baseline -- fires ONLY on the three actual leakage rounds (001, 010, 019), no false positives anywhere else.

## Round 21 — stone: outliers, dose {frac: 0.0365, scale: 15, col: "social_spend", target: "feature"}

### Wake-up sentences (written BEFORE reading hint)
This is the same "Spike" stone as round 4 but aimed at a spend column instead of revenue -- like a social-platform export where a handful of weeks' spend got double-billed, a campaign budget cap glitched and overspent 15x, or a currency conversion error inflated a few weeks' social_spend. My round-4 checker (outlier_spike.py) only scans the `revenue` column, so a spike planted in a feature column instead of the outcome would sail right through it -- I expect that's exactly why this went silent, and the fix is to generalize the outlier scan to every numeric predictor column, not just revenue.

### Hint (read AFTER wake-up)
{
  "id": "outliers",
  "character": "The Spike",
  "applies_to": [
    "tabular",
    "timeseries"
  ],
  "dose": {
    "frac": [
      0.005,
      0.05
    ],
    "scale": [
      5,
      30
    ]
  },
  "symptom": "a few extreme points drag means and slopes; residual plots show a lone cluster",
  "wakeup_hint": "a handful of impossible values (unit slip, sensor glitch, typo) that a squared-error method cannot ignore"
}

### Revised explanation
Confirmed: social_spend has robust z-scores (median/MAD) up to 13.7 in round-021 (baseline max 3.1), with 22/600 weeks far above the rest -- same signature as round 4's revenue spike, just landed on a feature column instead of the outcome. My original outlier_spike.py only ever looked at `revenue`, so it structurally could not see this.

### Checker: generalized existing checks/outlier_spike.py
Change: instead of only scanning `revenue`, it now scans every numeric non-dummy column (revenue and all spend/count feature columns) for the same MAD-based modified-z-score signature (threshold 6). Same script path, same antibody family.
Tested: fires on round-021 (social_spend, 22/600 extreme); still fires on round-004 (revenue, 22/600 extreme). Swept all 27 rounds + baseline: fires only on rounds that are genuinely corrupted (004, 013 = repeat of outliers-on-revenue; 021 = outliers-on-feature; and, as a useful bonus, it also independently catches the unit_mix rounds 002/011/020/025 via the same extreme-value signature -- no false positives on any clean round).

## Round 23 — stone: mnar_missing, dose {frac: 0.25, target: "outcome"}

### Wake-up sentences (written BEFORE reading hint)
"MNAR" (missing not at random) on the revenue outcome, in a weekly marketing table, sounds like a reporting gap that is itself caused by the value -- e.g. finance only finalizes/publishes a week's revenue figure once it clears a materiality threshold, or a region withholds reporting a week's revenue when it's unusually low or high (embarrassing or needing review), so the 25% of weeks with blank revenue are not a random sample of weeks. Since prepare.py does `df.dropna()` (drop incomplete weeks), all 150 blanked rows are simply discarded, shrinking the effective training sample to the weeks that happened to report -- if the missingness is correlated with revenue itself (not just with observed predictors), the surviving 450 weeks are a biased/truncated sample of the outcome distribution, and OLS on a non-randomly-truncated outcome will produce biased coefficients (selection bias) even though nothing in the remaining data looks obviously wrong.

### Hint (read AFTER wake-up)
{
  "id": "mnar_missing",
  "character": "The Ghost",
  "applies_to": [
    "tabular",
    "timeseries"
  ],
  "dose": {
    "frac": [
      0.05,
      0.3
    ]
  },
  "symptom": "rows vanish preferentially where values are extreme; estimates shift toward the middle",
  "wakeup_hint": "missingness that depends on the value itself, so dropping rows biases everything downstream"
}

### Revised explanation
Confirmed and sharper than my wake-up guess: revenue was blanked for 150/600 weeks (25%), and prepare.py's `dropna()` silently discards them, shrinking the training sample to 450 rows. The surviving revenue distribution is truncated at the top (max 586.5 vs baseline's 773.2) and compressed (std 61.1 vs baseline 80.8, mean 495.3 vs baseline 528.9). Crucially, the missing-revenue rows are not a random subset of the raw data: their tv_spend and search_spend are ~1 standard deviation higher than the present-revenue rows (std-diff 0.98/0.99), exactly consistent with "high-driver, high-revenue weeks go missing" -- a testable, non-random signature even without seeing the true (blanked) revenue values. Checked this same standardized-mean-difference test against every other missing-data case in rounds 1-27 (harmless social_spend-missing rounds 003/012, and the small type_corruption NaN counts in 007/016/022) -- none show anywhere near this level of association (max 0.32 on the harmless rounds); the small-n type_corruption NaN cases (6-8 rows) are gated out by a minimum-missing-count threshold so they don't add noise.

### Checker
File: checks/mnar_missing.py (new) -- reads the RAW stage input (pre-dropna) for `prepare`. For any column with >=30 missing values, computes the standardized mean difference in every other numeric column between the missing-group and present-group; fires if any exceeds 0.5. This is a proxy for true MNAR (missingness driven by the unobserved value itself) via its observable footprint: missingness correlated with the predictors that drive that value.
Tested: fires on round-023 (revenue missing 150/600, associated with tv_spend std-diff 0.98); does NOT fire on baseline, or on rounds 003/012 (harmless, legitimately-random social_spend missingness); swept all 27 rounds + baseline -- fires only on round-023.

## Round 25 — stone: unit_mix, dose {frac: 0.2, factor: 1000, col: "tv_spend", after_stage: "prepare"}

### Wake-up sentences (written BEFORE reading hint)
Same unit-mixup family as round 2 (a subset of tv_spend rows reported 1000x too large, like raw dollars vs $k), but this dose has `after_stage: "prepare"` -- meaning the corruption is injected into the ALREADY-PREPARED table, after one-hot encoding, rather than into the raw weekly export. In a real pipeline this is like a downstream step (a feature store write, a re-scaling script, a join with a differently-unit-ed source) corrupting the modeling table after cleaning rather than the raw ingestion having a unit bug -- so my existing check.stage="prepare" antibody (which runs right after the prepare step) should still see it in prepared.csv, unless something about my unit_mix.py column-selection logic specifically misses it this time (e.g. a different corrupted row count or corruption timing changing which columns look bimodal).

### Hint (read AFTER wake-up)
{
  "id": "unit_mix",
  "character": "The Metric Martian",
  "applies_to": [
    "tabular"
  ],
  "dose": {
    "frac": [
      0.05,
      0.3
    ],
    "factor": [
      10,
      1000
    ]
  },
  "symptom": "a feature has two populations of magnitudes; its coefficient becomes tiny and noisy",
  "wakeup_hint": "the same quantity recorded in two different units (mg vs g, cm vs inches, hg19 vs hg38 coordinates)"
}

### Revised explanation
Confirmed: tv_spend is bimodal in round-025's saved work/prepared.csv (104/600 rows >10x median), same signature as round 2. BUT running my existing unit_mix.py against it manually fires correctly -- so why was the round graded silent (checks_fired: [])? Inspected `.claude/skills/marketing_mix/history/round-025/run.json`: the stone's `after_stage` is `"prepare"`, and the run log shows the `prepare`-stage checks (including unit_mix.py) ran and reported "no column shows a bimodal magnitude split" -- because at that exact checkpoint the corruption had not been injected yet. The stone is applied to prepared.csv *after* the prepare-stage checks already ran clean, and that now-corrupted file is what `fit.py` actually consumes. This is a timing gap: a check registered only at `check.stage: "prepare"` runs too early to see an `after_stage: "prepare"` corruption.

### Checker: generalized existing checks/unit_mix.py + widened its registration
Change 1 (script): now scans every file path passed on the command line (not just argv[1]), so whichever checkpoint invokes it, it can see the corrupted file if it appears in either argument.
Change 2 (antibody ab-002): check.stage widened from `"prepare"` to `check.stages: ["prepare", "fit"]`, so the scan runs again using the `fit` stage's actual input (which by then reflects any `after_stage: "prepare"` corruption).
Tested: simulated both checkpoints' argv shapes for round-025 -- (prepared.csv, input.csv) and (result.json, prepared.csv) -- both fire correctly; both checkpoints on baseline stay silent; full sweep of all 27 rounds at both checkpoint shapes fires only on the four genuine unit_mix rounds (002, 011, 020, 025), no false positives.

## Round 26 — stone: measurement_error, dose {sd: 1.26, col: "discount_pct"}

### Wake-up sentences (written BEFORE reading hint)
Same family as round 9's email_sends noise, but this time it's discount_pct -- e.g. the promo/discount percentage being re-derived from a rounding or reconciliation process (a finance system recomputing the "effective" discount after coupon stacking, taxes, or returns) that adds a bit of jitter around the true value each week. Unlike email_sends, discount_pct is already a continuous, non-integer percentage in the baseline, so my round-9 "must be a whole number" integrity check has no foothold here -- I expect this one to need a different signature, most likely values dipping below the natural floor (discount_pct should never go negative) since sd=1.26 is large relative to the spec's low end (min 0, several weeks likely start near 0-2%).

### Hint (read AFTER wake-up)
{
  "id": "measurement_error",
  "character": "The Blur",
  "applies_to": [
    "tabular",
    "timeseries"
  ],
  "dose": {
    "sd": [
      0.3,
      1.5
    ]
  },
  "symptom": "effects attenuate toward zero; nothing crashes, everything looks a bit weaker",
  "wakeup_hint": "noise in a predictor (errors-in-variables) biases its coefficient toward zero"
}

### Revised explanation
Confirmed and cleaner than my wake-up guess: discount_pct is bounded at 0 in the spec (a discount cannot be negative), and 60/600 rows (10%) in round-026 are negative (min -13.0) versus zero negative values in baseline. Gaussian noise (sd=1.26) added directly to a percentage that sits close to zero for many weeks (spec mean 10, sd 5) pushes a meaningful chunk below the physical floor -- a simple, robust integrity signature, and (per the hint) classic errors-in-variables attenuation: only beta_discount_pct is degraded (rel_err 0.70) while every other channel stays accurate.

### Checker: new, but same family/pattern as round 9's integer check -- generalizes the "column has a natural bound" idea
File: checks/negative_spend_or_discount.py -- flags any of tv_spend/search_spend/social_spend/email_sends/discount_pct (all structurally >=0 per spec.yaml) that contains negative values.
Tested: fires on round-026 (discount_pct, 60/600 negative); does NOT fire on baseline; swept all 27 rounds -- fires only on genuinely corrupted rounds: 026 (this case), plus as a useful bonus on 009/018 (email_sends measurement-error, already caught by email_sends_not_integer.py) and 021 (social_spend outliers, already caught by the generalized outlier_spike.py) -- no false positives on any clean round.

## Round 27 — stone: batch_shift, dose {frac: 0.38, shift: 2.8, col: "discount_pct"}

### Wake-up sentences (written BEFORE reading hint)
Same "Drifter" batch-shift family as round 5, now landing on discount_pct instead of search_spend -- e.g. a promo/discount policy change applied to 38% of weeks (maybe a new pricing system or a different discount-calculation rule adopted mid-quarter) that adds a constant +2.8 points to those weeks without a batch/source flag recording which rule applied. I expect this to be largely undetectable the same way round 5 was (diffuse, unlabeled, not tied to region/quarter/row-order) -- BUT discount_pct has a hard floor at 0 (unlike search_spend, which just has a soft baseline), so I want to check whether this dose happens to push the shifted subgroup into a range that leaves a visible trace (e.g. a bimodal gap, or a floor-clipping asymmetry) even though the underlying mechanism is the same "no batch id in the data" problem as round 5.

### Hint (read AFTER wake-up)
{
  "id": "batch_shift",
  "character": "The Drifter",
  "applies_to": [
    "tabular",
    "timeseries",
    "genotype"
  ],
  "dose": {
    "frac": [
      0.2,
      0.5
    ],
    "shift": [
      1.0,
      4.0
    ]
  },
  "symptom": "a subgroup has a different baseline; effect estimates absorb the group difference",
  "wakeup_hint": "an unmodelled batch/plate/site/time effect that is confounded with the exposure"
}

### Revised explanation
Confirmed same unguardable class as round 5, now on discount_pct: std barely moves (5.24 vs baseline 5.05), skew/kurtosis nearly identical (0.15/0.16 vs 0.10/0.01), a 2-component Gaussian mixture is not preferred over 1 (BIC 3725 vs 3703), and region/quarter group means show no clean split (11.46-11.61 across regions, 10.9-12.2 across quarters -- normal variation). This belongs to the class already declared unguardable in round 5 (ab-004): a diffuse batch/export-level shift with no batch id, source flag, or timestamp column to key off, confounded with the exposure itself. Not writing a new checker (it would fire on nothing, since there is nothing in the data to detect). Updated ab-004 in place to generalize from "search_spend" to "any channel" and record this as confirmed evidence on a second column, rather than adding a duplicate antibody.

### Checker: none (same declared-unguardable class as round 5 / ab-004)

### Final full-sweep verification (all 7 checkers x all 27 rounds + baseline)
Ran every checker against every round's work/prepared.csv (plus input.csv). Result: every fire corresponds exactly to a known corrupted round (1,2,4,7,9,10,11,13,16,18,19,20,21,22,23,25,26); zero fires on baseline, on the harmless rounds (3,6,8,12,15,17,24), or on the three batch_shift rounds (5,14,27) -- consistent with batch_shift being genuinely unguardable from this data. No false positives anywhere.

Skill version bumped 1 -> 2.
