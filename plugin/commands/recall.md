---
description: The blurry-friend interview - the user describes something odd from a past run badly; enumerate the neighbourhood so they can recognize it; file what they recognize as a user_recognized antibody.
argument-hint: [skill dir] [a vague description]
---

# /skilljab:recall $ARGUMENTS

Follow the `skilljab-core` discipline. Locate the skill dir and read its `pipeline.yaml` stages.

1. If the user gave no description, ask for one and say explicitly: "describe it badly — where roughly, what it looked like, one detail; I'll list what it could have been."
2. Dose the blur: keep symptom + location + one attribute. Enumerate 4–8 concrete candidates specific to this pipeline's tools and domain, each with the stage and the stone that would reproduce it (`skilljab stones list`). Present them as a numbered list and ask which one(s) they recognize.
3. For each recognized candidate: `skilljab antibody add --skill <dir> --json '{... "evidence": "user_recognized", "provenance": {"trick": "blurry_probe"} ...}'` with a heads-up in the user's own words, and a `check` only if a cheap one exists.
4. For unrecognized but plausible candidates, append them to the next round's `candidates.json` as `elicited_unverified` — say nothing to the user about them; they will be stoned.
5. `skilljab skill render --skill <dir>`; show the user what was added.
