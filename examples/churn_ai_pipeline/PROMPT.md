# The prompt that produced this pipeline

> "I have a CSV of our customers (tenure, monthly charges, support tickets, contract type, plan, and
> whether they churned). Build me a churn model and tell me which factors matter most."

Claude wrote `prepare.py` and `train.py` below in one shot. They are clean, idiomatic, and exactly
what a competent analyst would accept. `pipeline.yaml` wraps them for SkillJab. Nothing here was
written to be fragile on purpose — this is the pipeline as the AI delivered it.
