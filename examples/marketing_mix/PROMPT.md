# The prompt

> *"Here's our weekly marketing data — one row per region per week: spend on TV, paid search, social and email, the discount we ran, the region and the quarter, and the revenue that week. Build a model that tells me which channels actually drive revenue and what the return per dollar is for each one. Marketing wants to move budget next quarter."*

This is the everyday business question people hand to an AI. The pipeline in this folder is what Claude writes for it — clean, idiomatic, and exactly what a marketing analyst would ship: drop incomplete weeks, one-hot the region and quarter, fit a linear regression of revenue on everything, report the coefficient per channel as "return per dollar".

Nothing here is about biology. That is the point of this example: SkillJab is for any analysis with a number at the end.
