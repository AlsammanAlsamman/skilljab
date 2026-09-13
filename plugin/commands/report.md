---
description: Render the SkillJab crash-test report (self-contained HTML) for a jabbed pipeline and summarize it in three lines.
argument-hint: [skill dir]
---

# /skilljab:report $ARGUMENTS

`skilljab report --skill <dir>` then read `history/report.json` and tell the user: the headline sentence, the weakest stage with its star rating, and the predicted total runtime (with the checkpoint suggestion if any). Give the path to `history/report.html`. If the Artifact tool is available, offer to publish it.
