# The churn model Claude wrote — and what SkillJab found in it

**The prompt** (the kind people give an AI every day):

> "I have a CSV of our customers (tenure, monthly charges, support tickets, contract type, plan, and
> whether they churned). Build me a churn model and tell me which factors matter most."

**What Claude delivered** — `prepare.py` (dropna, `get_dummies`) and `train.py` (logistic regression
on every column, AUC, top factors). Clean, idiomatic, the code any of us would accept. On the clean
miniature it recovers every planted effect and ranks the factors correctly: **AUC 0.73, contract >
support tickets > tenure**. Nothing looks wrong.

**Then the stones.** Ten rounds, one perturbation each, every one of them a thing that happens to
real customer tables:

| round | stone | what a real table does | the AI's pipeline | anyone warned? |
|---|---|---|---|---|
| 1 | The Time Traveler | a `churn_score_v1` column from an earlier model | AUC → 1.0, every real driver → 0 | **no** |
| 2 | The Typo | `monthly_charges` exported as text (`'1,234.50'`) | `get_dummies` one-hots 1,400 charges; coefficient vanishes | **no** |
| 3 | The Ghost | support history purged for closed accounts | `dropna` removes the churners; ticket effect 67% too small | **no** |
| 4 | The Twin | billing join duplicates rows | point estimates fine (standard errors would not be) | harmless |
| 5 | The Metric Martian | one region bills in cents | price effect → 0: "price doesn't matter" | **no** |
| 6 | The Drifter | one acquisition channel: pricier, churnier, unlabelled | every coefficient off by ~100% | **no** |
| 7 | The Unicorn | a new `enterprise` plan with 2 customers | fine | harmless |
| 8 | The Spike | ~50 bills at ±$800 (decimal slip) | price effect off by 90% | **no** |
| 9 | The Clique | charges + charges_with_tax + annual charges | price effect split three ways, sign unstable | **no** |
| 10 | The Blur | tenure derived from a noisy first-invoice date | tenure effect 70% too small, mis-ranked | **no** |

**Eight silent failures out of ten.** Each would have shipped as a confident report with a clean AUC.

**Then the antibodies.** For each silent failure the explainer wrote why (in the domain's own words —
"retention_offer_sent", "purged on account closure", "cents in one billing region"), a checker that
runs at the `prepare` boundary, and a heads-up. Rounds 11–20 replay the same stones:

- six are now **caught** by `no_leaky_columns`, `dummy_explosion`, `missingness_by_outcome`,
  `scale_and_outliers` (×2), `collinear_predictors`;
- two stay **silent, and the skill says so**: the hidden batch and the noisy tenure cannot be seen in
  the data as delivered. The heads-up tells the next analyst which columns to ask for (channel,
  region, export batch) and to treat the coefficients as confounded until then.

That distinction — guarded vs. known-but-unguardable — is the point. A tool that claimed to catch
everything would be lying; this one tells you which two questions to ask before you trust the model.

## Reproduce

```bash
pipx install skilljab            # needs python3 with pandas and scikit-learn for the pipeline itself
./run_demo.sh                    # ~3 minutes: baseline, 20 rounds, 7 sweeps, report
open .claude/skills/churn/history/report.html
cat  .claude/skills/churn/SKILL.md
```

A rendered copy of the report and the skill are in [`docs/demo/churn/`](../../docs/demo/churn/).

## Files

- `PROMPT.md` — the prompt; `prepare.py`, `train.py`, `pipeline.yaml` — the pipeline as delivered
- `spec.yaml` — the miniature: 1,500 customers with planted effects (tenure −0.04/month, charges +0.012/$, tickets +0.35, one-year −0.8, two-year −1.6)
- `plans/` — three persona plans (grad student, statistician, ML engineer) + the judge's lineup
- `checks/` — the six antibody checkers; `antibodies/` — the eight antibodies with their explanations
- `run_demo.sh` — replays everything
