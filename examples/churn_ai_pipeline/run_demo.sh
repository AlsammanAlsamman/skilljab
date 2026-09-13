#!/usr/bin/env bash
# Replays the SkillJab demo on the AI-written churn pipeline:
#   baseline -> 10 stones (one per round) -> antibodies -> re-test -> sweeps -> report
# Usage: ./run_demo.sh            (needs: pipx install skilljab ; python3 with pandas+sklearn)
set -euo pipefail
cd "$(dirname "$0")"
S=.claude/skills/churn
rm -rf .claude
skilljab init --name churn --pipeline pipeline.yaml --spec spec.yaml --skill-dir $S >/dev/null
echo "== baseline: can the AI's pipeline recover a planted truth?"
skilljab baseline --skill $S --target-n 2000000 --ram-mb 16000 | grep -E 'recovered|baseline_class'
echo "== three persona plans -> divergence map, tree, lineup"
skilljab plans diff plans/*.json --out $S/history/divergence.json >/dev/null
skilljab tree build plans/*.json --out $S/tree.json >/dev/null
skilljab lineup score --skill $S --lineup plans/lineup.json | grep hit

run() { skilljab round new --skill $S >/dev/null; skilljab round stones --skill $S "$1" --level "$2" ${3:+--dose "$3"} >/dev/null
        skilljab round run --skill $S | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'   {\"$1\":18s} -> {d[\"class\"]:9s} fired: {[c[\"script\"].split(\"/\")[-1] for c in d[\"checks_fired\"]]}')"; }
STONES=(
 'target_leakage    0.7 {"target_leakage":{"name":"churn_score_v1","noise_sd":0.3}}'
 'type_corruption   0.6 {"type_corruption":{"col":"monthly_charges"}}'
 'mnar_missing      0.7 {"mnar_missing":{"col":"support_tickets","target":"feature"}}'
 'duplicates        0.7'
 'unit_mix          0.5 {"unit_mix":{"col":"monthly_charges","factor":100}}'
 'batch_shift       0.8 {"batch_shift":{"col":"monthly_charges"}}'
 'rare_category     0.6 {"rare_category":{"level":"enterprise"}}'
 'outliers          0.7 {"outliers":{"col":"monthly_charges","target":"feature"}}'
 'correlated_block  0.7 {"correlated_block":{"col":"monthly_charges","n_copies":3}}'
 'measurement_error 0.6 {"measurement_error":{"col":"tenure_months"}}'
)
echo "== rounds 1-10: the pipeline as the AI wrote it"
for s in "${STONES[@]}"; do set -- $s; run "$1" "$2" "${3:-}"; done
echo "== explainer: antibodies (checkers + heads-ups) for every silent failure"
cp checks/*.py $S/checks/
for f in antibodies/*.json; do skilljab antibody add --skill $S --file "$f" >/dev/null; done
T=$S/tree.json
skilljab tree add-evidence --tree $T --node feature_selection --choice "all columns" --kind stone --verdict silent --round 1 --summary "target_leakage: churn_score_v1 swallowed, AUC ~1, drivers -> 0" --status rejected >/dev/null
skilljab tree add-evidence --tree $T --node feature_selection --choice "whitelist" --kind stone --verdict caught --round 11 --summary "no_leaky_columns.py catches the leak" --status default >/dev/null
skilljab tree add-evidence --tree $T --node missing_handling --choice "dropna" --kind stone --verdict silent --round 3 --summary "mnar_missing on support_tickets: effect 67% too small" --status rejected >/dev/null
skilljab tree add-evidence --tree $T --node missing_handling --choice "missing-indicator + report missingness by outcome" --kind stone --verdict caught --round 13 --summary "missingness_by_outcome.py fires" --status default >/dev/null
skilljab tree add-evidence --tree $T --node encoding --choice "get_dummies drop_first" --kind stone --verdict silent --round 2 --summary "type_corruption: numeric-as-text one-hot into ~1,400 columns" --status rejected >/dev/null
skilljab tree add-evidence --tree $T --node encoding --choice "explicit levels" --kind stone --verdict caught --round 12 --summary "dummy_explosion.py fires" --status default >/dev/null
skilljab tree add-evidence --tree $T --node duplicates --choice "no" --kind stone --verdict harmless --round 4 --summary "duplicates: point estimates unchanged (standard errors would be wrong)" >/dev/null
skilljab skill bump --skill $S --description "Churn model (logistic regression on a customer table), jabbed: 8 silent failures found, 6 now guarded by checks, 2 need data the table does not carry." >/dev/null
echo "== rounds 11-20: the same stones against the immunized pipeline"
for s in "${STONES[@]}"; do set -- $s; run "$1" "$2" "${3:-}"; done
echo "== dose sweeps"
for spec in 'target_leakage {"name":"churn_score_v1"}' 'mnar_missing {"col":"support_tickets","target":"feature"}' 'unit_mix {"col":"monthly_charges","factor":100}' 'outliers {"col":"monthly_charges","target":"feature"}' 'measurement_error {"col":"tenure_months"}' 'batch_shift {"col":"monthly_charges"}' 'correlated_block {"col":"monthly_charges"}'; do set -- $spec; skilljab sweep --skill $S --stone $1 --levels 6 --fixed "$2" >/dev/null; echo "   swept $1"; done
skilljab report --skill $S >/dev/null
skilljab status --skill $S | grep -E '"jabbed"|"reason"|n_antibodies'
echo "report: $S/history/report.html   skill: $S/SKILL.md"
