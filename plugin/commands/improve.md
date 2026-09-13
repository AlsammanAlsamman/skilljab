---
description: Turn a round's silent failures into antibodies - explainer wakes up domain knowledge, writes checkers, mitigations, heads-ups; re-tests until the round is clean; bumps the skill version.
argument-hint: [skill dir] [--round N]
---

# /skilljab:improve $ARGUMENTS

Follow the `skilljab-core` discipline. Locate the skill dir and the round (default: last). Read `skilljab round show --skill <dir> --round N` (without reveal) to confirm there is something to improve; if the class is clean, say so and stop.

1. Spawn the `explainer` with the skill dir and round N. It is the only role that may `--reveal`.
2. When it returns, re-test the same stones: `skilljab round new`, then `skilljab round stones --skill <dir> <same stones> --level <same>` (copy from `history/round-N/private/stones.json` — you may read it now, the round is over), then spawn a fresh `analyst` for the new round.
3. If the new round is `caught`: `skilljab skill render --skill <dir>`, `skilljab report --skill <dir>`, and show the user each antibody in one plain line plus the report path. If still `silent`: send the explainer back once with the new verdict; if it fails twice, tell the user exactly which stone resisted and stop.
4. Ask: "Anything odd you remember from past runs of this pipeline? Describe it badly." → if yes, run `/skilljab:recall`.
