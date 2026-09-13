---
description: The whole vaccine - loop /skilljab:test then /skilljab:improve until a round is clean or a round budget is spent.
argument-hint: [skill dir] [--rounds 3]
---

# /skilljab:jab $ARGUMENTS

Run `/skilljab:test`; if it produced silent failures run `/skilljab:improve`; repeat up to `--rounds` (default 3) or until `skilljab status --skill <dir>` says `jabbed: true`. Increase `--level` by 0.15 each clean round so the stones keep biting. At the end: `skilljab report --skill <dir>` and give the user the report path, the skill version, the number of antibodies, and the one sentence from the report headline.
