#!/usr/bin/env bash
# Replays the marketing-mix test on the AI-written ROI regression:
#   baseline -> 9 stones (one per round) -> the explainer's antibodies -> re-test -> hold-out 1 -> hold-out 2 -> sweeps -> report
# The antibodies and checkers in antibodies/ and checks/ are the ones a blind explainer agent wrote live
# (two passes; see EXPLAINER_LOG.md). This replay installs the final versions, so hold-out 1 is caught on the
# first try here — in the live run its first pass went 2 caught / 6 silent, and the second pass fixed those.
# Usage: ./run_demo.sh            (needs: pipx install skilljab ; python3 with pandas+sklearn)
set -euo pipefail
cd "$(dirname "$0")"
S=.claude/skills/marketing_mix
rm -rf .claude
skilljab init --name marketing_mix --pipeline pipeline.yaml --spec spec.yaml --skill-dir $S >/dev/null
echo "== baseline: can the AI's pipeline recover the planted return-per-dollar?"
skilljab baseline --skill $S --target-n 500000 --ram-mb 16000 | grep -E 'recovered|baseline_class'

run() { skilljab round new --skill $S >/dev/null; skilljab round stones --skill $S "$1" --level "$2" ${3:+--dose "$3"} ${4:+--after-stage "$4"} >/dev/null
        skilljab round run --skill $S | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'   {\"$5\":46s} -> {d[\"class\"]:11s} fired: {sorted({c[\"script\"].split(\"/\")[-1] for c in d[\"checks_fired\"]})}')"; }
stones() {
  run target_leakage    0.7 '{"target_leakage":{"name":"attributed_revenue","noise_sd":0.3}}'  "" "attribution tool's revenue column in the feed"
  run unit_mix          0.5 '{"unit_mix":{"col":"tv_spend","factor":1000}}'                     "" "one region reports TV spend in dollars, not \$k"
  run mnar_missing      0.7 '{"mnar_missing":{"col":"social_spend","target":"feature"}}'        "" "agency never reports its biggest social weeks"
  run outliers          0.7 '{"outliers":{"target":"outcome"}}'                                  "" "a few Black-Friday-scale revenue weeks"
  run batch_shift       0.8 '{"batch_shift":{"col":"search_spend"}}'                             "" "hidden market: pricier search, higher revenue"
  run correlated_block  0.7 '{"correlated_block":{"col":"search_spend","n_copies":3}}'          "" "search spend + clicks + impressions"
  run type_corruption   0.6 '{"type_corruption":{"col":"discount_pct"}}'                         "" "discount exported with stray whitespace"
  run duplicates        0.7 ''                                                                   "" "promo-calendar join duplicated weeks"
  run measurement_error 0.6 '{"measurement_error":{"col":"email_sends"}}'                        "" "email counts from a noisy ESP log"
}
echo "== rounds 1-9: the pipeline as the AI wrote it"; stones
echo "== explainer: antibodies (checkers + heads-ups) for every silent failure — written live, see EXPLAINER_LOG.md"
cp checks/*.py $S/checks/
for f in antibodies/*.json; do skilljab antibody add --skill $S --file "$f" >/dev/null; done
skilljab skill bump --skill $S --description "Marketing-mix ROI regression, jabbed: 6 silent failures found; 5 guarded by checks, 1 (a hidden batch) declared unguardable without a source/batch column." >/dev/null
echo "== rounds 10-18: the same stones against the immunized pipeline"; stones
echo "== rounds 19-27: HOLD-OUT 1 — perturbations the explainer was never shown (caught here after its second pass)"
run target_leakage    0.9 '{"target_leakage":{"name":"last_click_revenue","noise_sd":0.8}}'      "" "a noisier leak (0.8 sd)"
run unit_mix          0.6 '{"unit_mix":{"col":"search_spend","factor":100}}'                       "" "search spend x100 for some rows"
run outliers          0.7 '{"outliers":{"col":"social_spend","target":"feature","scale":15}}'      "" "impossible social spend values"
run type_corruption   0.6 '{"type_corruption":{"col":"tv_spend"}}'                                 "" "tv_spend exported as text"
run mnar_missing      0.8 '{"mnar_missing":{"target":"outcome"}}'                                  "" "revenue missing for the best weeks"
run correlated_block  0.9 '{"correlated_block":{"col":"tv_spend","n_copies":2}}'                   "" "tv GRPs + tv impressions copies"
run unit_mix          0.6 '{"unit_mix":{"col":"tv_spend","factor":1000}}'                          "prepare" "\$k mix-up introduced AFTER prepare"
run measurement_error 0.8 '{"measurement_error":{"col":"discount_pct"}}'                           "" "noisy discount (not a count)"
run batch_shift       0.6 '{"batch_shift":{"col":"discount_pct"}}'                                 "" "hidden batch on discount"
echo "== rounds 28-33: HOLD-OUT 2 — never seen by either explainer pass"
run target_leakage    0.9 '{"target_leakage":{"name":"conversion_rate","noise_sd":1.2}}'          "" "a very noisy leak (1.2 sd)"
run heavy_tails       0.7 ''                                                                       "" "heavy-tailed revenue noise"
run outliers          0.7 '{"outliers":{"target":"outcome"}}'                                      "prepare" "revenue spikes introduced AFTER prepare"
run unit_mix          0.6 '{"unit_mix":{"col":"email_sends","factor":10}}'                         "" "email_sends x10 for some rows (small factor)"
run type_corruption   0.6 '{"type_corruption":{"col":"revenue"}}'                                  "" "revenue itself exported as text"
run mnar_missing      0.8 '{"mnar_missing":{"col":"search_spend","target":"feature"}}'             "" "search spend missing for the biggest weeks"
echo "== dose sweeps"
for spec in 'target_leakage {"name":"attributed_revenue"}' 'unit_mix {"col":"tv_spend","factor":1000}' 'outliers {"target":"outcome"}' 'batch_shift {"col":"search_spend"}' 'measurement_error {"col":"email_sends"}' 'mnar_missing {"target":"outcome"}'; do set -- $spec; skilljab sweep --skill $S --stone $1 --levels 6 --fixed "$2" >/dev/null; echo "   swept $1"; done
skilljab report --skill $S >/dev/null
skilljab status --skill $S | grep -E '"jabbed"|"reason"|n_antibodies'
echo "report: $S/history/report.html   skill: $S/SKILL.md"
